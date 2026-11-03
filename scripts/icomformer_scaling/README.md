# iComformer study entry

`bootstrap.py` creates an independent task venv and downloads fixed PyPI wheels through an explicit SOCKS proxy; it is a lightweight login-node operation. Slurm check installs them offline inside that venv without modifying shared Torch/PyG/scatter or the CGCNN environment. `run.py check --output PATH` records and enforces the actual runtime and requires Jarvis to resolve within the new venv, avoiding a conflicting Python2 namespace in the shared site-packages.

`run.py prepare --archive ZIP --old-prepared ROOT --prepared NEW_ROOT` constructs official invariant graphs from the exact original library and existing task splits. All actions require Slurm. Checkpoint training/cache/report actions are added after source/geometry acceptance. All output paths must be independent of completed CGCNN results.
