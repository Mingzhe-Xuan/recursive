"""Share one Slurm GPU allocation across independent tasks; serialize deployment evaluation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, code_identity, digest, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from task_schedule import load_schedule, validate_groups

GIB = 1024**3


def wave_tasks(index: int, size: int = 4, schedule=None) -> list[str]:
    names = list(TASKS)
    if index < 0 or size < 1 or index * size >= len(names):
        raise ValueError("wave index outside the complete task list")
    if schedule is not None:
        return validate_groups(schedule)[index]["tasks"]
    return names[index * size : (index + 1) * size]


def select_workers(resources, maximum, allocated_cpus, threads, host_available=None):
    if maximum < 1 or threads < 1 or allocated_cpus < threads:
        raise ValueError("invalid worker/CPU allocation")
    limit = min(maximum, 4, allocated_cpus // threads)
    if host_available is not None:
        limit = min(limit, max(1, host_available // (8 * GIB)))
    if resources.get("largest_batch_status") != "measured":
        return 1
    rows = resources["largest_batch_stages"]
    if [row["round"] for row in rows] != [0, 1]:
        raise ValueError("incomplete largest-batch measurements")
    total = resources.get("device_memory_bytes")
    peaks = [row.get("peak_torch_reserved_bytes") for row in rows]
    if not total or any(not value or value < 0 for value in peaks):
        raise ValueError("GPU memory measurements are missing")
    per_worker = 2 * max(peaks) + GIB
    return max(1, min(limit, int(total * 0.75) // per_worker))


def validate_gate(run: Path, config: dict, graph_manifest: Path | None = None) -> dict:
    accepted = read_json(run / "real_acceptance.json")
    path = run / "pilot_resources.json"
    resources = read_json(path)
    if (
        accepted.get("status") != "passed"
        or accepted.get("resource_report_sha256") != file_hash(path)
        or resources.get("status") != "measured"
        or resources.get("device") != "cuda"
        or resources.get("config_hash") != digest(config)
        or resources.get("schema") != 1
        or resources.get("core_code_hash") != code_identity()
        or not resources.get("graphs_sha256")
        or accepted.get("graphs_sha256") != resources["graphs_sha256"]
        or (graph_manifest is not None and file_hash(graph_manifest) != resources["graphs_sha256"])
    ):
        raise ValueError("pool requires matching real CUDA acceptance and resource report")
    return resources


def host_available_bytes():
    path = Path("/proc/meminfo")
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    return None


def run_wave(
    prepared,
    run,
    config_path,
    config,
    index,
    workers,
    device="cuda",
    cli=None,
    gate=None,
    schedule=None,
):
    if not 1 <= workers <= 4:
        raise ValueError("worker count must be between one and four")
    names = wave_tasks(index, schedule=schedule)
    workers = min(workers, len(names))
    if workers < 1:
        raise ValueError("workers must be positive")
    directory = run / "pool" / f"wave_{index:03d}"
    directory.mkdir(parents=True, exist_ok=True)
    cli = cli or Path(__file__).with_name("run.py")
    started = time.perf_counter()
    record = {
        "status": "running",
        "wave": index,
        "tasks": names,
        "workers": workers,
        "config_hash": digest(config),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "training_condition": "independent processes sharing this one GPU allocation",
        "evaluation_condition": "serial after every training process in this wave exits",
        "training_wall_time_interpretation": "includes contention; not isolated GPU busy time",
        "results": {},
        "resource_gate": gate,
        "device": device,
        "allocated_gpu_count": 1 if device == "cuda" else 0,
    }
    handles = {}
    active = {}

    def task_root(task):
        return run / "cgcnn" / task / f"seed_{config['seed']}"

    def command(action, task):
        return [
            sys.executable,
            str(cli),
            action,
            "--config",
            str(config_path),
            "--prepared",
            str(prepared),
            "--output",
            str(run),
            "--task",
            task,
            "--device",
            device,
        ]

    def save():
        atomic_write(directory / "execution.json", record)

    def context(task, status):
        atomic_write(
            task_root(task) / "execution_context.json",
            {
                "status": status,
                "wave": index,
                "slurm_job_id": record["slurm_job_id"],
                "config_hash": record["config_hash"],
                "max_training_processes": workers,
                "training_gpu_condition": record["training_condition"],
                "evaluation_gpu_condition": record["evaluation_condition"],
                "training_wall_time_interpretation": record["training_wall_time_interpretation"],
            },
        )

    def preserve_old_report(task):
        path = task_root(task) / "report.json"
        if path.exists():
            target = directory / f"{task}-previous-report-{time.time_ns()}.json"
            path.replace(target)

    with task_lock(directory / ".lock"):
        for task in names:
            protocol = task_root(task) / "protocol.json"
            if protocol.exists() and read_json(protocol) != config:
                raise ValueError("existing task protocol does not match pool configuration")
            if (task_root(task) / "report.json").exists() and not protocol.is_file():
                raise ValueError("existing report has no matching task protocol")
        previous_path = directory / "execution.json"
        if previous_path.is_file():
            previous = read_json(previous_path)
            if previous["config_hash"] != record["config_hash"]:
                raise ValueError("existing wave has a different configuration")
            record["previous_observed_wall_seconds"] = previous.get(
                "wave_wall_seconds", 0
            ) + previous.get("previous_observed_wall_seconds", 0)
            previous_path.replace(directory / f"execution-attempt-{time.time_ns()}.json")
        save()
        pending = iter(names)
        pending_done = False
        try:
            while active or not pending_done:
                while len(active) < workers and not pending_done:
                    task = next(pending, None)
                    if task is None:
                        pending_done = True
                        break
                    preserve_old_report(task)
                    context(task, "training")
                    handles[task] = (directory / f"{task}-run.log").open("a", encoding="utf-8")
                    record["results"][task] = {"run_started_at": time.time()}
                    active[task] = subprocess.Popen(
                        command("run", task), stdout=handles[task], stderr=subprocess.STDOUT
                    )
                for task, process in list(active.items()):
                    code = process.poll()
                    if code is None:
                        continue
                    handles.pop(task).close()
                    del active[task]
                    record["results"][task].update(run_exit_code=code, run_finished_at=time.time())
                    context(task, "trained" if code == 0 else "failed")
                    if code:
                        preserve_old_report(task)
                    save()
                if active:
                    time.sleep(0.2)
            for task in names:
                entry = record["results"][task]
                if entry["run_exit_code"]:
                    continue
                context(task, "evaluating")
                entry["evaluation_started_at"] = time.time()
                with (directory / f"{task}-evaluate.log").open("a", encoding="utf-8") as output:
                    process = subprocess.Popen(
                        command("evaluate", task), stdout=output, stderr=subprocess.STDOUT
                    )
                    active[task] = process
                    code = process.wait()
                    del active[task]
                entry.update(evaluation_exit_code=code, evaluation_finished_at=time.time())
                context(task, "complete" if code == 0 else "failed")
                if code:
                    preserve_old_report(task)
                save()
            record["status"] = (
                "complete"
                if all(
                    row.get("run_exit_code") == 0 and row.get("evaluation_exit_code") == 0
                    for row in record["results"].values()
                )
                else "failed"
            )
        except BaseException as exc:
            record["status"] = "failed"
            record["launcher_error"] = str(exc)
            for task in active:
                context(task, "interrupted")
            raise
        finally:
            for process in active.values():
                if process.poll() is None:
                    process.terminate()
            for process in active.values():
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for handle in handles.values():
                handle.close()
            for task in active:
                preserve_old_report(task)
            record["wave_wall_seconds"] = time.perf_counter() - started
            save()
    return record


def enrich_summary(run: Path, summary: dict) -> dict:
    waves = [read_json(path) for path in sorted((run / "pool").glob("wave_*/execution.json"))]
    if waves:
        summary["execution_context"] = {
            "training_gpu_condition": "independent tasks share a single Slurm GPU per wave",
            "deployment_benchmark_gpu_condition": "serial after each wave's training processes exit",
            "stage_wall_seconds": "includes sharing contention; not isolated GPU busy time",
            "observed_wave_wall_seconds": sum(
                wave.get("wave_wall_seconds", 0) + wave.get("previous_observed_wall_seconds", 0)
                for wave in waves
            ),
            "wave_wall_scope": "launcher lifetime, excludes scheduler/bootstrap overhead",
            "task_schedule_sha256": file_hash(run / "pool/task_schedule.json")
            if (run / "pool/task_schedule.json").is_file()
            else None,
            "observed_reserved_gpu_seconds": sum(
                (wave.get("wave_wall_seconds", 0) + wave.get("previous_observed_wall_seconds", 0))
                * wave.get("allocated_gpu_count", 0)
                for wave in waves
            ),
            "waves": [
                {key: wave[key] for key in ["wave", "workers", "status", "tasks"]} for wave in waves
            ],
        }
        for row in summary["coverage"]:
            path = (
                run / "cgcnn" / row["task"] / f"seed_{summary['seed']}" / "execution_context.json"
            )
            if path.is_file() and read_json(path)["status"] != "complete":
                row["status"] = "failed" if read_json(path)["status"] == "failed" else "incomplete"
        summary["completed_tasks"] = sum(row["status"] == "complete" for row in summary["coverage"])
        summary["status"] = "complete" if summary["completed_tasks"] == len(TASKS) else "partial"
        atomic_write(run / "reports/summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wave-index", type=int, required=True)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("production pool requires a Slurm allocation")
    config = read_json(args.config)
    resources = validate_gate(args.output, config, args.prepared / "graphs/manifest.json")
    schedule = load_schedule(args.output, args.prepared, config)
    host_available = host_available_bytes()
    workers = select_workers(
        resources,
        args.max_workers,
        int(os.environ["SLURM_CPUS_PER_TASK"]),
        config["threads"],
        host_available,
    )
    gate = {
        "resources_sha256": file_hash(args.output / "pilot_resources.json"),
        "largest_batch_status": resources["largest_batch_status"],
        "host_available_before_launch_bytes": host_available,
        "memory_rule": "2*largest peak reserved + 1GiB per worker, 75% GPU; host planning 8GiB/worker",
        "fallback": "one worker if largest-batch measurement is unavailable or headroom is low",
        "task_schedule_sha256": file_hash(args.output / "pool/task_schedule.json")
        if schedule is not None
        else None,
    }
    result = run_wave(
        args.prepared,
        args.output,
        args.config,
        config,
        args.wave_index,
        workers,
        gate=gate,
        schedule=schedule,
    )
    print(result)
    raise SystemExit(0 if result["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
