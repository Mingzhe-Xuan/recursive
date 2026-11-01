import importlib.util
from pathlib import Path

import pytest

from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, code_identity, digest, file_hash


def load_pool():
    spec = importlib.util.spec_from_file_location(
        "execution_pool", Path("scripts/self_evolution/execution_pool.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_waves_cover_all_29_tasks_once():
    pool = load_pool()
    groups = [pool.wave_tasks(index) for index in range(8)]
    assert [name for group in groups for name in group] == list(TASKS)
    assert len(groups[-1]) == 1
    for index in [-1, 8]:
        with pytest.raises(ValueError, match="wave index"):
            pool.wave_tasks(index)


def test_worker_selection_respects_measured_memory_cpus_and_serial_fallback():
    pool = load_pool()
    resources = {
        "largest_batch_status": "measured",
        "device_memory_bytes": 32 * pool.GIB,
        "largest_batch_stages": [
            {"round": r, "peak_torch_reserved_bytes": pool.GIB} for r in range(2)
        ],
    }
    assert pool.select_workers(resources, 4, 16, 4, 64 * pool.GIB) == 4
    assert pool.select_workers(resources, 4, 8, 4, 64 * pool.GIB) == 2
    assert pool.select_workers(resources, 4, 16, 4, 16 * pool.GIB) == 2
    resources["largest_batch_stages"][0]["peak_torch_reserved_bytes"] = 12 * pool.GIB
    assert pool.select_workers(resources, 4, 16, 4) == 1
    resources["largest_batch_status"] = "out_of_memory"
    assert pool.select_workers(resources, 4, 16, 4) == 1
    with pytest.raises(ValueError, match="CPU allocation"):
        pool.select_workers(resources, 4, 2, 4)
    resources["largest_batch_status"] = "measured"
    resources["device_memory_bytes"] = None
    with pytest.raises(ValueError, match="measurements are missing"):
        pool.select_workers(resources, 4, 16, 4)


def test_pool_requires_real_acceptance_bound_to_configuration_and_resource_hash(tmp_path):
    pool = load_pool()
    config = {"seed": 123}
    graph_manifest = tmp_path / "graph_manifest.json"
    atomic_write(graph_manifest, {"graph": "test"})
    resource_path = tmp_path / "pilot_resources.json"
    atomic_write(
        resource_path,
        {
            "schema": 1,
            "status": "measured",
            "device": "cuda",
            "config_hash": digest(config),
            "core_code_hash": code_identity(),
            "graphs_sha256": file_hash(graph_manifest),
        },
    )
    accepted = {
        "status": "passed",
        "resource_report_sha256": file_hash(resource_path),
        "graphs_sha256": file_hash(graph_manifest),
    }
    atomic_write(tmp_path / "real_acceptance.json", accepted)
    assert pool.validate_gate(tmp_path, config, graph_manifest)["device"] == "cuda"
    atomic_write(graph_manifest, {"graph": "changed"})
    with pytest.raises(ValueError, match="matching real CUDA"):
        pool.validate_gate(tmp_path, config, graph_manifest)
    with pytest.raises(ValueError, match="matching real CUDA"):
        pool.validate_gate(tmp_path, {"seed": 42})
    accepted["resource_report_sha256"] = "wrong"
    atomic_write(tmp_path / "real_acceptance.json", accepted)
    with pytest.raises(ValueError, match="matching real CUDA"):
        pool.validate_gate(tmp_path, config)


@pytest.mark.parametrize("fail_one", [False, True])
def test_real_processes_finish_all_training_before_serial_evaluation(tmp_path, fail_one):
    pool = load_pool()
    names = pool.wave_tasks(0)
    run = tmp_path / "run"
    config = {"seed": 123, "threads": 1, "fake_failure": names[0] if fail_one else None}
    config_path = tmp_path / "config.json"
    atomic_write(config_path, config)
    if fail_one:
        root = run / "cgcnn" / names[0] / "seed_123"
        atomic_write(root / "protocol.json", config)
        atomic_write(root / "report.json", {"previous": True})
    cli = tmp_path / "fake_cli.py"
    cli.write_text(
        """import argparse, json, time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('action'); p.add_argument('--config'); p.add_argument('--prepared')
p.add_argument('--output'); p.add_argument('--task'); p.add_argument('--device')
a=p.parse_args()
cfg=json.loads(Path(a.config).read_text())
events=Path(a.output)/'events'; events.mkdir(parents=True,exist_ok=True)
root=Path(a.output)/'cgcnn'/a.task/'seed_123'; root.mkdir(parents=True,exist_ok=True)
if a.action=='run':
 (events/(a.task+'.start')).write_text(str(time.time()))
 deadline=time.monotonic()+15
 while len(list(events.glob('*.start')))<2:
  if time.monotonic()>deadline: raise RuntimeError('first two workers did not overlap')
  time.sleep(0.01)
 time.sleep(0.1)
 (events/(a.task+'.end')).write_text(str(time.time()))
 (root/'protocol.json').write_text(json.dumps(cfg))
 raise SystemExit(3 if a.task==cfg['fake_failure'] else 0)
assert len(list(events.glob('*.end')))==4, 'evaluation overlapped training'
(events/(a.task+'.eval_start')).write_text(str(time.time()))
time.sleep(0.1)
(root/'report.json').write_text(json.dumps({'rows':[]}))
(events/(a.task+'.eval_end')).write_text(str(time.time()))
""",
        encoding="utf-8",
    )
    record = pool.run_wave(tmp_path / "prepared", run, config_path, config, 0, 2, "cpu", cli)
    assert record["status"] == ("failed" if fail_one else "complete")
    assert record["workers"] == 2 and set(record["results"]) == set(names)
    assert record["wave_wall_seconds"] > 0
    intervals = [
        (float(path.read_text()), float(path.with_suffix(".end").read_text()))
        for path in (run / "events").glob("*.start")
    ]
    assert (
        max(sum(begin <= instant < end for begin, end in intervals) for instant, _ in intervals)
        == 2
    )
    evaluated = [row for row in record["results"].values() if "evaluation_started_at" in row]
    evaluated.sort(key=lambda row: row["evaluation_started_at"])
    assert len(evaluated) == (3 if fail_one else 4)
    assert min(row["evaluation_started_at"] for row in evaluated) >= max(
        row["run_finished_at"] for row in record["results"].values()
    )
    assert all(
        a["evaluation_finished_at"] <= b["evaluation_started_at"]
        for a, b in zip(evaluated, evaluated[1:])
    )
    if fail_one:
        assert not (run / "cgcnn" / names[0] / "seed_123/report.json").exists()
        assert list((run / "pool/wave_000").glob("*previous-report*.json"))
    summary = pool.enrich_summary(
        run,
        {
            "seed": 123,
            "coverage": [{"task": name, "status": "complete"} for name in names],
        },
    )
    assert summary["status"] == "partial"
    assert summary["completed_tasks"] == (3 if fail_one else 4)
    assert "contention" in summary["execution_context"]["stage_wall_seconds"]
    assert summary["execution_context"]["observed_reserved_gpu_seconds"] == 0
    if not fail_one:
        repeated = pool.run_wave(tmp_path / "prepared", run, config_path, config, 0, 2, "cpu", cli)
        assert repeated["status"] == "complete"
        assert repeated["previous_observed_wall_seconds"] == record["wave_wall_seconds"]
        assert list((run / "pool/wave_000").glob("execution-attempt-*.json"))
        assert len(list((run / "pool/wave_000").glob("*previous-report-*.json"))) == 4


def test_mismatched_existing_protocol_is_not_overwritten(tmp_path):
    pool = load_pool()
    root = tmp_path / "cgcnn" / pool.wave_tasks(0)[0] / "seed_123"
    atomic_write(root / "protocol.json", {"seed": 42})
    atomic_write(root / "report.json", {"previous": True})
    before = file_hash(root / "report.json")
    with pytest.raises(ValueError, match="existing task protocol"):
        pool.run_wave(tmp_path, tmp_path, tmp_path / "config.json", {"seed": 123}, 0, 2, "cpu")
    assert file_hash(root / "report.json") == before
