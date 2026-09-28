# MACE wrapper

Target checkpoint: official `MACE-MP-0 small`.

A logical block is an interaction/product pair. Native irreps must be converted to explicit packed
`IrrepBlock` entries without reordering magnetic components. Geometry and edge bases remain fixed.

`MACEMP0SmallWrapper` targets the released L=0 small checkpoint. Its node state is one even-scalar
irrep type with multiplicity equal to the channel count, so every interaction/product pair is
width- and type-compatible with recursive execution. Each block stores its latest feature output
in the per-forward context because native MACE applies a readout to every layer and sums those
contributions.

The wrapper reproduces the `ScaleShiftMACE` energy path: atomic baseline, optional pair repulsion,
per-layer readouts, scale/shift, and graph aggregation. It deliberately rejects LAMMPS mode, joint
embeddings, and any checkpoint whose blocks change the node-state width. Those variants require a
separate interface audit rather than silent padding or truncation.

Local fake-model tests cover K=0 parity and finite K=1. The official small checkpoint remains a
Slurm acceptance requirement.
