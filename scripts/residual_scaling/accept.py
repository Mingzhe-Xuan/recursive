"""Real-data GPU diagnostic in a separate directory, never a production result."""

import argparse
import copy
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch

from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.training.stage import load_stage
from residual_scaling.cache import Archive
from residual_scaling.pipeline import archive_mae, cache_model, verify_sequence
from residual_scaling.protocol import implementation_identity, validate_config
from residual_scaling.training import forward, train_stage


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/residual_scaling/seed123.json"))
    p.add_argument(
        "--base-config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    p.add_argument("--prepared", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not torch.cuda.is_available():
        raise RuntimeError("real acceptance requires a Slurm GPU allocation")
    base, study = read_json(args.base_config), read_json(args.config)
    validate_config(study, base)
    torch.set_num_threads(base["threads"])
    torch.use_deterministic_algorithms(True)
    graphs = GraphStore(args.prepared / "graphs")
    name = study["tasks"][0]
    source = read_json(args.output / name / "source.json")
    if source["status"] != "complete":
        raise ValueError("baseline import not complete")
    task = copy.deepcopy(read_json(args.prepared / "tasks" / f"{name}.json"))
    task["split"]["ids"]["train"] = task["split"]["ids"]["train"][:128]
    task["split"]["ids"]["val"] = task["split"]["ids"]["val"][:64]
    norm = source["normalization"]
    root = args.output / "diagnostics/gpu"
    evidence = []
    for variant in ["raw_residual", "feature_residual"]:
        parent = Archive(source["base_cache"])
        paths = [Path(source["references"][0]["stage"]) / "best.pt"]
        archives = [parent]
        for r in [1, 2]:
            identity = {
                **source["identity"],
                "diagnostic": True,
                "round": r,
                "variant": variant,
                "parent": parent.identity,
                "budget": 4,
            }
            stage = root / variant / f"round_{r:03d}"
            result = train_stage(
                stage,
                base,
                task,
                graphs,
                parent,
                norm,
                variant,
                study["eta"],
                4,
                source["references"][r]["training"]["identity"]["stage_seed"],
                identity,
                "cuda",
            )
            model, _ = load_stage(stage / "best.pt", "cuda")
            cache_identity = {
                **identity,
                "checkpoint_sha256": result["checkpoint_sha256"],
                "normalization": norm,
                "prediction_parent": parent.identity,
            }
            archive = cache_model(
                stage,
                model,
                stage / "best.pt",
                graphs,
                norm,
                cache_identity,
                base,
                "cuda",
                parent=parent,
                variant=variant,
                eta=study["eta"],
            )
            archive.verify_all()
            actual = archive_mae(archive, task)
            expected = result["best_val_mae"]
            if abs(actual - expected) > base["verification"]["atol"] + base["verification"][
                "rtol"
            ] * abs(expected):
                raise ValueError("GPU diagnostic cached ensemble selection mismatch")
            paths.append(stage / "best.pt")
            archives.append(archive)
            parent = archive
        chain = verify_sequence(
            graphs,
            paths,
            archives,
            variant,
            norm,
            study["eta"],
            base["verification"],
            "cuda",
            graphs.ids[:16],
        )
        # Surrogate loss measures backward memory on the largest structures without labels.
        largest = sorted(graphs.ids, key=lambda jid: (-graphs.entries[jid]["atoms"], jid))[
            : base["training"]["batch_size"]
        ]
        model, _ = load_stage(paths[-1], "cuda")
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        batch = collate_graphs([graphs.get(jid) for jid in largest], "cuda")
        nodes, previous = archives[-2].batch(largest, graphs, "cuda", variant == "feature_residual")
        _, prediction = forward(model, batch, nodes, previous, norm, study["eta"])
        loss = (prediction / norm["std"]).square().mean()
        loss.backward()
        optimizer.step()
        torch.cuda.synchronize()
        evidence.append(
            {
                "variant": variant,
                "chain": chain,
                "full_cache_structures": len(graphs.ids),
                "largest_atoms": sum(graphs.entries[jid]["atoms"] for jid in largest),
                "peak_torch_reserved_bytes": torch.cuda.max_memory_reserved(),
            }
        )
        del optimizer, model, batch, nodes, previous, prediction, loss
        torch.cuda.empty_cache()
    result = {
        "status": "passed",
        "study_hash": digest(study),
        "base_hash": digest(base),
        "implementation_hash": implementation_identity(),
        "graphs_sha256": graphs.identity,
        "device_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "diagnostic_only": True,
        "budget_steps_per_stage": 4,
        "test_labels_used": False,
        "rows": evidence,
        "source_sha256": file_hash(args.output / name / "source.json"),
    }
    atomic_write(args.output / "acceptance.json", result)
    print(result, flush=True)


if __name__ == "__main__":
    main()
