# CGCNN Sequential Self-Evolution

This package implements [plan_2.md](../../docs/plan/plan_2.md) for CGCNN, seed 123.
It is independent of the older frozen `recursive_backbones` execution mechanism.
Each stage trains a new model and head; stages after zero also train a shared-per-node
linear map from the previous hidden width to the original 92-dimensional atom descriptor.
The previous stage and its float32 node cache are immutable inputs, with no gradient across stages.
Distance features and periodic neighbors are shared; learned node representations evolve.

The pinned 2021 JARVIS archive contains 55,723 raw rows and 55,712 unique structure IDs.
All 29 scalar regression tasks from
the official ALIGNN results table are included, including EFG and effective masses.
The grouped deterministic 80/10/10 split is a project split, not an exact reproduction of
unavailable original paper IDs. Repeated identical IDs/structures are merged with a full audit;
conflicting finite labels are excluded only for the affected task, without choosing one value.
The structure remains in the whole-library feature cache. Duplicate grouping detects same-cell structures up to translation
and permutation, not all possible equivalent lattice bases. Zero labels remain valid.

Use the commands in [scripts](../../scripts/self_evolution/README.md).
Heavy preprocessing, training, caching, evaluation and compilation run through Slurm.
Data, graphs, checkpoints, feature shards and predictions live in ignored `outputs/` directories.
Read every submodule README for its inputs, outputs and integrity guarantees.

The committed protocol trains rounds 0 through 5 with independent initialization, constant-rate
Adam, training-label-only normalization, validation checkpoint selection and no test selection.
Controls retrain on raw inputs and train a raw-input model for exactly the cumulative number
of optimization steps taken by the evolution chain. One seed produces no uncertainty band.
Test evaluation is deferred until the full declared chain exists. Real benchmark completion
requires a complete task coverage report; unit tests and synthetic examples alone are insufficient.
