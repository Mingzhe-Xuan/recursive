"""Trainable node-wise seam projections."""

from torch import nn


class LinearProjection(nn.Linear):
    """Map cached scalar node channels into the native atom descriptor width."""
