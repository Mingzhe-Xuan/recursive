#!/usr/bin/env bash
#SBATCH --job-name=download-mattersim-wheels
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=12:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR}"
WHEELHOUSE="${RECURSIVE_WHEELHOUSE:?set RECURSIVE_WHEELHOUSE}"

cd "${PROJECT_DIR}"
unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
test -f "${WHEELHOUSE}/PYPI_URLS"
read -r _ _ probe_url < "${WHEELHOUSE}/PYPI_URLS"
probe_url="${probe_url%$'\r'}"
curl --head --fail --silent --show-error --max-time 15 "${probe_url}"
bash scripts/download_wheelhouse.sh "${WHEELHOUSE}"
