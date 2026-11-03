#!/usr/bin/env bash
#SBATCH --job-name=icomformer-probe
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=outputs/icomformer_scaling/logs/probe-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="$PWD/outputs/icomformer_scaling/runtime/seed123"
work="$PWD/outputs/icomformer_scaling/jarvis2021-seed123-r012-v1"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PIP_REQUIRE_VIRTUALENV=true PIP_CONFIG_FILE=/dev/null PIP_CACHE_DIR="$runtime/pip-cache"
"$runtime/venv/bin/python" -m pip install --no-deps --no-build-isolation -e .
"$runtime/venv/bin/python" scripts/self_evolution/inspect_environment.py --gpu \
    --output "$work/environment-probe-${SLURM_JOB_ID}.json"
"$runtime/venv/bin/python" scripts/icomformer_scaling/probe.py \
    --prepared "$work/prepared" --output "$work/resource_probe.json"
