import copy
import importlib.util
from pathlib import Path

import pytest

from self_evolution.cache import FeatureStore
from self_evolution.data.graphs import GraphConfig, make_graph
from self_evolution.data.tasks import grouped_split
from self_evolution.io import atomic_write, file_hash, read_json
from self_evolution.pipeline.chain import run_task
from self_evolution.evaluation.report import evaluate_task, summarize


def synthetic_prepared(root):
    graphs = root / "graphs"
    entries, labels, groups = {}, {}, {}
    for i in range(12):
        jid = f"crystal_{i:02d}"
        length = 4.8 + i * 0.1
        record = {
            "jid": jid,
            "atoms": {
                "lattice_mat": [[length, 0, 0], [0, length, 0], [0, 0, length]],
                "elements": ["Si", "Si"],
                "cartesian": False,
                "coords": [[0, 0, 0], [0.25, 0.25, 0.25]],
            },
        }
        graph = make_graph(record, GraphConfig())
        atomic_write(graphs / f"{jid}.pt", graph, tensor=True)
        entries[jid] = {
            "file": f"{jid}.pt",
            "sha256": file_hash(graphs / f"{jid}.pt"),
            "atoms": 2,
            "group": graph["group"],
        }
        labels[jid], groups[jid] = i / 12, graph["group"]
    atomic_write(
        graphs / "manifest.json",
        {
            "status": "complete",
            "failures": {},
            "entries": entries,
            "identity": {"dataset_sha256": "synthetic-test-snapshot"},
        },
    )
    task = {
        "task": "formation_energy_peratom",
        "unit": "eV/atom",
        "status": "ready",
        "labels": labels,
        "dataset_sha256": "synthetic-test-snapshot",
        "split": grouped_split(labels, groups),
    }
    atomic_write(root / "tasks/formation_energy_peratom.json", task)
    return task


def test_mixed_dataset_snapshot_is_rejected(tmp_path):
    task = synthetic_prepared(tmp_path / "prepared")
    task["dataset_sha256"] = "different-snapshot"
    atomic_write(tmp_path / "prepared/tasks/formation_energy_peratom.json", task)
    config = read_json(Path("configs/self_evolution/cgcnn_seed123.json"))
    with pytest.raises(ValueError, match="task snapshot does not match graph snapshot"):
        run_task(tmp_path / "prepared", tmp_path / "run", task["task"], config, "cpu")


def test_three_stage_pipeline_controls_and_deferred_test(tmp_path):
    prepared, run = tmp_path / "prepared", tmp_path / "run"
    task = synthetic_prepared(prepared)
    config = read_json(Path("configs/self_evolution/cgcnn_seed123.json"))
    config.update(max_round=2, threads=1)
    config["model"].update(hidden=4, convolutions=1, head_hidden=8)
    config["training"].update(epochs=2, patience=2, batch_size=4)
    config["cache"]["shard_size"] = 4
    root = run / "cgcnn/formation_energy_peratom/seed_123"
    run_task(prepared, run, task["task"], config, "cpu", stop_round=1)
    with pytest.raises(ValueError, match="complete predeclared"):
        evaluate_task(prepared, run, task["task"], config, "cpu")
    prior_hash = file_hash(root / "round_000/best.pt")
    chain = run_task(prepared, run, task["task"], config, "cpu")
    assert len(chain) == 3
    assert file_hash(root / "round_000/best.pt") == prior_hash
    assert read_json(root / "chain_verification.json")["depth"] == 2
    resource_spec = importlib.util.spec_from_file_location(
        "pilot_resources", Path("scripts/self_evolution/pilot_resources.py")
    )
    resource_module = importlib.util.module_from_spec(resource_spec)
    resource_spec.loader.exec_module(resource_module)
    hashes = {
        p: file_hash(p)
        for r in range(2)
        for p in [
            root / f"round_{r:03d}/best.pt",
            root / f"round_{r:03d}/cache/manifest.json",
            *(root / f"round_{r:03d}/cache").glob("nodes_*.pt"),
        ]
    }
    task_path = prepared / "tasks/formation_energy_peratom.json"
    unavailable = prepared / "unavailable_task.json"
    task_path.rename(unavailable)
    try:
        resources = resource_module.audit_pilot(root, prepared / "graphs", config, "cpu")
    finally:
        unavailable.rename(task_path)
    assert resources["status"] == "measured" and resources["labels_read"] is False
    assert resources["authoritative_training_outputs_modified"] is False
    assert [r["round"] for r in resources["stages"]] == [0, 1]
    for stage in resources["stages"]:
        assert stage["cache_structures"] == 12 and stage["cache_atoms"] == 24
        assert stage["cache_stored_bytes"] >= stage["cache_payload_bytes"] > 0
        assert stage["cache_stored_bytes"] >= stage["cache_shard_file_bytes"]
        assert stage["peak_torch_allocated_bytes"] is None
        assert stage["peak_torch_reserved_bytes"] is None
        assert stage["surrogate_step_seconds"] > 0
    assert all(file_hash(p) == before for p, before in hashes.items())
    different_protocol = copy.deepcopy(config)
    different_protocol["training"]["learning_rate"] = 0.02
    with pytest.raises(ValueError, match="completed protocol"):
        resource_module.audit_pilot(root, prepared / "graphs", different_protocol, "cpu")
    for r in range(1, 3):
        control = read_json(root / f"controls/cumulative/round_{r:03d}/training.json")
        assert control["optimizer_steps"] == chain[r]["cumulative_steps"]
        assert control["stop_reason"] == "matched_optimizer_steps"
        old = FeatureStore(root / f"round_{r - 1:03d}/cache")
        new = FeatureStore(root / f"round_{r:03d}/cache")
        assert new.manifest["identity"]["parent_cache_sha256"] == old.identity
    report = evaluate_task(prepared, run, task["task"], config, "cpu")
    assert len(report["rows"]) == 7
    assert all(row["test_mae"] >= 0 for row in report["rows"])
    expected = min(report["rows"][:3], key=lambda row: (row["val_mae"], row["round"]))
    assert report["validation_selected_round"] == expected["round"]
    summary = summarize(run, config)
    assert summary["completed_tasks"] == 1 and summary["status"] == "partial"
    assert (run / "reports/formation_energy_peratom.png").is_file()
    assert len(summary["coverage"]) == 29
    altered = copy.deepcopy(config)
    altered["model"]["hidden"] = 16
    with pytest.raises(ValueError, match="immutable protocol"):
        run_task(prepared, run, task["task"], altered, "cpu")
