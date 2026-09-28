#!/usr/bin/env bash
#SBATCH --job-name=setup-mace
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
RUNTIME_ROOT="${RECURSIVE_RUNTIME_ROOT:-/dev/shm/xmz-recursive}"
ENV_DIR="${RUNTIME_ROOT}/envs/mace"
WHEELHOUSE="${RECURSIVE_WHEELHOUSE:?set RECURSIVE_WHEELHOUSE}"

cd "${PROJECT_DIR}"
test -d "${WHEELHOUSE}"
test -f "${WHEELHOUSE}/SHA256SUMS"
unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
export PIP_NO_INDEX=1
export PIP_FIND_LINKS="${WHEELHOUSE}"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_CACHE_DIR="${RUNTIME_ROOT}/cache/pip"
export XDG_CACHE_HOME="${RUNTIME_ROOT}/cache/xdg"
export TORCH_HOME="${RUNTIME_ROOT}/cache/torch"
export HF_HOME="${RUNTIME_ROOT}/cache/huggingface"

tr -d '\r' < "${WHEELHOUSE}/SHA256SUMS" | (
  cd "${WHEELHOUSE}"
  sha256sum -c -
)
mkdir -p "${ENV_DIR}" "${PIP_CACHE_DIR}" "${RUNTIME_ROOT}/manifests"

if [[ "${RECURSIVE_RECREATE_ENV:-0}" == "1" ]]; then
  test "${ENV_DIR}" = "${RUNTIME_ROOT}/envs/mace"
  python3 -m venv --clear "${ENV_DIR}"
elif [[ ! -x "${ENV_DIR}/bin/python" ]]; then
  python3 -m venv "${ENV_DIR}"
fi

"${ENV_DIR}/bin/python" -m pip install \
  --no-index --find-links "${WHEELHOUSE}" \
  "${WHEELHOUSE}/PySocks-1.7.1-py3-none-any.whl" \
  "setuptools>=69" \
  wheel
"${ENV_DIR}/bin/python" -m pip install \
  --no-index --find-links "${WHEELHOUSE}" \
  --progress-bar off \
  --only-binary=:all: \
  mace-torch==0.3.16
"${ENV_DIR}/bin/python" -m pip install \
  --no-index --find-links "${WHEELHOUSE}" \
  --progress-bar off \
  --no-build-isolation \
  --no-deps \
  -e "${PROJECT_DIR}"
"${ENV_DIR}/bin/python" -m pip check
"${ENV_DIR}/bin/python" -c "from importlib.metadata import version; import torch; print(version('mace-torch')); print(version('e3nn')); print(torch.__version__)"
"${ENV_DIR}/bin/python" -m pip freeze > "${RUNTIME_ROOT}/manifests/mace-freeze.txt"
