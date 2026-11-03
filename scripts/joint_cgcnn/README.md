# Slurm entry

`run.py cpu-proof|accept|study|task --prepared ROOT --cached ROOT --output ROOT` requires Slurm. Config defaults to `configs/joint_cgcnn/seed123.json`. CPU tests precede proof publication. GPU acceptance checks the largest actual atom-count batch, finite nonzero gradients through both encoders and bridge, native-composition forward agreement, memory headroom and short real-label training in a diagnostic tree. Production requires unchanged source/config/code/proof and uses memory-limited independent property subprocesses sharing one GPU. Resume reruns completed tasks safely and preserves earlier pool ledgers.

Study outputs: `outputs/joint_cgcnn/seed123-double-v1/{run,pool,reports,diagnostics}`. No existing experiment or environment is modified.
