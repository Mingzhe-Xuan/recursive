# iComformer study entry

`bootstrap.py` creates an independent venv and verifies pinned offline wheels. Slurm `check` installs these and the local project without changing CGCNN dependencies. `run.py check` asserts the actual Jarvis import is inside this venv. All model/data/diagnostic actions require Slurm.

`run.py prepare --archive ZIP --old-prepared ROOT --prepared NEW_ROOT` builds the exact invariant graph library, reusing only the old IDs, labels and splits. Every one of 55,712 structures must succeed.

`probe.py --prepared ROOT --output JSON` measures native and projected float32 forward/backward on the batches with most edges and atoms. A smaller proposed batch must be adopted in the committed configuration before acceptance. `accept.py --prepared ROOT --old-prepared ROOT --work ROOT` checks native GPU outputs/gradients and seven short diagnostic stages with complete whole-library node/prediction archives. Diagnostic weights never enter production.

`dispatch.py --prepared ROOT --old-prepared ROOT --work ROOT --cgcnn-summary JSON` requires matching source/config/graphs/resource acceptance and shares the allocation among 1–4 independent property chains according to measured memory. `run.py run --task NAME --output ROOT` executes direct R0–2 and both residual R1–2 arms with matched direct update budgets. Whole-epoch checkpoints resume Adam and RNG state. `run.py summarize` verifies complete coverage and creates MAE/updates/parameter plots, CGCNN comparison, correction correlations, material improvements and train/validation residual diagnostics. Partial runs are explicitly incomplete.

Config: `configs/icomformer_scaling/seed123.json`. Outputs: `outputs/icomformer_scaling/jarvis2021-seed123-r012-v1`. Existing CGCNN outputs and paused jobs are independent.
