#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-pool-check
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=outputs/self_evolution/logs/pool-check-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123-final}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$runtime/matplotlib"
"$runtime/venv/bin/python" -m pytest tests/self_evolution -p no:cacheprovider \
    --basetemp "$work/diagnostics/pool-check-${SLURM_JOB_ID}"
