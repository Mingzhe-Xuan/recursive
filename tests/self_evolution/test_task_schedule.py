import copy
import importlib.util
from pathlib import Path

import pytest

from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, digest, file_hash


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, Path("scripts/self_evolution") / f"{name}.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def audit_fixture(graphs_hash):
    return {
        "graphs_sha256": graphs_hash,
        "dataset_sha256": "test-snapshot",
        "tasks": [
            {"task": name, "status": "ready", "label_audit": {"valid": i + 1}}
            for i, name in enumerate(TASKS)
        ],
    }


def test_balanced_schedule_preserves_started_wave_and_covers_all_tasks():
    scheduler = module("task_schedule")
    names = list(TASKS)
    plan = scheduler.build_schedule(
        audit_fixture("graphs"), {"seed": 123}, "audit", protected={0: names[:4]}
    )
    groups = scheduler.validate_groups(plan)
    assert groups[0]["tasks"] == names[:4]
    assert [task for group in groups[1:] for task in group["tasks"]] == names[:3:-1]
    assert set(task for group in groups for task in group["tasks"]) == set(TASKS)
    assert len(groups) == 8 and len(groups[-1]["tasks"]) == 1
    bad = copy.deepcopy(plan)
    bad["waves"][1]["tasks"][0] = names[0]
    with pytest.raises(ValueError, match="exactly once"):
        scheduler.validate_groups(bad)
    with pytest.raises(ValueError, match="overlap"):
        scheduler.build_schedule(
            audit_fixture("graphs"),
            {"seed": 123},
            "audit",
            protected={0: names[:4], 1: names[:4]},
        )


def test_runtime_schedule_rejects_context_drift_and_started_wave_changes(tmp_path):
    scheduler = module("task_schedule")
    prepared, run = tmp_path / "prepared", tmp_path / "run"
    config = {"seed": 123}
    atomic_write(prepared / "graphs/manifest.json", {"test": "geometry"})
    audit = audit_fixture(file_hash(prepared / "graphs/manifest.json"))
    atomic_write(prepared / "audit.json", audit)
    first = list(TASKS)[:4]
    plan = scheduler.build_schedule(
        audit, config, file_hash(prepared / "audit.json"), protected={0: first}
    )
    assert scheduler.validate_schedule(plan, run, prepared, config) == plan
    assert not (run / "pool/task_schedule.json").exists()
    atomic_write(run / "pool/task_schedule.json", plan)
    ledger = {"wave": 0, "tasks": first, "config_hash": digest(config)}
    atomic_write(run / "pool/wave_000/execution.json", ledger)
    assert scheduler.load_schedule(run, prepared, config) == plan
    with pytest.raises(ValueError, match="source/configuration"):
        scheduler.load_schedule(run, prepared, {"seed": 42})
    ledger["tasks"] = list(reversed(first))
    atomic_write(run / "pool/wave_000/execution.json", ledger)
    with pytest.raises(ValueError, match="already started"):
        scheduler.load_schedule(run, prepared, config)
    ledger["tasks"] = first
    atomic_write(run / "pool/wave_000/execution.json", ledger)
    atomic_write(prepared / "audit.json", {**audit, "changed": True})
    with pytest.raises(ValueError, match="source/configuration"):
        scheduler.load_schedule(run, prepared, config)


def test_dispatcher_uses_runtime_group_membership(tmp_path, monkeypatch):
    pool = module("execution_pool")
    scheduler = module("task_schedule")
    config = {"seed": 123}
    plan = scheduler.build_schedule(
        audit_fixture("graphs"), config, "audit", protected={0: list(TASKS)[:4]}
    )
    launched = []

    class Completed:
        def __init__(self, command, **kwargs):
            launched.append((command[2], command[command.index("--task") + 1]))

        def poll(self):
            return 0

        def wait(self, **kwargs):
            return 0

    monkeypatch.setattr(pool.subprocess, "Popen", Completed)
    result = pool.run_wave(
        tmp_path / "prepared",
        tmp_path / "run",
        tmp_path / "config.json",
        config,
        1,
        4,
        "cpu",
        schedule=plan,
    )
    expected = plan["waves"][1]["tasks"]
    assert result["tasks"] == expected and result["status"] == "complete"
    assert [task for action, task in launched if action == "run"] == expected
    assert [task for action, task in launched if action == "evaluate"] == expected
