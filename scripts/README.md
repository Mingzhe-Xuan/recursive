# Experiment scripts

`download_dataset.py` reads a versioned JSON manifest, resumes an HTTP download into `.partial`,
verifies SHA-256, and atomically publishes the final artifact. If a server ignores Range, it safely
restarts that artifact instead of appending duplicate bytes. Dataset payloads remain outside Git.

`validate_mattersim_k01.py` is the first real-checkpoint acceptance test. It loads the official 1M
checkpoint from an explicit task-local path, constructs one periodic silicon graph with the official
dataloader, and verifies:

- wrapper K=0 versus the raw M3GNet forward under explicit tolerances;
- full-backbone K=1 with atom/edge norm alignment is finite;
- model parameters and buffers stay unchanged and the model remains in eval mode;
- checkpoint hash, versions, energies, tolerances, and alignment scales are written to JSON.

Run compute only via Slurm:

```bash
sbatch --nodelist=node221 scripts/slurm/download_mattersim_checkpoint.sbatch
sbatch --nodelist=node221 scripts/slurm/mattersim_k01.sbatch
```

The download job writes atomically to
`/dev/shm/xmz-recursive/checkpoints/mattersim/mattersim-v1.0.0-1M.pth` and prints its size and
SHA-256. The inference job uses the MatterSim environment under
`/dev/shm/xmz-recursive/envs/mattersim`; override the common root with `RECURSIVE_RUNTIME_ROOT` or
the checkpoint itself with `MATTERSIM_CHECKPOINT`. Both jobs must target the node that owns the
node-local runtime directory.

`validate_mace_k01.py` applies the same acceptance pattern to the official MACE-MP-0 small L=0
checkpoint in float64. It uses the official calculator graph conversion, verifies raw
`ScaleShiftMACE` energy against wrapper K=0, then runs full-backbone K=1. Submit it with
`scripts/slurm/mace_k01.sbatch` from an environment installed with the `mace` optional dependency.
