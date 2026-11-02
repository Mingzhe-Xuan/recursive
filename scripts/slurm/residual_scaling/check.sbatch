#!/usr/bin/env bash
#SBATCH --job-name=residual-check
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=outputs/residual_scaling/logs/check-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
study="${RESIDUAL_WORK_ROOT:-$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$runtime/matplotlib"
mkdir -p "$study/diagnostics"
"$runtime/venv/bin/python" -m pytest tests/self_evolution tests/residual_scaling \
    -p no:cacheprovider --basetemp "$study/diagnostics/cpu-${SLURM_JOB_ID}"
