# Matched-budget residual validation

Independent package for CGCNN seed123, four properties, rounds 0..2. The paused legacy
experiment remains read-only and its scientific source identity is not changed. Protocol:
[residual_scaling_validation.md](../../docs/plan/residual_scaling_validation.md).

Inputs are the audited prepared graph/task store, legacy run and base/study JSON configs.
Outputs are paired full-library node/prediction archives, resumable residual checkpoints,
validation-only reports and compute records in a separate output root. No test evaluation.
