from __future__ import annotations

from typing import Any

import torch
from torch import Tensor, nn

from adapters.norm import IrrepNormAligner
from recursive_backbones.common.executor import run_layerwise, run_segment_cycles
from recursive_backbones.common.state import DynamicState, IrrepBlock, StateComponent, StateSpec


class MockBackbone(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.scales = nn.Parameter(torch.tensor([2.0, 3.0]), requires_grad=False)
        self.calls: list[int] = []
        self.spec = StateSpec("atom", (IrrepBlock(0, 1, 2, 0),))

    @property
    def num_blocks(self) -> int:
        return 2

    def encode_geometry(self, batch: Any) -> None:
        return None

    def initial_state(self, batch: Tensor, geometry: Any) -> DynamicState:
        return DynamicState({"atom": StateComponent(batch.clone(), self.spec)})

    def run_block(self, block_index: int, state: DynamicState, geometry: Any) -> DynamicState:
        self.calls.append(block_index)
        component = state.components["atom"]
        return DynamicState(
            {"atom": component.with_values(component.values * self.scales[block_index])}
        )

    def readout(self, state: DynamicState, batch: Any, geometry: Any) -> Tensor:
        return state.components["atom"].values.sum()


def test_segment_k0_is_native_and_never_calls_adapter() -> None:
    backbone = MockBackbone()

    class FailingAligner(IrrepNormAligner):
        def __call__(self, current: DynamicState, reference: DynamicState):
            raise AssertionError("K=0 must not call the seam adapter")

    result = run_segment_cycles(
        backbone,
        torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        start=0,
        stop=2,
        repeats=0,
        aligner=FailingAligner(),
    )
    assert backbone.calls == [0, 1]
    assert result.traces == ()
    torch.testing.assert_close(result.prediction, torch.tensor(60.0))


def test_segment_k1_repeats_segment_once_after_alignment() -> None:
    backbone = MockBackbone()
    result = run_segment_cycles(
        backbone,
        torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        start=0,
        stop=2,
        repeats=1,
        aligner=IrrepNormAligner(epsilon=1e-12),
    )
    assert backbone.calls == [0, 1, 0, 1]
    assert len(result.traces) == 1
    torch.testing.assert_close(result.prediction, torch.tensor(60.0))


def test_layerwise_repeats_only_requested_blocks() -> None:
    backbone = MockBackbone()
    result = run_layerwise(
        backbone,
        torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        repeats=(1, 0),
        aligner=IrrepNormAligner(epsilon=1e-12),
    )
    assert backbone.calls == [0, 0, 1]
    assert len(result.traces) == 1
    torch.testing.assert_close(result.prediction, torch.tensor(60.0))

