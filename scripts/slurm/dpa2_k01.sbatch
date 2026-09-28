#!/usr/bin/env bash
#SBATCH --job-name=dpa2-k01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
cd "${PROJECT_DIR}"
RUNTIME_ROOT="${RECURSIVE_RUNTIME_ROOT:-/dev/shm/xmz-recursive}"
source "${RUNTIME_ROOT}/envs/dpa2/bin/activate"
mkdir -p results/dpa2
mkdir -p "${RUNTIME_ROOT}/cache/xdg" "${RUNTIME_ROOT}/cache/torch" "${RUNTIME_ROOT}/cache/huggingface"

: "${OPENLAM_CHECKPOINT:?set OPENLAM_CHECKPOINT to OpenLAM_2.1.0_27heads_2024Q1.pt}"
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export XDG_CACHE_HOME="${RUNTIME_ROOT}/cache/xdg"
export TORCH_HOME="${RUNTIME_ROOT}/cache/torch"
export HF_HOME="${RUNTIME_ROOT}/cache/huggingface"
srun python scripts/validate_dpa2_k01.py \
  --checkpoint "${OPENLAM_CHECKPOINT}" \
  --head Domains_SSE-PBE \
  --output "results/dpa2/k01-${SLURM_JOB_ID}.json"
