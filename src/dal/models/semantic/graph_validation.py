"""Graph-level validation for the semantic layer (Milestone 5).

The OWL ontology in ``etf_allocations.owl`` states the semantic schema. OWL
follows the Open World Assumption, so a missing statement is not a violation and
an aggregate such as a total weight cannot be expressed at all. This module
therefore re-states the accepted Milestone 4 rules as explicit checks over an
RDF graph, and keeps a written record of which rule lives where.

Nothing here writes to the graph. Callers validate a proposed state before
committing it, mirroring ``src/dal/schema_validation.py`` on the relational side.
Owner: Mason Li, with AI assistance disclosed in the contribution notes.

Command line:
    python -m dal.models.semantic.graph_validation path/to/graph.ttl
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path
import sys
from typing import Iterable

from rdflib import Graph, Namespace, RDF, URIRef

ETF = Namespace("https://github.com/Pyrex111/CSC501_Data_Modeling_Project/ontology#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

DEFAULT_TOTAL_TOLERANCE = 0.005

# owl:inverseOf pairs declared by the ontology. rdflib performs no reasoning and
# the accepted ABox stores only the foreign-key direction (entry -> snapshot), so
# the validator closes each pair before checking. Without this, an at-least-one
# rule stated on hasEntry would fire on a perfectly valid ABox.
INVERSE_PAIRS = (
    (ETF.hasEntry, ETF.inSnapshot),
    (ETF.hasHolding, ETF.inPortfolio),
    (ETF.hasSnapshot, ETF.describesETF),
    (ETF.hasIdentifier, ETF.identifiesETF),
    (ETF.owns, ETF.ownedBy),
)


def _with_inverse_axioms(graph: Graph) -> Graph:
    """Return a read-only view with both directions of every inverse pair."""
    expanded = Graph()
    for triple in graph:
        expanded.add(triple)
    for forward, inverse in INVERSE_PAIRS:
        for subject, obj in graph.subject_objects(forward):
            expanded.add((obj, inverse, subject))
        for subject, obj in graph.subject_objects(inverse):
            expanded.add((obj, forward, subject))
    return expanded


ALLOWED_COVERAGE = {"Complete", "Partial", "Unknown"}
ALLOWED_DIMENSIONS = {"Sector", "Geography"}
ALLOWED_IDENTIFIER_SCHEMES = {"ISIN", "Ticker"}

# Columns that the accepted schema declares NOT NULL, plus the foreign keys that
# may not be null. Absence of a triple means "unknown" under the Open World
# Assumption, so a reasoner will not object to a missing value; the graph layer
# therefore restates each required slot as an explicit check for loaders.
REQUIRED_BY_CLASS = {
    ETF.Customer: ('customerNumber', 'givenName', 'familyName'),
    ETF.ETFProvider: ('legalName', 'registrationNumber', 'registrationJurisdiction'),
    ETF.Portfolio: ('portfolioReference', 'portfolioName', 'baseCurrency', 'ownedBy'),
    ETF.ETF: ('fundName', 'domicileCountryCode', 'baseCurrency', 'offeredBy'),
    ETF.ETFIdentifier: ('identifierScheme', 'identifierValue', 'identifiesETF'),
    ETF.Holding: ('inPortfolio', 'holdsETF', 'weightFraction', 'holdingAsOfDate'),
    ETF.SourceDocument: ('publishedBy', 'url', 'retrievedAt', 'capturedFileRef'),
    ETF.AllocationDimension: ('dimensionName',),
    ETF.ClassificationScheme: ('schemeAuthority', 'schemeName'),
    ETF.AllocationCategory: ('hasDimension', 'label', 'contextKey'),
    ETF.AllocationSnapshot: ('describesETF', 'hasDimension', 'supportedBy',
                             'allocationAsOfDate', 'basisNote', 'coverageStatus',
                             'sourceLocator'),
    ETF.AllocationEntry: ('inSnapshot', 'usesCategory', 'weightFraction'),
}

DATE_PROPERTIES = {ETF.holdingAsOfDate, ETF.allocationAsOfDate}
DATETIME_PROPERTIES = {ETF.retrievedAt, ETF.publishedAt}

# Rules the ontology itself states. A reasoner can report these as inconsistent
# or infer them, but none of them is enforced on write by OWL alone.
OWL_ENFORCED_RULES = (
    "class membership and subclass axioms (Portfolio, ETF, Holding, snapshots, "
    "entries and categories specialise FIBO classes)",
    "rdfs:domain and rdfs:range of every object and datatype property",
    "exactly-one and at-least-one cardinality restrictions on ownedBy, offeredBy, "
    "identifiesETF, inPortfolio, holdsETF, weightFraction, holdingAsOfDate, "
    "publishedBy, url, retrievedAt, capturedFileRef, hasDimension, describesETF, "
    "supportedBy, allocationAsOfDate, coverageStatus, inSnapshot, usesCategory, "
    "and the at-least-one entry restriction on a snapshot",
    "at-most-one classifier scheme on a category (maxQualifiedCardinality 1)",
    "owl:hasKey on Customer, ETFProvider, ETFIdentifier and AllocationDimension",
    "owl:FunctionalProperty on eleven single-valued properties",
    "the property chain hasEntry / usesCategory / hasDimension, which entails that "
    "a snapshot shares its entries' category dimension",
    "owl:disjointWith between snapshot/entry/category and between portfolio/ETF",
)

# Rules that must be checked explicitly. Each is justified on one of three grounds:
# aggregation, closed value sets, or a uniqueness constraint that involves a
# parent reference and therefore cannot be a plain owl:hasKey.
EXPLICIT_RULES = (
    "required (NOT NULL) attributes and links are present on every individual; the "
    "cardinality restrictions state the requirement, but an open world treats a "
    "missing filler as unknown rather than as invalid",
    "as-of dates and retrieval timestamps carry valid xsd:date and UTC xsd:dateTime "
    "lexical forms",
    "weight fractions lie in [0, 1] on holdings and on allocation entries",
    "a Complete snapshot's entry weights sum to 1 within the tolerance",
    "an entry's category dimension equals its snapshot's dimension (the chain axiom "
    "entails agreement but cannot flag a contradiction without an AllDifferent "
    "assertion on dimension individuals)",
    "every ETF carries at least one identifier resource",
    "every snapshot carries at least one entry",
    "coverage status, dimension name and identifier scheme use their permitted values",
    "identifier values follow the documented ISIN and ticker shapes",
    "a category's contextKey matches its scheme edition or its capture context",
    "single-valued properties hold at most one value (a functional-property clash "
    "is only visible to a reasoner)",
    "composite uniqueness that names a parent, e.g. (ETF, dimension, date, source, "
    "locator) for a snapshot",
    "the retained capture file exists when capture_root is supplied",
)


class GraphModelError(ValueError):
    """The proposed graph state violates the documented model rules."""


def _context(prefix: str, *parts: str) -> str:
    if any(not isinstance(part, str) or not part.strip() for part in parts):
        raise ValueError("Context components must be nonempty strings")
    return prefix + ":" + json.dumps(parts, ensure_ascii=True, separators=(",", ":"))


def scheme_context(authority: str, name: str, version: str) -> str:
    """Context for a classification edition whose authority/name/version are known.

    Must stay byte-identical to the relational helper so that the two models agree.
    """
    return _context("scheme", authority, name, version)


def disclosure_context(url: str, retrieved_at: str, locator: str, dimension: str) -> str:
    """Disclosure-local context when a scheme or its edition is unresolved."""
    return _context("source", url, retrieved_at, locator, dimension)


def _lit(graph: Graph, subject, predicate) -> str | None:
    for value in graph.objects(subject, predicate):
        return str(value)
    return None


def _floats(graph: Graph, subject, predicate) -> list[float]:
    values = []
    for value in graph.objects(subject, predicate):
        try:
            values.append(float(str(value)))
        except (TypeError, ValueError):
            values.append(math.nan)
    return values


def _local(term) -> str:
    """Compact label: fragment after #, else the last two path segments."""
    text = str(term)
    if "#" in text:
        return text.rsplit("#", 1)[-1]
    parts = [part for part in text.split("/") if part]
    return "/".join(parts[-2:]) if parts else text


