#!/usr/bin/env bash
#SBATCH --job-name=joint-cgcnn-check
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=outputs/joint_cgcnn/logs/check-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/self_evolution/runtime/cgcnn-seed123"
prepared="$PWD/outputs/self_evolution/jarvis2021-seed123-final/prepared"
cached="$PWD/outputs/residual_scaling/cgcnn-seed123-r012-v1"
work="$PWD/outputs/joint_cgcnn/seed123-double-v1"
export CUBLAS_WORKSPACE_CONFIG=:4096:8 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export MPLCONFIGDIR="$runtime/matplotlib"
"$runtime/venv/bin/python" -m pytest tests/joint_cgcnn -p no:cacheprovider --basetemp "$work/diagnostics/cpu-${SLURM_JOB_ID}" -q
"$runtime/venv/bin/python" scripts/joint_cgcnn/run.py cpu-proof \
    --prepared "$prepared" --cached "$cached" --output "$work"
