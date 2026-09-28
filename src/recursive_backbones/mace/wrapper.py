"""Recursive wrapper for the scalar MACE-MP-0 small backbone."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Mapping

import torch
from torch import Tensor, nn

from recursive_backbones.common.state import (
    DynamicState,
    IrrepBlock,
    StateComponent,
    StateSpec,
)

PrepareGraph = Callable[..., Any]
ScatterSum = Callable[..., Tensor]


def _official_prepare_graph(*args: Any, **kwargs: Any) -> Any:
    module = import_module("mace.modules.utils")
    return module.prepare_graph(*args, **kwargs)


def _official_scatter_sum(*args: Any, **kwargs: Any) -> Tensor:
    module = import_module("mace.tools.scatter")
    return module.scatter_sum(*args, **kwargs)


@dataclass(slots=True)
class MACEContext:
    """Fixed graph tensors plus the per-block feature history needed by readouts."""

    node_attrs: Tensor
    batch: Tensor
    edge_index: Tensor
    edge_attrs: Tensor
    edge_feats: Tensor
    cutoff: Tensor | None
    num_graphs: int
    num_atoms_arange: Tensor
    node_heads: Tensor
    lammps_class: Any
    lammps_natoms: Any
    baseline_energy: Tensor
    pair_node_energy: Tensor
    features_by_block: list[Tensor | None]


class MACEMP0SmallWrapper:
    """Expose each interaction/product pair of scalar MACE-MP-0 small.

    The released small checkpoint is the L=0 model, so its node state at every
    interaction boundary is a packed collection of even scalars. Models with
    non-scalar hidden irreps must use an explicit e3nn-irrep wrapper and are
    rejected if a block changes the scalar state width.
    """

    def __init__(
        self,
        model: nn.Module,
        *,
        prepare_graph: PrepareGraph | None = None,
        scatter_sum: ScatterSum | None = None,
    ) -> None:
        required = (
            "atomic_energies_fn",
            "interactions",
            "node_embedding",
            "products",
            "radial_embedding",
            "readouts",
            "scale_shift",
            "spherical_harmonics",
        )
        missing = [name for name in required if not hasattr(model, name)]
        if missing:
            raise TypeError(f"model is missing ScaleShiftMACE attributes: {missing}")
        if len(model.interactions) != len(model.products):
            raise ValueError("MACE interaction/product counts differ")
        self.model = model
        self.prepare_graph = prepare_graph or _official_prepare_graph
        self.scatter_sum = scatter_sum or _official_scatter_sum

    @property
    def num_blocks(self) -> int:
        return len(self.model.interactions)

    @staticmethod
    def _state(values: Tensor, batch: Tensor) -> DynamicState:
        spec = StateSpec(
            "node",
            (IrrepBlock(ell=0, parity=1, multiplicity=values.shape[-1], start=0),),
        )
        return DynamicState({"node": StateComponent(values, spec, batch=batch)})

    def encode_geometry(self, data: Mapping[str, Tensor]) -> MACEContext:
        ctx = self.prepare_graph(
            data,
            compute_virials=False,
            compute_stress=False,
            compute_displacement=False,
            lammps_mliap=False,
        )
        if ctx.is_lammps:
            raise NotImplementedError("LAMMPS MACE recursion is outside this wrapper")
        num_atoms_arange = ctx.num_atoms_arange.to(torch.int64)
        node_heads = ctx.node_heads.to(torch.int64)
        node_e0 = self.model.atomic_energies_fn(data["node_attrs"])[
            num_atoms_arange, node_heads
        ]
        baseline_energy = self.scatter_sum(
            src=node_e0,
            index=data["batch"],
            dim=0,
            dim_size=ctx.num_graphs,
        ).to(ctx.vectors.dtype)
        edge_attrs = self.model.spherical_harmonics(ctx.vectors)
        edge_feats, cutoff = self.model.radial_embedding(
            ctx.lengths,
            data["node_attrs"],
            data["edge_index"],
            self.model.atomic_numbers,
        )
        if hasattr(self.model, "pair_repulsion"):
            pair_node_energy = self.model.pair_repulsion_fn(
                ctx.lengths,
                data["node_attrs"],
                data["edge_index"],
                self.model.atomic_numbers,
            )
        else:
            pair_node_energy = torch.zeros_like(node_e0)

        if hasattr(self.model, "joint_embedding"):
            raise NotImplementedError(
                "MACE models with joint embeddings need an audited baseline path"
            )
        return MACEContext(
            node_attrs=data["node_attrs"],
            batch=data["batch"],
            edge_index=data["edge_index"],
            edge_attrs=edge_attrs,
            edge_feats=edge_feats,
            cutoff=cutoff,
            num_graphs=ctx.num_graphs,
            num_atoms_arange=num_atoms_arange,
            node_heads=node_heads,
            lammps_class=ctx.interaction_kwargs.lammps_class,
            lammps_natoms=ctx.interaction_kwargs.lammps_natoms,
            baseline_energy=baseline_energy,
            pair_node_energy=pair_node_energy,
            features_by_block=[None] * self.num_blocks,
        )

    def initial_state(
        self, data: Mapping[str, Tensor], geometry: MACEContext
    ) -> DynamicState:
        node_features = self.model.node_embedding(data["node_attrs"])
        return self._state(node_features, geometry.batch)

    def run_block(
        self, block_index: int, state: DynamicState, geometry: MACEContext
    ) -> DynamicState:
        node = state.components["node"]
        node_features, sc = self.model.interactions[block_index](
            node_attrs=geometry.node_attrs,
            node_feats=node.values,
            edge_attrs=geometry.edge_attrs,
            edge_feats=geometry.edge_feats,
            edge_index=geometry.edge_index,
            cutoff=geometry.cutoff,
            first_layer=(block_index == 0),
            lammps_class=geometry.lammps_class,
            lammps_natoms=geometry.lammps_natoms,
        )
        node_features = self.model.products[block_index](
            node_feats=node_features,
            sc=sc,
            node_attrs=geometry.node_attrs,
        )
        if node_features.shape != node.values.shape:
            raise ValueError(
                "MACE-MP-0 small recursion requires scalar, width-preserving blocks; "
                f"block {block_index} changed {tuple(node.values.shape)} to "
                f"{tuple(node_features.shape)}"
            )
        geometry.features_by_block[block_index] = node_features
        return self._state(node_features, geometry.batch)

    def readout(
        self,
        state: DynamicState,
        data: Mapping[str, Tensor],
        geometry: MACEContext,
    ) -> Tensor:
        del state, data
        if any(features is None for features in geometry.features_by_block):
            raise RuntimeError("not every MACE block produced features")
        features = [value for value in geometry.features_by_block if value is not None]
        node_energy_terms = [geometry.pair_node_energy]
        for index, readout in enumerate(self.model.readouts):
            feature_index = -1 if len(self.model.readouts) == 1 else index
            node_energy_terms.append(
                readout(features[feature_index], geometry.node_heads)[
                    geometry.num_atoms_arange, geometry.node_heads
                ]
            )
        node_interaction_energy = torch.stack(node_energy_terms, dim=0).sum(dim=0)
        node_interaction_energy = self.model.scale_shift(
            node_interaction_energy, geometry.node_heads
        )
        interaction_energy = self.scatter_sum(
            node_interaction_energy,
            geometry.batch,
            dim=-1,
            dim_size=geometry.num_graphs,
        )
        return geometry.baseline_energy + interaction_energy
