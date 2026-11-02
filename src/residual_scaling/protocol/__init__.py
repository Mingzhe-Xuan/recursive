"""Immutable experiment identity and audited references to the paused experiment."""

from pathlib import Path
import math

from self_evolution.cache import FeatureStore
from self_evolution.data.tasks import TASKS
from self_evolution.io import code_identity, digest, file_hash, read_json
from self_evolution.training.stage import normalization

VARIANTS = ("direct", "raw_residual", "feature_residual")


def implementation_identity():
    root = Path(__file__).resolve().parents[1]
    return digest(
        {
            p.relative_to(root).as_posix(): digest(p.read_text(encoding="utf-8"))
            for p in sorted(root.rglob("*.py"))
        }
    )


def validate_config(config, base):
    if (
        config["schema"] != 1
        or config["seed"] != base["seed"]
        or config["max_round"] != 2
        or config["eta"] != 1.0
        or config["variants"] != list(VARIANTS)
        or config["budget"] != "legacy_direct_actual_optimizer_steps"
        or config["initialization"] != "legacy_direct_stage_seed_and_native_initialization"
        or config["normalization"] != "fixed_round_zero_training_statistics"
        or config["checkpoint_selection"] != "best_ensemble_validation_mae_after_epoch_one"
        or config["test_policy"] != "sealed_during_method_selection"
        or config["expected_structures"] < 1
        or not config["tasks"]
        or len(set(config["tasks"])) != len(config["tasks"])
        or not set(config["tasks"]) <= set(TASKS)
        or base["backbone"] != "cgcnn"
        or base["max_round"] < 2
        or base["training"]["loss"] != "normalized_mse"
        or base["training"]["optimizer"] != "Adam"
        or base["training"]["scheduler"] != "constant"
    ):
        raise ValueError("unsupported residual study protocol")


def source_task(prepared, legacy, task_name, base, study, graphs, verify_shards=True):
    validate_config(study, base)
    if task_name not in study["tasks"]:
        raise ValueError("task outside the residual study")
    task = read_json(Path(prepared) / "tasks" / f"{task_name}.json")
    if (
        task["status"] != "ready"
        or task["dataset_sha256"] != graphs.manifest["identity"]["dataset_sha256"]
        or len(graphs.ids) != study["expected_structures"]
    ):
        raise ValueError("residual study dataset mismatch")
    root = Path(legacy) / "cgcnn" / task_name / f"seed_{base['seed']}"
    if read_json(root / "protocol.json") != base:
        raise ValueError("legacy scientific protocol changed")
    chain = read_json(root / "chain_manifest.json")
    if (
        chain["task"] != task_name
        or chain["seed"] != base["seed"]
        or chain["config_hash"] != digest(base)
        or len(chain["stages"]) < 3
    ):
        raise ValueError("legacy chain manifest mismatch")
    norm = normalization(task["labels"], task["split"]["ids"]["train"])
    refs, previous = [], None
    for r in range(3):
        stage = root / f"round_{r:03d}"
        training = read_json(stage / "training.json")
        identity = training["identity"]
        checkpoint = file_hash(stage / "best.pt")
        cache = FeatureStore(stage / "cache")
        ci = cache.manifest["identity"]
        if (
            identity["config_hash"] != digest(base)
            or identity["code_hash"] != code_identity()
            or identity["graphs_hash"] != graphs.identity
            or identity["task_hash"] != digest(task)
            or identity["mode"] != "evolution"
            or identity["round"] != r
            or identity["parent_cache"] != previous
            or ci["parent_cache_sha256"] != previous
            or checkpoint != training["checkpoint_sha256"]
            or checkpoint != ci["checkpoint_sha256"]
            or ci["task"] != task_name
            or ci["round"] != r
            or ci["config_hash"] != digest(base)
            or ci["graphs_sha256"] != graphs.identity
            or ci["code_hash"] != code_identity()
            or training["normalization"] != norm
            or cache.manifest["width"] != base["model"]["hidden"]
            or not math.isfinite(training["best_val_mae"])
            or training["optimizer_steps"] < 1
            or chain["stages"][r]["round"] != r
            or chain["stages"][r]["checkpoint_sha256"] != checkpoint
            or chain["stages"][r]["cache_sha256"] != cache.identity
        ):
            raise ValueError("legacy checkpoint/cache/source identity mismatch")
        ids = [jid for shard in cache.manifest["shards"] for jid in shard["ids"]]
        if len(ids) != len(set(ids)) or sorted(ids) != graphs.ids:
            raise ValueError("legacy cache does not cover the full library")
        for shard in cache.manifest["shards"]:
            if shard["atoms"] != [graphs.entries[jid]["atoms"] for jid in shard["ids"]]:
                raise ValueError("legacy atom ordering/count mismatch")
        if verify_shards:
            cache.verify_all()
        refs.append(
            {
                "round": r,
                "stage": str(stage.resolve()),
                "checkpoint_sha256": checkpoint,
                "training_sha256": file_hash(stage / "training.json"),
                "cache_sha256": cache.identity,
                "training": training,
            }
        )
        previous = cache.identity
    identity = {
        "study_hash": digest(study),
        "base_config_hash": digest(base),
        "implementation_hash": implementation_identity(),
        "legacy_core_hash": code_identity(),
        "graphs_sha256": graphs.identity,
        "task_sha256": digest(task),
        "source_checkpoints": [r["checkpoint_sha256"] for r in refs],
        "source_caches": [r["cache_sha256"] for r in refs],
        "source_training": [r["training_sha256"] for r in refs],
    }
    return task, norm, refs, identity
