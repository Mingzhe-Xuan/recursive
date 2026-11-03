#!/usr/bin/env bash
#SBATCH --job-name=icomformer-accept
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=outputs/icomformer_scaling/logs/accept-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/icomformer_scaling/runtime/seed123"
old="$PWD/outputs/self_evolution/jarvis2021-seed123-final"
work="$PWD/outputs/icomformer_scaling/jarvis2021-seed123-r012-v1"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLCONFIGDIR="$runtime/matplotlib"
"$runtime/venv/bin/python" scripts/self_evolution/inspect_environment.py --gpu \
    --output "$work/environment-accept-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" scripts/icomformer_scaling/accept.py \
    --prepared "$work/prepared" --old-prepared "$old/prepared" --work "$work"
