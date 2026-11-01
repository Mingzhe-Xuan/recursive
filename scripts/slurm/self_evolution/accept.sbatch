#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-real-accept
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --gres=gpu:1
#SBATCH --time=00:15:00
#SBATCH --output=outputs/self_evolution/logs/accept-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib" XDG_CACHE_HOME="$runtime/cache"
"$runtime/venv/bin/python" scripts/self_evolution/accept_real.py \
    --prepared "$work/prepared" --output "$work/run"