def collect_issues(
    graph: Graph,
    *,
    total_tolerance: float = DEFAULT_TOTAL_TOLERANCE,
    capture_root: Path | str | None = None,
) -> list[str]:
    """Return every rule violation in ``graph`` as a readable message."""
    if not isinstance(total_tolerance, (int, float)) or not math.isfinite(total_tolerance):
        raise ValueError("total_tolerance must be a finite number")
    if not 0 <= total_tolerance < 1:
        raise ValueError("total_tolerance must be at least zero and less than one")

    graph = _with_inverse_axioms(graph)
    issues: list[str] = []

    # --- required slots (NOT NULL semantics under an open world) -------------
    for relation, slots in REQUIRED_BY_CLASS.items():
        for subject in graph.subjects(RDF.type, relation):
            for slot in slots:
                if not list(graph.objects(subject, ETF[slot])):
                    issues.append(
                        f"{_local(subject)}: {_local(relation)} requires {slot}"
                    )

    # --- date lexical forms -------------------------------------------------
    for predicate in DATE_PROPERTIES | DATETIME_PROPERTIES:
        for subject, value in graph.subject_objects(predicate):
            text = str(value)
            try:
                if predicate in DATETIME_PROPERTIES:
                    # rdflib re-serialises "Z" as "+00:00"; both spell UTC. Any
                    # other offset would make the stored instant ambiguous.
                    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
                        raise ValueError
                else:
                    date.fromisoformat(text)
            except ValueError:
                issues.append(
                    f"{_local(subject)}: {_local(predicate)} {text!r} is not a valid "
                    f"{'UTC dateTime' if predicate in DATETIME_PROPERTIES else 'date'}"
                )

    # --- weight ranges -------------------------------------------------------
    for predicate, label in ((ETF.weightFraction, "weight fraction"),):
        for subject, value in graph.subject_objects(predicate):
            try:
                number = float(str(value))
            except (TypeError, ValueError):
                issues.append(f"{_local(subject)}: {label} {value!r} is not a number")
                continue
            if not 0.0 <= number <= 1.0:
                issues.append(f"{_local(subject)}: {label} {number:g} is outside [0, 1]")

    # --- complete totals -----------------------------------------------------
    for snapshot in graph.subjects(RDF.type, ETF.AllocationSnapshot):
        status = _lit(graph, snapshot, ETF.coverageStatus)
        weights = [
            number
            for entry in graph.objects(snapshot, ETF.hasEntry)
            for number in _floats(graph, entry, ETF.weightFraction)
        ]
        if not weights:
            continue
        if any(math.isnan(w) for w in weights):
            continue
        total = sum(weights)
        if status == "Complete" and abs(total - 1.0) > total_tolerance + 1e-12:
            issues.append(
                f"{_local(snapshot)}: complete total is {total:.12g}, expected 1"
            )

    # --- dimension agreement -------------------------------------------------
    for entry in graph.subjects(RDF.type, ETF.AllocationEntry):
        snapshot = next(graph.objects(entry, ETF.inSnapshot), None)
        category = next(graph.objects(entry, ETF.usesCategory), None)
        if snapshot is None or category is None:
            continue
        snapshot_dimension = next(graph.objects(snapshot, ETF.hasDimension), None)
        category_dimension = next(graph.objects(category, ETF.hasDimension), None)
        if snapshot_dimension is None or category_dimension is None:
            continue
        if snapshot_dimension != category_dimension:
            issues.append(
                f"{_local(entry)}: category dimension {_local(category_dimension)} "
                f"differs from snapshot dimension {_local(snapshot_dimension)}"
            )

    # --- required identifiers ------------------------------------------------
    for fund in graph.subjects(RDF.type, ETF.ETF):
        if not list(graph.objects(fund, ETF.hasIdentifier)):
            issues.append(f"{_local(fund)}: at least one identifier is required")

    # --- nonempty disclosures ------------------------------------------------
    for snapshot in graph.subjects(RDF.type, ETF.AllocationSnapshot):
        if not list(graph.objects(snapshot, ETF.hasEntry)):
            issues.append(f"{_local(snapshot)}: at least one entry is required")

    # --- permitted values ----------------------------------------------------
    for snapshot in graph.subjects(RDF.type, ETF.AllocationSnapshot):
        status = _lit(graph, snapshot, ETF.coverageStatus)
        if status is not None and status not in ALLOWED_COVERAGE:
            issues.append(f"{_local(snapshot)}: coverage status {status!r} is not permitted")
    for dimension in graph.subjects(RDF.type, ETF.AllocationDimension):
        name = _lit(graph, dimension, ETF.dimensionName)
        if name is not None and name not in ALLOWED_DIMENSIONS:
            issues.append(f"{_local(dimension)}: dimension name {name!r} is not permitted")
    for identifier in graph.subjects(RDF.type, ETF.ETFIdentifier):
        scheme = _lit(graph, identifier, ETF.identifierScheme)
        value = _lit(graph, identifier, ETF.identifierValue)
        exchange = _lit(graph, identifier, ETF.exchangeContext)
        if scheme is None or value is None:
            continue
        if scheme not in ALLOWED_IDENTIFIER_SCHEMES:
            issues.append(f"{_local(identifier)}: identifier scheme {scheme!r} is not permitted")
            continue
        if scheme == "ISIN":
            if exchange is not None:
                issues.append(f"{_local(identifier)}: an ISIN must not carry an exchange context")
            if not (len(value) == 12 and value[:2].isalpha() and value.isalnum()
                    and value[:2].isupper() and value[11].isdigit()):
                issues.append(f"{_local(identifier)}: ISIN {value!r} has the wrong shape")
        else:
            if not exchange:
                issues.append(f"{_local(identifier)}: a ticker requires an exchange context")

    # --- context key consistency --------------------------------------------
    for category in graph.subjects(RDF.type, ETF.AllocationCategory):
        actual = _lit(graph, category, ETF.contextKey)
        if actual is None:
            issues.append(f"{_local(category)}: a context key is required")
            continue
        scheme = next(graph.objects(category, ETF.definedBy), None)
        if scheme is not None:
            authority = _lit(graph, scheme, ETF.schemeAuthority)
            name = _lit(graph, scheme, ETF.schemeName)
            version = _lit(graph, scheme, ETF.version)
            if authority and name and version:
                expected = scheme_context(authority, name, version)
                if actual != expected:
                    issues.append(
                        f"{_local(category)}: context key does not match its scheme edition"
                    )

    # --- single-valued properties -------------------------------------------
    single_valued = (
        ETF.ownedBy, ETF.offeredBy, ETF.identifiesETF, ETF.inPortfolio,
        ETF.describesETF, ETF.hasDimension, ETF.supportedBy, ETF.publishedBy,
        ETF.definedBy, ETF.inSnapshot, ETF.usesCategory,
        ETF.weightFraction, ETF.baseCurrency, ETF.customerNumber,
    )
    for subject in {s for p in single_valued for s in graph.subjects(p, None)}:
        for predicate in single_valued:
            if len(list(graph.objects(subject, predicate))) > 1:
                issues.append(
                    f"{_local(subject)}: {_local(predicate)} has more than one value"
                )

    # --- composite uniqueness naming a parent -------------------------------
    seen: dict[tuple, str] = {}
    for snapshot in graph.subjects(RDF.type, ETF.AllocationSnapshot):
        fund = next(graph.objects(snapshot, ETF.describesETF), None)
        dimension = next(graph.objects(snapshot, ETF.hasDimension), None)
        source = next(graph.objects(snapshot, ETF.supportedBy), None)
        key = (
            fund,
            dimension,
            _lit(graph, snapshot, ETF.allocationAsOfDate),
            source,
            _lit(graph, snapshot, ETF.sourceLocator),
        )
        if key in seen:
            issues.append(
                f"{_local(snapshot)}: duplicates the disclosure block of {seen[key]}"
            )
        else:
            seen[key] = _local(snapshot)

    # --- retained capture ---------------------------------------------------
    if capture_root is not None:
        base = Path(capture_root).resolve()
        for source in graph.subjects(RDF.type, ETF.SourceDocument):
            reference = _lit(graph, source, ETF.capturedFileRef)
            if reference is None:
                continue
            path = (base / reference).resolve()
            if not path.is_relative_to(base) or not path.is_file():
                issues.append(
                    f"{_local(source)}: retained capture is missing or outside capture_root"
                )

    return issues


