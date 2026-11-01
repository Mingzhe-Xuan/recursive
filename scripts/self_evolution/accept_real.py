"""Label-free CUDA acceptance of the completed two-stage CGCNN pilot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch

from pilot_resources import audit_pilot

from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import atomic_write, code_revision, file_hash, read_json
from self_evolution.pipeline.chain import verify_chain
from self_evolution.training.stage import load_stage


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("real acceptance requires Slurm CUDA allocation")
    config = read_json(args.config)
    torch.set_num_threads(config["threads"])
    torch.use_deterministic_algorithms(True)
    root = args.output / "cgcnn/formation_energy_peratom/seed_123"
    chain = read_json(root / "chain_manifest.json")
    if len(chain["stages"]) < 2:
        raise ValueError("pilot must complete both stages and full-library caches")
    graphs = GraphStore(args.prepared / "graphs")
    ids = graphs.ids[:32]
    checkpoint_path = root / "round_000/best.pt"
    checkpoint_hash = file_hash(checkpoint_path)
    model, checkpoint = load_stage(checkpoint_path, "cuda")
    saved = {key: value.clone() for key, value in model.state_dict().items()}
    tolerance = config["verification"]
    batch = collate_graphs([graphs.get(jid) for jid in ids], "cuda")
    with torch.no_grad():
        official = model.forward_native(batch)
        wrapped = model(batch)
        single = torch.cat([model(collate_graphs([graphs.get(jid)], "cuda")) for jid in ids])
    torch.testing.assert_close(wrapped, official, **tolerance)
    torch.testing.assert_close(wrapped, single, **tolerance)
    if model.training or any(p.grad is not None for p in model.parameters()):
        raise ValueError("eval/gradient invariant failed")
    if any(not torch.equal(value, saved[key]) for key, value in model.state_dict().items()):
        raise ValueError("weights or buffers mutated")
    if file_hash(checkpoint_path) != checkpoint_hash:
        raise ValueError("checkpoint file changed")
    chain_result = verify_chain(root, graphs, config, 1, "cuda", count=32)
    result = {
        "status": "passed",
        "code_commit": code_revision(),
        "gpu": torch.cuda.get_device_name(),
        "torch_version": str(torch.__version__),
        "cuda": torch.version.cuda,
        "checkpoint_sha256": checkpoint_hash,
        "graphs_sha256": graphs.identity,
        "structures": ids,
        "tolerance": tolerance,
        "native_max_abs_error": (wrapped - official).abs().max().item(),
        "batch_max_abs_error": (wrapped - single).abs().max().item(),
        "chain": chain_result,
        "labels_read": False,
    }
    del model, saved, batch, official, wrapped, single
    resource_path = args.output / "pilot_resources.json"
    audit_pilot(root, args.prepared / "graphs", config, "cuda", resource_path)
    result["resource_report_sha256"] = file_hash(resource_path)
    atomic_write(args.output / "real_acceptance.json", result)
    print(result)


if __name__ == "__main__":
    main()
