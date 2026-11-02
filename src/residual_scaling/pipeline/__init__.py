"""Read-only baseline import and independent two-round residual branches."""

from pathlib import Path
import time

import torch

from self_evolution.cache import FeatureStore
from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, file_hash, read_json
from self_evolution.pipeline.chain import task_lock
from self_evolution.training.stage import batches, load_stage, synchronize

from residual_scaling.cache import Archive, publish
from residual_scaling.protocol import source_task
from residual_scaling.training import forward, train_stage


def archive_mae(archive, task):
    ids = task["split"]["ids"]["val"]
    return sum(abs(float(archive.get(jid)[1]) - task["labels"][jid]) for jid in ids) / len(ids)


def task_directory(output, task):
    return Path(output) / task


@torch.no_grad()
def cache_model(
    directory,
    model,
    checkpoint_path,
    graphs,
    norm,
    identity,
    base,
    device,
    parent=None,
    variant="direct",
    eta=1.0,
    legacy_features=None,
):
    directory = Path(directory)
    model.eval()
    before = {name: value.detach().clone() for name, value in model.state_dict().items()}
    checkpoint_hash = file_hash(checkpoint_path)

    def produce(ids):
        values = []
        for chunk in batches(ids, base["training"]["batch_size"]):
            raw = [graphs.get(jid) for jid in chunk]
            batch = collate_graphs(raw, device)
            if legacy_features is not None:
                nodes = torch.cat(
                    [legacy_features.get(jid, graphs.entries[jid]["atoms"]) for jid in chunk]
                ).to(device)
                predictions = norm["mean"] + norm["std"] * model.readout(nodes, batch)
            else:
                features, previous = parent.batch(
                    chunk, graphs, device, variant == "feature_residual"
                )
                nodes, predictions = forward(model, batch, features, previous, norm, eta)
            nodes, predictions = nodes.cpu(), predictions.cpu()
            offset = 0
            for i, graph in enumerate(raw):
                count = len(graph["atom_features"])
                values.append((nodes[offset : offset + count], predictions[i]))
                offset += count
        return values

    synchronize(device)
    start = time.perf_counter()
    archive = publish(
        directory / "cache",
        identity,
        graphs.ids,
        base["model"]["hidden"],
        produce,
        base["cache"]["shard_size"],
    )
    synchronize(device)
    if (
        file_hash(checkpoint_path) != checkpoint_hash
        or model.training
        or any(not torch.equal(before[name], value) for name, value in model.state_dict().items())
        or any(p.grad is not None for p in model.parameters())
    ):
        raise ValueError("model/checkpoint/BN changed during paired caching")
    path = directory / "cache_timing.json"
    if not path.exists():
        atomic_write(
            path, {"cache_seconds": time.perf_counter() - start, "cache_sha256": archive.identity}
        )
    elif read_json(path)["cache_sha256"] != archive.identity:
        raise ValueError("cache timer belongs to a different archive")
    return archive


