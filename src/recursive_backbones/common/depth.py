"""Validation-driven increasing recursion-depth scan state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DepthEarlyStopper:
    """Track a K=0,1,2,... scan and select the best observed validation score."""

    patience: int = 3
    hard_max: int = 16
    minimum_depth: int = 4
    min_delta: float = 0.0
    scores: dict[int, float] = field(default_factory=dict)
    best_depth: int | None = None
    best_score: float = float("inf")
    stale_depths: int = 0

    def __post_init__(self) -> None:
        if self.patience <= 0:
            raise ValueError("patience must be positive")
        if self.hard_max < self.minimum_depth:
            raise ValueError("hard_max must be at least minimum_depth")
        if self.minimum_depth < 0 or self.min_delta < 0:
            raise ValueError("minimum_depth and min_delta must be non-negative")

    def update(self, depth: int, score: float) -> bool:
        """Record one sequential depth; return True when scanning should stop."""

        expected = len(self.scores)
        if depth != expected:
            raise ValueError(f"expected depth {expected}, got {depth}")
        if depth > self.hard_max:
            raise ValueError(f"depth {depth} exceeds hard_max {self.hard_max}")
        self.scores[depth] = float(score)
        if self.best_depth is None or score < self.best_score - self.min_delta:
            self.best_depth = depth
            self.best_score = float(score)
            self.stale_depths = 0
        else:
            self.stale_depths += 1
        return depth >= self.hard_max or (
            depth >= self.minimum_depth and self.stale_depths >= self.patience
        )

