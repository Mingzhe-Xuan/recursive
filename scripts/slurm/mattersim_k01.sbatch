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
source .venv-mattersim/bin/activate
mkdir -p logs results/mattersim

export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
srun python scripts/validate_mattersim_k01.py \
  --checkpoint mattersim-v1.0.0-1m \
  --device cuda \
  --output "results/mattersim/k01-${SLURM_JOB_ID}.json"
