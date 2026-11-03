"""Immutable provenance and validation-only cached-feature comparison."""

import csv
from pathlib import Path
import time

from self_evolution.data.graphs import GraphStore
from self_evolution.io import atomic_write, code_identity, digest, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from self_evolution.training.stage import normalization
from joint_cgcnn.model import stage_seeds
from joint_cgcnn.training import evaluate, load_model, train


def implementation_identity():
    root = Path(__file__).parents[1]
    return digest(
        {
            p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*.py"))
        }
    )


def validate_config(cfg):
    if (
        cfg["schema"] != 1
        or cfg["name"] != "cgcnn_double_end_to_end"
        or cfg["initialization"] != "independent_fresh_matching_cached_stage_seeds"
        or cfg["test_policy"] != "sealed_during_method_selection"
        or cfg["budget"] != "same_300_epoch_patience50_protocol_not_equal_total_compute"
        or cfg["training"]["optimizer"] != "Adam"
        or cfg["training"]["scheduler"] != "constant"
        or cfg["training"]["loss"] != "normalized_mse"
        or not cfg["tasks"]
        or len(set(cfg["tasks"])) != len(cfg["tasks"])
    ):
        raise ValueError("unsupported joint protocol")


def inputs(prepared, cached, task_name, cfg):
    validate_config(cfg)
    if task_name not in cfg["tasks"]:
        raise ValueError("task outside joint study")
    prepared, cached = Path(prepared), Path(cached)
    graphs = GraphStore(prepared / "graphs")
    task = read_json(prepared / "tasks" / f"{task_name}.json")
    source_path = cached / task_name / "source.json"
    source = read_json(source_path)
    summary_path = cached / "reports/summary.json"
    summary = read_json(summary_path)
    norm = normalization(task["labels"], task["split"]["ids"]["train"])
    base = read_json(Path(source["references"][0]["stage"]).parent / "protocol.json")
    if (
        task["status"] != "ready"
        or source["status"] != "complete"
        or summary["status"] != "complete"
        or summary["scope"]["seed"] != cfg["seed"]
        or task["dataset_sha256"] != graphs.manifest["identity"]["dataset_sha256"]
        or len(graphs.ids) != cfg["expected_structures"]
        or source["task"] != task_name
        or source["normalization"] != norm
        or source["identity"]["task_sha256"] != digest(task)
        or source["identity"]["graphs_sha256"] != graphs.identity
        or source["identity"]["legacy_core_hash"] != code_identity()
        or source["identity"]["base_config_hash"] != digest(base)
        or base["seed"] != cfg["seed"]
        or base["model"] != cfg["model"]
        or base["training"] != cfg["training"]
    ):
        raise ValueError("joint source data/model/training protocol mismatch")
    seeds = stage_seeds(cfg["seed"], task_name)
    for r in [0, 1]:
        ref = source["references"][r]
        if (
            ref["round"] != r
            or ref["training"]["identity"]["stage_seed"] != seeds[r]
            or file_hash(Path(ref["stage"]) / "best.pt") != ref["checkpoint_sha256"]
        ):
            raise ValueError("cached reference checkpoint/initialization mismatch")
    identity = {
        "config_sha256": digest(cfg),
        "implementation_hash": implementation_identity(),
        "legacy_core_hash": code_identity(),
        "graphs_sha256": graphs.identity,
        "task_sha256": digest(task),
        "source_sha256": file_hash(source_path),
        "summary_sha256": file_hash(summary_path),
        "seeds": seeds,
    }
    return task, graphs, norm, identity, summary


def run_task(prepared, cached, output, task_name, cfg, device):
    task, graphs, norm, identity, _ = inputs(prepared, cached, task_name, cfg)
    root = Path(output) / "run" / task_name
    root.mkdir(parents=True, exist_ok=True)
    with task_lock(root / ".lock"):
        done = train(root, cfg, task, graphs, norm, identity, device)
        model, _ = load_model(root / "best.pt", device)
        evaluations = {}
        for split in ["train", "val"]:
            value = evaluate(
                model, graphs, task, norm, device, cfg["training"]["batch_size"], split
            )
            atomic_write(root / f"{split}_predictions.json", value)
            evaluations[split] = value["mae"]
        tolerance = cfg["verification"]
        if abs(evaluations["val"] - done["best_val_mae"]) > (
            tolerance["atol"] + tolerance["rtol"] * abs(done["best_val_mae"])
        ):
            raise ValueError("joint checkpoint validation mismatch")
        result = {
            "task": task_name,
            "status": "complete",
            "identity": identity,
            "train_mae": evaluations["train"],
            "val_mae": evaluations["val"],
            "parameters": done["parameters"],
            "optimizer_steps": done["optimizer_steps"],
            "encoder_update_applications": 2 * done["optimizer_steps"],
            "training_seconds": done["training_seconds"],
            "checkpoint_sha256": done["checkpoint_sha256"],
            "test_labels_used": False,
        }
        atomic_write(root / "result.json", result)
        return result


