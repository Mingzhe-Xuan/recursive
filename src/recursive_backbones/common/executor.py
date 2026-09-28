"""Model-independent segment and layer-wise recursive execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from torch import Tensor

from adapters.norm import AlignmentDiagnostics, IrrepNormAligner

from .protocol import RecursiveBackbone
from .state import DynamicState


@dataclass(frozen=True, slots=True)
class RecursionTrace:
    kind: str
    block_start: int
    block_stop: int
    repeat_index: int
    alignment: AlignmentDiagnostics


@dataclass(frozen=True, slots=True)
class RecursiveResult:
    state: DynamicState
    prediction: Tensor
    traces: tuple[RecursionTrace, ...]


def _validate_segment(backbone: RecursiveBackbone, start: int, stop: int, repeats: int) -> None:
    if repeats < 0:
        raise ValueError("repeats must be non-negative")
    if not 0 <= start < stop <= backbone.num_blocks:
        raise ValueError(
            f"segment [{start}, {stop}) outside backbone with {backbone.num_blocks} blocks"
        )


def _run_blocks(
    backbone: RecursiveBackbone,
    state: DynamicState,
    geometry: Any,
    start: int,
    stop: int,
) -> DynamicState:
    for block_index in range(start, stop):
        state = backbone.run_block(block_index, state, geometry)
    return state


def run_segment_cycles(
    backbone: RecursiveBackbone,
    batch: Any,
    *,
    start: int,
    stop: int,
    repeats: int,
    aligner: IrrepNormAligner,
) -> RecursiveResult:
    """Run a native forward with a recursively repeated half-open segment [start, stop)."""

    _validate_segment(backbone, start, stop, repeats)
    geometry = backbone.encode_geometry(batch)
    state = backbone.initial_state(batch, geometry)
    state = _run_blocks(backbone, state, geometry, 0, start)
    reference = state
    state = _run_blocks(backbone, state, geometry, start, stop)

    traces: list[RecursionTrace] = []
    for repeat_index in range(1, repeats + 1):
        state, diagnostics = aligner(state, reference)
        traces.append(
            RecursionTrace(
                kind="segment",
                block_start=start,
                block_stop=stop,
                repeat_index=repeat_index,
                alignment=diagnostics,
            )
        )
        state = _run_blocks(backbone, state, geometry, start, stop)

    state = _run_blocks(backbone, state, geometry, stop, backbone.num_blocks)
    return RecursiveResult(state, backbone.readout(state, batch, geometry), tuple(traces))


def run_layerwise(
    backbone: RecursiveBackbone,
    batch: Any,
    *,
    repeats: tuple[int, ...],
    aligner: IrrepNormAligner,
) -> RecursiveResult:
    """Run each native block once plus its configured number of extra repeats."""

    if len(repeats) != backbone.num_blocks:
        raise ValueError("one repeat count is required for every backbone block")
    if any(repeat < 0 for repeat in repeats):
        raise ValueError("repeat counts must be non-negative")

    geometry = backbone.encode_geometry(batch)
    state = backbone.initial_state(batch, geometry)
    traces: list[RecursionTrace] = []

    for block_index, block_repeats in enumerate(repeats):
        reference = state
        state = backbone.run_block(block_index, state, geometry)
        for repeat_index in range(1, block_repeats + 1):
            state, diagnostics = aligner(state, reference)
            traces.append(
                RecursionTrace(
                    kind="layer",
                    block_start=block_index,
                    block_stop=block_index + 1,
                    repeat_index=repeat_index,
                    alignment=diagnostics,
                )
            )
            state = backbone.run_block(block_index, state, geometry)

    return RecursiveResult(state, backbone.readout(state, batch, geometry), tuple(traces))

