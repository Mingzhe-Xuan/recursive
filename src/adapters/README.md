# Adapters

The only Goal 1 seam adapter is `IrrepNormAligner`.

It computes an RMS independently for every structure, dynamic-state component, and declared
irrep block. A single scalar is shared by every multiplicity channel and every magnetic component
inside the block. Padding and masked items do not contribute. The adapter has no parameters and
never reads labels or dataset-level statistics.

