# Joint CGCNN control

Two independently initialized native three-layer CGCNN encoders with a node-wise 64-to-92 linear bridge. Only the last encoder has a readout. All registered parameters receive gradients; no cache or detach is used at the bridge. New outputs are isolated from completed cached experiments and iComformer.

Modules: `model` defines the network, `training` implements recoverable Adam/validation selection, `study` verifies old experiment provenance and produces validation comparisons. See each module README.
