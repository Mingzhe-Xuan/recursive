"""Recursive execution controller for DeePMD-kit 2024Q1 DPA-2 repformers."""

from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module
from typing import Any, Callable, Iterator

import torch
from torch import Tensor

from adapters.norm import AlignmentDiagnostics, IrrepNormAligner
from recursive_backbones.common.state import (
    DynamicState,
    IrrepBlock,
    StateComponent,
    StateSpec,
)

EnvironmentBuilder = Callable[..., tuple[Tensor, Tensor, Tensor]]


def _official_environment(*args: Any, **kwargs: Any) -> tuple[Tensor, Tensor, Tensor]:
    module = import_module("deepmd.pt.model.descriptor.env_mat")
    return module.prod_env_mat(*args, **kwargs)


class DPA2RepformerRecursor:
    """Insert K complete repformer repeats into the native DPA-2 model path."""

    def __init__(
        self,
        repformers: Any,
        *,
        repeats: int,
        aligner: IrrepNormAligner,
        environment_builder: EnvironmentBuilder | None = None,
    ) -> None:
        if repeats < 0:
            raise ValueError("repeats must be non-negative")
        required = (
            "act",
            "dim_emb",
            "direct_dist",
            "emask",
            "env_protection",
            "g1_dim",
            "g2_embd",
            "layers",
            "mean",
            "rcut",
            "rcut_smth",
            "stddev",
        )
        missing = [name for name in required if not hasattr(repformers, name)]
        if missing:
            raise TypeError(f"repformer is missing 2024Q1 attributes: {missing}")
        if not repformers.layers:
            raise ValueError("repformer must contain at least one layer")
        self.repformers = repformers
        self.repeats = repeats
        self.aligner = aligner
        self.environment_builder = environment_builder or _official_environment
        self.last_diagnostics: tuple[AlignmentDiagnostics, ...] = ()

    @staticmethod
    def _state(g1: Tensor, g2: Tensor, h2: Tensor, mask: Tensor) -> DynamicState:
        nframes, nloc, ng1 = g1.shape
        _, _, nnei, ng2 = g2.shape
        atom_batch = torch.arange(nframes, device=g1.device).repeat_interleave(nloc)
        pair_batch = torch.arange(nframes, device=g1.device).repeat_interleave(nloc * nnei)
        atom_spec = StateSpec(
            "g1", (IrrepBlock(ell=0, parity=1, multiplicity=ng1, start=0),)
        )
        pair_spec = StateSpec(
            "g2", (IrrepBlock(ell=0, parity=1, multiplicity=ng2, start=0),)
        )
        vector_spec = StateSpec(
            "h2", (IrrepBlock(ell=1, parity=-1, multiplicity=1, start=0),)
        )
        pair_mask = mask.reshape(-1)
        return DynamicState(
            {
                "g1": StateComponent(g1.reshape(-1, ng1), atom_spec, atom_batch),
                "g2": StateComponent(
                    g2.reshape(-1, ng2), pair_spec, pair_batch, pair_mask
                ),
                "h2": StateComponent(
                    h2.reshape(-1, 3), vector_spec, pair_batch, pair_mask
                ),
            }
        )

    @staticmethod
    def _tensors(
        state: DynamicState, shapes: tuple[torch.Size, torch.Size, torch.Size]
    ) -> tuple[Tensor, Tensor, Tensor]:
        return (
            state.components["g1"].values.reshape(shapes[0]),
            state.components["g2"].values.reshape(shapes[1]),
            state.components["h2"].values.reshape(shapes[2]),
        )

    def _run_layers(
        self,
        g1: Tensor,
        g2: Tensor,
        h2: Tensor,
        mapping: Tensor,
        nlist: Tensor,
        nlist_mask: Tensor,
        sw: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        for layer in self.repformers.layers:
            g1_ext = torch.gather(g1, 1, mapping)
            g1, g2, h2 = layer.forward(g1_ext, g2, h2, nlist, nlist_mask, sw)
        return g1, g2, h2

    def forward(
        self,
        nlist: Tensor,
        extended_coord: Tensor,
        extended_atype: Tensor,
        extended_atype_embd: Tensor | None = None,
        mapping: Tensor | None = None,
    ):
        if mapping is None or extended_atype_embd is None:
            raise ValueError("DPA-2 repformer recursion requires mapping and type embeddings")
        base = self.repformers
        nframes, nloc, _ = nlist.shape
        nall = extended_coord.view(nframes, -1).shape[1] // 3
        atype = extended_atype[:, :nloc]
        exclude_mask = base.emask(nlist, extended_atype)
        nlist = torch.where(exclude_mask != 0, nlist, -1)
        dmatrix, diff, sw = self.environment_builder(
            extended_coord,
            nlist,
            atype,
            base.mean,
            base.stddev,
            base.rcut,
            base.rcut_smth,
            protection=base.env_protection,
        )
        nlist_mask = nlist != -1
        sw = torch.squeeze(sw, -1).masked_fill(~nlist_mask, 0.0)
        atype_embd = extended_atype_embd[:, :nloc, :]
        if list(atype_embd.shape) != [nframes, nloc, base.g1_dim]:
            raise ValueError("type embedding shape does not match repformer g1_dim")
        g1 = base.act(atype_embd)
        if not base.direct_dist:
            g2, h2 = torch.split(dmatrix, [1, 3], dim=-1)
        else:
            g2, h2 = torch.linalg.norm(diff, dim=-1, keepdim=True), diff
            g2 = g2 / base.rcut
            h2 = h2 / base.rcut
        g2 = base.act(base.g2_embd(g2))
        nlist = nlist.masked_fill(~nlist_mask, 0)
        mapping_index = (
            mapping.view(nframes, nall).unsqueeze(-1).expand(-1, -1, base.g1_dim)
        )

        reference = self._state(g1, g2, h2, nlist_mask)
        shapes = (g1.shape, g2.shape, h2.shape)
        g1, g2, h2 = self._run_layers(
            g1, g2, h2, mapping_index, nlist, nlist_mask, sw
        )
        diagnostics: list[AlignmentDiagnostics] = []
        for _ in range(self.repeats):
            current = self._state(g1, g2, h2, nlist_mask)
            aligned, detail = self.aligner(current, reference)
            diagnostics.append(detail)
            g1, g2, h2 = self._tensors(aligned, shapes)
            g1, g2, h2 = self._run_layers(
                g1, g2, h2, mapping_index, nlist, nlist_mask, sw
            )
        self.last_diagnostics = tuple(diagnostics)

        last_layer = self.repformers.layers[-1]
        h2g2 = last_layer._cal_h2g2(g2, h2, nlist_mask, sw)
        rot_mat = torch.permute(h2g2, (0, 1, 3, 2))
        return g1, g2, h2, rot_mat.view(-1, nloc, base.dim_emb, 3), sw

    @contextmanager
    def installed(self) -> Iterator[DPA2RepformerRecursor]:
        """Install the recursive forward for one scoped native-model call."""

        original_forward = self.repformers.forward
        self.repformers.forward = self.forward
        try:
            yield self
        finally:
            self.repformers.forward = original_forward

