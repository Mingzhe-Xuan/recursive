from __future__ import annotations

import contextlib
import os
from pathlib import Path
import time

import torch

from self_evolution.cache import FeatureStore, publish_cache
from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.training.stage import batches, load_stage, synchronize, train_stage


@contextlib.contextmanager
def task_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


@torch.no_grad()
def cache_stage(
    output: Path,
    graphs: GraphStore,
    parent: FeatureStore | None,
    config: dict,
    task: dict,
    round_index: int,
    device: str,
) -> FeatureStore:
    checkpoint_path = output / "best.pt"
    before = file_hash(checkpoint_path)
    model, checkpoint = load_stage(checkpoint_path, device)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    buffers = {name: value.clone() for name, value in model.named_buffers()}
    identity = {
        "backbone": "cgcnn",
        "task": task["task"],
        "seed": config["seed"],
        "round": round_index,
        "checkpoint_sha256": before,
        "graphs_sha256": graphs.identity,
        "parent_cache_sha256": None if parent is None else parent.identity,
        "split_hash": task["split"]["membership_hash"],
        "config_hash": digest(config),
        "code_commit": checkpoint["code_commit"],
        "code_hash": checkpoint["identity"]["code_hash"],
        "boundary": "post_last_convolution_pre_pooling",
    }

    def produce(ids):
        result = []
        for chunk in batches(ids, config["training"]["batch_size"]):
            values = [graphs.get(jid) for jid in chunk]
            batch = collate_graphs(values, device)
            previous = (
                None
                if parent is None
                else torch.cat(
                    [
                        parent.get(jid, len(graph["atom_features"]))
                        for jid, graph in zip(chunk, values)
                    ]
                ).to(device)
            )
            nodes = model.encode_nodes(batch, previous).cpu()
            result.extend(nodes[index.cpu()].clone() for index in batch["crystal_atom_indices"])
        return result

    synchronize(device)
    start = time.perf_counter()
    cache = publish_cache(
        output / "cache", identity, graphs.ids, produce, config["cache"]["shard_size"]
    )
    synchronize(device)
    if (
        model.training
        or any(p.grad is not None for p in model.parameters())
        or any(not torch.equal(value, buffers[name]) for name, value in model.named_buffers())
        or file_hash(checkpoint_path) != before
    ):
        raise ValueError("checkpoint/buffer state changed during feature caching")
    # Retain original construction time when a completed cache is resumed.
    timing_path = output / "cache_timing.json"
    if not timing_path.exists():
        atomic_write(
            timing_path,
            {"cache_seconds": time.perf_counter() - start, "cache_sha256": cache.identity},
        )
    elif read_json(timing_path)["cache_sha256"] != cache.identity:
        raise ValueError("cache timing belongs to different cache")
    return cache


@torch.no_grad()
def verify_chain(
    root: Path, graphs: GraphStore, config: dict, depth: int, device: str, count: int = 16
) -> dict:
    ids = graphs.ids[:count]
    batch = collate_graphs([graphs.get(jid) for jid in ids], device)
    nodes, errors, checkpoint_hashes = None, [], []
    synchronize(device)
    start = time.perf_counter()
    for r in range(depth + 1):
        output = root / f"round_{r:03d}"
        model, checkpoint = load_stage(output / "best.pt", device)
        checkpoint_hashes.append(file_hash(output / "best.pt"))
        nodes = model.encode_nodes(batch, nodes)
        cached = FeatureStore(output / "cache")
        if cached.manifest["identity"]["checkpoint_sha256"] != checkpoint_hashes[-1]:
            raise ValueError("cached features do not match historical checkpoint")
        expected = torch.cat([cached.get(jid) for jid in ids]).to(device)
        error = (nodes - expected).abs().max().item()
        torch.testing.assert_close(
            nodes,
            expected,
            atol=config["verification"]["atol"],
            rtol=config["verification"]["rtol"],
        )
        direct = model.readout(nodes, batch)
        restored = model.readout(expected, batch)
        torch.testing.assert_close(
            direct,
            restored,
            atol=config["verification"]["atol"],
            rtol=config["verification"]["rtol"],
        )
        errors.append(error)
    synchronize(device)
    result = {
        "structures": ids,
        "depth": depth,
        "node_max_abs_errors": errors,
        "checkpoint_sha256": checkpoint_hashes,
        "verification_wall_seconds_including_load": time.perf_counter() - start,
        "atol": config["verification"]["atol"],
        "rtol": config["verification"]["rtol"],
    }
    atomic_write(root / "chain_verification.json", result)
    return result


