#!/usr/bin/env bash
#SBATCH --job-name=recursive-diagnostics
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=outputs/recursive_diagnostics/logs/analyze-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/self_evolution/runtime/cgcnn-seed123"
legacy="$PWD/outputs/self_evolution/jarvis2021-seed123-final"
study="$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1"
diagnostic="${DIAGNOSTIC_ROOT:-$PWD/outputs/recursive_diagnostics/cgcnn-seed123-r012-v1}"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib"
mkdir -p "$diagnostic/test-tmp"
"$runtime/venv/bin/python" -m pytest tests/recursive_diagnostics \
    -p no:cacheprovider --basetemp "$diagnostic/test-tmp/job-${SLURM_JOB_ID}"
"$runtime/venv/bin/python" scripts/recursive_diagnostics/run.py \
    --study "$study" --prepared "$legacy/prepared" --output "$diagnostic"
