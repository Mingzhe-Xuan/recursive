#!/usr/bin/env bash

set -euo pipefail

SOURCE="${1:?usage: seed_wheelhouse.sh SOURCE_WHEELHOUSE TARGET_WHEELHOUSE}"
TARGET="${2:?usage: seed_wheelhouse.sh SOURCE_WHEELHOUSE TARGET_WHEELHOUSE}"
MANIFEST="${TARGET}/SHA256SUMS"

test -d "${SOURCE}"
test -d "${TARGET}"
test -f "${MANIFEST}"

seeded=0
skipped=0
while read -r expected_hash filename; do
  expected_hash="${expected_hash%$'\r'}"
  filename="${filename%$'\r'}"
  [[ "${expected_hash}" =~ ^[0-9a-f]{64}$ ]]
  [[ "${filename}" =~ ^[A-Za-z0-9][A-Za-z0-9._+-]*\.whl$ ]]

  source_file="${SOURCE}/${filename}"
  target_file="${TARGET}/${filename}"
  if [[ -e "${target_file}" ]]; then
    printf '%s  %s\n' "${expected_hash}" "${target_file}" | sha256sum -c - >/dev/null
    skipped=$((skipped + 1))
    continue
  fi
  if [[ ! -f "${source_file}" ]]; then
    continue
  fi
  if ! printf '%s  %s\n' "${expected_hash}" "${source_file}" | sha256sum -c - >/dev/null 2>&1; then
    continue
  fi
  ln "${source_file}" "${target_file}"
  seeded=$((seeded + 1))
done < "${MANIFEST}"

echo "seeded=${seeded} existing=${skipped}"
