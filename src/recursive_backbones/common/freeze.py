"""Freeze modules and prove that parameters and buffers remain unchanged."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass(frozen=True, slots=True)
class FrozenSnapshot:
    parameters: dict[str, Tensor]
    buffers: dict[str, Tensor]


def freeze_module(module: nn.Module) -> nn.Module:
    module.eval()
    for parameter in module.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    return module


def snapshot_frozen(module: nn.Module) -> FrozenSnapshot:
    return FrozenSnapshot(
        parameters={name: value.detach().cpu().clone() for name, value in module.named_parameters()},
        buffers={name: value.detach().cpu().clone() for name, value in module.named_buffers()},
    )


def assert_frozen_unchanged(module: nn.Module, snapshot: FrozenSnapshot) -> None:
    if module.training:
        raise AssertionError("frozen backbone left eval mode")
    current_parameters = dict(module.named_parameters())
    current_buffers = dict(module.named_buffers())
    if set(current_parameters) != set(snapshot.parameters):
        raise AssertionError("backbone parameter set changed")
    if set(current_buffers) != set(snapshot.buffers):
        raise AssertionError("backbone buffer set changed")
    for name, parameter in current_parameters.items():
        if parameter.requires_grad:
            raise AssertionError(f"backbone parameter {name} requires gradients")
        if parameter.grad is not None:
            raise AssertionError(f"backbone parameter {name} accumulated a gradient")
        if not torch.equal(parameter.detach().cpu(), snapshot.parameters[name]):
            raise AssertionError(f"backbone parameter {name} changed")
    for name, buffer in current_buffers.items():
        if not torch.equal(buffer.detach().cpu(), snapshot.buffers[name]):
            raise AssertionError(f"backbone buffer {name} changed")