def prepare_task(
    prepared, legacy, output, task_name, base, study, device="cuda", verify_shards=True
):
    torch.set_num_threads(base["threads"])
    torch.use_deterministic_algorithms(True)
    graphs = GraphStore(Path(prepared) / "graphs")
    task, norm, refs, identity = source_task(
        prepared, legacy, task_name, base, study, graphs, verify_shards
    )
    root = task_directory(output, task_name)
    root.mkdir(parents=True, exist_ok=True)
    with task_lock(root / ".import.lock"):
        source_path = root / "source.json"
        if source_path.exists():
            source = read_json(source_path)
            if source["identity"] != identity:
                raise ValueError("study import identity changed; use a new output root")
            if (
                source.get("status") == "complete"
                and (root / "direct/chain_check_002.json").is_file()
            ):
                return source
        atomic_write(root / "protocol.json", {"study": study, "base": base, "identity": identity})
        rows, previous = [], None
        for ref in refs:
            r = ref["round"]
            stage = Path(ref["stage"])
            target = root / "direct" / f"round_{r:03d}"
            model, checkpoint = load_stage(stage / "best.pt", device)
            if (
                checkpoint["norm"] != norm
                or checkpoint["identity"] != ref["training"]["identity"]
                or checkpoint["model_config"] != base["model"]
                or checkpoint["recursive"] != (r > 0)
            ):
                raise ValueError("imported checkpoint normalization mismatch")
            cache_identity = {
                **identity,
                "task": task_name,
                "variant": "direct",
                "round": r,
                "checkpoint_sha256": ref["checkpoint_sha256"],
                "normalization": norm,
                "prediction_parent": previous,
                "node_parent": previous,
                "legacy_features_sha256": ref["cache_sha256"],
                "prediction_role": "absolute",
            }
            archive = cache_model(
                target,
                model,
                stage / "best.pt",
                graphs,
                norm,
                cache_identity,
                base,
                device,
                legacy_features=FeatureStore(stage / "cache"),
            )
            mae = archive_mae(archive, task)
            expected = ref["training"]["best_val_mae"]
            if abs(mae - expected) > base["verification"]["atol"] + base["verification"][
                "rtol"
            ] * abs(expected):
                raise ValueError("imported cached validation differs from original checkpoint")
            row = {
                "task": task_name,
                "variant": "direct",
                "round": r,
                "val_mae": mae,
                "source_validation_mae": expected,
                "optimizer_steps": ref["training"]["optimizer_steps"],
                "parameters": ref["training"]["parameters"],
                "checkpoint_sha256": ref["checkpoint_sha256"],
                "cache_sha256": archive.identity,
                "training_seconds": ref["training"]["training_and_validation_seconds"],
                "training_cost_scope": "historical reference; no retraining",
                "cache_seconds": read_json(target / "cache_timing.json")["cache_seconds"],
            }
            atomic_write(target / "result.json", row)
            rows.append(row)
            previous = archive.identity
        source = {
            "identity": identity,
            "task": task_name,
            "normalization": norm,
            "references": refs,
            "direct_rows": rows,
            "base_cache": str((root / "direct/round_000/cache").resolve()),
            "graph_root": str((Path(prepared) / "graphs").resolve()),
            "test_labels_used": False,
            "status": "checking",
        }
        atomic_write(source_path, source)
    verify_chain(output, task_name, "direct", base, study, 2, device)
    source["status"] = "complete"
    atomic_write(source_path, source)
    return source


@torch.no_grad()
def verify_sequence(graphs, paths, archives, variant, norm, eta, tolerance, device, ids):
    if len(paths) != len(archives):
        raise ValueError("checkpoint/archive depth mismatch")
    batch = collate_graphs([graphs.get(jid) for jid in ids], device)
    nodes, predictions, rows = None, None, []
    for r, (path, archive) in enumerate(zip(paths, archives)):
        model, checkpoint = load_stage(path, device)
        if checkpoint["norm"] != norm:
            raise ValueError("chain normalization changed")
        if r == 0 or variant == "direct":
            nodes = model.encode_nodes(batch, nodes)
            predictions = norm["mean"] + norm["std"] * model.readout(nodes, batch)
        else:
            if checkpoint.get("prediction_role") != "residual_delta" or checkpoint["eta"] != eta:
                raise ValueError("residual checkpoint role/eta mismatch")
            nodes, predictions = forward(
                model,
                batch,
                nodes if variant == "feature_residual" else None,
                predictions,
                norm,
                eta,
            )
        expected_nodes, expected_predictions = archive.batch(ids, graphs, device, True)
        torch.testing.assert_close(nodes, expected_nodes, **tolerance)
        torch.testing.assert_close(predictions, expected_predictions, **tolerance)
        if archive.manifest["identity"]["checkpoint_sha256"] != file_hash(path):
            raise ValueError("direct chain checkpoint/cache mismatch")
        rows.append(
            {
                "round": r,
                "node_max_abs_error": float((nodes - expected_nodes).abs().max()),
                "prediction_max_abs_error": float((predictions - expected_predictions).abs().max()),
            }
        )
    return rows


