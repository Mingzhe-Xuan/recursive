#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-report
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=outputs/self_evolution/logs/report-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123}"
export MPLCONFIGDIR="$runtime/matplotlib"
"$runtime/venv/bin/python" scripts/self_evolution/run.py summarize --output "$work/run"
