"""Serializable recursion configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NormConfig:
    epsilon: float = 1e-8
    gamma_min: float = 0.0
    gamma_max: float = float("inf")


@dataclass(frozen=True, slots=True)
class SegmentConfig:
    start: int
    stop: int
    repeats: int
    norm: NormConfig = NormConfig()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> SegmentConfig:
        payload = dict(values)
        payload["norm"] = NormConfig(**payload.get("norm", {}))
        return cls(**payload)

