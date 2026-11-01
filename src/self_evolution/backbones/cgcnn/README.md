# CGCNN stage

`CGCNNStage(ModelConfig, recursive=False)` wraps the pinned official network unchanged.
Its exported node boundary is immediately after the final `ConvLayer` and before pooling.
The wrapper readout reproduces the official softplus, mean pooling and fully connected layers.
`recursive=True` adds a trainable `hidden -> original atom input` linear projection.
The projection consumes a detached cache; current stage parameters remain trainable.

`ModelConfig` controls atom/edge widths, convolution count and readout capacity.
Default dimensions are 92/41 input, 64 hidden, three convolutions, 128 head width.
Round zero has no seam layer and must pass exact native forward parity in unit tests.
Source and graph construction are independently checked against the fixed upstream code.
