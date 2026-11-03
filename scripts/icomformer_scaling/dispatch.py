"""Share one Slurm GPU allocation across independent property chains after acceptance."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from icomformer_scaling.pipeline import implementation_identity, validate_config

GIB = 1024**3


def validate_gate(work, prepared, config):
    accepted = read_json(work / "acceptance.json")
    resource = read_json(work / "resource_probe.json")
    expected = [
        ("direct", 0),
        ("direct", 1),
        ("direct", 2),
        ("raw_residual", 1),
        ("raw_residual", 2),
        ("feature_residual", 1),
        ("feature_residual", 2),
    ]
    if (
        accepted["status"] != "passed"
        or accepted["native"]["gradients"] != "passed"
        or not accepted["diagnostic_only"]
        or accepted["test_labels_used"]
        or accepted["study_hash"] != digest(config)
        or accepted["implementation_hash"] != implementation_identity()
        or accepted["graphs_sha256"] != file_hash(prepared / "graphs/manifest.json")
        or accepted["resource_probe_sha256"] != file_hash(work / "resource_probe.json")
        or [(r["variant"], r["round"]) for r in accepted["rows"]] != expected
        or any(
            row["structures"] != config["expected_structures"]
            or row["width"] != config["model"]["hidden"]
            or row["optimizer_steps"] != 4
            for row in accepted["rows"]
        )
    ):
        raise ValueError("iComformer GPU acceptance/config/code/coverage mismatch")
    if (
        resource["status"] != "measured"
        or resource["model_hash"] != digest(config["model"])
        or resource["accepted"]["batch_size"] != config["training"]["batch_size"]
        or resource["probe_script_sha256"] != file_hash(Path(__file__).with_name("probe.py"))
    ):
        raise ValueError("iComformer resource/config mismatch")
    return accepted, resource


def select_workers(resource, cpus, threads, memory, maximum=4):
    total = resource["device_memory_bytes"]
    peak = resource["accepted"]["peak_torch_reserved_bytes"]
    if cpus < threads or threads < 1 or maximum < 1 or not 0 < peak < total:
        raise ValueError("invalid native resource measurement/allocation")
    gpu_limit = max(1, int(total * 0.75) // int(peak * 1.3 + GIB))
    return max(1, min(maximum, 4, cpus // threads, max(1, memory // (8 * GIB)), gpu_limit))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/icomformer_scaling/seed123.json")
    )
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--old-prepared", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--cgcnn-summary", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("production dispatcher requires Slurm")
    config = read_json(args.config)
    validate_config(config)
    accepted, resource = validate_gate(args.work, args.prepared, config)
    workers = select_workers(
        resource,
        int(os.environ["SLURM_CPUS_PER_TASK"]),
        config["threads"],
        int(os.environ.get("SLURM_MEM_PER_NODE", "65536")) * 1024**2,
        args.max_workers,
    )
    pool = args.work / "pool"
    pool.mkdir(parents=True, exist_ok=True)
    run = args.work / "run"
    cli = Path(__file__).with_name("run.py")
    shared = [
        "--config",
        str(args.config),
        "--prepared",
        str(args.prepared),
        "--old-prepared",
        str(args.old_prepared),
        "--output",
        str(run),
    ]
    record = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "config_hash": digest(config),
        "implementation_hash": implementation_identity(),
        "workers": workers,
        "resource_probe_sha256": accepted["resource_probe_sha256"],
        "results": {},
        "test_labels_used": False,
        "training_time_scope": "independent properties sharing one GPU; elapsed includes contention",
    }
    active, pending = {}, list(config["tasks"])
    start = time.perf_counter()
    with task_lock(pool / ".lock"):
        execution = pool / "execution.json"
        if execution.exists():
            previous = read_json(execution)
            if (
                previous["config_hash"] != record["config_hash"]
                or previous["implementation_hash"] != record["implementation_hash"]
            ):
                raise ValueError("existing execution belongs to another protocol")
            execution.replace(pool / f"execution-attempt-{time.time_ns()}.json")
        try:
            while pending or active:
                while pending and len(active) < workers:
                    task = pending.pop(0)
                    log = (pool / f"{task}-{time.time_ns()}.out").open("w", encoding="utf-8")
                    process = subprocess.Popen(
                        [sys.executable, str(cli), "run", *shared, "--task", task],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                    active[task] = (process, log)
                    record["results"][task] = {
                        "status": "running",
                        "pid": process.pid,
                        "log": log.name,
                    }
                for task, (process, log) in list(active.items()):
                    code = process.poll()
                    if code is not None:
                        log.close()
                        record["results"][task].update(
                            status="complete" if code == 0 else "failed", exit_code=code
                        )
                        del active[task]
                record["wall_seconds"] = time.perf_counter() - start
                atomic_write(execution, record)
                if pending or active:
                    time.sleep(5)
            subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "summarize",
                    *shared,
                    "--cgcnn-summary",
                    str(args.cgcnn_summary),
                ],
                check=True,
            )
            if any(value["exit_code"] != 0 for value in record["results"].values()):
                raise RuntimeError("one or more property chains failed")
            record.update(status="complete", total_wall_seconds=time.perf_counter() - start)
            atomic_write(execution, record)
        except BaseException as exc:
            record.update(
                status="failed", error=str(exc), total_wall_seconds=time.perf_counter() - start
            )
            atomic_write(execution, record)
            raise
        finally:
            for process, log in active.values():
                process.terminate()
                process.wait()
                log.close()


if __name__ == "__main__":
    main()
