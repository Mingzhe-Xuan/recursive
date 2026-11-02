#!/usr/bin/env bash
#SBATCH --job-name=residual-study
#SBATCH --partition=compute
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=outputs/residual_scaling/logs/study-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
legacy="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123-final}"
study="${RESIDUAL_WORK_ROOT:-$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib" XDG_CACHE_HOME="$runtime/cache"
"$runtime/venv/bin/python" scripts/self_evolution/inspect_environment.py --gpu \
    --output "$study/environments/study-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" scripts/residual_scaling/dispatch.py \
    --prepared "$legacy/prepared" --legacy "$legacy/run" --output "$study" --max-workers 4
