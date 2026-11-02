# Residual validation entry points

run.py prepare/run/verify/summarize accepts --prepared, --legacy, --output and base/study
JSON configurations. CUDA operations require Slurm and the pinned existing environment.
Use a separate output root; do not resume the legacy rounds-0..5 job or release held893.
The study is described in [the plan](../../docs/plan/residual_scaling_validation.md).
# Real GPU acceptance and dispatch

`accept.py --prepared PATH --output PATH` checks four short residual stages on real structures, full-library paired caches and recomputed chains. It writes `acceptance.json` only after both variants pass; its diagnostic checkpoints never enter the main comparison.

`dispatch.py --prepared PATH --legacy PATH --output PATH` requires Slurm, matching old resource measurements and current residual GPU acceptance. It runs eight independent branches, at most four simultaneously on one GPU, then publishes validated reports. Each branch is restartable; old experiment files remain read only.
