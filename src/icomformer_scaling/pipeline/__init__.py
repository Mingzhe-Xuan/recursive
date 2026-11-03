"""Three independent branches with shared R0 and audited full-library archives."""

from pathlib import Path
import time

import torch

from self_evolution.io import atomic_write, digest, derived_seed, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from self_evolution.training.stage import batches, normalization, synchronize
from residual_scaling.cache import Archive, publish
from icomformer_scaling.graphs import GraphStore, collate_graphs
from icomformer_scaling.model import ModelConfig
from icomformer_scaling.training import load_stage, prediction, train_stage


def implementation_identity():
    root = Path(__file__).parents[1]
    return digest(
        {
            p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*.py"))
        }
    )


def validate_config(config):
    ModelConfig(**config["model"])
    if (
        config["backbone"] != "icomformer"
        or config["max_round"] != 2
        or config["eta"] != 1
        or config["variants"] != ["direct", "raw_residual", "feature_residual"]
        or config["training"]["optimizer"] != "Adam"
        or config["training"]["scheduler"] != "constant"
        or config["test_policy"] != "sealed_during_method_selection"
        or not config["tasks"]
        or len(set(config["tasks"])) != len(config["tasks"])
    ):
        raise ValueError("unsupported iComformer protocol")


def task_source(prepared, old_prepared, output, name, config):
    validate_config(config)
    if name not in config["tasks"]:
        raise ValueError("task outside the current study")
    graphs = GraphStore(Path(prepared) / "graphs")
    task = read_json(Path(old_prepared) / "tasks" / f"{name}.json")
    if (
        task["status"] != "ready"
        or task["dataset_sha256"] != graphs.manifest["identity"]["dataset_sha256"]
        or len(graphs.ids) != config["expected_structures"]
        or file_hash(Path(old_prepared) / "graphs/manifest.json")
        != graphs.manifest["identity"]["source_graphs_sha256"]
    ):
        raise ValueError("original task/data library mismatch")
    norm = normalization(task["labels"], task["split"]["ids"]["train"])
    identity = {
        "study_hash": digest(config),
        "implementation_hash": implementation_identity(),
        "graphs_sha256": graphs.identity,
        "source_graphs_sha256": graphs.manifest["identity"]["source_graphs_sha256"],
        "task_sha256": digest(task),
        "normalization": norm,
    }
    root = Path(output) / name
    root.mkdir(parents=True, exist_ok=True)
    protocol = {"config": config, "identity": identity}
    if (root / "protocol.json").exists() and read_json(root / "protocol.json") != protocol:
        raise ValueError("immutable iComformer task protocol changed")
    atomic_write(root / "protocol.json", protocol)
    return task, graphs, norm, identity


@torch.no_grad()
def cache_model(stage, model, graphs, parent, norm, variant, config, identity, device):
    stage = Path(stage)
    model.eval()
    before = {k: v.detach().clone() for k, v in model.state_dict().items()}
    checkpoint = file_hash(stage / "best.pt")
    cache_identity = {
        **identity,
        "checkpoint_sha256": checkpoint,
        "normalization": norm,
        "prediction_parent": parent.identity
        if parent is not None and variant != "direct"
        else None,
        "node_parent": parent.identity
        if parent is not None and variant != "raw_residual"
        else None,
        "prediction_role": "absolute" if variant == "direct" else "cumulative_residual_ensemble",
        "boundary": "post_fourth_node_update_pre_pooling",
    }

    def producer(ids):
        result = []
        for chunk in batches(ids, config["training"]["batch_size"]):
            batch = collate_graphs([graphs.get(jid) for jid in chunk], device)
            nodes, previous = (
                (None, None)
                if parent is None
                else parent.batch(chunk, graphs, device, variant != "raw_residual")
            )
            hidden, values = prediction(model, batch, nodes, previous, norm, variant)
            hidden, values = hidden.cpu(), values.cpu()
            start = 0
            for i, jid in enumerate(chunk):
                count = graphs.entries[jid]["atoms"]
                result.append((hidden[start : start + count], values[i]))
                start += count
        return result

    synchronize(device)
    start = time.perf_counter()
    archive = publish(
        stage / "cache",
        cache_identity,
        graphs.ids,
        config["model"]["hidden"],
        producer,
        config["cache"]["shard_size"],
    )
    synchronize(device)
    if (
        model.training
        or any(p.grad is not None for p in model.parameters())
        or any(not torch.equal(before[k], v) for k, v in model.state_dict().items())
        or file_hash(stage / "best.pt") != checkpoint
    ):
        raise ValueError("model/BN/checkpoint changed during caching")
    timing = stage / "cache_timing.json"
    if not timing.exists():
        atomic_write(
            timing, {"cache_seconds": time.perf_counter() - start, "cache_sha256": archive.identity}
        )
    elif read_json(timing)["cache_sha256"] != archive.identity:
        raise ValueError("cache timing identity changed")
    return archive


