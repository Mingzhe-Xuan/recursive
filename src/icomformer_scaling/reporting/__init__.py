"""Complete validation curves, existing-CGCNN comparison, and correction diagnostics."""

import csv
from pathlib import Path
import time

from self_evolution.io import atomic_write, digest, file_hash, read_json
from residual_scaling.cache import Archive
from icomformer_scaling.pipeline import implementation_identity


def summarize(output, config, old_prepared=None, cgcnn_summary=None, diagnose=True):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output)
    reports = output / f"reports-staging-{time.time_ns()}"
    reports.mkdir(parents=True)
    coverage, rows = [], []
    for task in config["tasks"]:
        root = output / task
        for variant in config["variants"]:
            try:
                source = read_json(root / "source.json")
                report = read_json(root / variant / "report.json")
                if (
                    source["status"] != "complete"
                    or source["identity"]["study_hash"] != digest(config)
                    or source["identity"]["implementation_hash"] != implementation_identity()
                    or report["status"] != "complete"
                    or report["protocol_identity"] != source["identity"]
                ):
                    raise ValueError("incomplete or changed source branch")
                if [r["round"] for r in report["rows"]] != [0, 1, 2]:
                    raise ValueError("missing comparison rounds")
                verified, steps, parameters = [], 0, 0
                for r, row in enumerate(report["rows"]):
                    if (
                        row["task"] != task
                        or row["variant"] != variant
                        or row["optimizer_steps"]
                        != source["references"][r]["training"]["optimizer_steps"]
                    ):
                        raise ValueError("mismatched task or direct update budget")
                    stage = root / ("direct" if r == 0 else variant) / f"round_{r:03d}"
                    if (
                        file_hash(stage / "best.pt") != row["checkpoint_sha256"]
                        or file_hash(stage / "cache/manifest.json") != row["cache_sha256"]
                    ):
                        raise ValueError("report checkpoint/archive changed")
                    archive = Archive(stage / "cache")
                    archive.verify_all()
                    if (
                        archive.manifest["structures"] != config["expected_structures"]
                        or archive.manifest["width"] != config["model"]["hidden"]
                    ):
                        raise ValueError("incomplete full-library archive")
                    if variant != "direct" and r > 0:
                        metrics = read_json(stage / "training.json")
                        ref = source["references"][r]["training"]
                        if (
                            metrics["stage_seed"] != ref["stage_seed"]
                            or metrics["normalization"] != source["normalization"]
                        ):
                            raise ValueError("residual seed or normalization mismatch")
                    if not (root / variant / f"chain_check_{r:03d}.json").exists() and not (
                        r == 0 and variant != "direct"
                    ):
                        raise ValueError("missing raw-to-cached chain check")
                    steps += row["optimizer_steps"]
                    parameters += row["parameters"]
                    verified.append(
                        {
                            **row,
                            "seed": config["seed"],
                            "evaluation_split": "validation",
                            "cumulative_optimizer_steps": steps,
                            "cumulative_parameters": parameters,
                        }
                    )
                rows.extend(verified)
                coverage.append({"task": task, "variant": variant, "status": "complete"})
            except (OSError, ValueError, KeyError) as exc:
                coverage.append(
                    {"task": task, "variant": variant, "status": "incomplete", "reason": str(exc)}
                )
        task_rows = [r for r in rows if r["task"] == task]
        if task_rows:
            fig, axes = plt.subplots(1, 2, figsize=(11, 4))
            for variant in config["variants"]:
                points = [r for r in task_rows if r["variant"] == variant]
                if len(points) != 3:
                    continue
                axes[0].plot(
                    [p["round"] for p in points],
                    [p["val_mae"] for p in points],
                    "o-",
                    label=variant,
                )
                axes[1].plot(
                    [p["cumulative_optimizer_steps"] for p in points],
                    [p["val_mae"] for p in points],
                    "o-",
                    label=variant,
                )
            axes[0].set(xlabel="Round", ylabel="Validation MAE", xticks=[0, 1, 2])
            axes[1].set(xlabel="Cumulative optimizer updates", ylabel="Validation MAE")
            for ax in axes:
                ax.legend(fontsize=8)
            fig.suptitle(f"iComformer / {task} / seed {config['seed']}")
            fig.tight_layout()
            for ext in ["png", "svg"]:
                fig.savefig(reports / f"{task}.{ext}", dpi=160)
            plt.close(fig)
    complete = len(coverage) == len(config["tasks"]) * 3 and all(
        c["status"] == "complete" for c in coverage
    )
    result = {
        "status": "complete" if complete else "partial",
        "scope": config,
        "coverage": coverage,
        "rows": rows,
        "test_labels_used": False,
        "seeds": 1,
        "epoch_zero_fallback": False,
    }
    atomic_write(reports / "summary.json", result)
    if rows:
        with (reports / "validation_metrics.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=sorted(set().union(*(row.keys() for row in rows)))
            )
            writer.writeheader()
            writer.writerows(rows)
    if (output / "reports").exists():
        old = output / "reports_history" / str(time.time_ns())
        old.parent.mkdir(exist_ok=True)
        (output / "reports").replace(old)
    reports.replace(output / "reports")
    if complete and cgcnn_summary is not None:
        baseline = read_json(cgcnn_summary)
        if (
            baseline["status"] != "complete"
            or baseline["test_labels_used"]
            or baseline["scope"]["seed"] != config["seed"]
        ):
            raise ValueError("CGCNN comparison requires the completed matching validation study")
        for task in config["tasks"]:
            previous_source = read_json(Path(cgcnn_summary).parents[1] / task / "source.json")
            current_source = read_json(output / task / "source.json")
            if (
                previous_source["identity"]["task_sha256"]
                != current_source["identity"]["task_sha256"]
            ):
                raise ValueError("cross-backbone tasks/splits differ")
        values = {(r["task"], r["variant"], r["round"]): r for r in baseline["rows"]}
        comparisons = []
        for row in rows:
            previous = values[(row["task"], row["variant"], row["round"])]
            comparisons.append(
                {
                    "task": row["task"],
                    "variant": row["variant"],
                    "round": row["round"],
                    "icomformer_val_mae": row["val_mae"],
                    "cgcnn_val_mae": previous["val_mae"],
                    "mae_reduction_percent": 100
                    * (previous["val_mae"] - row["val_mae"])
                    / previous["val_mae"],
                    "icomformer_parameters": row["parameters"],
                    "cgcnn_parameters": previous["parameters"],
                    "icomformer_cumulative_parameters": row["cumulative_parameters"],
                    "cgcnn_cumulative_parameters": sum(
                        values[(row["task"], row["variant"], r)]["parameters"]
                        for r in range(row["round"] + 1)
                    ),
                    "icomformer_updates": row["cumulative_optimizer_steps"],
                    "cgcnn_updates": previous["cumulative_optimizer_steps"],
                }
            )
        atomic_write(
            output / "reports/cross_backbone.json",
            {
                "rows": comparisons,
                "interpretation": "same project tasks and splits; native geometry/capacity and actual early-stop budgets differ; not an isolated parameter-count ablation",
                "test_labels_used": False,
            },
        )
    if complete and diagnose:
        if old_prepared is None:
            raise ValueError("diagnostics require original task label/split directory")
        from recursive_diagnostics.analysis import analyze

        analyze(
            output,
            old_prepared,
            output.parent / "diagnostics/final-study",
            expected_implementation=implementation_identity(),
        )
    return result
