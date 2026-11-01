from __future__ import annotations

import csv
from pathlib import Path

from self_evolution.cache import FeatureStore
from self_evolution.data.graphs import GraphStore
from self_evolution.data.tasks import TASKS
from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.training.stage import evaluate, load_stage


def evaluate_task(
    prepared: Path, run: Path, task_name: str, config: dict, device: str = "cuda"
) -> dict:
    task = read_json(prepared / "tasks" / f"{task_name}.json")
    graphs = GraphStore(prepared / "graphs")
    root = run / "cgcnn" / task_name / f"seed_{config['seed']}"
    chain = read_json(root / "chain_manifest.json")
    if (
        chain["status"] != "complete"
        or len(chain["stages"]) != config["max_round"] + 1
        or chain["config_hash"] != digest(config)
    ):
        raise ValueError("test evaluation requires the complete predeclared evolution chain")
    from self_evolution.pipeline.chain import benchmark_chain

    timing = benchmark_chain(root, graphs, config, device)
    output, cumulative_seconds, cumulative_cache = [], 0.0, 0.0
    for mode in ["evolution", "original", "cumulative"]:
        for r in range(config["max_round"] + 1):
            if mode != "evolution" and r == 0:
                continue
            stage = (
                root / f"round_{r:03d}"
                if mode == "evolution"
                else root / "controls" / mode / f"round_{r:03d}"
            )
            training = read_json(stage / "training.json")
            if file_hash(stage / "best.pt") != training["checkpoint_sha256"]:
                raise ValueError("checkpoint changed since training")
            model, checkpoint = load_stage(stage / "best.pt", device)
            parent = (
                FeatureStore(root / f"round_{r - 1:03d}" / "cache")
                if (mode == "evolution" and r > 0)
                else None
            )
            if training["identity"]["parent_cache"] != (
                None if parent is None else parent.identity
            ):
                raise ValueError("evaluation cache does not match trained input")
            result = {
                "task": task_name,
                "unit": TASKS[task_name],
                "mode": mode,
                "round": r,
                "seed": config["seed"],
                "checkpoint_sha256": training["checkpoint_sha256"],
                "optimizer_steps": training["optimizer_steps"],
                "training_and_validation_seconds": training["training_and_validation_seconds"],
            }
            for split, ids in task["split"]["ids"].items():
                score = evaluate(
                    model,
                    graphs,
                    ids,
                    task["labels"],
                    checkpoint["norm"],
                    parent,
                    device,
                    config["training"]["batch_size"],
                )
                result[f"{split}_mae"] = score["mae"]
                prediction_path = stage / "predictions" / f"{split}.csv"
                prediction_path.parent.mkdir(parents=True, exist_ok=True)
                temporary = prediction_path.with_suffix(".csv.partial")
                with temporary.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["jid", "prediction", "target"])
                    writer.writeheader()
                    writer.writerows(score["predictions"])
                temporary.replace(prediction_path)
            if mode == "evolution":
                cumulative_seconds += result["training_and_validation_seconds"]
                cumulative_cache += read_json(stage / "cache_timing.json")["cache_seconds"]
                result.update(
                    cumulative_training_validation_seconds=cumulative_seconds,
                    cumulative_cache_seconds=cumulative_cache,
                    cumulative_optimizer_steps=chain["stages"][r]["cumulative_steps"],
                    deployment_stages=r + 1,
                    full_chain_seconds_per_batch=timing["rows"][r]["full_chain_seconds_per_batch"],
                    cached_last_stage_seconds_per_batch=timing["rows"][r][
                        "cached_last_stage_seconds_per_batch"
                    ],
                )
            atomic_write(stage / "metrics.json", result)
            output.append(result)
    evolution = [row for row in output if row["mode"] == "evolution"]
    baseline = evolution[0]["test_mae"]
    for row in output:
        row["relative_test_improvement"] = (
            None if baseline == 0 else (baseline - row["test_mae"]) / baseline
        )
    best = min(evolution, key=lambda row: (row["val_mae"], row["round"]))
    report = {
        "task": task_name,
        "seed": config["seed"],
        "rows": output,
        "validation_selected_round": best["round"],
        "selected_test_mae": best["test_mae"],
        "baseline_test_mae": baseline,
        "split_hash": task["split"]["membership_hash"],
        "split_source": task["split"]["source"],
        "seeds": 1,
    }
    atomic_write(root / "report.json", report)
    return report


