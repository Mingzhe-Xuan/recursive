"""Validate MatterSim-v1.0.0-1M native inference and full-backbone K=1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import torch
from ase.build import bulk
from mattersim.datasets.utils.build import build_dataloader
from mattersim.forcefield.potential import Potential, batch_to_dict

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.executor import run_segment_cycles
from recursive_backbones.common.freeze import (
    assert_frozen_unchanged,
    freeze_module,
    snapshot_frozen,
)
from recursive_backbones.mattersim import MatterSimM3GNetWrapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="mattersim-v1.0.0-1m")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--gamma-min", type=float, default=0.1)
    parser.add_argument("--gamma-max", type=float, default=10.0)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_checkpoint(argument: str) -> Path | None:
    supplied = Path(argument).expanduser()
    if supplied.is_file():
        return supplied.resolve()
    if argument.lower() in {"mattersim-v1.0.0-1m", "mattersim-v1.0.0-1m.pth"}:
        candidate = Path("~/.local/mattersim/pretrained_models/mattersim-v1.0.0-1M.pth").expanduser()
        return candidate.resolve() if candidate.is_file() else None
    return None


def tensor_list(value: torch.Tensor) -> list[Any]:
    return value.detach().cpu().tolist()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")

    potential = Potential.from_checkpoint(
        load_path=args.checkpoint,
        device=str(device),
        load_training_state=False,
    )
    model = freeze_module(potential.model)
    snapshot = snapshot_frozen(model)
    wrapper = MatterSimM3GNetWrapper(model)

    structure = bulk("Si", "diamond", a=5.43)
    dataloader = build_dataloader(
        [structure],
        only_inference=True,
        batch_size=1,
        cutoff=model.model_args["cutoff"],
        threebody_cutoff=model.model_args["threebody_cutoff"],
    )
    graph_batch = next(iter(dataloader))
    batch = batch_to_dict(graph_batch, device=str(device))
    aligner = IrrepNormAligner(
        epsilon=1e-8,
        gamma_min=args.gamma_min,
        gamma_max=args.gamma_max,
    )

    with torch.no_grad():
        native = model(batch)
        k0 = run_segment_cycles(
            wrapper,
            batch,
            start=0,
            stop=wrapper.num_blocks,
            repeats=0,
            aligner=aligner,
        )
        torch.testing.assert_close(k0.prediction, native, atol=args.atol, rtol=args.rtol)
        k1 = run_segment_cycles(
            wrapper,
            batch,
            start=0,
            stop=wrapper.num_blocks,
            repeats=1,
            aligner=aligner,
        )

    if not torch.isfinite(k1.prediction).all():
        raise AssertionError("K=1 produced NaN or Inf")
    assert_frozen_unchanged(model, snapshot)
    checkpoint = resolve_checkpoint(args.checkpoint)
    max_abs_error = float((k0.prediction - native).abs().max().item())
    gamma = {
        component: {key: tensor_list(value) for key, value in blocks.items()}
        for component, blocks in k1.traces[0].alignment.gamma.items()
    }
    report = {
        "status": "passed",
        "matter_sim_version": importlib.metadata.version("mattersim"),
        "torch_version": torch.__version__,
        "device": str(device),
        "device_name": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
        "checkpoint_argument": args.checkpoint,
        "checkpoint_path": str(checkpoint) if checkpoint else None,
        "checkpoint_sha256": sha256(checkpoint) if checkpoint else None,
        "model_args": model.model_args,
        "num_blocks": wrapper.num_blocks,
        "num_atoms": len(structure),
        "native_energy_ev": tensor_list(native),
        "k0_energy_ev": tensor_list(k0.prediction),
        "k0_max_abs_error": max_abs_error,
        "k0_atol": args.atol,
        "k0_rtol": args.rtol,
        "k1_energy_ev": tensor_list(k1.prediction),
        "k1_finite": True,
        "k1_gamma": gamma,
        "backbone_eval": not model.training,
        "backbone_unchanged": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
