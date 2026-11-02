"""Eight independent residual branches sharing one Slurm GPU allocation."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "self_evolution"))

from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from execution_pool import select_workers, validate_gate
from residual_scaling.protocol import implementation_identity, validate_config


def validate_acceptance(output, study, base, graph_manifest):
    accepted = read_json(output / "acceptance.json")
    if (
        accepted["status"] != "passed"
        or accepted["study_hash"] != digest(study)
        or accepted["base_hash"] != digest(base)
        or accepted["implementation_hash"] != implementation_identity()
        or accepted["graphs_sha256"] != file_hash(graph_manifest)
        or accepted["source_sha256"] != file_hash(output / study["tasks"][0] / "source.json")
        or [row["variant"] for row in accepted["rows"]] != ["raw_residual", "feature_residual"]
        or any(
            row["full_cache_structures"] != study["expected_structures"] for row in accepted["rows"]
        )
    ):
        raise ValueError("residual GPU acceptance mismatch")
    return accepted


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/residual_scaling/seed123.json"))
    p.add_argument(
        "--base-config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    p.add_argument("--prepared", type=Path, required=True)
    p.add_argument("--legacy", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-workers", type=int, default=4)
    args = p.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("dispatcher requires Slurm")
    base, study = read_json(args.base_config), read_json(args.config)
    validate_config(study, base)
    resources = validate_gate(args.legacy, base, args.prepared / "graphs/manifest.json")
    accepted = validate_acceptance(args.output, study, base, args.prepared / "graphs/manifest.json")
    # Both old architecture and the real residual largest-batch backward must fit.
    peak = max(row["peak_torch_reserved_bytes"] for row in accepted["rows"])
    largest = resources["largest_batch_stages"]
    for row in largest:
        row["peak_torch_reserved_bytes"] = max(peak, row["peak_torch_reserved_bytes"])
    workers = select_workers(
        resources,
        args.max_workers,
        int(os.environ["SLURM_CPUS_PER_TASK"]),
        base["threads"],
        int(os.environ.get("SLURM_MEM_PER_NODE", "32768")) * 1024**2,
    )
    jobs = []
    for task in study["tasks"]:
        source = read_json(args.output / task / "source.json")
        if (
            source["status"] != "complete"
            or source["identity"]["implementation_hash"] != implementation_identity()
        ):
            raise ValueError("unprepared source")
        cost = sum(ref["training"]["optimizer_steps"] for ref in source["references"][1:])
        jobs.extend((cost, task, variant) for variant in ["raw_residual", "feature_residual"])
    jobs.sort(key=lambda value: (-value[0], value[1], value[2]))
    cli = Path(__file__).with_name("run.py")
    shared = [
        "--config",
        str(args.config),
        "--base-config",
        str(args.base_config),
        "--prepared",
        str(args.prepared),
        "--legacy",
        str(args.legacy),
        "--output",
        str(args.output),
    ]
    pool = args.output / "pool"
    pool.mkdir(exist_ok=True)
    record = {
        "status": "running",
        "workers": workers,
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "study_hash": digest(study),
        "implementation_hash": implementation_identity(),
        "results": {},
        "old_experiment": "paused; independent output and jobs",
        "test_labels_used": False,
    }
    active = {}
    started = time.perf_counter()
    with task_lock(pool / ".lock"):
        if (pool / "execution.json").exists():
            (pool / "execution.json").replace(pool / f"execution-attempt-{time.time_ns()}.json")
        try:
            while jobs or active:
                while jobs and len(active) < workers:
                    _, task, variant = jobs.pop(0)
                    key = f"{task}-{variant}"
                    log = (pool / f"{key}-{time.time_ns()}.out").open("w", encoding="utf-8")
                    command = [
                        sys.executable,
                        str(cli),
                        "run",
                        *shared,
                        "--task",
                        task,
                        "--variant",
                        variant,
                    ]
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                    active[key] = (process, log)
                    record["results"][key] = {
                        "status": "running",
                        "pid": process.pid,
                        "log": log.name,
                    }
                for key, (process, log) in list(active.items()):
                    code = process.poll()
                    if code is not None:
                        log.close()
                        record["results"][key].update(
                            status="complete" if code == 0 else "failed", exit_code=code
                        )
                        del active[key]
                record["wall_seconds"] = time.perf_counter() - started
                atomic_write(pool / "execution.json", record)
                if jobs or active:
                    time.sleep(5)
            subprocess.run([sys.executable, str(cli), "summarize", *shared], check=True)
            summary = read_json(args.output / "reports/summary.json")
            record["status"] = (
                "complete"
                if summary["status"] == "complete"
                and all(v["exit_code"] == 0 for v in record["results"].values())
                else "failed"
            )
            atomic_write(pool / "execution.json", record)
            if record["status"] != "complete":
                raise RuntimeError("incomplete residual comparison; see pool logs")
        finally:
            for process, log in active.values():
                process.terminate()
                process.wait()
                log.close()


if __name__ == "__main__":
    main()
