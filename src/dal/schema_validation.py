"""Transaction-level rules supplementing schema.sql; no application CRUD here.

Use validated_transaction for application writes that may affect these rules.
SQL constraints/triggers protect row-local integrity and matching dimensions.
This module protects parent-side minimums, category contexts and complete totals.
Owner: Taimoor Shahzad. AI assistance is disclosed in the contribution notes.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import math
from pathlib import Path
import sqlite3
from typing import Iterator

DEFAULT_TOTAL_TOLERANCE = 0.005  # fraction: 0.5 percentage points, inclusive


class ModelIntegrityError(ValueError):
    """The proposed committed state violates the documented model rules."""


def _context(prefix: str, *parts: str) -> str:
    if any(not isinstance(part, str) or not part.strip() for part in parts):
        raise ValueError('Context components must be nonempty strings')
    return prefix + ':' + json.dumps(parts, ensure_ascii=True, separators=(',', ':'))


def scheme_context(authority: str, name: str, version: str) -> str:
    """Context for a classification edition whose authority/name/version are known."""
    return _context('scheme', authority, name, version)


def disclosure_context(url: str, retrieved_at: str, locator: str, dimension: str) -> str:
    """Disclosure-local context when a scheme or its edition is unresolved."""
    return _context('source', url, retrieved_at, locator, dimension)


def validate_database(
    connection: sqlite3.Connection,
    *,
    total_tolerance: float = DEFAULT_TOTAL_TOLERANCE,
    capture_root: Path | str | None = None,
) -> None:
    """Raise ModelIntegrityError if the current state must not be committed.

    Pass the repository root as capture_root to check retained files as well.
    No network calls are performed. A file's existence is not verification of its
    contents or of the truth of the reported observation.
    """
    if not isinstance(total_tolerance, (int, float)) or not math.isfinite(total_tolerance):
        raise ValueError('total_tolerance must be a finite number')
    if not 0 <= total_tolerance < 1:
        raise ValueError('total_tolerance must be at least zero and less than one')
    if connection.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
        raise ModelIntegrityError('Enable PRAGMA foreign_keys = ON before starting a transaction')

    issues: list[str] = []
    for table, row_id, parent, _ in connection.execute('PRAGMA foreign_key_check'):
        issues.append(f'{table} row {row_id}: missing parent in {parent}')

    for (etf_id,) in connection.execute('''
        SELECT F.Id FROM ETF AS F
        WHERE NOT EXISTS (SELECT 1 FROM ETFIdentifier AS I WHERE I.ETFId = F.Id)
    '''):
        issues.append(f'ETF {etf_id}: at least one identifier is required')

    for (snapshot_id,) in connection.execute('''
        SELECT S.Id FROM AllocationSnapshot AS S
        WHERE NOT EXISTS (
            SELECT 1 FROM AllocationEntry AS E WHERE E.AllocationSnapshotId = S.Id
        )
    '''):
        issues.append(f'AllocationSnapshot {snapshot_id}: at least one entry is required')

    for snapshot_id, total in connection.execute('''
        SELECT S.Id, SUM(E.WeightFraction)
        FROM AllocationSnapshot AS S
        JOIN AllocationEntry AS E ON E.AllocationSnapshotId = S.Id
        WHERE S.CoverageStatus = 'Complete'
        GROUP BY S.Id
    '''):
        if abs(total - 1.0) > total_tolerance + 1e-12:
            issues.append(f'AllocationSnapshot {snapshot_id}: complete total is {total:.12g}, expected 1')

    # Interpret the context per entry: unresolved labels cannot silently cross
    # source capture/block boundaries; known contexts include their version.
    for row in connection.execute('''
        SELECT E.Id, C.ContextKey, C.AllocationDimensionId, S.AllocationDimensionId,
               CS.SchemeAuthority, CS.SchemeName, CS.Version,
               D.Url, D.RetrievedAt, S.SourceLocator, A.DimensionName
        FROM AllocationEntry AS E
        JOIN AllocationCategory AS C ON C.Id = E.AllocationCategoryId
        JOIN AllocationSnapshot AS S ON S.Id = E.AllocationSnapshotId
        JOIN SourceDocument AS D ON D.Id = S.SourceDocumentId
        JOIN AllocationDimension AS A ON A.Id = S.AllocationDimensionId
        LEFT JOIN ClassificationScheme AS CS ON CS.Id = C.ClassificationSchemeId
    '''):
        entry_id, actual, category_dimension, snapshot_dimension, authority, name, version, url, retrieved, locator, dimension = row
        if category_dimension != snapshot_dimension:
            issues.append(f'AllocationEntry {entry_id}: category/snapshot dimensions disagree')
        expected = (scheme_context(authority, name, version) if version is not None
                    else disclosure_context(url, retrieved, locator, dimension))
        if actual != expected:
            issues.append(f'AllocationEntry {entry_id}: ContextKey does not match its classification/source context')

    if capture_root is not None:
        base = Path(capture_root).resolve()
        for source_id, reference in connection.execute('SELECT Id, CapturedFileRef FROM SourceDocument'):
            path = (base / reference).resolve()
            if not path.is_relative_to(base) or not path.is_file():
                issues.append(f'SourceDocument {source_id}: retained capture is missing or outside capture_root')

    if issues:
        raise ModelIntegrityError('\n'.join(issues))


@contextmanager
def validated_transaction(
    connection: sqlite3.Connection,
    *,
    total_tolerance: float = DEFAULT_TOTAL_TOLERANCE,
    capture_root: Path | str | None = None,
) -> Iterator[sqlite3.Connection]:
    """Atomically save a valid final state; roll back the whole unit on failure.

    The caller supplies an open connection with no transaction in progress and
    foreign keys already enabled. Do not commit, executescript or start another
    transaction inside the block. Parent rows and children can be created in the
    same block. An error must propagate out of the block for rollback.
    """
    if connection.in_transaction:
        raise ValueError('validated_transaction requires no active transaction')
    if connection.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
        raise ModelIntegrityError('Enable foreign keys before validated_transaction')
    connection.execute('BEGIN')
    try:
        yield connection
        if not connection.in_transaction:
            raise RuntimeError('The transaction was ended inside validated_transaction')
        validate_database(connection, total_tolerance=total_tolerance, capture_root=capture_root)
        connection.execute('COMMIT')
    except BaseException:
        if connection.in_transaction:
            connection.execute('ROLLBACK')
        raise
