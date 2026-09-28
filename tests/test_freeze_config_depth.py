from __future__ import annotations

import pytest
import torch
from torch import nn

from recursive_backbones.common.config import NormConfig, SegmentConfig
from recursive_backbones.common.depth import DepthEarlyStopper
from recursive_backbones.common.freeze import (
    assert_frozen_unchanged,
    freeze_module,
    snapshot_frozen,
)


def test_freeze_snapshot_detects_training_or_buffer_changes() -> None:
    module = nn.Sequential(nn.Linear(3, 4), nn.BatchNorm1d(4))
    freeze_module(module)
    snapshot = snapshot_frozen(module)
    assert_frozen_unchanged(module, snapshot)

    module.train()
    with pytest.raises(AssertionError, match="eval mode"):
        assert_frozen_unchanged(module, snapshot)

    module.eval()
    module[1].running_mean.add_(1)
    with pytest.raises(AssertionError, match="buffer"):
        assert_frozen_unchanged(module, snapshot)


def test_segment_config_round_trip() -> None:
    config = SegmentConfig(1, 3, 1, NormConfig(epsilon=1e-6, gamma_min=0.2, gamma_max=5))
    assert SegmentConfig.from_dict(config.to_dict()) == config


def test_depth_scan_is_sequential_and_returns_best_observed() -> None:
    stopper = DepthEarlyStopper(patience=3, hard_max=16, minimum_depth=4)
    assert not stopper.update(0, 1.0)
    assert not stopper.update(1, 0.8)
    assert not stopper.update(2, 0.9)
    assert not stopper.update(3, 0.85)
    assert stopper.update(4, 0.83)
    assert stopper.best_depth == 1
    assert stopper.best_score == 0.8
    with pytest.raises(ValueError, match="expected depth 5"):
        stopper.update(6, 0.7)

