# Validation and correction reports

`summarize` requires every property/branch/round, verifies checkpoint and full archive hashes/coverage, actual update budgets, residual seeds and frozen normalization, and emits validation CSV/JSON and round/update curves. Missing branches remain explicit instead of being filled with zero. Existing reports are preserved before replacement.

When complete, the generic `recursive_diagnostics` analyzer is called with an explicit iComformer implementation identity. It produces train/validation cached MAE/RMSE, material correction records/correlations and original-metric learning curves without inference or test labels. The optional CGCNN comparison reports actual parameters and updates, acknowledging different native geometry and early-stop budgets; it does not claim a pure parameter-count ablation.