def validate_graph(
    graph: Graph,
    *,
    total_tolerance: float = DEFAULT_TOTAL_TOLERANCE,
    capture_root: Path | str | None = None,
) -> None:
    """Raise GraphModelError listing every violation in the proposed state."""
    issues = collect_issues(graph, total_tolerance=total_tolerance, capture_root=capture_root)
    if issues:
        raise GraphModelError("\n".join(issues))


def describe_rule_split() -> str:
    """Human-readable record of which rule is expressed where."""
    lines = ["Expressed in the ontology (OWL/RDFS axioms):"]
    lines += [f"  - {rule}" for rule in OWL_ENFORCED_RULES]
    lines += ["Requires explicit validation:", ]
    lines += [f"  - {rule}" for rule in EXPLICIT_RULES]
    return "\n".join(lines)


def load_graph(path: Path | str, *, rdf_format: str | None = None) -> Graph:
    graph = Graph()
    graph.parse(str(path), format=rdf_format)
    return graph


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ETF allocation RDF graph")
    parser.add_argument("graph", type=Path, nargs="?",
                        help="RDF file to validate; omit only with --rules")
    parser.add_argument("--format", default=None,
                        help="rdflib serialisation name, e.g. turtle or xml")
    parser.add_argument("--capture-root", type=Path, default=None,
                        help="repository root used to resolve captured file references")
    parser.add_argument("--rules", action="store_true",
                        help="print the OWL/explicit rule split and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.rules:
        print(describe_rule_split())
        return 0

    if args.graph is None:
        parser.error("a graph file is required unless --rules is given")

    graph = load_graph(args.graph, rdf_format=args.format)
    issues = collect_issues(graph, capture_root=args.capture_root)
    print(f"{len(graph)} triples, {len(issues)} issue(s)")
    for issue in issues:
        print(f"  - {issue}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