@torch.no_grad()
def benchmark_chain(root: Path, graphs: GraphStore, config: dict, device: str) -> dict:
    """Time full deployment forwards separately from feature-cache assisted forwards."""
    ids = graphs.ids[: config["training"]["batch_size"]]
    started = time.perf_counter()
    batch = collate_graphs([graphs.get(jid) for jid in ids], device)
    synchronize(device)
    graph_load = time.perf_counter() - started
    models = [
        load_stage(root / f"round_{r:03d}/best.pt", device)[0]
        for r in range(config["max_round"] + 1)
    ]
    rows = []
    for depth, final_model in enumerate(models):

        def direct():
            nodes = None
            for stage in models[: depth + 1]:
                nodes = stage.encode_nodes(batch, nodes)
            return final_model.readout(nodes, batch)

        previous = None if depth == 0 else FeatureStore(root / f"round_{depth - 1:03d}/cache")
        features = (
            None if previous is None else torch.cat([previous.get(jid) for jid in ids]).to(device)
        )

        def cached():
            return final_model(batch, features)

        record = {"round": depth, "deployment_stages": depth + 1}
        for name, forward in [("full_chain", direct), ("cached_last_stage", cached)]:
            for _ in range(2):
                forward()
            synchronize(device)
            started = time.perf_counter()
            for _ in range(5):
                forward()
            synchronize(device)
            record[name + "_seconds_per_batch"] = (time.perf_counter() - started) / 5
        rows.append(record)
    result = {
        "device": str(device),
        "gpu": torch.cuda.get_device_name(device)
        if (torch.device(device).type == "cuda")
        else None,
        "torch_version": str(torch.__version__),
        "structures": len(ids),
        "warmup": 2,
        "repeats": 5,
        "geometry_cache_load_seconds": graph_load,
        "cold_structure_graph_build": "reported separately in preparation audit; not included here",
        "rows": rows,
    }
    atomic_write(root / "benchmark.json", result)
    return result


def run_task(
    prepared: Path,
    run: Path,
    task_name: str,
    config: dict,
    device: str = "cuda",
    stop_round: int | None = None,
    controls: bool = True,
):
    if config["backbone"] != "cgcnn" or config["seed"] != 123:
        raise ValueError("this run protocol is CGCNN seed 123")
    if (
        config["initialization"] != "independent_random"
        or config["training"]["optimizer"] != "Adam"
        or config["training"]["scheduler"] != "constant"
        or config["training"]["loss"] != "normalized_mse"
        or config["cache"]["dtype"] != "float32"
    ):
        raise ValueError("unsupported protocol option")
    if torch.device(device).type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; refusing silent CPU fallback")
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    task = read_json(prepared / "tasks" / f"{task_name}.json")
    if task["status"] != "ready":
        raise ValueError(f"task not ready: {task_name}")
    root = run / "cgcnn" / task_name / f"seed_{config['seed']}"
    graphs = GraphStore(prepared / "graphs")
    if not task.get("dataset_sha256") or task["dataset_sha256"] != graphs.manifest.get(
        "identity", {}
    ).get("dataset_sha256"):
        raise ValueError("task snapshot does not match graph snapshot")
    max_round = config["max_round"] if stop_round is None else stop_round
    if not 0 <= max_round <= config["max_round"]:
        raise ValueError("invalid stop_round")
    with task_lock(root / ".lock"):
        protocol = root / "protocol.json"
        if protocol.exists() and read_json(protocol) != config:
            raise ValueError("immutable protocol changed; choose a separate run directory")
        atomic_write(protocol, config)
        parent, total_steps, chain = None, 0, []
        for r in range(max_round + 1):
            output = root / f"round_{r:03d}"
            metrics = train_stage(output, config, task, graphs, parent, r, "evolution", device)
            total_steps += metrics["optimizer_steps"]
            parent = cache_stage(output, graphs, parent, config, task, r, device)
            chain.append(
                {
                    "round": r,
                    "checkpoint_sha256": metrics["checkpoint_sha256"],
                    "cache_sha256": parent.identity,
                    "cumulative_steps": total_steps,
                }
            )
            verify_chain(root, graphs, config, r, device)
            atomic_write(
                root / "chain_manifest.json",
                {
                    "task": task_name,
                    "seed": config["seed"],
                    "config_hash": digest(config),
                    "target_max_round": config["max_round"],
                    "stages": chain,
                    "status": "complete" if r == config["max_round"] else "partial",
                },
            )
            if controls and r > 0:
                train_stage(
                    root / "controls" / "original" / f"round_{r:03d}",
                    config,
                    task,
                    graphs,
                    None,
                    r,
                    "original",
                    device,
                )
                train_stage(
                    root / "controls" / "cumulative" / f"round_{r:03d}",
                    config,
                    task,
                    graphs,
                    None,
                    r,
                    "cumulative",
                    device,
                    target_steps=total_steps,
                )
        return chain
