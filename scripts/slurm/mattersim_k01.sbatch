#!/usr/bin/env bash
#SBATCH --job-name=mattersim-k01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
cd "${PROJECT_DIR}"
RUNTIME_ROOT="${RECURSIVE_RUNTIME_ROOT:-/dev/shm/xmz-recursive}"
CHECKPOINT="${MATTERSIM_CHECKPOINT:-${RUNTIME_ROOT}/checkpoints/mattersim/mattersim-v1.0.0-1M.pth}"
source "${RUNTIME_ROOT}/envs/mattersim/bin/activate"
test -s "${CHECKPOINT}"
mkdir -p logs results/mattersim
mkdir -p "${RUNTIME_ROOT}/cache/xdg" "${RUNTIME_ROOT}/cache/torch" "${RUNTIME_ROOT}/cache/huggingface"

export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export XDG_CACHE_HOME="${RUNTIME_ROOT}/cache/xdg"
export TORCH_HOME="${RUNTIME_ROOT}/cache/torch"
export HF_HOME="${RUNTIME_ROOT}/cache/huggingface"
srun python scripts/validate_mattersim_k01.py \
  --checkpoint "${CHECKPOINT}" \
  --device cuda \
  --output "results/mattersim/k01-${SLURM_JOB_ID}.json"
