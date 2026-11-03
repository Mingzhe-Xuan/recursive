# iComformer Slurm stages

Create the task venv and pinned wheelhouse with `scripts/icomformer_scaling/bootstrap.py`, then create `outputs/icomformer_scaling/logs`. All compute runs in Slurm:

1. `sbatch scripts/slurm/icomformer_scaling/check.sbatch`: offline independent environment install and native/chain CPU tests.
2. `sbatch --dependency=afterok:CHECK_ID scripts/slurm/icomformer_scaling/prepare.sbatch`: all 55,712 native graphs, no discarded failures.
3. `sbatch --dependency=afterok:PREPARE_ID scripts/slurm/icomformer_scaling/probe.sbatch`: actual worst-batch GPU memory measurement. Adopt a smaller batch in local committed config if needed before continuing.
4. `sbatch scripts/slurm/icomformer_scaling/accept.sbatch`: native GPU/gradient and seven-stage whole-library cache acceptance in a separate diagnostic tree.
5. `sbatch --dependency=afterok:ACCEPT_ID scripts/slurm/icomformer_scaling/study.sbatch`: validated four-property production R0–2, automatic summary/CGCNN comparison/correction diagnostics.

Root: `outputs/icomformer_scaling/jarvis2021-seed123-r012-v1`; independent venv: `outputs/icomformer_scaling/runtime/seed123/venv`. Study allocates one GPU, 16 CPUs, 64 GiB; worker count is limited by measured memory and CPU allocation. The 21-day walltime is a ceiling, not a training budget change. Config/code/graph identities are locked; acceptance failure prevents production. No old CGCNN training or held reporting job is resumed.
