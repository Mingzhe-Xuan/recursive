"""Per-structure, per-state, per-irrep RMS norm alignment."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from recursive_backbones.common.state import DynamicState, IrrepBlock, StateComponent


@dataclass(frozen=True, slots=True)
class AlignmentDiagnostics:
    """Scaling factors keyed by state component and irrep block."""

    gamma: dict[str, dict[str, Tensor]]


class IrrepNormAligner:
    """Match current RMS to the reference RMS without trainable parameters."""

    def __init__(
        self,
        *,
        epsilon: float = 1e-8,
        gamma_min: float = 0.0,
        gamma_max: float = float("inf"),
    ) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be positive")
        if gamma_min < 0 or gamma_max < gamma_min:
            raise ValueError("invalid gamma clipping interval")
        self.epsilon = epsilon
        self.gamma_min = gamma_min
        self.gamma_max = gamma_max

    def __call__(
        self, current: DynamicState, reference: DynamicState
    ) -> tuple[DynamicState, AlignmentDiagnostics]:
        current.assert_compatible(reference)
        aligned: dict[str, StateComponent] = {}
        diagnostics: dict[str, dict[str, Tensor]] = {}

        for name, current_component in current.components.items():
            reference_component = reference.components[name]
            values = current_component.values.clone()
            diagnostics[name] = {}

            grouped: dict[tuple[int, int], list[IrrepBlock]] = {}
            for block in current_component.spec.irreps:
                grouped.setdefault((block.ell, block.parity), []).append(block)

            for (ell, parity), blocks in grouped.items():
                current_rms = self._rms_by_structure(current_component, blocks)
                reference_rms = self._rms_by_structure(reference_component, blocks)
                gamma = reference_rms / (current_rms + self.epsilon)
                gamma = gamma.clamp(min=self.gamma_min, max=self.gamma_max)
                scale = gamma[current_component.batch].to(values.dtype).unsqueeze(-1)
                for block in blocks:
                    values[:, block.start : block.stop] *= scale
                diagnostics[name][f"l={ell},p={parity}"] = gamma.detach()

            aligned[name] = current_component.with_values(values)

        return DynamicState(aligned), AlignmentDiagnostics(diagnostics)

    @staticmethod
    def _rms_by_structure(component: StateComponent, blocks: list[IrrepBlock]) -> Tensor:
        num_structures = component.num_structures
        if num_structures == 0:
            return component.values.new_zeros((0,))

        valid = component.mask
        sum_sq = component.values.new_zeros((num_structures,))
        count = component.values.new_zeros((num_structures,))

        item_sum_sq = component.values.new_zeros((component.values.shape[0],))
        width = 0
        for block in blocks:
            block_values = component.values[:, block.start : block.stop]
            item_sum_sq += block_values.square().sum(dim=-1)
            width += block.width
        item_sum_sq *= valid.to(component.values.dtype)
        item_count = valid.to(component.values.dtype) * width
        sum_sq.index_add_(0, component.batch, item_sum_sq)
        count.index_add_(0, component.batch, item_count)
        return torch.sqrt(sum_sq / count.clamp_min(1))
