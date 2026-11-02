"""Independent matched-budget CGCNN residual validation, rounds zero through two."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.io import atomic_write, read_json
from residual_scaling.pipeline import prepare_task, run_variant, verify_chain
from residual_scaling.protocol import validate_config
from residual_scaling.reporting import summarize


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("action", choices=["prepare", "run", "verify", "summarize"])
    p.add_argument("--config", type=Path, default=Path("configs/residual_scaling/seed123.json"))
    p.add_argument(
        "--base-config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    p.add_argument("--prepared", type=Path)
    p.add_argument("--legacy", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--task")
    p.add_argument("--variant", choices=["direct", "raw_residual", "feature_residual"])
    p.add_argument("--device", default="cuda")
    p.add_argument("--stop-round", type=int, default=2)
    args = p.parse_args()
    study = read_json(args.config)
    base = read_json(args.base_config)
    validate_config(study, base)
    if args.task is not None and args.task not in study["tasks"]:
        p.error("task outside study")
    if args.action == "summarize":
        print(json.dumps(summarize(args.output, study)))
        return
    args.output.mkdir(parents=True, exist_ok=True)
    if args.device.startswith("cuda"):
        if not os.environ.get("SLURM_JOB_ID"):
            raise RuntimeError("CUDA work requires Slurm")
        subprocess.run(
            [
                sys.executable,
                "scripts/self_evolution/inspect_environment.py",
                "--gpu",
                "--output",
                str(
                    args.output
                    / f"environments/{args.action}-{args.task}-{args.variant}-{os.getpid()}.json"
                ),
            ],
            check=True,
        )
    if args.action != "verify" and (args.prepared is None or args.legacy is None):
        p.error("prepared and legacy are required")
    if args.action in ["run", "verify"] and (args.task is None or args.variant is None):
        p.error("task and variant are required")
    failure = (
        args.output / (args.task or "preparation") / (args.variant or "import") / "failure.json"
    )
    try:
        if args.action == "prepare":
            for task in [args.task] if args.task else study["tasks"]:
                print("PREPARING", task, flush=True)
                prepare_task(
                    args.prepared, args.legacy, args.output, task, base, study, args.device
                )
                print("PREPARED", task, flush=True)
        elif args.action == "run":
            run_variant(
                args.prepared,
                args.legacy,
                args.output,
                args.task,
                args.variant,
                base,
                study,
                args.device,
                args.stop_round,
            )
        else:
            verify_chain(
                args.output, args.task, args.variant, base, study, args.stop_round, args.device
            )
        if failure.exists():
            failure.unlink()
    except BaseException as exc:
        atomic_write(
            failure,
            {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
        )
        raise


if __name__ == "__main__":
    main()
