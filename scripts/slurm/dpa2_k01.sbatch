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
source .venv-dpa2/bin/activate
mkdir -p results/dpa2

: "${OPENLAM_CHECKPOINT:?set OPENLAM_CHECKPOINT to OpenLAM_2.1.0_27heads_2024Q1.pt}"
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
srun python scripts/validate_dpa2_k01.py \
  --checkpoint "${OPENLAM_CHECKPOINT}" \
  --head Domains_SSE-PBE \
  --output "results/dpa2/k01-${SLURM_JOB_ID}.json"
