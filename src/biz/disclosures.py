"""Business logic between the Flask routes and the DAL (Shahmeer).

Turns raw form/query-string text into validated values, builds the payload for
an atomic snapshot-and-entries insert, and translates database and rule errors
into plain messages. No SQL is written here and no HTML is produced here.
"""
from __future__ import annotations

import datetime
import json
import math
import re
import sqlite3
from itertools import zip_longest
from typing import Any, Mapping

from dal.repositories import RepositoryError, ValidationError

COVERAGE_STATUSES = ("Complete", "Partial", "Unknown")
DIMENSIONS = ("Sector", "Geography")


# --------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------
def parse_id(raw: Any, label: str) -> int:
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{label} is missing or invalid.")


def parse_weight(raw: Any) -> float:
    text = "" if raw is None else str(raw).strip()
    if not text:
        raise ValidationError("Weight is required.")
    try:
        value = float(text)
    except ValueError:
        raise ValidationError("Weight must be a number.")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValidationError("Weight must be a fraction between 0 and 1 (for example 0.25 for 25%).")
    return value


def parse_date(raw: Any, label: str) -> str:
    text = "" if raw is None else str(raw).strip()
    if not text:
        raise ValidationError(f"{label} is required.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValidationError(f"{label} must use the format YYYY-MM-DD.")
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        raise ValidationError(f"{label} is not a real calendar date.")
    return text


def _required_text(raw: Any, label: str) -> str:
    text = "" if raw is None else str(raw).strip()
    if not text:
        raise ValidationError(f"{label} is required.")
    return text


def normalize_ticker(raw: Any) -> str | None:
    text = "" if raw is None else str(raw).strip().upper()
    return text or None


def parse_search(args: Mapping[str, str]) -> dict:
    """Search filters from the query string; blank means 'do not filter'."""
    dimension = (args.get("dimension") or "").strip() or None
    if dimension is not None and dimension not in DIMENSIONS:
        raise ValidationError("Dimension must be Sector or Geography.")
    as_of = (args.get("as_of") or "").strip() or None
    if as_of is not None:
        as_of = parse_date(as_of, "As-of date")
    return {"ticker": normalize_ticker(args.get("ticker")), "dimension": dimension, "as_of": as_of}


def parse_new_disclosure(form: Any) -> dict:
    """Validate the create form and build the payload for create_disclosure."""
    payload: dict[str, Any] = {
        "ETFId": parse_id(form.get("etf_id"), "ETF"),
        "AllocationDimensionId": parse_id(form.get("dimension_id"), "Dimension"),
        "SourceDocumentId": parse_id(form.get("source_id"), "Source document"),
        "AllocationAsOfDate": parse_date(form.get("as_of_date"), "As-of date"),
        "BasisNote": _required_text(form.get("basis_note"), "Basis note"),
        "SourceLocator": _required_text(form.get("source_locator"), "Source locator"),
        "CoverageStatus": (form.get("coverage_status") or "").strip(),
    }
    if payload["CoverageStatus"] not in COVERAGE_STATUSES:
        raise ValidationError("Coverage must be Complete, Partial or Unknown.")

    entries, seen = [], set()
    for category, weight in zip_longest(form.getlist("category"), form.getlist("weight"), fillvalue=""):
        category, weight = (category or "").strip(), (weight or "").strip()
        if not category and not weight:
            continue  # unused row
        if not category:
            raise ValidationError("Every weight needs a category.")
        if not weight:
            raise ValidationError("Every category needs a weight.")
        category_id = parse_id(category, "Category")
        if category_id in seen:
            raise ValidationError("A category can appear only once in a disclosure.")
        seen.add(category_id)
        entries.append({"AllocationCategoryId": category_id, "WeightFraction": parse_weight(weight)})
    if not entries:
        raise ValidationError("Add at least one allocation entry.")
    payload["Entries"] = entries
    return payload


# --------------------------------------------------------------------------
# Presentation helpers (data only, no HTML)
# --------------------------------------------------------------------------
def category_scopes(categories: list[dict], sources: list[dict]) -> list[dict]:
    """Which categories may be used for which source/locator.

    A category with a known classification edition is valid for any disclosure
    in its dimension. Any other category is tied to one captured source, locator
    and dimension, recorded in its ContextKey; only those can be saved.
    """
    by_capture = {(s["Url"], s["RetrievedAt"]): s["SourceDocumentId"] for s in sources}
    out = []
    for c in categories:
        item = {"id": c["CategoryId"], "dim": c["AllocationDimensionId"],
                "label": c["Label"], "source": "", "locator": "", "hint": ""}
        if c["Version"] is not None:
            item["hint"] = f'{c["SchemeName"]} {c["Version"]}'
        else:
            try:
                url, retrieved, locator, _dimension = json.loads(c["ContextKey"].split(":", 1)[1])
            except (ValueError, IndexError):
                continue
            source_id = by_capture.get((url, retrieved))
            if source_id is None:
                continue
            item.update(source=source_id, locator=locator, hint=f"source {source_id}, {locator}")
        out.append(item)
    return out


def describe_context(entry: Mapping[str, Any]) -> str:
    if entry.get("SchemeName") and entry.get("Version"):
        return f'{entry["SchemeAuthority"]}: {entry["SchemeName"]} {entry["Version"]}'
    if entry.get("SchemeName"):
        return f'{entry["SchemeName"]} (edition unknown)'
    return "Disclosure-local label (meaning limited to this source and locator)"


def annotate_entries(entries: list[dict]) -> list[dict]:
    return [dict(e, ContextLabel=describe_context(e)) for e in entries]


def total_weight(entries: list[dict]) -> float:
    return round(sum(e["WeightFraction"] for e in entries), 6)


# --------------------------------------------------------------------------
# Error translation
# --------------------------------------------------------------------------
_RULES = (
    (re.compile(r"AllocationSnapshot \d+: complete total is ([\d.]+), expected 1"),
     lambda m: f"A Complete disclosure must add up to 1 (allowed error 0.005). This change would make the total {m.group(1)}."),
    (re.compile(r"AllocationSnapshot \d+: at least one entry is required"),
     lambda m: "A disclosure must keep at least one entry."),
    (re.compile(r"AllocationEntry \d+: ContextKey does not match"),
     lambda m: "A selected category does not belong to this source document and locator."),
    (re.compile(r"AllocationEntry \d+: category/snapshot dimensions disagree"),
     lambda m: "Every category must belong to the selected dimension."),
)


def _translate(line: str) -> str:
    for pattern, build in _RULES:
        match = pattern.search(line)
        if match:
            return build(match)
    return line


def friendly_error(exc: BaseException) -> str:
    if isinstance(exc, RepositoryError):
        return " ".join(dict.fromkeys(_translate(l) for l in str(exc).splitlines() if l.strip()))
    if isinstance(exc, sqlite3.IntegrityError):
        text = str(exc)
        if "dimensions must agree" in text:
            return "Every category must belong to the selected dimension."
        if "UNIQUE constraint failed" in text:
            return "That record already exists (same ETF, dimension, date, source and locator)."
        if "FOREIGN KEY" in text:
            return "A selected ETF, source document or category does not exist."
        return "The database rejected the change. Nothing was saved."
    if isinstance(exc, sqlite3.Error):
        return "The database could not complete the request. Nothing was saved."
    return "Something went wrong. Nothing was saved."
