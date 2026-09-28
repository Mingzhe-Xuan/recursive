from __future__ import annotations

import pytest
import torch

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.state import DynamicState, IrrepBlock, StateComponent, StateSpec


def _spec(name: str = "atom") -> StateSpec:
    return StateSpec(
        name=name,
        irreps=(
            IrrepBlock(ell=0, parity=1, multiplicity=1, start=0, label="scalar"),
            IrrepBlock(ell=1, parity=-1, multiplicity=1, start=1, label="vector"),
        ),
    )


def test_irrep_norm_alignment_is_per_structure_and_shares_all_m() -> None:
    spec = _spec()
    batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)
    mask = torch.tensor([True, True, True, False])
    reference_values = torch.tensor(
        [
            [1.0, 1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0, 6.0],
            [2.0, 2.0, 4.0, 8.0],
            [999.0, 999.0, 999.0, 999.0],
        ]
    )
    current_values = reference_values.clone()
    current_values[:2, 0] *= 2
    current_values[:2, 1:] *= 4
    current_values[2, 0] *= 5
    current_values[2, 1:] *= 10
    current_values[3] = -12345

    reference = DynamicState(
        {"atom": StateComponent(reference_values, spec, batch=batch, mask=mask)}
    )
    current = DynamicState(
        {"atom": StateComponent(current_values, spec, batch=batch, mask=mask)}
    )
    aligned, diagnostics = IrrepNormAligner(epsilon=1e-12)(current, reference)

    torch.testing.assert_close(aligned.components["atom"].values[:3], reference_values[:3])
    scalar_gamma = diagnostics.gamma["atom"]["l=0,p=1"]
    vector_gamma = diagnostics.gamma["atom"]["l=1,p=-1"]
    torch.testing.assert_close(scalar_gamma, torch.tensor([0.5, 0.2]))
    torch.testing.assert_close(vector_gamma, torch.tensor([0.25, 0.1]))

    ratios = (
        aligned.components["atom"].values[0, 1:]
        / current.components["atom"].values[0, 1:]
    )
    assert torch.unique(ratios).numel() == 1


def test_state_rejects_overlapping_or_incompatible_layouts() -> None:
    with pytest.raises(ValueError, match="overlapping"):
        StateSpec(
            "atom",
            (
                IrrepBlock(ell=1, parity=1, multiplicity=1, start=0),
                IrrepBlock(ell=0, parity=1, multiplicity=1, start=2),
            ),
        )

    left_spec = StateSpec("atom", (IrrepBlock(0, 1, 1, 0),))
    right_spec = StateSpec("atom", (IrrepBlock(0, -1, 1, 0),))
    left = DynamicState({"atom": StateComponent(torch.ones(2, 1), left_spec)})
    right = DynamicState({"atom": StateComponent(torch.ones(2, 1), right_spec)})
    with pytest.raises(ValueError, match="incompatible state spec"):
        IrrepNormAligner()(left, right)


def test_disjoint_blocks_of_same_irrep_type_share_one_scale() -> None:
    spec = StateSpec(
        "node",
        (
            IrrepBlock(ell=0, parity=1, multiplicity=1, start=0, label="first"),
            IrrepBlock(ell=1, parity=-1, multiplicity=1, start=1),
            IrrepBlock(ell=0, parity=1, multiplicity=1, start=4, label="second"),
        ),
    )
    reference = DynamicState(
        {"node": StateComponent(torch.tensor([[2.0, 1.0, 0.0, 0.0, 6.0]]), spec)}
    )
    current = DynamicState(
        {"node": StateComponent(torch.tensor([[1.0, 1.0, 0.0, 0.0, 1.0]]), spec)}
    )

    aligned, diagnostics = IrrepNormAligner(epsilon=1e-12)(current, reference)

    expected_gamma = torch.sqrt(torch.tensor(20.0))
    torch.testing.assert_close(aligned.components["node"].values[0, 0], expected_gamma)
    torch.testing.assert_close(aligned.components["node"].values[0, 4], expected_gamma)
    torch.testing.assert_close(
        aligned.components["node"].values[0, 1:4],
        current.components["node"].values[0, 1:4],
    )
    assert set(diagnostics.gamma["node"]) == {"l=0,p=1", "l=1,p=-1"}
