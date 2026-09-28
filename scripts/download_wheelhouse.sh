#!/usr/bin/env bash

set -euo pipefail

WHEELHOUSE="${1:?usage: download_wheelhouse.sh WHEELHOUSE_DIR}"
URL_MANIFEST="${WHEELHOUSE}/PYPI_URLS"
CHECKSUM_MANIFEST="${WHEELHOUSE}/SHA256SUMS"
EXPECTED_COUNT="${RECURSIVE_WHEEL_COUNT:-144}"
CURL_RETRIES="${RECURSIVE_CURL_RETRIES:-100}"
CURL_RETRY_MAX_TIME="${RECURSIVE_CURL_RETRY_MAX_TIME:-7200}"
CURL_SPEED_LIMIT="${RECURSIVE_CURL_SPEED_LIMIT:-128}"
CURL_SPEED_TIME="${RECURSIVE_CURL_SPEED_TIME:-120}"

test -d "${WHEELHOUSE}"
test -f "${URL_MANIFEST}"
test -f "${CHECKSUM_MANIFEST}"

completed=0
while read -r expected_hash filename url; do
  expected_hash="${expected_hash%$'\r'}"
  filename="${filename%$'\r'}"
  url="${url%$'\r'}"
  [[ "${expected_hash}" =~ ^[0-9a-f]{64}$ ]]
  [[ -n "${filename}" && "${filename}" != */* ]]
  [[ -n "${url}" ]]

  destination="${WHEELHOUSE}/${filename}"
  partial="${destination}.partial"
  if [[ -f "${destination}" ]] && printf '%s  %s\n' "${expected_hash}" "${destination}" | sha256sum -c - >/dev/null 2>&1; then
    completed=$((completed + 1))
    continue
  fi

  echo "downloading ${filename}"
  curl \
    --fail \
    --location \
    --silent \
    --show-error \
    --retry "${CURL_RETRIES}" \
    --retry-all-errors \
    --retry-delay 1 \
    --retry-max-time "${CURL_RETRY_MAX_TIME}" \
    --connect-timeout 15 \
    --speed-limit "${CURL_SPEED_LIMIT}" \
    --speed-time "${CURL_SPEED_TIME}" \
    --continue-at - \
    --output "${partial}" \
    "${url}"
  printf '%s  %s\n' "${expected_hash}" "${partial}" | sha256sum -c - >/dev/null
  mv -f "${partial}" "${destination}"
  completed=$((completed + 1))
done < "${URL_MANIFEST}"

if [[ "${completed}" -ne "${EXPECTED_COUNT}" ]]; then
  echo "expected ${EXPECTED_COUNT} verified wheels, found ${completed}" >&2
  exit 1
fi

tr -d '\r' < "${CHECKSUM_MANIFEST}" > "${CHECKSUM_MANIFEST}.lf"
(
  cd "${WHEELHOUSE}"
  sha256sum -c "$(basename "${CHECKSUM_MANIFEST}.lf")"
)
