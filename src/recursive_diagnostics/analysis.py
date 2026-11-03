"""Audit completed archives, analyze their corrections, and plot existing histories."""

import csv
import gzip
from pathlib import Path

import numpy as np

from self_evolution.io import atomic_write, digest, file_hash, read_json
from residual_scaling.cache import Archive
from residual_scaling.protocol import implementation_identity
from recursive_diagnostics.metrics import correction_summary, curve_summary, split_metrics


def predictions(archive):
    values = {}
    for shard in archive.manifest["shards"]:
        data = archive.shard(shard)
        values.update(zip(data["ids"], data["predictions"].double().tolist()))
        archive.decoded.clear()
    if len(values) != archive.manifest["structures"]:
        raise ValueError("prediction coverage mismatch")
    return values


def write_csv(path, values):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(set().union(*(row.keys() for row in values))))
        writer.writeheader()
        writer.writerows(values)


def analyze(study_root, prepared, output, make_plots=True, expected_implementation=None):
    study_root, prepared, output = map(Path, [study_root, prepared, output])
    if output.resolve() == study_root.resolve() or study_root.resolve() in output.resolve().parents:
        raise ValueError("diagnostic output must be outside the completed study")
    summary_path = study_root / "reports/summary.json"
    summary = read_json(summary_path)
    if summary["status"] != "complete" or summary["test_labels_used"]:
        raise ValueError("requires completed validation-only study")
    scope = summary["scope"]
    index = {(row["task"], row["variant"], row["round"]): row for row in summary["rows"]}
    required = {(t, v, r) for t in scope["tasks"] for v in scope["variants"] for r in range(3)}
    if set(index) != required or len(index) != len(summary["rows"]):
        raise ValueError("incomplete or duplicate study coverage")
    seals = {summary_path: file_hash(summary_path)}
    output.mkdir(parents=True, exist_ok=True)
    module_root = Path(__file__).parent
    protocol = {
        "source_summary_sha256": seals[summary_path],
        "diagnostic_code_hash": digest(
            {
                p.relative_to(module_root).as_posix(): p.read_text(encoding="utf-8")
                for p in sorted(module_root.glob("*.py"))
            }
        ),
    }
    if (output / "protocol.json").exists() and read_json(output / "protocol.json") != protocol:
        raise ValueError("diagnostic protocol changed; use a new output directory")
    atomic_write(output / "protocol.json", protocol)
    residuals, corrections, curves, histories = [], [], [], []
    point_clouds = []
    with gzip.open(output / "validation_materials.csv.gz", "wt", encoding="utf-8", newline="") as f:
        material_writer = csv.writer(f)
        material_writer.writerow(
            [
                "task",
                "variant",
                "round",
                "jid",
                "parent_residual",
                "correction",
                "after_residual",
                "absolute_error_gain",
                "status",
            ]
        )
        for task_name in scope["tasks"]:
            root = study_root / task_name
            source_path = root / "source.json"
            source = read_json(source_path)
            task_path = prepared / "tasks" / f"{task_name}.json"
            task = read_json(task_path)
            if (
                source["status"] != "complete"
                or source["identity"]["task_sha256"] != digest(task)
                or source["identity"]["implementation_hash"]
                != (expected_implementation or implementation_identity())
            ):
                raise ValueError("source identity mismatch")
            seals[source_path], seals[task_path] = file_hash(source_path), file_hash(task_path)
            train_ids, val_ids = (task["split"]["ids"][k] for k in ["train", "val"])
            if set(train_ids) & set(val_ids):
                raise ValueError("train/validation overlap")
            norm = source["normalization"]
            variants_predictions = {}
            base_prediction = None
            for variant in scope["variants"]:
                all_predictions = []
                previous_archive = None
                for r in range(3):
                    row = index[(task_name, variant, r)]
                    stage = root / ("direct" if r == 0 else variant) / f"round_{r:03d}"
                    manifest = stage / "cache/manifest.json"
                    seals[manifest] = file_hash(manifest)
                    if seals[manifest] != row["cache_sha256"]:
                        raise ValueError("report archive mismatch")
                    archive = Archive(stage / "cache")
                    ci = archive.manifest["identity"]
                    if (
                        ci["checkpoint_sha256"] != row["checkpoint_sha256"]
                        or ci["normalization"] != norm
                        or archive.manifest["structures"] != scope["expected_structures"]
                    ):
                        raise ValueError("archive checkpoint/normalization/count mismatch")
                    if (
                        r > 0
                        and variant != "direct"
                        and (
                            ci["prediction_parent"] != previous_archive
                            or ci["node_parent"]
                            != (previous_archive if variant == "feature_residual" else None)
                        )
                    ):
                        raise ValueError("correction parent branch mismatch")
                    previous_archive = archive.identity
                    ref = source["references"][r]
                    checkpoint = (
                        Path(ref["stage"]) / "best.pt"
                        if variant == "direct" or r == 0
                        else stage / "best.pt"
                    )
                    seals[checkpoint] = file_hash(checkpoint)
                    if seals[checkpoint] != row["checkpoint_sha256"]:
                        raise ValueError("checkpoint changed")
                    if variant == "direct" or r == 0:
                        metrics = ref["training"]
                    else:
                        metrics_path = stage / "training.json"
                        seals[metrics_path] = file_hash(metrics_path)
                        metrics = read_json(metrics_path)
                    if (
                        metrics["optimizer_steps"] != row["optimizer_steps"]
                        or metrics["normalization"] != norm
                    ):
                        raise ValueError("training budget/normalization mismatch")
                    if r == 0 and base_prediction is not None:
                        cached = base_prediction
                    else:
                        cached = predictions(archive)
                        if r == 0:
                            base_prediction = cached
                    scores = split_metrics(task, cached, norm["std"])
                    np.testing.assert_allclose(
                        scores["val"]["mae"], row["val_mae"], rtol=1e-4, atol=2e-5
                    )
                    for split, values in scores.items():
                        residuals.append(
                            {
                                "task": task_name,
                                "variant": variant,
                                "round": r,
                                "split": split,
                                **values,
                            }
                        )
                    if r > 0 or variant == "direct":
                        history = metrics["history"]
                        curves.append(
                            {
                                "task": task_name,
                                "variant": variant,
                                "round": r,
                                **curve_summary(history),
                            }
                        )
                        histories.append(
                            {
                                "task": task_name,
                                "variant": variant,
                                "round": r,
                                "normalization_std": norm["std"],
                                "history": history,
                            }
                        )
                    all_predictions.append(cached)
                variants_predictions[variant] = all_predictions
                for r in [1, 2]:
                    before, current = all_predictions[r - 1 : r + 1]
                    for split in ["train", "val"]:
                        ids = task["split"]["ids"][split]
                        e = np.array([task["labels"][jid] - before[jid] for jid in ids])
                        delta = np.array([current[jid] - before[jid] for jid in ids])
                        comparison = correction_summary(e, delta)
                        corrections.append(
                            {
                                "task": task_name,
                                "variant": variant,
                                "round": r,
                                "split": split,
                                **comparison,
                            }
                        )
                        if split == "val":
                            point_clouds.append(
                                {
                                    "task": task_name,
                                    "variant": variant,
                                    "round": r,
                                    "e": e,
                                    "delta": delta,
                                    "metrics": comparison,
                                }
                            )
                            for jid, parent, correction in zip(ids, e, delta):
                                gain = abs(parent) - abs(parent - correction)
                                status = (
                                    "improved"
                                    if gain > 1e-8
                                    else "worse"
                                    if gain < -1e-8
                                    else "unchanged"
                                )
                                material_writer.writerow(
                                    [
                                        task_name,
                                        variant,
                                        r,
                                        jid,
                                        parent,
                                        correction,
                                        parent - correction,
                                        gain,
                                        status,
                                    ]
                                )
                print("ANALYZED", task_name, variant, flush=True)
            del variants_predictions
    for path, expected in seals.items():
        if file_hash(path) != expected:
            raise ValueError(f"input changed during read-only analysis: {path}")
    report = {
        "status": "complete",
        "scope": scope,
        "source_summary_sha256": seals[summary_path],
        "residuals": residuals,
        "corrections": corrections,
        "learning_curves": curves,
        "test_labels_used": False,
        "predictions_or_weights_updated": False,
        "correction_definition": "e=y-F_previous; delta=F_current-F_previous",
        "training_curve_limitation": "online train-mode MSE is not fixed-checkpoint eval error; val curve is eval MAE",
        "eval_cache_comparison": "best-checkpoint train/val MAE and RMSE in original units",
        "protocol": protocol,
        "input_seals": {str(p): value for p, value in seals.items()},
    }
    write_csv(output / "residuals.csv", residuals)
    flat = [
        {
            **{k: v for k, v in row.items() if k not in ["before", "after"]},
            **{
                prefix + "_" + key: value
                for prefix in ["before", "after"]
                for key, value in row[prefix].items()
            },
        }
        for row in corrections
    ]
    write_csv(output / "corrections.csv", flat)
    write_csv(output / "learning_curves.csv", curves)
    atomic_write(output / "histories.json", histories)
    if make_plots:
        from recursive_diagnostics.plots import plot_all

        plot_all(output, scope, residuals, histories, point_clouds)
    atomic_write(output / "summary.json", report)
    return report
