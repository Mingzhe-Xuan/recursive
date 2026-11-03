# Three-arm recursive chain

`run_task` locks a property and trains direct R0–2, then raw-residual R1–2 and feature-residual R1–2. The same R0 is shared and each residual stage matches its corresponding direct stage's actual optimizer updates and initialization seed. Parent features/predictions always come from the same branch; only node features are fed back. R0 training-only normalization stays fixed.

Full-library paired archives reuse the audited generic `residual_scaling.cache` format. Each archive binds model/geometry/task/config/code/parent identity and preserves its original construction time. Caching uses native eval mode and verifies checkpoint/BN/state immutability. `verify_sequence` recomputes actual cumulative chains from raw input and compares both node features and original-unit predictions against cached values under fixed tolerances. Report metadata is compatible with the generic read-only correction diagnostics through an explicit implementation identity.

Task protocols pin the complete new package code and config. Changes after training starts require a separate output root. Completed CGCNN packages, checkpoints and graphs are never changed.
