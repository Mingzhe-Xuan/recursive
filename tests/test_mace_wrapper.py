from __future__ import annotations

from types import SimpleNamespace

import torch
from torch import Tensor, nn

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.executor import run_segment_cycles
from recursive_backbones.mace import MACEMP0SmallWrapper


def scatter_sum(src: Tensor, index: Tensor, *, dim: int, dim_size: int) -> Tensor:
    assert dim in (0, -1)
    output = src.new_zeros(dim_size)
    output.index_add_(0, index, src)
    return output


def prepare_graph(data: dict[str, Tensor], **_: bool) -> SimpleNamespace:
    return SimpleNamespace(
        is_lammps=False,
        num_atoms_arange=torch.arange(data["node_attrs"].shape[0]),
        num_graphs=data["ptr"].numel() - 1,
        vectors=data["vectors"],
        lengths=data["lengths"],
        node_heads=torch.zeros(data["node_attrs"].shape[0], dtype=torch.long),
        interaction_kwargs=SimpleNamespace(lammps_class=None, lammps_natoms=None),
    )


class AtomicEnergies(nn.Module):
    def forward(self, attrs: Tensor) -> Tensor:
        return (attrs[:, :1] * 0.5) + (attrs[:, 1:2] * 0.25)


class Radial(nn.Module):
    def forward(self, lengths: Tensor, *_: Tensor):
        return torch.cat((lengths, lengths.square()), dim=-1), None


class Interaction(nn.Module):
    def __init__(self, factor: float) -> None:
        super().__init__()
        self.factor = nn.Parameter(torch.tensor(factor))

    def forward(self, *, node_feats: Tensor, **_: Tensor):
        return node_feats * self.factor + 0.1, node_feats * 0.05


class Product(nn.Module):
    def forward(self, *, node_feats: Tensor, sc: Tensor, **_: Tensor) -> Tensor:
        return node_feats + sc


class Readout(nn.Module):
    def __init__(self, weight: tuple[float, float]) -> None:
        super().__init__()
        self.register_buffer("weight", torch.tensor(weight).view(2, 1))

    def forward(self, features: Tensor, heads: Tensor) -> Tensor:
        del heads
        return features @ self.weight


class ScaleShift(nn.Module):
    def forward(self, values: Tensor, heads: Tensor) -> Tensor:
        del heads
        return values * 1.25 - 0.2


class FakeMACE(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.atomic_energies_fn = AtomicEnergies()
        self.node_embedding = nn.Linear(2, 2, bias=False)
        self.spherical_harmonics = nn.Identity()
        self.radial_embedding = Radial()
        self.interactions = nn.ModuleList([Interaction(0.8), Interaction(1.1)])
        self.products = nn.ModuleList([Product(), Product()])
        self.readouts = nn.ModuleList([Readout((0.2, 0.3)), Readout((0.4, -0.1))])
        self.scale_shift = ScaleShift()
        self.register_buffer("atomic_numbers", torch.tensor([1, 14]))
        with torch.no_grad():
            self.node_embedding.weight.copy_(torch.tensor([[0.5, 0.2], [0.1, 0.7]]))

    def forward(self, data: dict[str, Tensor]) -> Tensor:
        ctx = prepare_graph(data)
        arange = ctx.num_atoms_arange.long()
        heads = ctx.node_heads.long()
        node_e0 = self.atomic_energies_fn(data["node_attrs"])[arange, heads]
        baseline = scatter_sum(node_e0, data["batch"], dim=0, dim_size=ctx.num_graphs)
        node_features = self.node_embedding(data["node_attrs"])
        edge_attrs = self.spherical_harmonics(ctx.vectors)
        edge_feats, cutoff = self.radial_embedding(
            ctx.lengths, data["node_attrs"], data["edge_index"], self.atomic_numbers
        )
        history = []
        for index, (interaction, product) in enumerate(zip(self.interactions, self.products)):
            node_features, sc = interaction(
                node_attrs=data["node_attrs"],
                node_feats=node_features,
                edge_attrs=edge_attrs,
                edge_feats=edge_feats,
                edge_index=data["edge_index"],
                cutoff=cutoff,
                first_layer=index == 0,
                lammps_class=None,
                lammps_natoms=None,
            )
            node_features = product(
                node_feats=node_features, sc=sc, node_attrs=data["node_attrs"]
            )
            history.append(node_features)
        terms = [torch.zeros_like(node_e0)]
        for index, readout in enumerate(self.readouts):
            terms.append(readout(history[index], heads)[arange, heads])
        interaction_node = self.scale_shift(torch.stack(terms).sum(dim=0), heads)
        return baseline + scatter_sum(
            interaction_node, data["batch"], dim=-1, dim_size=ctx.num_graphs
        )


def make_batch() -> dict[str, Tensor]:
    return {
        "node_attrs": torch.tensor([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]),
        "batch": torch.tensor([0, 0, 1]),
        "ptr": torch.tensor([0, 2, 3]),
        "edge_index": torch.tensor([[0, 1, 2], [1, 0, 2]]),
        "vectors": torch.tensor([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        "lengths": torch.ones(3, 1),
    }


def test_mace_k0_matches_native_scalar_forward() -> None:
    model = FakeMACE().eval()
    wrapper = MACEMP0SmallWrapper(
        model, prepare_graph=prepare_graph, scatter_sum=scatter_sum
    )
    batch = make_batch()
    result = run_segment_cycles(
        wrapper,
        batch,
        start=0,
        stop=wrapper.num_blocks,
        repeats=0,
        aligner=IrrepNormAligner(),
    )
    torch.testing.assert_close(result.prediction, model(batch), atol=0, rtol=0)
    assert result.state.components["node"].spec.irreps[0].ell == 0


def test_mace_k1_full_backbone_is_finite() -> None:
    model = FakeMACE().eval()
    wrapper = MACEMP0SmallWrapper(
        model, prepare_graph=prepare_graph, scatter_sum=scatter_sum
    )
    result = run_segment_cycles(
        wrapper,
        make_batch(),
        start=0,
        stop=wrapper.num_blocks,
        repeats=1,
        aligner=IrrepNormAligner(gamma_min=0.1, gamma_max=10.0),
    )
    assert torch.isfinite(result.prediction).all()
    assert set(result.traces[0].alignment.gamma["node"]) == {"l=0,p=1"}
