# Existing-run correction diagnostics

`run.py --study ROOT --prepared ROOT --output NEW_ROOT` requires Slurm and uses the existing CGCNN virtual environment. Inputs are completed `residual_scaling` reports, caches, legacy checkpoint hashes and histories. Outputs are new summaries, per-validation-material correction records, and figures. No model inference, optimization, test-label evaluation or mutation of the completed study is performed. The input summary and analysis implementation are pinned by `protocol.json`; changes require a new output directory.
