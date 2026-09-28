"""Typed dynamic state carried across recursive backbone boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch
from torch import Tensor


@dataclass(frozen=True, slots=True)
class IrrepBlock:
    """A contiguous packed irrep block in the final tensor dimension."""

    ell: int
    parity: int
    multiplicity: int
    start: int
    label: str = ""

    def __post_init__(self) -> None:
        if self.ell < 0:
            raise ValueError("ell must be non-negative")
        if self.parity not in (-1, 1):
            raise ValueError("parity must be -1 or +1")
        if self.multiplicity <= 0:
            raise ValueError("multiplicity must be positive")
        if self.start < 0:
            raise ValueError("start must be non-negative")

    @property
    def width(self) -> int:
        return self.multiplicity * (2 * self.ell + 1)

    @property
    def stop(self) -> int:
        return self.start + self.width

    @property
    def key(self) -> str:
        suffix = f":{self.label}" if self.label else ""
        return f"l={self.ell},p={self.parity}{suffix}"


@dataclass(frozen=True, slots=True)
class StateSpec:
    """Layout of one state component with features packed on the last axis."""

    name: str
    irreps: tuple[IrrepBlock, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("state component name cannot be empty")
        ordered = sorted(self.irreps, key=lambda block: block.start)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if previous.stop > current.start:
                raise ValueError(f"overlapping irrep blocks in {self.name}")

    @property
    def feature_width(self) -> int:
        return max((block.stop for block in self.irreps), default=0)

    def compatible_with(self, other: StateSpec) -> bool:
        return self.name == other.name and self.irreps == other.irreps


@dataclass(slots=True)
class StateComponent:
    """Tensor values and per-item structure membership for one state type."""

    values: Tensor
    spec: StateSpec
    batch: Tensor | None = None
    mask: Tensor | None = None

    def __post_init__(self) -> None:
        if self.values.ndim != 2:
            raise ValueError(
                f"{self.spec.name}: expected [items, features], got {tuple(self.values.shape)}"
            )
        if self.values.shape[-1] != self.spec.feature_width:
            raise ValueError(
                f"{self.spec.name}: feature width {self.values.shape[-1]} does not match "
                f"state spec {self.spec.feature_width}"
            )
        item_count = self.values.shape[0]
        if self.batch is None:
            self.batch = torch.zeros(item_count, dtype=torch.long, device=self.values.device)
        if self.mask is None:
            self.mask = torch.ones(item_count, dtype=torch.bool, device=self.values.device)
        if self.batch.shape != (item_count,):
            raise ValueError(f"{self.spec.name}: batch must have shape ({item_count},)")
        if self.mask.shape != (item_count,):
            raise ValueError(f"{self.spec.name}: mask must have shape ({item_count},)")
        if self.batch.dtype != torch.long:
            raise TypeError(f"{self.spec.name}: batch must use torch.long")
        if self.mask.dtype != torch.bool:
            raise TypeError(f"{self.spec.name}: mask must use torch.bool")
        if self.batch.device != self.values.device or self.mask.device != self.values.device:
            raise ValueError(f"{self.spec.name}: values, batch, and mask must share a device")
        if bool((self.batch < 0).any()):
            raise ValueError(f"{self.spec.name}: batch indices must be non-negative")

    @property
    def num_structures(self) -> int:
        if self.batch.numel() == 0:
            return 0
        return int(self.batch.max().item()) + 1

    def with_values(self, values: Tensor) -> StateComponent:
        return StateComponent(values=values, spec=self.spec, batch=self.batch, mask=self.mask)


@dataclass(slots=True)
class DynamicState:
    """Complete mutable state at a backbone boundary."""

    components: Mapping[str, StateComponent]

    def __post_init__(self) -> None:
        if not self.components:
            raise ValueError("dynamic state must contain at least one component")
        for name, component in self.components.items():
            if name != component.spec.name:
                raise ValueError(f"component key {name!r} != spec name {component.spec.name!r}")

    def assert_compatible(self, other: DynamicState) -> None:
        if set(self.components) != set(other.components):
            raise ValueError(
                "state components differ: "
                f"{sorted(self.components)} != {sorted(other.components)}"
            )
        for name, component in self.components.items():
            other_component = other.components[name]
            if not component.spec.compatible_with(other_component.spec):
                raise ValueError(f"incompatible state spec for component {name}")
            if component.values.shape != other_component.values.shape:
                raise ValueError(
                    f"incompatible values shape for {name}: {tuple(component.values.shape)} != "
                    f"{tuple(other_component.values.shape)}"
                )
            if not torch.equal(component.batch, other_component.batch):
                raise ValueError(f"batch membership changed for component {name}")
            if not torch.equal(component.mask, other_component.mask):
                raise ValueError(f"mask changed for component {name}")

    def tensors(self) -> Mapping[str, Tensor]:
        return {name: component.values for name, component in self.components.items()}

