"""Interface implemented by model-specific frozen backbone wrappers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from torch import Tensor

from .state import DynamicState


@runtime_checkable
class RecursiveBackbone(Protocol):
    """Minimal interface consumed by the model-independent executor."""

    @property
    def num_blocks(self) -> int: ...

    def encode_geometry(self, batch: Any) -> Any: ...

    def initial_state(self, batch: Any, geometry: Any) -> DynamicState: ...

    def run_block(self, block_index: int, state: DynamicState, geometry: Any) -> DynamicState: ...

    def readout(self, state: DynamicState, batch: Any, geometry: Any) -> Tensor: ...

