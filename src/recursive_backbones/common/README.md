# Common recursive execution

This module defines the model-independent contract used by all backbone wrappers.

Inputs are a model-specific batch plus a complete `DynamicState`. Each state component is a
two-dimensional `[items, packed_features]` tensor with per-item structure indices, masks, and an
explicit packed-irrep specification. Model wrappers own all conversion between native tensors and
this representation.

`run_segment_cycles` executes a half-open block interval `[start, stop)` once natively and then
`repeats` additional times. `run_layerwise` applies independent repeat counts per block. Both leave
geometry construction, native blocks, and readout in the model wrapper.

The executor never trains or mutates a backbone. Use `freeze_module`, `snapshot_frozen`, and
`assert_frozen_unchanged` around integration runs.

