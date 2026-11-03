"""Read-only correction diagnostics; all server computation runs inside Slurm."""

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch
from recursive_diagnostics.analysis import analyze


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--study", type=Path, required=True)
    p.add_argument("--prepared", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("server diagnostic entry requires a Slurm allocation")
    torch.set_num_threads(min(4, int(os.environ.get("SLURM_CPUS_PER_TASK", 1))))
    result = analyze(args.study, args.prepared, args.output)
    print(
        "COMPLETE",
        len(result["residuals"]),
        "residual rows",
        len(result["corrections"]),
        "correction rows",
        flush=True,
    )


if __name__ == "__main__":
    main()