def summarize(prepared, cached, output, cfg):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output)
    reports = output / f"reports-staging-{time.time_ns()}"
    reports.mkdir(parents=True)
    rows, coverage = [], []
    for name in cfg["tasks"]:
        try:
            _, _, _, identity, summary = inputs(prepared, cached, name, cfg)
            root = output / "run" / name
            joint = read_json(root / "result.json")
            done = read_json(root / "training.json")
            if (
                joint["identity"] != identity
                or done["identity"] != identity
                or joint["checkpoint_sha256"] != file_hash(root / "best.pt")
            ):
                raise ValueError("joint result/checkpoint changed")
            selected = {(r["variant"], r["round"]): r for r in summary["rows"] if r["task"] == name}
            base = selected[("direct", 0)]
            direct = selected[("direct", 1)]
            residual = selected[("feature_residual", 1)]
            encoder_budget = base["optimizer_steps"] + direct["optimizer_steps"]
            prefix = [h for h in done["history"] if 2 * h["optimizer_steps"] <= encoder_budget]
            comparable = min(prefix, key=lambda h: h["val_mae"]) if prefix else None
            improvement = (direct["val_mae"] - joint["val_mae"]) / direct["val_mae"] * 100
            row = {
                "task": name,
                "joint_val_mae": joint["val_mae"],
                "joint_train_mae": joint["train_mae"],
                "joint_best_val_within_cached_encoder_update_budget": None
                if comparable is None
                else comparable["val_mae"],
                "joint_budget_prefix_selected_epoch": None
                if comparable is None
                else comparable["epoch"],
                "joint_encoder_update_budget_ratio": joint["encoder_update_applications"]
                / encoder_budget,
                "cached_direct_r0_mae": base["val_mae"],
                "cached_direct_r1_mae": direct["val_mae"],
                "cached_feature_residual_r1_mae": residual["val_mae"],
                "joint_improvement_over_cached_direct_pct": improvement,
                "joint_optimizer_steps": joint["optimizer_steps"],
                "joint_encoder_update_applications": joint["encoder_update_applications"],
                "joint_parameters": joint["parameters"],
                "cached_total_trained_parameters": base["parameters"] + direct["parameters"],
                "cached_optimizer_steps_r0_plus_r1": base["optimizer_steps"]
                + direct["optimizer_steps"],
                "joint_training_seconds": joint["training_seconds"],
                "cached_training_seconds_r0_plus_r1": base["training_seconds"]
                + direct["training_seconds"],
                "cached_archiving_seconds_r0_plus_r1": base["cache_seconds"]
                + direct["cache_seconds"],
            }
            rows.append(row)
            coverage.append({"task": name, "status": "complete"})
            fig, ax = plt.subplots(figsize=(7, 4))
            history = done["history"]
            ax.plot(
                [h["epoch"] for h in history],
                [h["val_mae"] for h in history],
                label="joint CGCNN x2",
            )
            ax.axhline(direct["val_mae"], label="cached direct R1", color="C1")
            ax.axhline(base["val_mae"], label="cached R0", linestyle=":", color="C2")
            ax.axhline(
                residual["val_mae"],
                label="cached residual R1 (different head)",
                linestyle="--",
                color="C3",
            )
            ax.set(xlabel="Joint training epoch", ylabel="Validation MAE", title=name)
            ax.legend()
            fig.tight_layout()
            for ext in ["png", "svg"]:
                fig.savefig(reports / f"{name}.{ext}", dpi=160)
            plt.close(fig)
        except (OSError, ValueError, KeyError) as exc:
            coverage.append({"task": name, "status": "incomplete", "reason": str(exc)})
    if rows:
        with (reports / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    result = {
        "status": "complete" if all(c["status"] == "complete" for c in coverage) else "partial",
        "config": cfg,
        "coverage": coverage,
        "rows": rows,
        "test_labels_used": False,
        "caveats": "encoder-update prefix is a work proxy, not matched FLOPs; single seed; same early-stop protocol, not equal total compute; joint has one final readout, cached R0 head used only in pretraining; elapsed times may have different GPU contention",
    }
    atomic_write(reports / "summary.json", result)
    if (output / "reports").exists():
        previous = output / "reports_history" / str(time.time_ns())
        previous.parent.mkdir(exist_ok=True)
        (output / "reports").replace(previous)
    reports.replace(output / "reports")
    return result
