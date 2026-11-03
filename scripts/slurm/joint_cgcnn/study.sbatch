#!/usr/bin/env bash
#SBATCH --job-name=joint-cgcnn-study
#SBATCH --partition=compute
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=outputs/joint_cgcnn/logs/study-%j.out
#SBATCH --gres=gpu:1
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/self_evolution/runtime/cgcnn-seed123"
prepared="$PWD/outputs/self_evolution/jarvis2021-seed123-final/prepared"
cached="$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1"
work="$PWD/outputs/joint_cgcnn/seed123-double-v1"
export CUBLAS_WORKSPACE_CONFIG=:4096:8 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib"
"$runtime/venv/bin/python" scripts/self_evolution/inspect_environment.py --gpu --output "$work/environment-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" scripts/joint_cgcnn/run.py study \
    --prepared "$prepared" --cached "$cached" --output "$work"
