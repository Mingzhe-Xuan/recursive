#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-setup
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=outputs/self_evolution/logs/setup-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
mkdir -p "$runtime/manifests" "$runtime/pip-cache"
if [[ ! -x "$runtime/venv/bin/python" ]]; then
    python3 -m venv --system-site-packages "$runtime/venv"
fi
python_bin="$runtime/venv/bin/python"
rm -f "$runtime/manifests/SETUP_COMPLETE"
export PIP_REQUIRE_VIRTUALENV=true
export PIP_CACHE_DIR="$runtime/pip-cache"
if [[ -n "${CGCNN_WHEELHOUSE:-}" ]]; then
    (cd "$CGCNN_WHEELHOUSE" && sha256sum -c SHA256SUMS)
    "$python_bin" -m pip install --no-index --find-links "$CGCNN_WHEELHOUSE" \
        numpy==1.26.4 pymatgen==2024.5.1 matplotlib==3.9.4 pytest==8.3.5
else
export ALL_PROXY="${CGCNN_PROXY:-socks5h://127.0.0.1:1080}"
export HTTP_PROXY="$ALL_PROXY" HTTPS_PROXY="$ALL_PROXY"
curl --proxy "$ALL_PROXY" --connect-timeout 10 --max-time 25 --fail --silent \
    --output /dev/null https://pypi.org/simple/numpy/
if ! "$python_bin" -m pip show PySocks >/dev/null 2>&1; then
    bootstrap="$runtime/PySocks-1.7.1-py3-none-any.whl"
    curl --proxy "$ALL_PROXY" --connect-timeout 10 --max-time 90 --fail --location \
        --output "$bootstrap.partial" \
        https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl
    echo "2725bd0a9925919b9b51739eea5f9e2bae91e83288108a9ad338b2e3a4435ee5  $bootstrap.partial" | sha256sum -c -
    mv "$bootstrap.partial" "$bootstrap"
    "$python_bin" -m pip install --no-index "$bootstrap"
fi
"$python_bin" -m pip install --only-binary=:all: --timeout 30 --retries 2 \
    numpy==1.26.4 pymatgen==2024.5.1 matplotlib==3.9.4 pytest==8.3.5
fi
# Install source without modifying inherited user packages or asking a resolver to replace torch.
"$python_bin" -m pip install --no-deps --no-build-isolation -e .
"$python_bin" -m pip freeze --all > "$runtime/manifests/freeze.txt"
"$python_bin" scripts/self_evolution/inspect_environment.py --output "$runtime/manifests/environment.json" --gpu
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
"$python_bin" -m pytest tests/self_evolution -p no:cacheprovider \
    --basetemp "$runtime/pytest" -q
touch "$runtime/manifests/SETUP_COMPLETE"
