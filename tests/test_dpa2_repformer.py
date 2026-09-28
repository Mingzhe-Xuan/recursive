from __future__ import annotations

import torch
from torch import Tensor, nn

from adapters.norm import IrrepNormAligner
from recursive_backbones.dpa2 import DPA2RepformerRecursor


def fake_environment(
    extended_coord: Tensor,
    nlist: Tensor,
    atype: Tensor,
    mean: Tensor,
    stddev: Tensor,
    rcut: float,
    rcut_smth: float,
    *,
    protection: float,
) -> tuple[Tensor, Tensor, Tensor]:
    del extended_coord, atype, mean, stddev, rcut, rcut_smth, protection
    valid = nlist != -1
    distance = torch.where(valid, nlist + 1, 0).to(torch.float32).unsqueeze(-1)
    direction = torch.cat((distance, distance * 0.5, -distance), dim=-1)
    dmatrix = torch.cat((distance * 0.25, direction), dim=-1)
    switching = valid.to(torch.float32).unsqueeze(-1)
    return dmatrix, direction, switching


class ExcludeMask(nn.Module):
    def forward(self, nlist: Tensor, extended_atype: Tensor) -> Tensor:
        del extended_atype
        return torch.ones_like(nlist, dtype=torch.bool)


class FakeLayer(nn.Module):
    def __init__(self, scale: float) -> None:
        super().__init__()
        self.register_buffer("scale", torch.tensor(scale))

    def forward(
        self,
        g1_ext: Tensor,
        g2: Tensor,
        h2: Tensor,
        nlist: Tensor,
        nlist_mask: Tensor,
        sw: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        del nlist
        nloc = g2.shape[1]
        valid = nlist_mask.unsqueeze(-1)
        g1 = g1_ext[:, :nloc] * self.scale + 0.05
        g2 = torch.where(valid, g2 * self.scale + g1.unsqueeze(2) * 0.1, g2)
        h2 = torch.where(valid, h2 * self.scale + sw.unsqueeze(-1) * 0.02, h2)
        return g1, g2, h2

    def _cal_h2g2(
        self, g2: Tensor, h2: Tensor, nlist_mask: Tensor, sw: Tensor
    ) -> Tensor:
        weight = g2 * sw.unsqueeze(-1) * nlist_mask.unsqueeze(-1)
        return torch.einsum("bijn,bijc->bicn", weight, h2)


class FakeRepformers(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.act = nn.Tanh()
        self.dim_emb = 2
        self.direct_dist = False
        self.emask = ExcludeMask()
        self.env_protection = 0.0
        self.g1_dim = 2
        self.g2_embd = nn.Linear(1, 2)
        self.layers = nn.ModuleList((FakeLayer(0.8), FakeLayer(1.1)))
        self.register_buffer("mean", torch.zeros(1))
        self.rcut = 6.0
        self.rcut_smth = 5.5
        self.register_buffer("stddev", torch.ones(1))
        with torch.no_grad():
            self.g2_embd.weight.copy_(torch.tensor([[0.4], [-0.2]]))
            self.g2_embd.bias.copy_(torch.tensor([0.1, 0.3]))

    def forward(
        self,
        nlist: Tensor,
        extended_coord: Tensor,
        extended_atype: Tensor,
        extended_atype_embd: Tensor | None = None,
        mapping: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
        assert extended_atype_embd is not None and mapping is not None
        nframes, nloc, _ = nlist.shape
        nall = extended_coord.view(nframes, -1).shape[1] // 3
        atype = extended_atype[:, :nloc]
        exclude_mask = self.emask(nlist, extended_atype)
        nlist = torch.where(exclude_mask != 0, nlist, -1)
        dmatrix, _, sw = fake_environment(
            extended_coord,
            nlist,
            atype,
            self.mean,
            self.stddev,
            self.rcut,
            self.rcut_smth,
            protection=self.env_protection,
        )
        nlist_mask = nlist != -1
        sw = torch.squeeze(sw, -1).masked_fill(~nlist_mask, 0.0)
        g1 = self.act(extended_atype_embd[:, :nloc, :])
        g2, h2 = torch.split(dmatrix, [1, 3], dim=-1)
        g2 = self.act(self.g2_embd(g2))
        nlist = nlist.masked_fill(~nlist_mask, 0)
        mapping_index = mapping.view(nframes, nall).unsqueeze(-1).expand(-1, -1, self.g1_dim)
        for layer in self.layers:
            g1_ext = torch.gather(g1, 1, mapping_index)
            g1, g2, h2 = layer(g1_ext, g2, h2, nlist, nlist_mask, sw)
        h2g2 = self.layers[-1]._cal_h2g2(g2, h2, nlist_mask, sw)
        rot_mat = torch.permute(h2g2, (0, 1, 3, 2))
        return g1, g2, h2, rot_mat.view(-1, nloc, self.dim_emb, 3), sw


def inputs() -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    return (
        torch.tensor([[[1, 2], [0, -1]]]),
        torch.tensor([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]]),
        torch.tensor([[0, 1, 0]]),
        torch.tensor([[[0.2, 0.7], [0.6, -0.1], [0.2, 0.7]]]),
        torch.tensor([[0, 1, 0]]),
    )


def test_dpa2_k0_matches_independent_native_forward() -> None:
    repformers = FakeRepformers().eval()
    expected = repformers(*inputs())
    recursor = DPA2RepformerRecursor(
        repformers,
        repeats=0,
        aligner=IrrepNormAligner(),
        environment_builder=fake_environment,
    )
    actual = recursor.forward(*inputs())
    for actual_tensor, expected_tensor in zip(actual, expected):
        torch.testing.assert_close(actual_tensor, expected_tensor, atol=0, rtol=0)
    assert recursor.last_diagnostics == ()


def test_dpa2_k1_is_finite_and_uses_three_irrep_states() -> None:
    repformers = FakeRepformers().eval()
    recursor = DPA2RepformerRecursor(
        repformers,
        repeats=1,
        aligner=IrrepNormAligner(gamma_min=0.1, gamma_max=10.0),
        environment_builder=fake_environment,
    )
    result = recursor.forward(*inputs())
    assert all(torch.isfinite(value).all() for value in result)
    gamma = recursor.last_diagnostics[0].gamma
    assert set(gamma) == {"g1", "g2", "h2"}
    assert set(gamma["g1"]) == {"l=0,p=1"}
    assert set(gamma["g2"]) == {"l=0,p=1"}
    assert set(gamma["h2"]) == {"l=1,p=-1"}


def test_dpa2_scoped_install_restores_native_forward() -> None:
    repformers = FakeRepformers().eval()
    native_function = repformers.forward.__func__
    recursor = DPA2RepformerRecursor(
        repformers,
        repeats=0,
        aligner=IrrepNormAligner(),
        environment_builder=fake_environment,
    )
    with recursor.installed():
        assert repformers.forward == recursor.forward
        result = repformers(*inputs())
        assert all(torch.isfinite(value).all() for value in result)
    assert repformers.forward.__func__ is native_function
