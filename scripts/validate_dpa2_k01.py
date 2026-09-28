"""Validate OpenLAM DPA-2 native inference and full-Repformer K=1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import deepmd
import torch
from deepmd.pt.infer.inference import Tester

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.freeze import (
    assert_frozen_unchanged,
    freeze_module,
    snapshot_frozen,
)
from recursive_backbones.dpa2 import DPA2RepformerRecursor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--head", default="Domains_SSE-PBE")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--rtol", type=float, default=1e-8)
    parser.add_argument("--gamma-min", type=float, default=0.1)
    parser.add_argument("--gamma-max", type=float, default=10.0)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_list(value: torch.Tensor) -> list[Any]:
    return value.detach().cpu().tolist()


def predict(
    model: torch.nn.Module,
    coord: torch.Tensor,
    atype: torch.Tensor,
    box: torch.Tensor,
) -> dict[str, torch.Tensor]:
    # DeePMD constructs coordinate derivatives internally to return forces; no no_grad here.
    output = model(coord.clone(), atype, box.clone())
    return {name: value.detach() for name, value in output.items() if value is not None}


def main() -> None:
    args = parse_args()
    checkpoint = args.checkpoint.resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    if not torch.cuda.is_available():
        raise RuntimeError("OpenLAM validation requires a Slurm CUDA allocation")

    tester = Tester(str(checkpoint), head=args.head)
    model = freeze_module(tester.model)
    descriptor = model.atomic_model.descriptor
    repformers = descriptor.repformers
    if not hasattr(repformers.layers[-1], "_cal_h2g2"):
        raise RuntimeError("expected the DeePMD-kit 2024Q1 Repformer ABI (_cal_h2g2)")

    device = next(model.parameters()).device
    type_map = model.get_type_map()
    chosen = [name for name in ("Li", "S") if name in type_map]
    if len(chosen) < 2:
        chosen = type_map[:2]
    if len(chosen) < 2:
        raise RuntimeError("checkpoint type map must contain at least two species")
    atype = torch.tensor([[type_map.index(name) for name in chosen]], device=device)
    coord = torch.tensor(
        [[[0.0, 0.0, 0.0], [2.5, 0.0, 0.0]]],
        dtype=torch.float64,
        device=device,
    )
    box = torch.tensor(
        [[12.0, 0.0, 0.0, 0.0, 12.0, 0.0, 0.0, 0.0, 12.0]],
        dtype=torch.float64,
        device=device,
    )
    snapshot = snapshot_frozen(model)
    native = predict(model, coord, atype, box)
    aligner = IrrepNormAligner(
        epsilon=1e-12,
        gamma_min=args.gamma_min,
        gamma_max=args.gamma_max,
    )

    k0_controller = DPA2RepformerRecursor(repformers, repeats=0, aligner=aligner)
    with k0_controller.installed():
        k0 = predict(model, coord, atype, box)
    for name in ("energy", "force"):
        torch.testing.assert_close(k0[name], native[name], atol=args.atol, rtol=args.rtol)

    k1_controller = DPA2RepformerRecursor(repformers, repeats=1, aligner=aligner)
    with k1_controller.installed():
        k1 = predict(model, coord, atype, box)
    for name in ("energy", "force"):
        if not torch.isfinite(k1[name]).all():
            raise AssertionError(f"K=1 {name} contains NaN or Inf")
    assert_frozen_unchanged(model, snapshot)

    gamma = {
        component: {key: tensor_list(value) for key, value in blocks.items()}
        for component, blocks in k1_controller.last_diagnostics[0].gamma.items()
    }
    report = {
        "status": "passed",
        "deepmd_version": str(deepmd.__version__),
        "required_deepmd_ref": "2024Q1",
        "torch_version": str(torch.__version__),
        "device": str(device),
        "device_name": torch.cuda.get_device_name(device),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
        "checkpoint_size_bytes": checkpoint.stat().st_size,
        "head": args.head,
        "type_map": type_map,
        "sample_species": chosen,
        "native_energy": tensor_list(native["energy"]),
        "k0_energy": tensor_list(k0["energy"]),
        "k0_energy_max_abs_error": float((k0["energy"] - native["energy"]).abs().max()),
        "k0_force_max_abs_error": float((k0["force"] - native["force"]).abs().max()),
        "k0_atol": args.atol,
        "k0_rtol": args.rtol,
        "k1_energy": tensor_list(k1["energy"]),
        "k1_force_finite": True,
        "k1_gamma": gamma,
        "backbone_eval": not model.training,
        "backbone_unchanged": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
