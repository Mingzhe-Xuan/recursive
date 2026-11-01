"""Immutable task grouping for pending waves; trained-task protocols remain unchanged."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.data.tasks import TASKS
from self_evolution.io import digest, file_hash, read_json


def validate_groups(schedule):
    groups = schedule["waves"]
    names = list(TASKS)
    count = (len(names) + 3) // 4
    if len(groups) != count or [g["wave"] for g in groups] != list(range(count)):
        raise ValueError("task schedule has invalid wave coverage")
    if any(len(g["tasks"]) != min(4, len(names) - 4 * g["wave"]) for g in groups):
        raise ValueError("task schedule has invalid group capacity")
    flattened = [task for group in groups for task in group["tasks"]]
    if len(flattened) != len(names) or set(flattened) != set(names):
        raise ValueError("task schedule must cover every task exactly once")
    return groups


def build_schedule(audit, config, audit_sha256, *, protected=None):
    rows = audit["tasks"]
    counts = {row["task"]: row["label_audit"]["valid"] for row in rows}
    names = list(TASKS)
    if (
        len(rows) != len(names)
        or set(counts) != set(names)
        or any(row["status"] != "ready" for row in rows)
        or any(not isinstance(n, int) or n < 1 for n in counts.values())
    ):
        raise ValueError("task schedule requires the full ready label audit")
    protected = {} if protected is None else protected
    groups = [None] * ((len(names) + 3) // 4)
    assigned = []
    for index, tasks in protected.items():
        if not 0 <= index < len(groups) or len(tasks) != min(4, len(names) - 4 * index):
            raise ValueError("protected wave has invalid group capacity")
        groups[index] = {"wave": index, "tasks": list(tasks)}
        assigned.extend(tasks)
    if len(assigned) != len(set(assigned)) or not set(assigned) <= set(names):
        raise ValueError("protected waves overlap or contain unknown tasks")
    rank = {task: i for i, task in enumerate(names)}
    remaining = sorted(set(names) - set(assigned), key=lambda task: (-counts[task], rank[task]))
    for index, group in enumerate(groups):
        if group is None:
            size = min(4, len(names) - index * 4)
            groups[index] = {"wave": index, "tasks": remaining[:size]}
            del remaining[:size]
    schedule = {
        "schema": 1,
        "config_hash": digest(config),
        "graphs_sha256": audit["graphs_sha256"],
        "dataset_sha256": audit["dataset_sha256"],
        "audit_sha256": audit_sha256,
        "planning_metric": "descending valid label counts; a workload proxy, not a speed guarantee",
        "label_counts": counts,
        "protected_waves": sorted(protected),
        "waves": groups,
    }
    validate_groups(schedule)
    return schedule


def load_schedule(run, prepared, config):
    run, prepared = Path(run), Path(prepared)
    path = run / "pool/task_schedule.json"
    if not path.exists():
        return None
    schedule = read_json(path)
    return validate_schedule(schedule, run, prepared, config)


def validate_schedule(schedule, run, prepared, config):
    """Validate an unpublished candidate as well as an installed schedule."""
    run, prepared = Path(run), Path(prepared)
    validate_groups(schedule)
    audit = read_json(prepared / "audit.json")
    if (
        schedule["schema"] != 1
        or schedule["config_hash"] != digest(config)
        or schedule["graphs_sha256"] != file_hash(prepared / "graphs/manifest.json")
        or schedule["audit_sha256"] != file_hash(prepared / "audit.json")
        or schedule["dataset_sha256"] != audit["dataset_sha256"]
        or schedule["label_counts"]
        != {row["task"]: row["label_audit"]["valid"] for row in audit["tasks"]}
    ):
        raise ValueError("task schedule source/configuration mismatch")
    for ledger in (run / "pool").glob("wave_*/execution.json"):
        existing = read_json(ledger)
        if (
            existing["config_hash"] != schedule["config_hash"]
            or existing["tasks"] != schedule["waves"][existing["wave"]]["tasks"]
        ):
            raise ValueError("task schedule would change an already started wave")
    return schedule
