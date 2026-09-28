"""Recursive wrapper for MatterSim's M3GNet backbone."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from importlib import import_module
from typing import Callable, Mapping

import torch
from torch import Tensor, nn
from torch.utils.checkpoint import checkpoint

from recursive_backbones.common.state import (
    DynamicState,
    IrrepBlock,
    StateComponent,
    StateSpec,
)

ScatterSum = Callable[..., Tensor]


@dataclass(frozen=True, slots=True)
class MatterSimGeometry:
    """Geometry and graph tensors that stay fixed across recursive cycles."""

    atomic_numbers: Tensor
    atom_batch: Tensor
    edge_batch: Tensor
    edge_attr_zero: Tensor
    edge_index: Tensor
    three_basis: Tensor
    three_body_indices: Tensor
    edge_length: Tensor
    num_bonds: Tensor
    num_triple_ij: Tensor
    num_atoms: Tensor
    num_structures: int


def _official_scatter_sum() -> ScatterSum:
    """Load MatterSim's own reduction to preserve K=0 numerical behavior."""

    module = import_module("mattersim.forcefield.m3gnet.modules.scatter")
    return module.scatter_sum


class MatterSimM3GNetWrapper:
    """Expose M3GNet ``MainBlock`` modules through the recursive protocol.

    MatterSim's current M3GNet atom and edge hidden features are invariant
    scalars. Each component is therefore one ``(ell=0, parity=+1)`` irrep
    type whose multiplicity equals the hidden width. The single scale shared
    by that packed block consequently covers every channel.
    """

    def __init__(self, model: nn.Module, *, scatter_sum: ScatterSum | None = None) -> None:
        required = (
            "atom_embedding",
            "edge_encoder",
            "final",
            "graph_conv",
            "normalizer",
            "one_hot_atoms",
            "rbf",
            "sbf",
        )
        missing = [name for name in required if not hasattr(model, name)]
        if missing:
            raise TypeError(f"model is missing M3GNet attributes: {missing}")
        self.model = model
        self.scatter_sum = scatter_sum if scatter_sum is not None else _official_scatter_sum()

    @property
    def num_blocks(self) -> int:
        return len(self.model.graph_conv)

    def encode_geometry(self, batch: Mapping[str, Tensor]) -> MatterSimGeometry:
        """Reproduce the official M3GNet forward preamble exactly."""

        pos = batch["atom_pos"]
        cell = batch["cell"]
        pbc_offsets = batch["pbc_offsets"].to(pos.dtype)
        edge_index = batch["edge_index"].long()
        three_body_indices = batch["three_body_indices"].long()
        atom_batch = batch["batch"]

        edge_batch = atom_batch[edge_index[0]]
        edge_vector = pos[edge_index[0]] - (
            pos[edge_index[1]]
            + torch.einsum("bi, bij->bj", pbc_offsets, cell[edge_batch])
        )
        edge_length_flat = torch.linalg.norm(edge_vector, dim=1)
        first = three_body_indices[:, 0].clone()
        second = three_body_indices[:, 1].clone()
        vij = edge_vector[first]
        vik = edge_vector[second]
        rij = edge_length_flat[first]
        rik = edge_length_flat[second]
        cos_jik = torch.sum(vij * vik, dim=1) / (rij * rik)
        cos_jik = torch.clamp(cos_jik, min=-1.0 + 1e-7, max=1.0 - 1e-7)
        triple_edge_length = rik.view(-1)
        edge_length = edge_length_flat.unsqueeze(-1)
        atomic_numbers = batch["atom_attr"].squeeze(1).long()

        edge_attr_zero = self.model.rbf(edge_length.view(-1))
        three_basis = self.model.sbf(triple_edge_length, torch.acos(cos_jik))
        return MatterSimGeometry(
            atomic_numbers=atomic_numbers,
            atom_batch=atom_batch,
            edge_batch=edge_batch,
            edge_attr_zero=edge_attr_zero,
            edge_index=edge_index,
            three_basis=three_basis,
            three_body_indices=three_body_indices,
            edge_length=edge_length,
            num_bonds=batch["num_bonds"],
            num_triple_ij=batch["num_triple_ij"],
            num_atoms=batch["num_atoms"],
            num_structures=cell.shape[0],
        )

    @staticmethod
    def _scalar_spec(name: str, width: int) -> StateSpec:
        return StateSpec(
            name=name,
            irreps=(IrrepBlock(ell=0, parity=1, multiplicity=width, start=0),),
        )

    def initial_state(
        self, batch: Mapping[str, Tensor], geometry: MatterSimGeometry
    ) -> DynamicState:
        del batch
        atom_values = self.model.atom_embedding(
            self.model.one_hot_atoms(geometry.atomic_numbers)
        )
        edge_values = self.model.edge_encoder(geometry.edge_attr_zero)
        return DynamicState(
            {
                "atom": StateComponent(
                    atom_values,
                    self._scalar_spec("atom", atom_values.shape[-1]),
                    geometry.atom_batch,
                ),
                "edge": StateComponent(
                    edge_values,
                    self._scalar_spec("edge", edge_values.shape[-1]),
                    geometry.edge_batch,
                ),
            }
        )

    def run_block(
        self, block_index: int, state: DynamicState, geometry: MatterSimGeometry
    ) -> DynamicState:
        atom = state.components["atom"]
        edge = state.components["edge"]
        conv = self.model.graph_conv[block_index]
        func = partial(
            conv,
            atom_attr=atom.values,
            edge_attr=edge.values,
            edge_attr_zero=geometry.edge_attr_zero,
            edge_index=geometry.edge_index,
            three_basis=geometry.three_basis,
            three_body_index=geometry.three_body_indices,
            edge_length=geometry.edge_length,
            num_edges=geometry.num_bonds,
            num_triple_ij=geometry.num_triple_ij,
            num_atoms=geometry.num_atoms,
        )
        if getattr(self.model, "gradient_checkpointing", False):
            atom_values, edge_values = checkpoint(func, use_reentrant=False)
        else:
            atom_values, edge_values = func()
        return DynamicState(
            {
                "atom": atom.with_values(atom_values),
                "edge": edge.with_values(edge_values),
            }
        )

    def readout(
        self,
        state: DynamicState,
        batch: Mapping[str, Tensor],
        geometry: MatterSimGeometry,
    ) -> Tensor:
        del batch
        energies_i = self.model.final(state.components["atom"].values).view(-1)
        energies_i = self.model.normalizer(energies_i, geometry.atomic_numbers)
        return self.scatter_sum(
            energies_i,
            geometry.atom_batch,
            dim=0,
            dim_size=geometry.num_structures,
        )

