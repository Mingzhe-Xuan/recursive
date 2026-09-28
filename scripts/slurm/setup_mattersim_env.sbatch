#!/usr/bin/env bash
#SBATCH --job-name=setup-mattersim
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
RUNTIME_ROOT="${RECURSIVE_RUNTIME_ROOT:-/dev/shm/xmz-recursive}"
ENV_DIR="${RUNTIME_ROOT}/envs/mattersim"
WHEELHOUSE="${RECURSIVE_WHEELHOUSE:-}"
PYSOCKS_WHEEL="${RUNTIME_ROOT}/cache/bootstrap/PySocks-1.7.1-py3-none-any.whl"
PIP_SOURCE=()

cd "${PROJECT_DIR}"
export PIP_CACHE_DIR="${RUNTIME_ROOT}/cache/pip"
export XDG_CACHE_HOME="${RUNTIME_ROOT}/cache/xdg"
export TORCH_HOME="${RUNTIME_ROOT}/cache/torch"
export HF_HOME="${RUNTIME_ROOT}/cache/huggingface"
export PIP_DISABLE_PIP_VERSION_CHECK=1

if [[ -n "${WHEELHOUSE}" ]]; then
  test -d "${WHEELHOUSE}"
  test -f "${WHEELHOUSE}/SHA256SUMS"
  unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
  export PIP_NO_INDEX=1
  export PIP_FIND_LINKS="${WHEELHOUSE}"
  PIP_SOURCE=(--no-index --find-links "${WHEELHOUSE}")
  tr -d '\r' < "${WHEELHOUSE}/SHA256SUMS" | (
    cd "${WHEELHOUSE}"
    sha256sum -c -
  )
else
  PROXY_PORT="${RECURSIVE_PROXY_PORT:?set RECURSIVE_PROXY_PORT or RECURSIVE_WHEELHOUSE}"
  PROXY_URL="socks5h://127.0.0.1:${PROXY_PORT}"
  export ALL_PROXY="${PROXY_URL}"
  export HTTP_PROXY="${PROXY_URL}"
  export HTTPS_PROXY="${PROXY_URL}"
fi

mkdir -p \
  "${ENV_DIR}" \
  "${RUNTIME_ROOT}/cache/bootstrap" \
  "${PIP_CACHE_DIR}" \
  "${RUNTIME_ROOT}/manifests"
if [[ -z "${WHEELHOUSE}" ]]; then
  curl --fail --silent --show-error --max-time 15 --proxy "${PROXY_URL}" https://api.ipify.org
fi

if [[ "${RECURSIVE_RECREATE_ENV:-0}" == "1" ]]; then
  test "${ENV_DIR}" = "${RUNTIME_ROOT}/envs/mattersim"
  python3 -m venv --clear "${ENV_DIR}"
elif [[ ! -x "${ENV_DIR}/bin/python" ]]; then
  python3 -m venv "${ENV_DIR}"
fi
if ! "${ENV_DIR}/bin/python" -c "import socks"; then
  if [[ -n "${WHEELHOUSE}" ]]; then
    PYSOCKS_WHEEL="${WHEELHOUSE}/PySocks-1.7.1-py3-none-any.whl"
    test -f "${PYSOCKS_WHEEL}"
  else
    curl --fail --location --proxy "${PROXY_URL}" --output "${PYSOCKS_WHEEL}" \
      https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl
  fi
  "${ENV_DIR}/bin/python" -m pip install "${PYSOCKS_WHEEL}"
fi

"${ENV_DIR}/bin/python" -m pip install \
  "${PIP_SOURCE[@]}" "setuptools>=69" wheel
"${ENV_DIR}/bin/python" -m pip install \
  "${PIP_SOURCE[@]}" \
  --progress-bar off --timeout 120 --retries 5 --only-binary=:all: mattersim==1.2.3
"${ENV_DIR}/bin/python" -m pip install \
  "${PIP_SOURCE[@]}" \
  --progress-bar off --no-build-isolation --no-deps -e "${PROJECT_DIR}"
"${ENV_DIR}/bin/python" -m pip check
"${ENV_DIR}/bin/python" -c "from importlib.metadata import version; import torch; print(version('mattersim')); print(torch.__version__)"
"${ENV_DIR}/bin/python" -m pip freeze > "${RUNTIME_ROOT}/manifests/mattersim-freeze.txt"
