"""Read-only short diagnostics on a copy of a CGCNN checkpoint; no training outputs changed."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch

from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, read_json
from self_evolution.training.stage import load_stage


def main(args):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot = args.checkpoint.read_bytes()
    snapshot_path = args.output / "isolated_checkpoint.pt"
    snapshot_path.write_bytes(snapshot)
    model, checkpoint = load_stage(snapshot_path, args.device)
    if checkpoint["recursive"]:
        raise ValueError("diagnostic expects a native round-zero checkpoint")
    initial = deepcopy(model.state_dict())
    config = read_json(args.config)
    store = GraphStore(args.prepared / "graphs")
    ids = random.Random(123).sample(store.ids, min(64, len(store.ids)))
    graphs = [store.get(jid) for jid in ids]
    batch = collate_graphs(graphs, args.device)
    lengths = torch.tensor([len(g["atom_features"]) for g in graphs], device=args.device)
    original_pool = model.native.pooling

    def segment_pool(self, nodes, crystal_indices):
        return torch.segment_reduce(nodes, "mean", lengths=lengths)

    def synchronize():
        if args.device == "cuda":
            torch.cuda.synchronize()

    def gradient_snapshot():
        model.eval()
        model.zero_grad(set_to_none=True)
        prediction = model(batch)
        prediction.square().mean().backward()
        return prediction.detach().clone(), {
            name: p.grad.detach().clone()
            for name, p in model.named_parameters()
            if p.grad is not None
        }

    reference, gradients = gradient_snapshot()
    result = {
        "status": "diagnostic",
        "source_snapshot_sha256": hashlib.sha256(snapshot).hexdigest(),
        "allocation_job": os.environ.get("SLURM_JOB_ID"),
        "step_id": os.environ.get("SLURM_STEP_ID"),
        "shared_gpu": args.shared_gpu,
        "device": args.device,
        "structures": len(ids),
        "atoms": len(batch["atom_features"]),
        "labels_read": False,
        "training_outputs_modified": False,
        "variants": {},
    }

    for name in ["native", "segment_candidate"]:
        model.load_state_dict(initial)
        model.native.pooling = (
            original_pool if name == "native" else types.MethodType(segment_pool, model.native)
        )
        try:
            prediction, candidate_gradients = gradient_snapshot()
            torch.testing.assert_close(prediction, reference, **config["verification"])
            for key in gradients:
                torch.testing.assert_close(
                    candidate_gradients[key], gradients[key], **config["verification"]
                )
            model.train()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.0)

            def step():
                optimizer.zero_grad(set_to_none=True)
                prediction = model(batch)
                loss = prediction.square().mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError("non-finite isolated diagnostic loss")
                loss.backward()
                if not torch.stack(
                    [torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]
                ).all():
                    raise FloatingPointError("non-finite isolated diagnostic gradient")
                optimizer.step()
                return loss.item()

            for _ in range(3):
                step()
            synchronize()
            start = time.perf_counter()
            for _ in range(15):
                step()
            synchronize()
            seconds = (time.perf_counter() - start) / 15
            with torch.profiler.profile(
                activities=[torch.profiler.ProfilerActivity.CPU]
            ) as profiler:
                for _ in range(3):
                    step()
                synchronize()
            table = profiler.key_averages().table(sort_by="self_cpu_time_total", row_limit=25)
            (args.output / f"{name}_operators.txt").write_text(table)
            result["variants"][name] = {
                "numerical_check": "passed",
                "step_seconds": seconds,
                "prediction_max_abs_error": (prediction - reference).abs().max().item(),
            }
            print(name, result["variants"][name], flush=True)
        except Exception as exc:
            result["variants"][name] = {
                "numerical_check": "rejected",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            print(name, "REJECTED", str(exc), flush=True)
    atomic_write(args.output / "diagnostic.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--shared-gpu", action="store_true")
    parsed = parser.parse_args()
    try:
        main(parsed)
    except Exception:
        parsed.output.mkdir(parents=True, exist_ok=True)
        atomic_write(
            parsed.output / "diagnostic.json",
            {
                "status": "diagnostic_failed",
                "traceback": traceback.format_exc(),
                "training_outputs_modified": False,
            },
        )
        traceback.print_exc()
