import copy
import csv
import importlib.util
from pathlib import Path
import sys
import subprocess

import pytest

from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, digest, read_json

sys.path.insert(0, str(Path("scripts/self_evolution").resolve()))


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, Path("scripts/self_evolution") / f"{name}.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture(run):
    config = {"seed": 123, "max_round": 5}
    selected = list(TASKS)[:4]
    scope = {
        "schema": 1,
        "name": "four-properties",
        "config_hash": digest(config),
        "selected_tasks": selected,
        "deferred_tasks": list(TASKS)[4:],
    }
    atomic_write(run / "execution_scope.json", scope)
    for task in selected:
        root = run / "cgcnn" / task / "seed_123"
        atomic_write(root / "protocol.json", config)
        stages, rows, cumulative = [], [], 0
        for r in range(6):
            cumulative += 10
            stages.append(
                {"round": r, "checkpoint_sha256": f"evolution-{r}", "cumulative_steps": cumulative}
            )
        atomic_write(
            root / "chain_manifest.json",
            {"status": "complete", "config_hash": digest(config), "stages": stages},
        )
        for mode in ["evolution", "original", "cumulative"]:
            for r in range(6):
                if mode != "evolution" and r == 0:
                    continue
                steps = stages[r]["cumulative_steps"] if mode == "cumulative" else 10
                row = {
                    "task": task,
                    "unit": TASKS[task],
                    "seed": 123,
                    "mode": mode,
                    "round": r,
                    "checkpoint_sha256": f"{mode}-{r}",
                    "optimizer_steps": steps,
                    "train_mae": 0.1,
                    "val_mae": 0.8 / (r + 1),
                    "test_mae": 1 / (r + 1),
                    "relative_test_improvement": 1 - 1 / (r + 1),
                    "cumulative_training_validation_seconds": r + 1,
                    "cumulative_cache_seconds": r + 1,
                    "full_chain_seconds_per_batch": 0.001 * (r + 1),
                }
                rows.append(row)
                stage = (
                    root / f"round_{r:03d}"
                    if mode == "evolution"
                    else root / "controls" / mode / f"round_{r:03d}"
                )
                atomic_write(
                    stage / "training.json",
                    {
                        "checkpoint_sha256": row["checkpoint_sha256"],
                        "optimizer_steps": steps,
                        "identity": {"config_hash": digest(config), "round": r, "mode": mode},
                    },
                )
        atomic_write(
            root / "report.json",
            {"task": task, "seed": 123, "validation_selected_round": 5, "rows": rows},
        )
    return config, scope


def test_cli_refuses_deferred_task_before_training(tmp_path):
    config, scope = fixture(tmp_path)
    config_path = tmp_path / "config.json"
    atomic_write(config_path, config)
    deferred = scope["deferred_tasks"][0]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/self_evolution/run.py",
            "run",
            "--config",
            str(config_path),
            "--output",
            str(tmp_path),
            "--prepared",
            str(tmp_path / "not-prepared"),
            "--task",
            deferred,
            "--device",
            "cpu",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "outside the current execution scope" in result.stderr
    assert not (tmp_path / "cgcnn" / deferred).exists()


def test_scope_configuration_and_default_catalog(tmp_path):
    scope_module = module("execution_scope")
    assert scope_module.load_scope(tmp_path, {}) is None
    config, scope = fixture(tmp_path)
    assert scope_module.load_scope(tmp_path, config) == scope
    assert scope_module.validate_scope(scope, config) == scope
    with pytest.raises(ValueError, match="coverage or configuration"):
        scope_module.load_scope(tmp_path, {**config, "seed": 42})
    bad = copy.deepcopy(scope)
    bad["deferred_tasks"][0] = bad["selected_tasks"][0]
    atomic_write(tmp_path / "execution_scope.json", bad)
    with pytest.raises(ValueError, match="coverage or configuration"):
        scope_module.load_scope(tmp_path, config)
    empty = tmp_path / "default"
    result = scope_module.summarize_scope(empty, config)
    assert result["required_tasks"] == 29 and result["status"] == "partial"


def test_four_tasks_complete_with_deferred_reports_excluded(tmp_path):
    scope_module = module("execution_scope")
    config, scope = fixture(tmp_path)
    excluded = scope["deferred_tasks"][0]
    atomic_write(
        tmp_path / "cgcnn" / excluded / "seed_123/report.json", {"invalid": "must not be read"}
    )
    result = scope_module.summarize_scope(tmp_path, config)
    assert (
        result["status"] == "complete"
        and result["required_tasks"] == result["completed_tasks"] == 4
    )
    assert sum(row["status"] == "deferred" for row in result["coverage"]) == 25
    assert not (tmp_path / "reports" / f"{excluded}.png").exists()
    for task in scope["selected_tasks"]:
        assert (tmp_path / "reports" / f"{task}.svg").is_file()
    with (tmp_path / "reports/metrics.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 64 and {row["task"] for row in rows} == set(scope["selected_tasks"])


@pytest.mark.parametrize(
    "defect", ["missing_control", "missing_round", "missing_training", "stale_context"]
)
def test_incomplete_required_artifacts_cannot_complete_scope(tmp_path, defect):
    scope_module = module("execution_scope")
    config, scope = fixture(tmp_path)
    task = scope["selected_tasks"][0]
    root = tmp_path / "cgcnn" / task / "seed_123"
    if defect == "missing_control":
        report = read_json(root / "report.json")
        report["rows"] = report["rows"][:-1]
        atomic_write(root / "report.json", report)
    elif defect == "missing_round":
        chain = read_json(root / "chain_manifest.json")
        chain["stages"].pop()
        atomic_write(root / "chain_manifest.json", chain)
    elif defect == "missing_training":
        (root / "controls/original/round_005/training.json").unlink()
    else:
        atomic_write(root / "execution_context.json", {"status": "training"})
    with pytest.raises((ValueError, OSError)):
        scope_module.validate_report(root, task, config)
    if defect == "missing_control":
        result = scope_module.summarize_scope(tmp_path, config)
        assert result["status"] == "partial" and result["completed_tasks"] == 3
        assert not (tmp_path / "reports" / f"{task}.png").exists()


def test_pool_enrichment_respects_selected_scope(tmp_path):
    pool = module("execution_pool")
    selected = list(TASKS)[:4]
    atomic_write(
        tmp_path / "pool/wave_000/execution.json",
        {"wave": 0, "workers": 4, "status": "complete", "tasks": selected},
    )
    summary = {
        "seed": 123,
        "required_tasks": 4,
        "coverage": [
            {"task": task, "status": "complete" if task in selected else "deferred"}
            for task in TASKS
        ],
    }
    assert pool.enrich_summary(tmp_path, copy.deepcopy(summary))["status"] == "complete"
    atomic_write(
        tmp_path / "cgcnn" / selected[0] / "seed_123/execution_context.json", {"status": "training"}
    )
    deferred = list(TASKS)[4]
    atomic_write(
        tmp_path / "cgcnn" / deferred / "seed_123/execution_context.json", {"status": "failed"}
    )
    result = pool.enrich_summary(tmp_path, copy.deepcopy(summary))
    assert result["status"] == "partial" and result["completed_tasks"] == 3
    assert (
        next(row for row in result["coverage"] if row["task"] == deferred)["status"] == "deferred"
    )
