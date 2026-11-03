"""Real GPU/native/cumulative-cache acceptance in a separate diagnostic tree."""

import argparse
import copy
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch
from self_evolution.io import atomic_write, digest, derived_seed, file_hash, read_json
from self_evolution.training.stage import normalization
from icomformer_scaling.graphs import GraphStore, collate_graphs
from icomformer_scaling.pipeline import (
    cache_model,
    implementation_identity,
    validate_config,
    verify_sequence,
)
from icomformer_scaling.training import load_stage, train_stage


def native_parity(model, graphs, config):
    wrapped, native = copy.deepcopy(model).eval(), copy.deepcopy(model).eval()
    batch = collate_graphs([graphs.get(jid) for jid in graphs.ids[:16]], "cuda")
    actual, expected = wrapped(batch), native.forward_native(batch)
    torch.testing.assert_close(actual, expected, **config["verification"])
    actual.square().sum().backward()
    expected.square().sum().backward()
    for (_, a), (_, b) in zip(wrapped.named_parameters(), native.named_parameters()):
        if a.grad is None:
            if b.grad is not None:
                raise ValueError("native gradient presence mismatch")
        else:
            torch.testing.assert_close(a.grad, b.grad, **config["verification"])
    return {
        "structures": 16,
        "max_abs_output_error": float((actual - expected).abs().max()),
        "gradients": "passed",
        "mode": "eval forward and backward, same real graphs",
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/icomformer_scaling/seed123.json")
    )
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--old-prepared", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not torch.cuda.is_available():
        raise RuntimeError("acceptance requires a Slurm GPU allocation")
    config = read_json(args.config)
    validate_config(config)
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    graphs = GraphStore(args.prepared / "graphs")
    probe = read_json(args.work / "resource_probe.json")
    if (
        probe["status"] != "measured"
        or probe["graphs_sha256"] != graphs.identity
        or probe["model_hash"] != digest(config["model"])
        or probe["accepted"]["batch_size"] != config["training"]["batch_size"]
    ):
        raise ValueError("GPU resource proposal not adopted in the locked configuration")
    if len(graphs.ids) != config["expected_structures"]:
        raise ValueError("acceptance requires the complete invariant library")
    task = read_json(args.old_prepared / "tasks" / f"{config['tasks'][0]}.json")
    norm = normalization(task["labels"], task["split"]["ids"]["train"])
    diagnostic_task = copy.deepcopy(task)
    diagnostic_task["split"]["ids"]["train"] = task["split"]["ids"]["train"][:128]
    diagnostic_task["split"]["ids"]["val"] = task["split"]["ids"]["val"][:64]
    root = (
        args.work
        / "diagnostics"
        / ("gpu-" + digest(config)[:10] + "-" + implementation_identity()[:10])
    )
    model_paths, archives, records, base = {}, {}, [], None
    native_check = None
    for variant in config["variants"]:
        paths = [] if variant == "direct" else [model_paths["direct"][0]]
        stores = [] if variant == "direct" else [archives["direct"][0]]
        parent = None if variant == "direct" else base
        for r in range(0 if variant == "direct" else 1, 3):
            identity = {
                "diagnostic": True,
                "task": task["task"],
                "variant": variant,
                "round": r,
                "stage_seed": derived_seed(config["seed"], "icomformer", task["task"], r, "direct"),
                "study_hash": digest(config),
                "implementation_hash": implementation_identity(),
                "graphs_sha256": graphs.identity,
                "parent_archive": None if parent is None else parent.identity,
                "budget_steps": 4,
            }
            stage = root / variant / f"round_{r:03d}"
            metrics = train_stage(
                stage,
                config,
                diagnostic_task,
                graphs,
                parent,
                norm,
                variant,
                r,
                identity,
                "cuda",
                budget=4,
            )
            model, _ = load_stage(stage / "best.pt", "cuda")
            if r == 0:
                native_check = native_parity(model, graphs, config)
            cache = cache_model(
                stage, model, graphs, parent, norm, variant, config, identity, "cuda"
            )
            actual = sum(
                abs(float(cache.get(jid)[1]) - task["labels"][jid])
                for jid in diagnostic_task["split"]["ids"]["val"]
            ) / len(diagnostic_task["split"]["ids"]["val"])
            if abs(actual - metrics["best_val_mae"]) > config["verification"]["atol"] + config[
                "verification"
            ]["rtol"] * abs(metrics["best_val_mae"]):
                raise ValueError("GPU cached cumulative validation mismatch")
            if cache.manifest["structures"] != config["expected_structures"] or cache.manifest[
                "atoms"
            ] != sum(v["atoms"] for v in graphs.entries.values()):
                raise ValueError("GPU archive coverage mismatch")
            paths.append(stage / "best.pt")
            stores.append(cache)
            parent = cache
            if r == 0:
                base = cache
            records.append(
                {
                    "variant": variant,
                    "round": r,
                    "optimizer_steps": metrics["optimizer_steps"],
                    "structures": cache.manifest["structures"],
                    "atoms": cache.manifest["atoms"],
                    "width": cache.manifest["width"],
                    "cache_sha256": cache.identity,
                    "chain": verify_sequence(paths, stores, graphs, norm, variant, config, "cuda"),
                }
            )
            print("GPU_STAGE_ACCEPTED", variant, r, flush=True)
        model_paths[variant], archives[variant] = paths, stores
    result = {
        "status": "passed",
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "study_hash": digest(config),
        "implementation_hash": implementation_identity(),
        "graphs_sha256": graphs.identity,
        "resource_probe_sha256": file_hash(args.work / "resource_probe.json"),
        "batch_size": config["training"]["batch_size"],
        "native": native_check,
        "rows": records,
        "diagnostic_only": True,
        "test_labels_used": False,
    }
    atomic_write(args.work / "acceptance.json", result)
    print("GPU_ACCEPTANCE_PASSED", flush=True)


if __name__ == "__main__":
    main()
