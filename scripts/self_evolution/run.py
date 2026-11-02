"""CLI for CGCNN seed-123 preparation, stages, and deferred test evaluation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.data.graphs import GraphConfig
from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, read_json


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=["prepare", "run", "evaluate", "summarize", "tasks"])
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument(
        "--source", type=Path, default=Path("data/manifests/self_evolution/jarvis_2021.json")
    )
    parser.add_argument("--task", choices=list(TASKS))
    parser.add_argument("--task-index", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--stop-round", type=int)
    parser.add_argument(
        "--no-controls", action="store_true", help="pilot only; reports require controls"
    )
    args = parser.parse_args()
    config = read_json(args.config)
    if args.action == "tasks":
        print(json.dumps(list(TASKS)))
        return
    if args.action == "prepare":
        from self_evolution.data.prepare import prepare_dataset

        if args.archive is None or args.prepared is None:
            parser.error("prepare requires --archive and --prepared")
        print(
            json.dumps(
                prepare_dataset(
                    args.archive,
                    args.source,
                    args.prepared,
                    GraphConfig(**config["graph"]),
                    args.workers,
                    config["split"]["seed"],
                )
            )
        )
        return
    if args.output is None:
        parser.error("--output required")
    if args.action == "summarize":
        from execution_pool import enrich_summary
        from execution_scope import summarize_scope

        print(json.dumps(enrich_summary(args.output, summarize_scope(args.output, config))))
        return
    if args.task_index is not None:
        if not 0 <= args.task_index < len(TASKS):
            parser.error("task-index outside complete task list")
        args.task = list(TASKS)[args.task_index]
    if args.task is None or args.prepared is None:
        parser.error("--task/--task-index and --prepared required")
    from execution_scope import load_scope

    scope = load_scope(args.output, config)
    if scope is not None and args.task not in scope["selected_tasks"]:
        parser.error("task is outside the current execution scope and has been deferred")
    failure = args.output / "cgcnn" / args.task / f"seed_{config['seed']}" / "failure.json"
    try:
        if args.device.split(":")[0] == "cuda":
            environment = (
                args.output
                / "environments"
                / (
                    f"{args.task}-{args.action}-{os.environ.get('SLURM_JOB_ID', 'local')}-{os.getpid()}.json"
                )
            )
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("inspect_environment.py")),
                    "--gpu",
                    "--output",
                    str(environment),
                ],
                check=True,
            )
        from cache_provenance import audit_task

        root = failure.parent
        if args.action == "run":
            from self_evolution.pipeline.chain import run_task

            run_task(
                args.prepared,
                args.output,
                args.task,
                config,
                args.device,
                args.stop_round,
                not args.no_controls,
            )
            audit_task(root, args.prepared, config)
        else:
            from self_evolution.evaluation.report import evaluate_task

            audit_task(root, args.prepared, config, require_complete=True)
            evaluate_task(args.prepared, args.output, args.task, config, args.device)
        if failure.exists():
            failure.unlink()
    except Exception as exc:
        atomic_write(
            failure,
            {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "slurm_job": os.environ.get("SLURM_JOB_ID"),
                "action": args.action,
            },
        )
        raise


if __name__ == "__main__":
    main()
