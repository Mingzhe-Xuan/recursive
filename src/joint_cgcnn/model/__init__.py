"""Two independent native encoders, one linear bridge and one final readout."""

import torch
from torch import nn

from self_evolution.backbones.cgcnn import CGCNNStage, ModelConfig
from self_evolution.io import derived_seed


def stage_seeds(seed, task):
    return [derived_seed(seed, "cgcnn", task, r, "evolution") for r in [0, 1]]


class Encoder(nn.Module):
    def __init__(self, stage):
        super().__init__()
        self.embedding = stage.native.embedding
        self.convs = stage.native.convs

    def forward(self, batch):
        nodes = self.embedding(batch["atom_features"])
        for conv in self.convs:
            nodes = conv(nodes, batch["neighbor_features"], batch["neighbor_indices"])
        return nodes


class DoubleCGCNN(nn.Module):
    def __init__(self, config: ModelConfig, seeds):
        super().__init__()
        self.config = config
        # Match each fresh cached-stage initialization without loading trained weights.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(seeds[0])
            self.first = Encoder(CGCNNStage(config))
            torch.random.default_generator.manual_seed(seeds[1])
            self.second = CGCNNStage(config, recursive=True)

    def forward(self, batch):
        nodes = self.first(batch)
        # The cached-stage encode_nodes detaches features; keep this seam differentiable.
        nodes = self.second.native.embedding(self.second.projection(nodes))
        for conv in self.second.native.convs:
            nodes = conv(nodes, batch["neighbor_features"], batch["neighbor_indices"])
        return self.second.readout(nodes, batch)
