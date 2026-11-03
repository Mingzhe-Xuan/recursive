# Recursive correction diagnostics

Read-only analysis of completed three-arm CGCNN rounds 0–2. This separate package preserves the hashes of both existing training packages.

`metrics.py` defines parent residual `e=y-F_previous`, correction `delta=F_current-F_previous`, Pearson/Spearman/uncentered alignment, per-material absolute-error improvements, calibration and exact MSE benefit decomposition. Constant-vector correlations are `null`. Improvement ties use absolute tolerance `1e-8` in original property units. A diagnostic least-squares multiplier is reported without applying it or changing any prediction.

`analysis.py` consumes audited task splits, existing full-library paired archives and histories, then writes train/validation residual and correction summaries plus learning curves. Only train and validation labels are accessed. The full cache is integrity-checked by streaming shards; no model training or inference is needed. Outputs are new task-specific generated artifacts.

Best-checkpoint cached predictions use eval mode and support comparable train/validation MAE and RMSE. Historical training MSE is an online average while parameters and BatchNorm changed during an epoch; historical validation is eval MAE. Curves stay in separate panels, with their original metric labels. Intermediate checkpoints are unavailable, so per-epoch eval training MAE cannot be reconstructed. No test labels, new tuning, or claims of independent validation are introduced.
