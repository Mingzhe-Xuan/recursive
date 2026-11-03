import copy
import importlib.util
from pathlib import Path

import pytest
import torch

from self_evolution.io import atomic_write, digest, file_hash, load_tensor, read_json
from residual_scaling.cache import Archive
from icomformer_scaling.graphs import GraphStore, make_graph
from icomformer_scaling.pipeline import run_task, verify_chain
from icomformer_scaling.reporting import summarize
from icomformer_scaling.training import train_stage


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("icomformer-study")
    old, prepared, run = root / "old", root / "prepared", root / "run"
    spec = importlib.util.spec_from_file_location(
        "cg_fixture", Path("tests/self_evolution/test_pipeline.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    task = m.synthetic_prepared(old)
    cfg = read_json(Path("configs/icomformer_scaling/seed123.json"))
    cfg.update(tasks=[task["task"]], expected_structures=12, threads=1)
    cfg["model"].update(hidden=8, edge_features=8, triplet_features=8, head_hidden=8)
    cfg["training"].update(epochs=2, patience=2, batch_size=4)
    cfg["cache"]["shard_size"] = 4
    entries = {}
    for i in range(12):
        jid = f"crystal_{i:02d}"
        length = 4.8 + i * 0.1
        graph = make_graph(
            {
                "jid": jid,
                "atoms": {
                    "lattice_mat": [[length, 0, 0], [0, length, 0], [0, 0, length]],
                    "elements": ["Si", "Si"],
                    "cartesian": False,
                    "coords": [[0, 0, 0], [0.25, 0.25, 0.25]],
                },
            },
            cfg["graph"],
        )
        path = prepared / "graphs" / f"{jid}.pt"
        atomic_write(path, graph, tensor=True)
        entries[jid] = {
            "file": path.name,
            "atoms": 2,
            "edges": graph["edge_index"].shape[1],
            "sha256": file_hash(path),
        }
    atomic_write(
        prepared / "graphs/manifest.json",
        {
            "schema": 1,
            "status": "complete",
            "failures": {},
            "entries": entries,
            "record_count": 12,
            "ids_hash": digest(sorted(entries)),
            "identity": {
                "dataset_sha256": task["dataset_sha256"],
                "source_graphs_sha256": file_hash(old / "graphs/manifest.json"),
                "graph_config": cfg["graph"],
            },
        },
    )
    seals = {
        p: file_hash(p)
        for directory in [old, prepared]
        for p in directory.rglob("*")
        if p.is_file()
    }
    run_task(prepared, old, run, task["task"], cfg, "cpu")
    assert all(file_hash(p) == value for p, value in seals.items())
    return root, old, prepared, run, cfg, task


def test_three_branches_budgets_shared_base_diagnostics_and_resume(completed):
    root, old, prepared, run, cfg, task = completed
    source = read_json(run / task["task"] / "source.json")
    seals = {
        p: file_hash(p)
        for p in run.rglob("*")
        if p.is_file() and (p.suffix == ".pt" or p.name == "training.json")
    }
    for variant in cfg["variants"]:
        report = read_json(run / task["task"] / variant / "report.json")
        assert report["status"] == "complete" and [r["round"] for r in report["rows"]] == [0, 1, 2]
        assert (
            report["rows"][0]["checkpoint_sha256"] == source["direct_rows"][0]["checkpoint_sha256"]
        )
        for r in [1, 2]:
            metrics = read_json(run / task["task"] / variant / f"round_{r:03d}/training.json")
            assert (
                metrics["optimizer_steps"] == source["references"][r]["training"]["optimizer_steps"]
            )
            assert metrics["stage_seed"] == source["references"][r]["training"]["stage_seed"]
            assert metrics["normalization"] == source["normalization"]
        verify_chain(
            run / task["task"],
            GraphStore(prepared / "graphs"),
            source["normalization"],
            variant,
            2,
            cfg,
            "cpu",
        )
    run_task(prepared, old, run, task["task"], cfg, "cpu")
    assert all(file_hash(p) == value for p, value in seals.items())
    result = summarize(run, cfg, old_prepared=old)
    assert result["status"] == "complete" and len(result["rows"]) == 9
    diagnostic = read_json(run.parent / "diagnostics/final-study/summary.json")
    assert (
        len(diagnostic["residuals"]) == 18
        and len(diagnostic["corrections"]) == 12
        and not diagnostic["test_labels_used"]
    )
    assert (run / "reports" / f"{task['task']}.png").exists()
    branch = run / task["task"] / "raw_residual/report.json"
    value = read_json(branch)
    value["status"] = "partial"
    atomic_write(branch, value)
    partial = summarize(run, cfg, diagnose=False)
    assert partial["status"] == "partial" and len(partial["rows"]) == 6
    value["status"] = "complete"
    atomic_write(branch, value)


def test_optimizer_rng_resume_and_test_label_isolation(completed):
    root, old, prepared, run, cfg, task = completed
    source = read_json(run / task["task"] / "source.json")
    base = Archive(source["base_cache"])
    ref = source["references"][1]["training"]
    identity = {
        "round": 1,
        "stage_seed": ref["stage_seed"],
        "parent": base.identity,
        "purpose": "controlled-resume",
    }
    kwargs = dict(
        config=cfg,
        task=task,
        graphs=GraphStore(prepared / "graphs"),
        parent=base,
        norm=source["normalization"],
        variant="feature_residual",
        round_index=1,
        identity=identity,
        device="cpu",
        budget=ref["optimizer_steps"],
    )
    assert train_stage(root / "resumed", **kwargs, interrupt_after_epochs=1) is None
    first = train_stage(root / "resumed", **kwargs)
    changed = copy.deepcopy(task)
    for jid in changed["split"]["ids"]["test"]:
        changed["labels"][jid] = 1e12
    kwargs["task"] = changed
    second = train_stage(root / "continuous", **kwargs)
    a, b = load_tensor(root / "resumed/best.pt"), load_tensor(root / "continuous/best.pt")
    assert first["best_val_mae"] == second["best_val_mae"] and a["epoch"] >= 1
    assert all(torch.equal(a["model"][k], b["model"][k]) for k in a["model"])
    with pytest.raises(ValueError, match="identity"):
        train_stage(root / "resumed", **{**kwargs, "identity": {**identity, "parent": "wrong"}})
