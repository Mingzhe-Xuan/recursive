#!/usr/bin/env bash
#SBATCH --job-name=probe-runtime
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --mem=1G
#SBATCH --time=00:02:00
#SBATCH --output=results/probes/network-latest.out

set -euo pipefail

PROXY_PORT="${RECURSIVE_PROXY_PORT:?set RECURSIVE_PROXY_PORT for the active keeper}"
PROXY_URL="socks5h://127.0.0.1:${PROXY_PORT}"

hostname
df -hT /dev/shm
test -w /dev/shm
curl --fail --silent --show-error --max-time 15 --proxy "${PROXY_URL}" https://api.ipify.org
printf "\n"
