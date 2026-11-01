#!/usr/bin/env bash
#SBATCH --job-name=cgcnn-prepare
#SBATCH --partition=compute
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=outputs/self_evolution/logs/prepare-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
runtime="${CGCNN_RUNTIME_ROOT:-$PWD/outputs/self_evolution/runtime/cgcnn-seed123}"
work="${CGCNN_WORK_ROOT:-$PWD/outputs/self_evolution/jarvis2021-seed123}"
python_bin="$runtime/venv/bin/python"
test -f "$runtime/manifests/SETUP_COMPLETE"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$work/downloads"
export ALL_PROXY="${CGCNN_PROXY:-socks5h://127.0.0.1:1080}"
export HTTP_PROXY="$ALL_PROXY" HTTPS_PROXY="$ALL_PROXY"
# urllib does not implement SOCKS. curl downloads the fixed artifact; Python verifies its MD5/size.
archive="$work/downloads/jdft_3d-8-18-2021.json.zip"
if [[ ! -f "$archive" ]]; then
    curl --proxy "$ALL_PROXY" --connect-timeout 15 --max-time 900 --retry 3 \
        --retry-delay 2 --fail --location --continue-at - \
        --output "$archive.partial" https://api.figshare.com/v2/file/download/29204826
    "$python_bin" -c 'import hashlib,sys; p=sys.argv[1]; b=open(p,"rb").read(); assert len(b)==31911815 and hashlib.md5(b).hexdigest()=="8f619035a2cd8030de1ce38ce8b561b2"' "$archive.partial"
    mv "$archive.partial" "$archive"
fi
"$python_bin" scripts/self_evolution/run.py prepare --archive "$archive" \
    --prepared "$work/prepared" --workers "${SLURM_CPUS_PER_TASK:-8}"
