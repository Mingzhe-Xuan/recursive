"""Slurm-only iComformer geometry, training and experiment orchestration."""

import argparse
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch
from self_evolution.io import atomic_write, read_json
from icomformer_scaling.graphs import prepare
from icomformer_scaling.source import audit


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=["check", "prepare", "run", "summarize"])
    parser.add_argument(
        "--config", type=Path, default=Path("configs/icomformer_scaling/seed123.json")
    )
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--old-prepared", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cgcnn-summary", type=Path)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("all iComformer server work requires Slurm")
    config = read_json(args.config)
    if args.action == "check":
        import torch_geometric
        import torch_scatter
        import jarvis
        from jarvis.core.atoms import Atoms

        versions = {
            name: importlib.metadata.version(name)
            for name in [
                "torch",
                "torch-geometric",
                "torch-scatter",
                "jarvis-tools",
                "numpy",
                "scipy",
                "matplotlib",
                "pytest",
            ]
        }
        required = {
            "torch": "2.8.0+cu128",
            "torch-geometric": "2.6.1",
            "torch-scatter": "2.1.2+pt28cu128",
            "jarvis-tools": "2026.4.2",
            "numpy": "2.2.6",
        }
        if any(versions[name] != value for name, value in required.items()):
            raise ValueError(f"unlocked server environment: {versions}")
        if not Path(jarvis.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()):
            raise ValueError("Jarvis import must resolve inside the independent iComformer venv")
        result = {
            "status": "passed",
            "versions": versions,
            "source": audit(),
            "python": sys.version,
            "slurm_job": os.environ["SLURM_JOB_ID"],
            "pyg": torch_geometric.__version__,
            "scatter": torch_scatter.__version__,
            "jarvis_atoms": str(Atoms),
            "jarvis_module_path": str(jarvis.__file__),
            "venv_prefix": sys.prefix,
            "pip_freeze": subprocess.check_output(
                [sys.executable, "-m", "pip", "freeze", "--all"], text=True
            ),
        }
        atomic_write(args.output, result)
        print("ENVIRONMENT", versions, flush=True)
    elif args.action == "prepare":
        torch.set_num_threads(1)
        prepare(
            args.archive,
            args.old_prepared,
            args.prepared,
            config["graph"],
            int(os.environ.get("SLURM_CPUS_PER_TASK", "4")),
        )
        print("FULL_GEOMETRY_COMPLETE", flush=True)
    elif args.action == "run":
        from icomformer_scaling.pipeline import run_task

        failure = args.output / args.task / "failure.json"
        try:
            if args.device.startswith("cuda"):
                subprocess.run(
                    [
                        sys.executable,
                        "scripts/self_evolution/inspect_environment.py",
                        "--gpu",
                        "--output",
                        str(
                            args.output.parent
                            / "environments"
                            / f"worker-{args.task}-{os.getpid()}.json"
                        ),
                    ],
                    check=True,
                )
            run_task(args.prepared, args.old_prepared, args.output, args.task, config, args.device)
            if failure.exists():
                failure.unlink()
        except BaseException as exc:
            atomic_write(
                failure,
                {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                    "slurm_job_id": os.environ["SLURM_JOB_ID"],
                },
            )
            raise
    else:
        from icomformer_scaling.reporting import summarize

        result = summarize(args.output, config, args.old_prepared, args.cgcnn_summary)
        print("SUMMARY", result["status"], "points", len(result["rows"]), flush=True)
        if result["status"] != "complete":
            raise RuntimeError("incomplete iComformer comparison")


if __name__ == "__main__":
    main()
