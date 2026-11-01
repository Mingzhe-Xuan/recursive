# Stage training

`train_stage` receives an immutable protocol, task labels/splits, `GraphStore` and optional
previous-stage `FeatureStore`. It trains a fresh CGCNN and seam using training-only target mean
and sample standard deviation, normalized MSE and constant-rate Adam.
Validation MAE in original units chooses `best.pt`; no test evaluation occurs during training.
`last.pt` saves optimizer, RNG, completed epoch, step count, elapsed time and history for resume.
Interrupted epochs replay from the last complete epoch. A final singleton graph is merged into
the previous training batch, preserving all samples and node BatchNorm requirements.

The output includes `training.json`, full history, checkpoint SHA-256 and parameter count.
`target_steps` disables early stopping and fixes the raw-input cumulative control budget exactly.
`evaluate` uses eval/no_grad and restores original target units; it requires explicit split IDs.
Training refuses changed configuration/inputs at an existing stage path and checks parent identity.