def verify_chain(output, task_name, variant, base, study, depth, device="cuda", count=16):
    root = task_directory(output, task_name)
    source = read_json(root / "source.json")
    graphs = GraphStore(source["graph_root"])
    ids = graphs.ids[:count]
    paths, archives = [], []
    for r in range(depth + 1):
        direct = r == 0 or variant == "direct"
        paths.append(
            Path(source["references"][r]["stage"]) / "best.pt"
            if direct
            else root / variant / f"round_{r:03d}/best.pt"
        )
        archives.append(Archive(root / ("direct" if direct else variant) / f"round_{r:03d}/cache"))
    rows = verify_sequence(
        graphs,
        paths,
        archives,
        variant,
        source["normalization"],
        study["eta"],
        base["verification"],
        device,
        ids,
    )
    result = {
        "task": task_name,
        "variant": variant,
        "depth": depth,
        "structures": ids,
        "atol": base["verification"]["atol"],
        "rtol": base["verification"]["rtol"],
        "rows": rows,
        "labels_used": False,
    }
    directory = root / variant
    directory.mkdir(exist_ok=True)
    atomic_write(directory / f"chain_check_{depth:03d}.json", result)
    return result


def run_variant(
    prepared, legacy, output, task_name, variant, base, study, device="cuda", stop_round=2
):
    if variant not in ["raw_residual", "feature_residual"] or not 1 <= stop_round <= 2:
        raise ValueError("invalid residual branch or stop round")
    torch.set_num_threads(base["threads"])
    torch.use_deterministic_algorithms(True)
    source = prepare_task(
        prepared, legacy, output, task_name, base, study, device, verify_shards=False
    )
    graphs = GraphStore(Path(prepared) / "graphs")
    task = read_json(Path(prepared) / "tasks" / f"{task_name}.json")
    root = task_directory(output, task_name)
    branch = root / variant
    branch.mkdir(exist_ok=True)
    parent = Archive(source["base_cache"])
    norm = source["normalization"]
    if parent.identity != source["direct_rows"][0]["cache_sha256"]:
        raise ValueError("shared round-zero archive changed")
    rows = [{**source["direct_rows"][0], "variant": variant, "shared_round_zero": True}]
    with task_lock(branch / ".lock"):
        for r in range(1, stop_round + 1):
            reference = source["references"][r]["training"]
            budget, seed = reference["optimizer_steps"], reference["identity"]["stage_seed"]
            identity = {
                **source["identity"],
                "task": task_name,
                "variant": variant,
                "round": r,
                "parent_archive": parent.identity,
                "node_parent": parent.identity if variant == "feature_residual" else None,
                "budget_steps": budget,
                "stage_seed": seed,
                "normalization": norm,
                "eta": study["eta"],
            }
            stage = branch / f"round_{r:03d}"
            metrics = train_stage(
                stage,
                base,
                task,
                graphs,
                parent,
                norm,
                variant,
                study["eta"],
                budget,
                seed,
                identity,
                device,
            )
            model, checkpoint = load_stage(stage / "best.pt", device)
            cache_identity = {
                **identity,
                "checkpoint_sha256": metrics["checkpoint_sha256"],
                "prediction_parent": parent.identity,
                "prediction_role": "cumulative_residual_ensemble",
            }
            cache = cache_model(
                stage,
                model,
                stage / "best.pt",
                graphs,
                norm,
                cache_identity,
                base,
                device,
                parent=parent,
                variant=variant,
                eta=study["eta"],
            )
            mae = archive_mae(cache, task)
            if abs(mae - metrics["best_val_mae"]) > base["verification"]["atol"] + base[
                "verification"
            ]["rtol"] * abs(metrics["best_val_mae"]):
                raise ValueError("cumulative cached validation does not match checkpoint selection")
            row = {
                "task": task_name,
                "variant": variant,
                "round": r,
                "val_mae": mae,
                "optimizer_steps": metrics["optimizer_steps"],
                "parameters": metrics["parameters"],
                "checkpoint_sha256": metrics["checkpoint_sha256"],
                "cache_sha256": cache.identity,
                "training_seconds": metrics["training_and_validation_seconds"],
                "training_cost_scope": "new training; shared GPU if dispatched",
                "cache_seconds": read_json(stage / "cache_timing.json")["cache_seconds"],
            }
            atomic_write(stage / "result.json", row)
            rows.append(row)
            parent = cache
            verify_chain(output, task_name, variant, base, study, r, device)
            atomic_write(
                branch / "report.json",
                {
                    "task": task_name,
                    "variant": variant,
                    "rows": rows,
                    "status": "complete" if r == 2 else "partial",
                    "test_labels_used": False,
                    "protocol_identity": source["identity"],
                },
            )
    return rows
