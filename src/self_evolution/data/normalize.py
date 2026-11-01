"""Audited resolution of repeated source IDs, without choosing conflicting ground truth."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json

from .tasks import TASKS, numeric_label


def source_hash(row: dict) -> str:
    # Raw JARVIS can contain NaNs; only provenance serialization permits them.
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()


def canonicalize_records(records: list[dict]) -> tuple[list[dict], dict]:
    groups = defaultdict(list)
    for index, row in enumerate(records):
        jid = row.get("jid")
        if not isinstance(jid, str) or not jid:
            raise ValueError(f"invalid source ID at raw row {index}")
        groups[jid].append((index, row))
    unique, duplicates, conflicts = [], {}, defaultdict(list)
    for jid, indexed in groups.items():
        rows = [row for _, row in indexed]
        canonical = dict(rows[0])
        if len(rows) > 1:
            structures = {source_hash(row["atoms"]) for row in rows}
            if len(structures) != 1:
                raise ValueError(f"conflicting structures for repeated source ID: {jid}")
            duplicates[jid] = {
                "raw_indices": [i for i, _ in indexed],
                "record_sha256": [source_hash(row) for row in rows],
            }
            for task in TASKS:
                values = sorted(
                    {
                        value
                        for row in rows
                        if (value := numeric_label(row.get(task))[0]) is not None
                    }
                )
                if len(values) > 1:
                    canonical[task] = "na"
                    conflicts[task].append({"jid": jid, "values": values})
                elif len(values) == 1:
                    canonical[task] = values[0]
        unique.append(canonical)
    audit = {
        "policy": "same_id_same_structure_merge; exact_conflicting_finite_labels_excluded_per_task",
        "raw_records": len(records),
        "unique_structures": len(unique),
        "duplicate_rows_removed": len(records) - len(unique),
        "duplicate_ids": duplicates,
        "label_conflicts": dict(conflicts),
    }
    return unique, audit
