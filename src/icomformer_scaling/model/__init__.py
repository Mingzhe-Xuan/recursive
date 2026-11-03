"""Official forward with a last-node-layer hook and explicit recursive projection."""

from dataclasses import dataclass, asdict

from torch import nn

from icomformer_scaling.source import model_components


@dataclass(frozen=True)
class ModelConfig:
    atom_input: int = 92
    hidden: int = 256
    edge_features: int = 256
    triplet_features: int = 256
    head_hidden: int = 256
    convolutions: int = 4

    def __post_init__(self):
        if min(asdict(self).values()) < 1 or self.convolutions != 4:
            raise ValueError(
                "official invariant forward requires four node layers and positive widths"
            )


class IComformerStage(nn.Module):
    def __init__(self, config=ModelConfig(), recursive=False):
        super().__init__()
        self.config = config
        native, configuration = model_components()
        self.native = native(
            configuration(
                atom_input_features=config.atom_input,
                node_features=config.hidden,
                edge_features=config.edge_features,
                triplet_input_features=config.triplet_features,
                fc_features=config.head_hidden,
                conv_layers=config.convolutions,
            )
        )
        self.projection = nn.Linear(config.hidden, config.atom_input) if recursive else None

    def encode_nodes(self, batch, features=None):
        data = batch["data"]
        if self.projection is not None:
            if features is None or features.shape != (data.num_nodes, self.config.hidden):
                raise ValueError("recursive node-cache dimensions mismatch")
            data = data.clone()
            data.x = self.projection(features.detach())
        elif features is not None:
            raise ValueError("native stage cannot consume previous features")
        nodes = []
        hook = self.native.att_layers[-1].register_forward_hook(
            lambda module, inputs, output: nodes.append(output)
        )
        try:
            self.native((data, None, None))
        finally:
            hook.remove()
        if len(nodes) != 1:
            raise ValueError("unexpected official node boundary")
        return nodes[0]

    def readout(self, nodes, batch):
        from torch_scatter import scatter

        features = scatter(nodes, batch["data"].batch, dim=0, reduce="mean")
        return self.native.fc_out(self.native.fc(features)).reshape(-1)

    def forward(self, batch, features=None):
        return self.readout(self.encode_nodes(batch, features), batch)

    def forward_native(self, batch):
        return self.native((batch["data"], None, None)).reshape(-1)
