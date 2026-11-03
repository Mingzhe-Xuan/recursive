#!/usr/bin/env bash
#SBATCH --job-name=icomformer-prepare
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=outputs/icomformer_scaling/logs/prepare-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/icomformer_scaling/runtime/seed123"
old="$PWD/outputs/self_evolution/jarvis2021-seed123-final"
work="$PWD/outputs/icomformer_scaling/jarvis2021-seed123-r012-v1"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
"$runtime/venv/bin/python" scripts/icomformer_scaling/run.py prepare \
    --archive "$old/downloads/jdft_3d-8-18-2021.json.zip" \
    --old-prepared "$old/prepared" --prepared "$work/prepared"
