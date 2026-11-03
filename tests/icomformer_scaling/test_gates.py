import copy
import importlib.util
from pathlib import Path

import pytest

from self_evolution.io import atomic_write, digest, file_hash, read_json
from icomformer_scaling.pipeline import implementation_identity


def dispatcher():
    spec = importlib.util.spec_from_file_location(
        "icom_dispatch", Path("scripts/icomformer_scaling/dispatch.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_limits_use_real_peak_host_memory_and_cpu():
    module = dispatcher()
    gib = 1024**3
    resource = {"device_memory_bytes": 32 * gib, "accepted": {"peak_torch_reserved_bytes": 2 * gib}}
    assert module.select_workers(resource, 16, 4, 64 * gib) == 4
    assert module.select_workers(resource, 8, 4, 64 * gib) == 2
    assert module.select_workers(resource, 16, 4, 16 * gib) == 2
    resource["accepted"]["peak_torch_reserved_bytes"] = 12 * gib
    assert module.select_workers(resource, 16, 4, 64 * gib) == 1
    with pytest.raises(ValueError):
        module.select_workers(resource, 2, 4, 64 * gib)


def test_gate_rejects_stale_config_code_graphs_and_missing_native_checks(tmp_path):
    module = dispatcher()
    cfg = read_json(Path("configs/icomformer_scaling/seed123.json"))
    prepared = tmp_path / "prepared"
    atomic_write(prepared / "graphs/manifest.json", {"status": "complete", "test": True})
    resource = {
        "status": "measured",
        "model_hash": digest(cfg["model"]),
        "accepted": {"batch_size": cfg["training"]["batch_size"]},
        "probe_script_sha256": file_hash(Path("scripts/icomformer_scaling/probe.py")),
    }
    atomic_write(tmp_path / "resource_probe.json", resource)
    pairs = [
        ("direct", 0),
        ("direct", 1),
        ("direct", 2),
        ("raw_residual", 1),
        ("raw_residual", 2),
        ("feature_residual", 1),
        ("feature_residual", 2),
    ]
    accepted = {
        "status": "passed",
        "native": {"gradients": "passed"},
        "diagnostic_only": True,
        "test_labels_used": False,
        "study_hash": digest(cfg),
        "implementation_hash": implementation_identity(),
        "graphs_sha256": file_hash(prepared / "graphs/manifest.json"),
        "resource_probe_sha256": file_hash(tmp_path / "resource_probe.json"),
        "rows": [
            {
                "variant": v,
                "round": r,
                "structures": cfg["expected_structures"],
                "width": cfg["model"]["hidden"],
                "optimizer_steps": 4,
            }
            for v, r in pairs
        ],
    }
    atomic_write(tmp_path / "acceptance.json", accepted)
    assert module.validate_gate(tmp_path, prepared, cfg)[0]["status"] == "passed"
    for key, value in [
        ("study_hash", "wrong"),
        ("implementation_hash", "wrong"),
        ("graphs_sha256", "wrong"),
        ("native", {"gradients": "failed"}),
        ("rows", accepted["rows"][:-1]),
    ]:
        changed = copy.deepcopy(accepted)
        changed[key] = value
        atomic_write(tmp_path / "acceptance.json", changed)
        with pytest.raises(ValueError):
            module.validate_gate(tmp_path, prepared, cfg)
