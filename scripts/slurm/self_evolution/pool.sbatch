#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-pool
#SBATCH --partition=compute
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=21-00:00:00
#SBATCH --output=outputs/self_evolution/logs/pool-%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123-final}"
test -f "$runtime/manifests/SETUP_COMPLETE"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export MPLCONFIGDIR="$runtime/matplotlib" XDG_CACHE_HOME="$runtime/cache"
"$runtime/venv/bin/python" scripts/self_evolution/inspect_environment.py --gpu \
    --output "$work/run/environments/pool-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" scripts/self_evolution/execution_pool.py \
    --prepared "$work/prepared" --output "$work/run" \
    --wave-index "${SLURM_ARRAY_TASK_ID:?}" --max-workers 4
