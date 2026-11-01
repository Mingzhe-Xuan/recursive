# Slurm workflow

`setup.sbatch` creates a dedicated Python venv, pins task dependencies, records package paths
and runs GPU diagnostics plus unit/integration tests. `prepare.sbatch` downloads/checksums the
fixed source and constructs geometry/splits. `task.sbatch` runs one task's stage chain and controls.
`summarize.sbatch` produces reports even if some task jobs failed, preserving incomplete coverage.

Each job runs from SLURM_SUBMIT_DIR. Setup/prepare verify their own proxy/network path.
Default persistent outputs are repository outputs/self_evolution; no unique result is kept only
in /dev/shm. See [submission instructions](../../self_evolution/README.md) for resume conventions.
