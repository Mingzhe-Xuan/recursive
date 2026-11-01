"""Label-free, fixed-batch resource measurements on copies of a completed pilot."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch

from self_evolution.cache import FeatureStore
from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import (
    atomic_write,
    checked_path,
    code_identity,
    code_revision,
    digest,
    file_hash,
    read_json,
)
from self_evolution.training.stage import load_stage


def synchronize(device):
    if torch.device(device).type == "cuda":
        torch.cuda.synchronize(device)


def measure_stage(root, round_index, graph_root, config, ids, device):
    cuda = torch.device(device).type == "cuda"
    synchronize(device)
    if cuda:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)
    stage = root / f"round_{round_index:03d}"
    checkpoint_path = stage / "best.pt"
    checkpoint_hash = file_hash(checkpoint_path)
    cache = FeatureStore(stage / "cache")
    graphs = GraphStore(graph_root)
    cached_ids = {jid for shard in cache.manifest["shards"] for jid in shard["ids"]}
    if cached_ids != set(graphs.ids):
        raise ValueError("pilot cache must cover the entire graph library")
    if cache.manifest["identity"]["checkpoint_sha256"] != checkpoint_hash:
        raise ValueError("pilot cache does not match its checkpoint")
    identity = cache.manifest["identity"]
    if (
        identity["graphs_sha256"] != graphs.identity
        or identity["config_hash"] != digest(config)
        or identity["round"] != round_index
        or cache.manifest["width"] != config["model"]["hidden"]
        or cache.manifest["dtype"] != "float32"
        or read_json(stage / "training.json")["checkpoint_sha256"] != checkpoint_hash
    ):
        raise ValueError("resource probe inputs do not match the completed protocol")
    checkpoint, _ = load_stage(checkpoint_path, device)
    if (checkpoint.projection is not None) != (round_index > 0):
        raise ValueError("pilot stage has an unexpected recursive input")
    started = time.perf_counter()
    selected = [graphs.get(jid) for jid in ids]
    graph_seconds = time.perf_counter() - started
    started = time.perf_counter()
    batch = collate_graphs(selected, device)
    synchronize(device)
    collate_seconds = time.perf_counter() - started
    features = None
    parent_seconds = transfer_seconds = None
    parent = None
    if round_index:
        parent = FeatureStore(root / f"round_{round_index - 1:03d}/cache")
        if identity["parent_cache_sha256"] != parent.identity:
            raise ValueError("resource probe parent cache does not match the chain")
        started = time.perf_counter()
        cpu_features = torch.cat(
            [parent.get(jid, len(graph["atom_features"])) for jid, graph in zip(ids, selected)]
        )
        parent_seconds = time.perf_counter() - started
        started = time.perf_counter()
        features = cpu_features.to(device)
        synchronize(device)
        transfer_seconds = time.perf_counter() - started
    checkpoint.train()
    optimizer = torch.optim.Adam(checkpoint.parameters(), lr=0.0)

    def step():
        optimizer.zero_grad(set_to_none=True)
        prediction = checkpoint(batch, features)
        loss = prediction.square().mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite resource-probe loss")
        loss.backward()
        if not torch.stack(
            [torch.isfinite(p.grad).all() for p in checkpoint.parameters() if p.grad is not None]
        ).all():
            raise FloatingPointError("non-finite resource-probe gradient")
        optimizer.step()
        return loss.item()

    for _ in range(2):
        step()
    synchronize(device)
    started = time.perf_counter()
    for _ in range(3):
        step()
    synchronize(device)
    step_seconds = (time.perf_counter() - started) / 3
    atoms = sum(sum(shard["atoms"]) for shard in cache.manifest["shards"])
    result = {
        "round": round_index,
        "checkpoint_sha256": checkpoint_hash,
        "cache_sha256": cache.identity,
        "cache_structures": len(cached_ids),
        "cache_atoms": atoms,
        "cache_shards": len(cache.manifest["shards"]),
        "cache_payload_bytes": atoms * cache.manifest["width"] * 4,
        "cache_shard_file_bytes": sum(
            checked_path(cache.root, shard["file"]).stat().st_size
            for shard in cache.manifest["shards"]
        ),
        "cache_stored_bytes": sum(p.stat().st_size for p in cache.root.iterdir() if p.is_file()),
        "batch_atoms": len(batch["atom_features"]),
        "graph_first_verified_read_seconds": graph_seconds,
        "collation_and_graph_device_transfer_seconds": collate_seconds,
        "parent_first_verified_read_and_concat_seconds": parent_seconds,
        "parent_device_transfer_seconds": transfer_seconds,
        "surrogate_step_seconds": step_seconds,
        "peak_torch_allocated_bytes": torch.cuda.max_memory_allocated(device) if cuda else None,
        "peak_torch_reserved_bytes": torch.cuda.max_memory_reserved(device) if cuda else None,
    }
    if file_hash(checkpoint_path) != checkpoint_hash:
        raise ValueError("resource probe changed an authoritative checkpoint")
    if file_hash(cache.root / "manifest.json") != cache.identity:
        raise ValueError("resource probe changed a cache manifest")
    if parent is not None and file_hash(parent.root / "manifest.json") != parent.identity:
        raise ValueError("resource probe changed a parent cache manifest")
    return result


def audit_pilot(root: Path, graph_root: Path, config: dict, device="cuda", output=None):
    cuda = torch.device(device).type == "cuda"
    if cuda and (not torch.cuda.is_available() or not os.environ.get("SLURM_JOB_ID")):
        raise RuntimeError("CUDA resource probe requires a Slurm allocation")
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    graphs = GraphStore(graph_root)
    count = min(config["training"]["batch_size"], len(graphs.ids))
    ids = random.Random(123).sample(graphs.ids, count)
    if count < 2:
        raise ValueError("resource probe requires at least two structures")
    for r in range(2):
        if not (root / f"round_{r:03d}/training.json").is_file():
            raise ValueError("resource probe requires two completed pilot stages")
    largest_ids = sorted(graphs.ids, key=lambda jid: (-graphs.entries[jid]["atoms"], jid))[:count]
    result = {
        "schema": 1,
        "status": "measured",
        "scope": "representative and largest atom-count batches on independent two-stage copies",
        "loss": "mean squared output (zero surrogate targets); no labels",
        "learning_rate": 0.0,
        "warmup_steps": 2,
        "timed_steps": 3,
        "os_page_cache_state": "unknown; reads include checksums/deserialization/concatenation",
        "peak_scope": "PyTorch allocator from model load through isolated surrogate steps",
        "labels_read": False,
        "authoritative_training_outputs_modified": False,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(device) if cuda else None,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "code_commit": code_revision(),
        "config_hash": digest(config),
        "core_code_hash": code_identity(),
        "device_memory_bytes": torch.cuda.get_device_properties(device).total_memory
        if cuda
        else None,
        "graphs_sha256": graphs.identity,
        "batch_ids": ids,
        "stages": [measure_stage(root, r, graph_root, config, ids, device) for r in range(2)],
        "largest_batch_ids": largest_ids,
    }
    try:
        result["largest_batch_stages"] = [
            measure_stage(root, r, graph_root, config, largest_ids, device) for r in range(2)
        ]
        result["largest_batch_status"] = "measured"
    except torch.cuda.OutOfMemoryError as exc:
        result["largest_batch_stages"] = []
        result["largest_batch_status"] = "out_of_memory"
        result["largest_batch_error"] = str(exc)
    if cuda:
        torch.cuda.empty_cache()
    atomic_write(output or root / "pilot_resources.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    parser.add_argument("--device", default="cuda", choices=["cpu", "cuda"])
    args = parser.parse_args()
    print(audit_pilot(args.root, args.graphs, read_json(args.config), args.device))
