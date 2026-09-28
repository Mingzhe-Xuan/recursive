from __future__ import annotations

import torch
from torch import Tensor, nn

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.executor import run_segment_cycles
from recursive_backbones.mattersim import MatterSimM3GNetWrapper


def scatter_sum(src: Tensor, index: Tensor, *, dim: int, dim_size: int) -> Tensor:
    assert dim == 0
    output = src.new_zeros(dim_size)
    output.index_add_(0, index, src)
    return output


class FakeConv(nn.Module):
    def __init__(self, scale: float) -> None:
        super().__init__()
        self.scale = nn.Parameter(torch.tensor(scale))

    def forward(self, *, atom_attr: Tensor, edge_attr: Tensor, **_: Tensor):
        return atom_attr * self.scale + 0.1, edge_attr * self.scale - 0.2


class FakeM3GNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.atom_embedding = nn.Linear(5, 3, bias=False)
        self.edge_encoder = nn.Linear(2, 3, bias=False)
        self.graph_conv = nn.ModuleList([FakeConv(0.8), FakeConv(1.1)])
        self.final = nn.Linear(3, 1, bias=False)
        self.normalizer = lambda values, atomic_numbers: values + atomic_numbers * 0.01
        self.gradient_checkpointing = False
        with torch.no_grad():
            self.atom_embedding.weight.copy_(torch.arange(15).view(3, 5) / 10)
            self.edge_encoder.weight.copy_(torch.arange(6).view(3, 2) / 10)
            self.final.weight.fill_(0.25)

    @staticmethod
    def one_hot_atoms(species: Tensor) -> Tensor:
        return torch.nn.functional.one_hot(species, num_classes=5).float()

    @staticmethod
    def rbf(distance: Tensor) -> Tensor:
        return torch.stack((distance, distance.square()), dim=-1)

    @staticmethod
    def sbf(distance: Tensor, angle: Tensor) -> Tensor:
        return torch.stack((distance, angle), dim=-1)

    def forward(self, data: dict[str, Tensor]) -> Tensor:
        pos = data["atom_pos"]
        cell = data["cell"]
        offsets = data["pbc_offsets"].to(pos.dtype)
        edge_index = data["edge_index"].long()
        triples = data["three_body_indices"].long()
        batch = data["batch"]
        edge_batch = batch[edge_index[0]]
        vectors = pos[edge_index[0]] - (
            pos[edge_index[1]] + torch.einsum("bi, bij->bj", offsets, cell[edge_batch])
        )
        lengths_flat = torch.linalg.norm(vectors, dim=1)
        vij, vik = vectors[triples[:, 0]], vectors[triples[:, 1]]
        rij, rik = lengths_flat[triples[:, 0]], lengths_flat[triples[:, 1]]
        cosine = (vij * vik).sum(dim=1) / (rij * rik)
        cosine = cosine.clamp(-1 + 1e-7, 1 - 1e-7)
        lengths = lengths_flat.unsqueeze(-1)
        numbers = data["atom_attr"].squeeze(1).long()
        atom_attr = self.atom_embedding(self.one_hot_atoms(numbers))
        edge_zero = self.rbf(lengths.view(-1))
        edge_attr = self.edge_encoder(edge_zero)
        three_basis = self.sbf(rik.view(-1), torch.acos(cosine))
        for conv in self.graph_conv:
            atom_attr, edge_attr = conv(
                atom_attr=atom_attr,
                edge_attr=edge_attr,
                edge_attr_zero=edge_zero,
                edge_index=edge_index,
                three_basis=three_basis,
                three_body_index=triples,
                edge_length=lengths,
                num_edges=data["num_bonds"],
                num_triple_ij=data["num_triple_ij"],
                num_atoms=data["num_atoms"],
            )
        energies_i = self.normalizer(self.final(atom_attr).view(-1), numbers)
        return scatter_sum(energies_i, batch, dim=0, dim_size=cell.shape[0])


def make_batch() -> dict[str, Tensor]:
    return {
        "atom_pos": torch.tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]),
        "cell": torch.eye(3).repeat(2, 1, 1),
        "pbc_offsets": torch.zeros(2, 3),
        "atom_attr": torch.tensor([[1], [2], [3]]),
        "edge_index": torch.tensor([[0, 2], [1, 1]]),
        "three_body_indices": torch.tensor([[0, 1]]),
        "num_bonds": torch.tensor([1, 1]),
        "num_triple_ij": torch.tensor([1, 0]),
        "num_atoms": torch.tensor([2, 1]),
        "batch": torch.tensor([0, 0, 1]),
    }


def test_k0_matches_native_forward_and_state_is_complete() -> None:
    model = FakeM3GNet().eval()
    wrapper = MatterSimM3GNetWrapper(model, scatter_sum=scatter_sum)
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
    assert set(result.state.components) == {"atom", "edge"}
    assert result.traces == ()


def test_k1_is_finite_and_has_separate_atom_edge_scales() -> None:
    model = FakeM3GNet().eval()
    wrapper = MatterSimM3GNetWrapper(model, scatter_sum=scatter_sum)
    result = run_segment_cycles(
        wrapper,
        make_batch(),
        start=0,
        stop=wrapper.num_blocks,
        repeats=1,
        aligner=IrrepNormAligner(epsilon=1e-8, gamma_min=0.1, gamma_max=10.0),
    )
    assert torch.isfinite(result.prediction).all()
    assert len(result.traces) == 1
    assert set(result.traces[0].alignment.gamma) == {"atom", "edge"}
    assert result.traces[0].alignment.gamma["atom"]["l=0,p=1"].shape == (2,)

