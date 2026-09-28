# MatterSim wrapper

Target checkpoint: `MatterSim-v1.0.0-1M`.

The wrapper must expose each M3GNet `MainBlock` while carrying atom and edge features together.
Geometry, graph indices, periodic offsets, basis values, and masks remain fixed during one recursive
forward. K=0 must reproduce the official predictor before K=1 is accepted.

`MatterSimM3GNetWrapper` mirrors the official M3GNet forward preamble, exposes every
`graph_conv` block, and uses MatterSim's own `scatter_sum` by default. The wrapped state is:

- `atom`: `[num_atoms, units]`, scalar `(ell=0, parity=+1)` with multiplicity `units`;
- `edge`: `[num_edges, units]`, scalar `(ell=0, parity=+1)` with multiplicity `units`.

The fixed context contains graph indices, periodic offsets after displacement construction,
radial/spherical bases, edge lengths, and per-structure counts. Instantiate the wrapper with the
raw `M3Gnet` module (not the higher-level potential object), freeze it with the common freeze
utility, and call the common segment or layer-wise executor.

The local fake-model integration test checks exact K=0 path parity and finite K=1 execution. A
real-checkpoint CUDA acceptance run remains mandatory through Slurm before the integration is
considered complete.
