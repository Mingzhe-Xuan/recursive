"""Real cached-reference fixtures for joint CGCNN acceptance."""

import copy
import importlib.util
from pathlib import Path

import pytest
import torch

from self_evolution.backbones.cgcnn import CGCNNStage, ModelConfig
from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, load_tensor, read_json
from self_evolution.pipeline.chain import run_task as cached_chain
from residual_scaling.pipeline import prepare_task, run_variant
from residual_scaling.reporting import summarize as cached_summary
from joint_cgcnn.model import DoubleCGCNN, stage_seeds
from joint_cgcnn.study import inputs, run_task, summarize
from joint_cgcnn.training import gradients, train


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    root = tmp_path_factory.mktemp("joint-fixture")
    spec = importlib.util.spec_from_file_location(
        "joint_graph_fixture", Path("tests/self_evolution/test_pipeline.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    prepared, legacy, cached = root / "prepared", root / "legacy", root / "cached"
    task = m.synthetic_prepared(prepared)
    base = read_json(Path("configs/self_evolution/cgcnn_seed123.json"))
    base.update(max_round=2, threads=1)
    base["model"].update(hidden=4, convolutions=1, head_hidden=8)
    base["training"].update(epochs=2, patience=2, batch_size=4)
    base["cache"]["shard_size"] = 4
    cached_chain(prepared, legacy, task["task"], base, "cpu", controls=False)
    study = read_json(Path("configs/residual_scaling/seed123.json"))
    study.update(tasks=[task["task"]], expected_structures=12)
    prepare_task(prepared, legacy, cached, task["task"], base, study, "cpu")
    for variant in ["raw_residual", "feature_residual"]:
        run_variant(prepared, legacy, cached, task["task"], variant, base, study, "cpu")
    assert cached_summary(cached, study)["status"] == "complete"
    cfg = read_json(Path("configs/joint_cgcnn/seed123.json"))
    cfg.update(
        model=base["model"],
        training=base["training"],
        threads=1,
        tasks=[task["task"]],
        expected_structures=12,
    )
    return prepared, cached, task, cfg


def test_native_composition_all_parameters_receive_gradient(fixture):
    prepared, _, task, cfg = fixture
    graphs = GraphStore(prepared / "graphs")
    batch = collate_graphs([graphs.get(jid) for jid in graphs.ids[:4]])
    seeds = stage_seeds(cfg["seed"], task["task"])
    model = DoubleCGCNN(ModelConfig(**cfg["model"]), seeds).eval()
    with torch.random.fork_rng():
        torch.manual_seed(seeds[0])
        first = CGCNNStage(ModelConfig(**cfg["model"])).eval()
        torch.manual_seed(seeds[1])
        second = CGCNNStage(ModelConfig(**cfg["model"]), recursive=True).eval()
    expected = second(batch, first.encode_nodes(batch))
    actual = model(batch)
    torch.testing.assert_close(actual, expected, rtol=1e-6, atol=1e-7)
    actual.square().sum().backward()
    assert all(v > 0 for v in gradients(model).values())
    assert (
        model.first.embedding.weight.data_ptr() != model.second.native.embedding.weight.data_ptr()
    )
    assert not any(
        "first" in k and "fc" in k and "convs" not in k for k, _ in model.named_parameters()
    )
    single = collate_graphs([graphs.get(graphs.ids[0])])
    torch.testing.assert_close(model(single)[0], actual[0], rtol=1e-5, atol=1e-6)


def test_joint_resume_exact_and_test_labels_unused(fixture, tmp_path):
    prepared, cached, task, cfg = fixture
    task, graphs, norm, identity, _ = inputs(prepared, cached, task["task"], cfg)
    kwargs = dict(config=cfg, task=task, graphs=graphs, norm=norm, identity=identity, device="cpu")
    assert train(tmp_path / "resume", **kwargs, interrupt_after=1) is None
    a = train(tmp_path / "resume", **kwargs)
    different = copy.deepcopy(task)
    for jid in different["split"]["ids"]["test"]:
        different["labels"][jid] = 1e12
    b = train(tmp_path / "continuous", **{**kwargs, "task": different})
    assert a["optimizer_steps"] == b["optimizer_steps"]
    for filename in ["last.pt", "best.pt"]:
        x, y = (
            load_tensor(tmp_path / "resume" / filename),
            load_tensor(tmp_path / "continuous" / filename),
        )
        assert all(torch.equal(x["model"][k], y["model"][k]) for k in x["model"])
    with pytest.raises(ValueError, match="identity"):
        train(
            tmp_path / "resume", **{**kwargs, "identity": {**identity, "config_sha256": "changed"}}
        )


def test_comparison_real_sources_and_partial_rejected(fixture, tmp_path):
    prepared, cached, task, cfg = fixture
    result = run_task(prepared, cached, tmp_path, task["task"], cfg, "cpu")
    assert not result["test_labels_used"]
    report = summarize(prepared, cached, tmp_path, cfg)
    assert report["status"] == "complete" and len(report["rows"]) == 1
    row = report["rows"][0]
    assert row["joint_encoder_update_applications"] == 2 * row["joint_optimizer_steps"]
    assert (tmp_path / "reports/comparison.csv").exists()
    assert (tmp_path / "reports" / f"{task['task']}.png").exists()
    changed = copy.deepcopy(cfg)
    changed["model"]["hidden"] += 1
    with pytest.raises(ValueError, match="protocol"):
        inputs(prepared, cached, task["task"], changed)
    bad = read_json(tmp_path / "run" / task["task"] / "result.json")
    bad["identity"]["task_sha256"] = "bad"
    atomic_write(tmp_path / "run" / task["task"] / "result.json", bad)
    assert summarize(prepared, cached, tmp_path, cfg)["status"] == "partial"


def test_default_parameter_count_and_acceptance_rejects_stale_inputs(fixture, tmp_path):
    import importlib.util
    from types import SimpleNamespace
    from joint_cgcnn.study import implementation_identity
    from self_evolution.io import digest, file_hash

    production = read_json(Path("configs/joint_cgcnn/seed123.json"))
    model = DoubleCGCNN(ModelConfig(**production["model"]), [1, 2])
    assert sum(p.numel() for p in model.parameters()) == 159197
    prepared, cached, _, cfg = fixture
    script = Path("scripts/joint_cgcnn/run.py")
    spec = importlib.util.spec_from_file_location("joint_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    args = SimpleNamespace(prepared=prepared, cached=cached, output=tmp_path)
    sources = cli.provenance(args, cfg)
    atomic_write(tmp_path / "cpu-proof.json", {"status": "passed", "sources": sources})
    accepted = {
        "status": "passed",
        "config_sha256": digest(cfg),
        "implementation_hash": implementation_identity(),
        "sources": sources,
        "cpu_proof_sha256": file_hash(tmp_path / "cpu-proof.json"),
        "script_sha256": file_hash(script),
        "gradient_l1": {"first": 1, "bridge": 1, "second": 1},
        "diagnostic_only": True,
        "test_labels_used": False,
    }
    atomic_write(tmp_path / "acceptance.json", accepted)
    assert cli.validate_gate(args, cfg)["status"] == "passed"
    for key, value in [
        ("config_sha256", "bad"),
        ("script_sha256", "bad"),
        ("gradient_l1", {"first": 0, "bridge": 1, "second": 1}),
        ("sources", {}),
        ("test_labels_used", True),
    ]:
        atomic_write(tmp_path / "acceptance.json", {**accepted, key: value})
        with pytest.raises(ValueError, match="acceptance"):
            cli.validate_gate(args, cfg)
