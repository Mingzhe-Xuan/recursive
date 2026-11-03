#!/usr/bin/env bash
#SBATCH --job-name=icomformer-check
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:20:00
#SBATCH --output=outputs/icomformer_scaling/logs/check-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/self_evolution/runtime/cgcnn-seed123"
work="$PWD/outputs/icomformer_scaling/jarvis2021-seed123-r012-v1"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$runtime/matplotlib"
mkdir -p "$work/diagnostics"
"$runtime/venv/bin/python" scripts/icomformer_scaling/run.py check \
    --output "$work/environment-cpu-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" -m pytest tests/icomformer_scaling \
    -p no:cacheprovider --basetemp "$work/diagnostics/check-${SLURM_JOB_ID}"
