#!/usr/bin/env bash
#SBATCH --job-name=residual-accept
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=outputs/residual_scaling/logs/accept-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
legacy="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123-final}"
study="${RESIDUAL_WORK_ROOT:-$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib" XDG_CACHE_HOME="$runtime/cache"
"$runtime/venv/bin/python" scripts/residual_scaling/run.py prepare \
    --prepared "$legacy/prepared" --legacy "$legacy/run" --output "$study"
"$runtime/venv/bin/python" scripts/residual_scaling/accept.py \
    --prepared "$legacy/prepared" --output "$study"