def summarize(run: Path, config: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    reports = run / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    coverage, all_rows, heatmap, heatmap_labels = [], [], [], []
    for task in TASKS:
        path = run / "cgcnn" / task / f"seed_{config['seed']}" / "report.json"
        if not path.exists():
            failure = path.parent / "failure.json"
            coverage.append(
                {
                    "task": task,
                    "status": "failed" if failure.exists() else "incomplete",
                    "reason": read_json(failure) if failure.exists() else None,
                }
            )
            continue
        result = read_json(path)
        coverage.append(
            {
                "task": task,
                "status": "complete",
                "validation_selected_round": result["validation_selected_round"],
            }
        )
        all_rows.extend(result["rows"])
        evo = sorted(
            [r for r in result["rows"] if r["mode"] == "evolution"], key=lambda r: r["round"]
        )
        heatmap.append([r["relative_test_improvement"] for r in evo])
        heatmap_labels.append(task)
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        for mode in ["evolution", "original", "cumulative"]:
            rows = sorted(
                [r for r in result["rows"] if r["mode"] == mode], key=lambda r: r["round"]
            )
            if mode != "evolution":
                rows = [evo[0], *rows]
            axes[0].plot(
                [r["round"] for r in rows], [r["test_mae"] for r in rows], "o-", label=mode
            )
        axes[0].plot(
            [r["round"] for r in evo], [r["val_mae"] for r in evo], "--", label="validation"
        )
        axes[0].set(xlabel="Round (0 = native)", ylabel=f"MAE ({TASKS[task]})")
        axes[0].legend()
        axes[1].plot(
            [
                r["cumulative_training_validation_seconds"] + r["cumulative_cache_seconds"]
                for r in evo
            ],
            [r["test_mae"] for r in evo],
            "o-",
        )
        axes[1].set(xlabel="Cumulative train + validation + cache wall seconds", ylabel="Test MAE")
        axes[2].plot(
            [r["full_chain_seconds_per_batch"] for r in evo], [r["test_mae"] for r in evo], "o-"
        )
        axes[2].set(xlabel="Full-chain forward seconds / fixed batch", ylabel="Test MAE")
        fig.suptitle(f"CGCNN / {task} / seed {config['seed']} (one seed, no uncertainty band)")
        fig.tight_layout()
        for extension in ["png", "svg"]:
            fig.savefig(reports / f"{task}.{extension}", dpi=160)
        plt.close(fig)
    if heatmap:
        fig, axis = plt.subplots(figsize=(9, max(4, len(heatmap) * 0.3)))
        data = np.array([[np.nan if v is None else v for v in row] for row in heatmap])
        image = axis.imshow(data, aspect="auto", cmap="RdBu", vmin=-0.25, vmax=0.25)
        axis.set(
            yticks=range(len(heatmap_labels)),
            yticklabels=heatmap_labels,
            xticks=range(config["max_round"] + 1),
            xlabel="Round",
            title="Relative test MAE improvement (positive = better)",
        )
        fig.colorbar(image, ax=axis)
        fig.tight_layout()
        fig.savefig(reports / "relative_improvement.png", dpi=180)
        plt.close(fig)
    if all_rows:
        keys = sorted(set().union(*(row.keys() for row in all_rows)))
        with (reports / "metrics.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
    summary = {
        "seed": config["seed"],
        "backbone": "cgcnn",
        "coverage": coverage,
        "completed_tasks": sum(r["status"] == "complete" for r in coverage),
        "required_tasks": len(TASKS),
        "status": "complete" if all(r["status"] == "complete" for r in coverage) else "partial",
    }
    atomic_write(reports / "summary.json", summary)
    return summary
