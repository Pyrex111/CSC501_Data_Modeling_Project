"""Execute graph-backed create/update/delete and rejected writes on a temporary graph."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dal.seed_data import seed
from semantic import repositories as repo
from semantic.codec import export_connection
from semantic.store import GraphDatabase
from semantic.vocabulary import ROOT, schema_connection


def main():
    sql = schema_connection()
    try:
        seed(sql, ROOT)
        db = GraphDatabase(capture_root=ROOT)
        db.load_data(export_connection(sql))
    finally:
        sql.close()
    payload = {
        "ETFId": 1,
        "AllocationDimensionId": 1,
        "SourceDocumentId": 1,
        "AllocationAsOfDate": "2026-07-31",
        "SourceLocator": "synthetic-crud-demo",
        "BasisNote": "Wholly fictional CRUD demonstration",
        "CoverageStatus": "Complete",
        "Entries": [
            {"AllocationCategoryId": 1, "WeightFraction": 0.3},
            {"AllocationCategoryId": 2, "WeightFraction": 0.7},
        ],
    }
    disclosure = repo.create_disclosure(db, payload)
    entries = disclosure["Entries"]
    first, second = entries[0]["EntryId"], entries[1]["EntryId"]
    events = [
        {"operation": "create", "snapshot": disclosure["SnapshotId"], "result": "saved"}
    ]

    def reject(name, operation):
        before = db.snapshot()
        try:
            operation()
        except repo.BusinessRuleError as exc:
            assert db.snapshot() == before
            events.append(
                {
                    "operation": name,
                    "result": "rejected; graph unchanged",
                    "message": str(exc),
                }
            )
        else:
            raise AssertionError(name + " unexpectedly succeeded")

    reject("invalid Complete edit", lambda: repo.update_entry_weight(db, first, 0.1))
    repo.update_weights_batch(
        db,
        [
            {"EntryId": first, "WeightFraction": 0.4},
            {"EntryId": second, "WeightFraction": 0.6},
        ],
    )
    events.append({"operation": "coherent batch update", "result": "saved"})
    reject("invalid Complete deletion", lambda: repo.delete_entry(db, first))
    payload.update(
        CoverageStatus="Partial", SourceLocator="synthetic-partial-crud-demo"
    )
    partial = repo.create_disclosure(db, payload)
    entries = partial["Entries"]
    repo.delete_entry(db, entries[0]["EntryId"])
    events.append({"operation": "Partial entry deletion", "result": "saved"})
    reject("final-entry deletion", lambda: repo.delete_entry(db, entries[1]["EntryId"]))
    print(json.dumps(events, indent=2))
    return events


if __name__ == "__main__":
    main()
