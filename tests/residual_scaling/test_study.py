import copy
import importlib.util
from pathlib import Path

import pytest
import torch

from self_evolution.data.graphs import GraphStore
from self_evolution.io import atomic_write, file_hash, load_tensor, read_json
from self_evolution.pipeline.chain import run_task
from residual_scaling.cache import Archive, publish
from residual_scaling.pipeline import prepare_task, run_variant, verify_chain
from residual_scaling.reporting import summarize
from residual_scaling.training import compose_prediction, train_stage
from residual_scaling.protocol import validate_config


@pytest.fixture(scope="module")
def reference(tmp_path_factory):
    root = tmp_path_factory.mktemp("reference")
    prepared = root / "prepared"
    legacy = root / "legacy"
    spec = importlib.util.spec_from_file_location(
        "legacy_fixture", Path("tests/self_evolution/test_pipeline.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    task = m.synthetic_prepared(prepared)
    base = read_json(Path("configs/self_evolution/cgcnn_seed123.json"))
    base.update(max_round=2, threads=1)
    base["model"].update(hidden=4, convolutions=1, head_hidden=8)
    base["training"].update(epochs=2, patience=2, batch_size=4)
    base["cache"]["shard_size"] = 4
    run_task(prepared, legacy, task["task"], base, "cpu", controls=False)
    study = read_json(Path("configs/residual_scaling/seed123.json"))
    study.update(tasks=[task["task"]], expected_structures=12)
    return prepared, legacy, base, study, task


def test_original_unit_residual_arithmetic_and_gradient():
    previous = torch.tensor([10.0, -3.0], requires_grad=True)
    delta = torch.tensor([0.5, -1.0], requires_grad=True)
    norm = {"mean": 100.0, "std": 2.0}
    pred = compose_prediction(previous, delta, norm)
    torch.testing.assert_close(pred, torch.tensor([11.0, -5.0]))
    torch.testing.assert_close(compose_prediction(previous, torch.zeros(2), norm), previous)
    target = torch.tensor([12.0, -4.0])
    a = (((pred - target) / 2) ** 2).mean()
    b = ((delta - (target - previous.detach()) / 2) ** 2).mean()
    torch.testing.assert_close(a, b)
    a.backward()
    assert previous.grad is None and delta.grad is not None


def test_locked_protocol_and_gpu_acceptance_reject_stale_inputs(tmp_path):
    base = read_json(Path("configs/self_evolution/cgcnn_seed123.json"))
    study = read_json(Path("configs/residual_scaling/seed123.json"))
    validate_config(study, base)
    for key, value in [
        ("eta", 0.1),
        ("checkpoint_selection", "monotonic_fallback"),
        ("normalization", "refit_residual"),
        ("expected_structures", 0),
    ]:
        with pytest.raises(ValueError):
            validate_config({**study, key: value}, base)
    spec = importlib.util.spec_from_file_location(
        "residual_dispatch", Path("scripts/residual_scaling/dispatch.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from residual_scaling.protocol import implementation_identity
    from self_evolution.io import digest

    graph = tmp_path / "graph.json"
    atomic_write(graph, {"dummy": True})
    source = tmp_path / study["tasks"][0] / "source.json"
    atomic_write(source, {"dummy": True})
    accepted = {
        "status": "passed",
        "study_hash": digest(study),
        "base_hash": digest(base),
        "implementation_hash": implementation_identity(),
        "graphs_sha256": file_hash(graph),
        "source_sha256": file_hash(source),
        "rows": [
            {"variant": v, "full_cache_structures": study["expected_structures"]}
            for v in ["raw_residual", "feature_residual"]
        ],
    }
    atomic_write(tmp_path / "acceptance.json", accepted)
    assert module.validate_acceptance(tmp_path, study, base, graph)["status"] == "passed"
    atomic_write(source, {"changed": True})
    with pytest.raises(ValueError, match="acceptance"):
        module.validate_acceptance(tmp_path, study, base, graph)


def test_paired_cache_resume_parent_identity_and_corruption(tmp_path):
    ids = ["a", "b", "c"]
    identity = {"parent": "p", "checkpoint": "c"}
    calls = []

    def produce(chunk):
        calls.extend(chunk)
        return [(torch.ones(i + 1, 4), torch.tensor(float(i))) for i, _ in enumerate(chunk)]

    a = publish(tmp_path, identity, ids, 4, produce, 2)
    assert len(calls) == 3
    publish(tmp_path, identity, ids, 4, lambda _: pytest.fail("completed cache regenerated"), 2)
    with pytest.raises(ValueError, match="mismatched"):
        Archive(tmp_path, {"parent": "wrong"})
    a.get("a")
    shard = tmp_path / a.manifest["shards"][0]["file"]
    shard.write_bytes(shard.read_bytes() + b"bad")
    with pytest.raises(ValueError, match="checksum"):
        a.verify_all()
    interrupted = tmp_path / "interrupted"
    counter = [0]

    def stop(chunk):
        counter[0] += 1
        if counter[0] == 2:
            raise RuntimeError("controlled interruption")
        return produce(chunk)

    with pytest.raises(RuntimeError):
        publish(interrupted, identity, ids, 4, stop, 2)
    assert not (interrupted / "manifest.json").exists()
    calls.clear()
    publish(interrupted, identity, ids, 4, produce, 2)
    assert calls == ["c"]


def test_three_arm_two_round_real_cpu_and_frozen_sources(reference, tmp_path):
    prepared, legacy, base, study, task = reference
    hashes = {
        p: file_hash(p) for p in legacy.rglob("*") if p.is_file() and (p.suffix in [".pt", ".json"])
    }
    source = prepare_task(prepared, legacy, tmp_path, task["task"], base, study, "cpu")
    for variant in ["raw_residual", "feature_residual"]:
        rows = run_variant(prepared, legacy, tmp_path, task["task"], variant, base, study, "cpu")
        assert [row["round"] for row in rows] == [0, 1, 2]
        for r in [1, 2]:
            path = tmp_path / task["task"] / variant / f"round_{r:03d}"
            trained = read_json(path / "training.json")
            assert (
                trained["optimizer_steps"] == source["references"][r]["training"]["optimizer_steps"]
            )
            assert (
                trained["stage_seed"]
                == source["references"][r]["training"]["identity"]["stage_seed"]
            )
            assert trained["normalization"] == source["normalization"]
            chosen = load_tensor(path / "best.pt")
            assert chosen["prediction_role"] == "residual_delta"
            assert chosen["epoch"] >= 1
            assert chosen["val_mae"] == min(row["val_mae"] for row in trained["history"])
            cache = Archive(path / "cache")
            assert len(cache.locations) == 12 and cache.manifest["atoms"] == 24
        assert verify_chain(tmp_path, task["task"], variant, base, study, 2, "cpu")["depth"] == 2
        run_variant(prepared, legacy, tmp_path, task["task"], variant, base, study, "cpu")
    assert all(file_hash(p) == h for p, h in hashes.items())
    report = summarize(tmp_path, study)
    assert (
        report["status"] == "complete"
        and len(report["rows"]) == 9
        and not report["test_labels_used"]
    )
    assert (tmp_path / "reports" / f"{task['task']}.png").exists()
    incomplete = read_json(tmp_path / task["task"] / "raw_residual/report.json")
    incomplete["status"] = "partial"
    atomic_write(tmp_path / task["task"] / "raw_residual/report.json", incomplete)
    assert summarize(tmp_path, study)["status"] == "partial"


def test_stage_resume_and_test_labels_do_not_change_training(reference, tmp_path):
    prepared, legacy, base, study, task = reference
    source = prepare_task(prepared, legacy, tmp_path / "imported", task["task"], base, study, "cpu")
    graphs = GraphStore(prepared / "graphs")
    parent = Archive(source["base_cache"])
    ref = source["references"][1]["training"]
    budget = ref["optimizer_steps"]
    seed = ref["identity"]["stage_seed"]
    identity = {"round": 1, "test": "resume", "parent": parent.identity}
    kwargs = dict(
        base=base,
        task=task,
        graphs=graphs,
        parent=parent,
        norm=source["normalization"],
        variant="feature_residual",
        eta=1.0,
        budget=budget,
        seed=seed,
        identity=identity,
        device="cpu",
    )
    assert train_stage(tmp_path / "resumed", **kwargs, interrupt_after_epochs=1) is None
    resumed = train_stage(tmp_path / "resumed", **kwargs)
    different = copy.deepcopy(task)
    for jid in different["split"]["ids"]["test"]:
        different["labels"][jid] = 1e9
    kwargs["task"] = different
    continuous = train_stage(tmp_path / "continuous", **kwargs)
    assert resumed["optimizer_steps"] == continuous["optimizer_steps"] == budget
    a = load_tensor(tmp_path / "resumed/best.pt")
    b = load_tensor(tmp_path / "continuous/best.pt")
    assert all(torch.equal(a["model"][k], b["model"][k]) for k in a["model"])
    assert a["val_mae"] == b["val_mae"]
    wrong = {**identity, "parent": "wrong"}
    with pytest.raises(ValueError, match="identity"):
        train_stage(tmp_path / "resumed", **{**kwargs, "identity": wrong})
