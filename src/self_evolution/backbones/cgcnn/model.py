"""Native CGCNN and an explicit pre-pooling node feature interface."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import nn

from self_evolution.adapters import LinearProjection

from .upstream.model import CrystalGraphConvNet


@dataclass(frozen=True)
class ModelConfig:
    atom_input: int = 92
    edge_input: int = 41
    hidden: int = 64
    convolutions: int = 3
    head_hidden: int = 128
    head_layers: int = 1

    def __post_init__(self):
        if any(v < 1 for v in asdict(self).values()):
            raise ValueError("all model dimensions and layer counts must be positive")


class CGCNNStage(nn.Module):
    def __init__(self, config: ModelConfig, recursive: bool = False):
        super().__init__()
        self.config = config
        self.native = CrystalGraphConvNet(
            config.atom_input,
            config.edge_input,
            config.hidden,
            config.convolutions,
            config.head_hidden,
            config.head_layers,
        )
        self.projection = LinearProjection(config.hidden, config.atom_input) if recursive else None

    def encode_nodes(self, batch: dict, features: torch.Tensor | None = None) -> torch.Tensor:
        if self.projection is None:
            if features is not None:
                raise ValueError("native stage cannot consume a previous-stage cache")
            x = batch["atom_features"]
        else:
            if features is None:
                raise ValueError("recursive stage requires previous-stage node features")
            if features.shape != (len(batch["atom_features"]), self.config.hidden):
                raise ValueError("cached node shape does not match current graph")
            x = self.projection(features.detach())
        x = self.native.embedding(x)
        for conv in self.native.convs:
            x = conv(x, batch["neighbor_features"], batch["neighbor_indices"])
        return x

    def readout(self, nodes: torch.Tensor, batch: dict) -> torch.Tensor:
        x = self.native.pooling(nodes, batch["crystal_atom_indices"])
        x = self.native.conv_to_fc(self.native.conv_to_fc_softplus(x))
        x = self.native.conv_to_fc_softplus(x)
        if hasattr(self.native, "fcs"):
            for fc, softplus in zip(self.native.fcs, self.native.softpluses):
                x = softplus(fc(x))
        return self.native.fc_out(x).reshape(-1)

    def forward_native(self, batch: dict) -> torch.Tensor:
        return self.native(
            batch["atom_features"],
            batch["neighbor_features"],
            batch["neighbor_indices"],
            batch["crystal_atom_indices"],
        ).reshape(-1)

    def forward_from_features(self, batch: dict, features: torch.Tensor) -> torch.Tensor:
        return self.readout(self.encode_nodes(batch, features), batch)

    def forward(self, batch: dict, features: torch.Tensor | None = None) -> torch.Tensor:
        return self.readout(self.encode_nodes(batch, features), batch)