@torch.no_grad()
def verify_sequence(paths, archives, graphs, norm, variant, config, device, count=16):
    ids = graphs.ids[:count]
    batch = collate_graphs([graphs.get(jid) for jid in ids], device)
    nodes, values, errors = None, None, []
    for r, (path, archive) in enumerate(zip(paths, archives)):
        model, checkpoint = load_stage(path, device)
        if checkpoint["norm"] != norm or archive.manifest["identity"][
            "checkpoint_sha256"
        ] != file_hash(path):
            raise ValueError("direct-chain checkpoint/cache mismatch")
        actual_variant = "direct" if r == 0 else variant
        nodes, values = prediction(
            model,
            batch,
            nodes if actual_variant != "raw_residual" else None,
            values,
            norm,
            actual_variant,
        )
        expected_nodes, expected_values = archive.batch(ids, graphs, device, True)
        torch.testing.assert_close(nodes, expected_nodes, **config["verification"])
        torch.testing.assert_close(values, expected_values, **config["verification"])
        errors.append(
            {
                "round": r,
                "node_max_abs_error": float((nodes - expected_nodes).abs().max()),
                "prediction_max_abs_error": float((values - expected_values).abs().max()),
            }
        )
    return {
        "rows": errors,
        "structures": ids,
        "depth": len(paths) - 1,
        "atol": config["verification"]["atol"],
        "rtol": config["verification"]["rtol"],
        "labels_used": False,
    }


def verify_chain(root, graphs, norm, variant, depth, config, device):
    paths = [
        root / ("direct" if r == 0 else variant) / f"round_{r:03d}/best.pt"
        for r in range(depth + 1)
    ]
    archives = [Archive(path.parent / "cache") for path in paths]
    result = verify_sequence(paths, archives, graphs, norm, variant, config, device)
    result.update(task=root.name, variant=variant)
    atomic_write(root / variant / f"chain_check_{depth:03d}.json", result)
    return result


def run_task(
    prepared, old_prepared, output, name, config, device="cuda", stop_variant=None, stop_round=2
):
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    task, graphs, norm, source_identity = task_source(prepared, old_prepared, output, name, config)
    root = Path(output) / name
    with task_lock(root / ".lock"):
        rows, references = [], []
        for variant in config["variants"]:
            parent = None if variant == "direct" else Archive(root / "direct/round_000/cache")
            branch_rows = (
                []
                if variant == "direct"
                else [{**rows[0], "variant": variant, "shared_round_zero": True}]
            )
            for r in range(0 if variant == "direct" else 1, stop_round + 1):
                seed = derived_seed(config["seed"], "icomformer", name, r, "direct")
                budget = (
                    None if variant == "direct" else references[r]["training"]["optimizer_steps"]
                )
                identity = {
                    **source_identity,
                    "task": name,
                    "variant": variant,
                    "round": r,
                    "stage_seed": seed,
                    "parent_archive": None if parent is None else parent.identity,
                    "budget_steps": budget,
                }
                stage = root / variant / f"round_{r:03d}"
                metrics = train_stage(
                    stage, config, task, graphs, parent, norm, variant, r, identity, device, budget
                )
                model, _ = load_stage(stage / "best.pt", device)
                cache = cache_model(
                    stage, model, graphs, parent, norm, variant, config, identity, device
                )
                val_ids = task["split"]["ids"]["val"]
                mae = sum(
                    abs(float(cache.get(jid)[1]) - task["labels"][jid]) for jid in val_ids
                ) / len(val_ids)
                if abs(mae - metrics["best_val_mae"]) > config["verification"]["atol"] + config[
                    "verification"
                ]["rtol"] * abs(metrics["best_val_mae"]):
                    raise ValueError("cached validation differs from selected checkpoint")
                row = {
                    "task": name,
                    "variant": variant,
                    "round": r,
                    "val_mae": mae,
                    "optimizer_steps": metrics["optimizer_steps"],
                    "parameters": metrics["parameters"],
                    "checkpoint_sha256": metrics["checkpoint_sha256"],
                    "cache_sha256": cache.identity,
                    "training_seconds": metrics["training_and_validation_seconds"],
                    "cache_seconds": read_json(stage / "cache_timing.json")["cache_seconds"],
                    "training_cost_scope": "independent process; GPU may be shared with other properties",
                }
                atomic_write(stage / "result.json", row)
                branch_rows.append(row)
                parent = cache
                verify_chain(root, graphs, norm, variant, r, config, device)
                if variant == "direct":
                    references.append(
                        {
                            "round": r,
                            "stage": str(stage.resolve()),
                            "training": metrics,
                            "checkpoint_sha256": metrics["checkpoint_sha256"],
                            "cache_sha256": cache.identity,
                        }
                    )
                atomic_write(
                    root / variant / "report.json",
                    {
                        "status": "complete" if r == 2 else "partial",
                        "rows": branch_rows,
                        "test_labels_used": False,
                        "protocol_identity": source_identity,
                    },
                )
            if variant == "direct":
                rows = branch_rows
                if stop_round == 2:
                    atomic_write(
                        root / "source.json",
                        {
                            "status": "complete",
                            "task": name,
                            "identity": source_identity,
                            "normalization": norm,
                            "references": references,
                            "direct_rows": rows,
                            "base_cache": str((root / "direct/round_000/cache").resolve()),
                            "graph_root": str((Path(prepared) / "graphs").resolve()),
                            "test_labels_used": False,
                        },
                    )
            if stop_variant == variant:
                break
    return root
