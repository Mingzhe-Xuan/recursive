# Submit joint CGCNN

Create `outputs/joint_cgcnn/logs`, then submit `check.sbatch`, `accept.sbatch --dependency=afterok:CHECK_ID`, and `study.sbatch --dependency=afterok:ACCEPT_ID` (sbatch options precede the script path). Check is CPU-only and may run while iComformer owns the GPU. Both GPU jobs queue normally and never preempt other jobs. Acceptance failure prevents training.

The scripts use the existing CGCNN task venv read-only, with no dependency installation or rebuild. Study allocates one GPU,16 CPUs,64GiB,2-day walltime; all four properties can share that allocation subject to measured peak memory. Adam300/patience50 and batch64 are fixed. Results are compared to completed cached R1 after all properties finish.
