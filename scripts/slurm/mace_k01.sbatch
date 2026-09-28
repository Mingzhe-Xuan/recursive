#!/usr/bin/env bash
#SBATCH --job-name=mace-k01
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
source .venv-mace/bin/activate
mkdir -p results/mace

export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
srun python scripts/validate_mace_k01.py \
  --device cuda \
  --output "results/mace/k01-${SLURM_JOB_ID}.json"
