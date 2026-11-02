"""Validation-only matched-budget comparison; no held-out test evaluation."""

import csv
import math
from pathlib import Path
import time

from self_evolution.io import atomic_write, digest, file_hash, read_json
from residual_scaling.protocol import VARIANTS, implementation_identity
from residual_scaling.cache import Archive


def summarize(output, study):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    reports = output / f"reports-staging-{time.time_ns()}"
    reports.mkdir()
    coverage, rows = [], []
    for task in study["tasks"]:
        root = output / task
        task_rows = []
        for variant in VARIANTS:
            try:
                source = read_json(root / "source.json")
                if (
                    source["status"] != "complete"
                    or source["identity"]["study_hash"] != digest(study)
                    or source["identity"]["implementation_hash"] != implementation_identity()
                ):
                    raise ValueError("source study identity mismatch")
                if variant == "direct":
                    values = source["direct_rows"]
                else:
                    report = read_json(root / variant / "report.json")
                    if (
                        report["status"] != "complete"
                        or report["protocol_identity"] != source["identity"]
                    ):
                        raise ValueError("residual branch is not complete")
                    values = report["rows"]
                if [v["round"] for v in values] != [0, 1, 2]:
                    raise ValueError("missing required comparison rounds")
                cumulative = 0
                verified_rows = []
                for r, row in enumerate(values):
                    if (
                        row["task"] != task
                        or row["variant"] != variant
                        or row["optimizer_steps"]
                        != source["references"][r]["training"]["optimizer_steps"]
                        or not math.isfinite(row["val_mae"])
                        or row["val_mae"] < 0
                    ):
                        raise ValueError("comparison task/variant/step budget mismatch")
                    stage = root / ("direct" if r == 0 else variant) / f"round_{r:03d}"
                    if file_hash(stage / "cache/manifest.json") != row["cache_sha256"]:
                        raise ValueError("comparison cache identity changed")
                    checkpoint = (
                        Path(source["references"][r]["stage"]) / "best.pt"
                        if r == 0 or variant == "direct"
                        else stage / "best.pt"
                    )
                    if file_hash(checkpoint) != row["checkpoint_sha256"]:
                        raise ValueError("comparison checkpoint changed")
                    Archive(stage / "cache").verify_all()
                    cumulative += row["optimizer_steps"]
                    value = {
                        **row,
                        "cumulative_optimizer_steps": cumulative,
                        "seed": study["seed"],
                        "evaluation_split": "validation",
                    }
                    verified_rows.append(value)
                task_rows.extend(verified_rows)
                coverage.append({"task": task, "variant": variant, "status": "complete"})
            except (ValueError, KeyError, OSError) as exc:
                coverage.append(
                    {"task": task, "variant": variant, "status": "incomplete", "reason": str(exc)}
                )
        rows.extend(task_rows)
        if task_rows:
            fig, axes = plt.subplots(1, 2, figsize=(11, 4))
            for variant in VARIANTS:
                values = [v for v in task_rows if v["variant"] == variant]
                if len(values) != 3:
                    continue
                axes[0].plot(
                    [v["round"] for v in values],
                    [v["val_mae"] for v in values],
                    "o-",
                    label=variant,
                )
                axes[1].plot(
                    [v["cumulative_optimizer_steps"] for v in values],
                    [v["val_mae"] for v in values],
                    "o-",
                    label=variant,
                )
            axes[0].set(xlabel="Round", ylabel="Validation MAE (original units)", xticks=[0, 1, 2])
            axes[1].set(xlabel="Cumulative optimizer steps", ylabel="Validation MAE")
            axes[0].legend()
            axes[1].legend()
            fig.suptitle(f"{task} / seed {study['seed']} / no test selection")
            fig.tight_layout()
            for ext in ["png", "svg"]:
                fig.savefig(reports / f"{task}.{ext}", dpi=160)
            plt.close(fig)
    if rows:
        keys = sorted(set().union(*(row.keys() for row in rows)))
        with (reports / "validation_metrics.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    result = {
        "status": "complete"
        if len(coverage) == len(study["tasks"]) * 3
        and all(c["status"] == "complete" for c in coverage)
        else "partial",
        "scope": study,
        "coverage": coverage,
        "rows": rows,
        "seeds": 1,
        "test_labels_used": False,
        "budget_match": "optimizer update count; wall time and adapter parameters reported separately",
        "epoch_zero_fallback": False,
    }
    atomic_write(reports / "summary.json", result)
    if (output / "reports").exists():
        archive = output / "reports_history" / str(time.time_ns())
        archive.parent.mkdir(exist_ok=True)
        (output / "reports").replace(archive)
    reports.replace(output / "reports")
    return result
