"""Select a reporting scope without changing immutable training protocols."""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.data.tasks import TASKS
from self_evolution.evaluation.report import summarize
from self_evolution.io import atomic_write, digest, file_hash, read_json


def load_scope(run, config):
    path = Path(run) / "execution_scope.json"
    if not path.exists():
        return None
    scope = read_json(path)
    return validate_scope(scope, config)


def validate_scope(scope, config):
    """Check a candidate before publishing it in the run directory."""
    selected, deferred = scope["selected_tasks"], scope["deferred_tasks"]
    if (
        scope["schema"] != 1
        or scope["config_hash"] != digest(config)
        or not selected
        or len(selected) != len(set(selected))
        or len(deferred) != len(set(deferred))
        or set(selected) & set(deferred)
        or set(selected) | set(deferred) != set(TASKS)
    ):
        raise ValueError("execution scope has invalid coverage or configuration")
    return scope


def validate_report(root, task, config):
    """Require the complete predeclared chain and both controls before plotting."""
    result = read_json(root / "report.json")
    if read_json(root / "protocol.json") != config:
        raise ValueError("report protocol mismatch")
    chain = read_json(root / "chain_manifest.json")
    rounds = list(range(config["max_round"] + 1))
    expected = {
        (mode, r)
        for mode in ["evolution", "original", "cumulative"]
        for r in rounds
        if mode == "evolution" or r > 0
    }
    rows = result["rows"]
    if (
        result["task"] != task
        or result["seed"] != config["seed"]
        or len(rows) != len(expected)
        or {(row["mode"], row["round"]) for row in rows} != expected
        or chain["status"] != "complete"
        or chain["config_hash"] != digest(config)
        or [stage["round"] for stage in chain["stages"]] != rounds
    ):
        raise ValueError("report is missing a required round/control or has a different identity")
    context = root / "execution_context.json"
    if context.exists() and read_json(context)["status"] != "complete":
        raise ValueError("task execution is not complete")
    for row in rows:
        if (
            row["task"] != task
            or row["seed"] != config["seed"]
            or any(
                not isinstance(row[key], (float, int))
                or not math.isfinite(row[key])
                or row[key] < 0
                for key in ["train_mae", "val_mae", "test_mae"]
            )
        ):
            raise ValueError("report contains invalid metrics or task identity")
        r, mode = row["round"], row["mode"]
        stage = (
            root / f"round_{r:03d}"
            if mode == "evolution"
            else root / "controls" / mode / f"round_{r:03d}"
        )
        training = read_json(stage / "training.json")
        if (
            training["checkpoint_sha256"] != row["checkpoint_sha256"]
            or training["identity"]["config_hash"] != digest(config)
            or training["identity"]["round"] != r
            or training["identity"]["mode"] != mode
            or training["optimizer_steps"] != row["optimizer_steps"]
            or (
                mode == "evolution"
                and chain["stages"][r]["checkpoint_sha256"] != row["checkpoint_sha256"]
            )
            or (
                mode == "cumulative"
                and row["optimizer_steps"] != chain["stages"][r]["cumulative_steps"]
            )
        ):
            raise ValueError("report stage/control identity mismatch")
    evolution = [row for row in rows if row["mode"] == "evolution"]
    best = min(evolution, key=lambda row: (row["val_mae"], row["round"]))
    if result["validation_selected_round"] != best["round"]:
        raise ValueError("selected round does not follow validation metrics")
    return result


def summarize_scope(run, config):
    run = Path(run)
    scope = load_scope(run, config)
    if scope is None:
        return summarize(run, config)
    run.mkdir(parents=True, exist_ok=True)
    rejected = {}
    # A report-only view reuses the pinned plotter without changing its task registry.
    with tempfile.TemporaryDirectory(prefix="scope-view-", dir=run) as temporary:
        view = Path(temporary)
        for task in scope["selected_tasks"]:
            source = run / "cgcnn" / task / f"seed_{config['seed']}"
            target = view / "cgcnn" / task / f"seed_{config['seed']}"
            if not (source / "report.json").exists():
                continue
            try:
                result = validate_report(source, task, config)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                rejected[task] = str(exc)
                continue
            atomic_write(target / "report.json", result)
        summary = summarize(view, config)
        for row in summary["coverage"]:
            task = row["task"]
            if task in scope["deferred_tasks"]:
                row.update(status="deferred", reason="outside the current user-selected scope")
            elif task in rejected:
                row.update(status="incomplete", reason=rejected[task])
            elif (run / "cgcnn" / task / f"seed_{config['seed']}" / "failure.json").exists():
                row.update(status="failed", reason="see task failure.json")
        summary.update(
            required_tasks=len(scope["selected_tasks"]),
            catalog_tasks=len(TASKS),
            scope={**scope, "sha256": file_hash(run / "execution_scope.json")},
        )
        summary["completed_tasks"] = sum(row["status"] == "complete" for row in summary["coverage"])
        summary["status"] = (
            "complete" if summary["completed_tasks"] == summary["required_tasks"] else "partial"
        )
        atomic_write(view / "reports/summary.json", summary)
        destination = run / "reports"
        if destination.exists():
            archive = run / "reports_archive" / str(time.time_ns())
            archive.parent.mkdir(exist_ok=True)
            destination.replace(archive)
        shutil.move(str(view / "reports"), destination)
    return summary
