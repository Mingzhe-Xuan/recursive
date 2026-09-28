#!/usr/bin/env bash
#SBATCH --job-name=download-mattersim-checkpoint
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
RUNTIME_ROOT="${RECURSIVE_RUNTIME_ROOT:-/dev/shm/xmz-recursive}"
CHECKPOINT_DIR="${RUNTIME_ROOT}/checkpoints/mattersim"
CHECKPOINT="${CHECKPOINT_DIR}/mattersim-v1.0.0-1M.pth"
PARTIAL="${CHECKPOINT}.partial"
URL="https://raw.githubusercontent.com/microsoft/mattersim/main/pretrained_models/mattersim-v1.0.0-1M.pth"

cd "${PROJECT_DIR}"
unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
mkdir -p "${CHECKPOINT_DIR}"

if [[ ! -s "${CHECKPOINT}" ]]; then
  curl \
    --fail \
    --location \
    --show-error \
    --continue-at - \
    --retry 100 \
    --retry-all-errors \
    --retry-delay 2 \
    --retry-max-time 7200 \
    --connect-timeout 15 \
    --speed-limit 128 \
    --speed-time 120 \
    --output "${PARTIAL}" \
    "${URL}"
  test -s "${PARTIAL}"
  mv "${PARTIAL}" "${CHECKPOINT}"
fi

test -s "${CHECKPOINT}"
wc -c "${CHECKPOINT}"
sha256sum "${CHECKPOINT}"
