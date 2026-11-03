"""Measure native float32 backward memory on the actual largest periodic graphs."""

import argparse
import gc
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch
from self_evolution.io import atomic_write, digest, file_hash, read_json
from icomformer_scaling.graphs import GraphStore, collate_graphs
from icomformer_scaling.model import IComformerStage, ModelConfig


def measure(ids, graphs, model_config, recursive):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(123)
    model = IComformerStage(ModelConfig(**model_config), recursive).cuda().train()
    batch = collate_graphs([graphs.get(jid) for jid in ids], "cuda")
    features = (
        torch.randn(len(batch["atom_features"]), model_config["hidden"], device="cuda")
        if recursive
        else None
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0)
    torch.cuda.synchronize()
    started = time.perf_counter()
    loss = model(batch, features).square().mean()
    loss.backward()
    if (
        not torch.isfinite(loss)
        or not torch.stack(
            [torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]
        ).all()
    ):
        raise FloatingPointError("non-finite native GPU probe")
    optimizer.step()
    torch.cuda.synchronize()
    return {
        "recursive": recursive,
        "structures": len(ids),
        "atoms": sum(graphs.entries[jid]["atoms"] for jid in ids),
        "edges": sum(graphs.entries[jid]["edges"] for jid in ids),
        "peak_torch_reserved_bytes": torch.cuda.max_memory_reserved(),
        "peak_torch_allocated_bytes": torch.cuda.max_memory_allocated(),
        "forward_backward_adam_seconds": time.perf_counter() - started,
        "ids": ids,
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/icomformer_scaling/seed123.json")
    )
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not torch.cuda.is_available():
        raise RuntimeError("real resource probe requires Slurm GPU")
    config = read_json(args.config)
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    graphs = GraphStore(args.prepared / "graphs")
    total = torch.cuda.get_device_properties(0).total_memory
    ordered = {
        name: sorted(graphs.ids, key=lambda jid: (-graphs.entries[jid][name], jid))
        for name in ["edges", "atoms"]
    }
    attempts, accepted, size = [], None, config["training"]["batch_size"]
    while size >= 2:
        rows, failed, seen = [], False, set()
        for name, ids in ordered.items():
            selected = ids[:size]
            key = tuple(sorted(selected))
            if key in seen:
                continue
            seen.add(key)
            for recursive in [False, True]:
                try:
                    row = measure(selected, graphs, config["model"], recursive)
                    row.update(selection="largest_" + name, status="measured")
                    rows.append(row)
                    print(
                        "MEASURED",
                        size,
                        name,
                        recursive,
                        row["peak_torch_reserved_bytes"],
                        flush=True,
                    )
                except torch.cuda.OutOfMemoryError:
                    rows.append(
                        {"selection": "largest_" + name, "recursive": recursive, "status": "oom"}
                    )
                    failed = True
                    print("OOM", size, name, recursive, flush=True)
                gc.collect()
                torch.cuda.empty_cache()
                if failed:
                    break
            if failed:
                break
        peak = max((row.get("peak_torch_reserved_bytes", 0) for row in rows), default=0)
        attempts.append({"batch_size": size, "rows": rows})
        if not failed and peak <= total * 0.90:
            accepted = {"batch_size": size, "peak_torch_reserved_bytes": peak, "rows": rows}
            break
        size //= 2
    if accepted is None:
        raise RuntimeError("no safe float32 native batch >=2; see probe stdout")
    result = {
        "status": "measured",
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "device": torch.cuda.get_device_name(),
        "device_memory_bytes": total,
        "dtype": "float32",
        "model_hash": digest(config["model"]),
        "graphs_sha256": graphs.identity,
        "probe_script_sha256": file_hash(Path(__file__)),
        "accepted": accepted,
        "attempts": attempts,
        "labels_used": False,
        "measurement_scope": "random model copies, largest edge-count and atom-count batches, native and projected inputs; not complete epoch throughput",
    }
    atomic_write(args.output, result)
    print("PROPOSED_BATCH_SIZE", accepted["batch_size"], flush=True)


if __name__ == "__main__":
    main()
