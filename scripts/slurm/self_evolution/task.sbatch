#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-evolution
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --gres=gpu:1
#SBATCH --time=7-00:00:00
#SBATCH --output=outputs/self_evolution/logs/task-%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123}"
python_bin="$runtime/venv/bin/python"
test -f "$runtime/manifests/SETUP_COMPLETE"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8
arguments=(--prepared "$work/prepared" --output "$work/run" --device cuda)
if [[ -n "${CGCNN_TASK:-}" ]]; then
    arguments+=(--task "$CGCNN_TASK")
else
    arguments+=(--task-index "${SLURM_ARRAY_TASK_ID:?}")
fi
if [[ -n "${CGCNN_STOP_ROUND:-}" ]]; then
    arguments+=(--stop-round "$CGCNN_STOP_ROUND")
fi
if [[ "${CGCNN_NO_CONTROLS:-0}" == 1 ]]; then
    arguments+=(--no-controls)
fi
"$python_bin" scripts/self_evolution/run.py run "${arguments[@]}"
if [[ -z "${CGCNN_STOP_ROUND:-}" && "${CGCNN_NO_CONTROLS:-0}" != 1 ]]; then
    "$python_bin" scripts/self_evolution/run.py evaluate "${arguments[@]}"
fi
