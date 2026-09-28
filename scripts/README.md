# Experiment scripts

`validate_mattersim_k01.py` is the first real-checkpoint acceptance test. It downloads/loads the
official 1M checkpoint through MatterSim, constructs one periodic silicon graph with the official
dataloader, and verifies:

- wrapper K=0 versus the raw M3GNet forward under explicit tolerances;
- full-backbone K=1 with atom/edge norm alignment is finite;
- model parameters and buffers stay unchanged and the model remains in eval mode;
- checkpoint hash, versions, energies, tolerances, and alignment scales are written to JSON.

Run compute only via Slurm:

```bash
sbatch scripts/slurm/mattersim_k01.sbatch
```

The submission directory must contain `.venv-mattersim` with the project and the `mattersim`
optional dependency installed. Cluster-specific partition/account directives may be supplied to
`sbatch`; they are intentionally not hard-coded before cluster inspection.

`validate_mace_k01.py` applies the same acceptance pattern to the official MACE-MP-0 small L=0
checkpoint in float64. It uses the official calculator graph conversion, verifies raw
`ScaleShiftMACE` energy against wrapper K=0, then runs full-backbone K=1. Submit it with
`scripts/slurm/mace_k01.sbatch` from an environment installed with the `mace` optional dependency.
