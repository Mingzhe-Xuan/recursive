#!/usr/bin/env python3
"""Download dataset artifacts from a versioned manifest with checksum gating."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_CHECKSUM_PATTERNS = {
    "sha256": re.compile(r"[0-9a-f]{64}"),
    "md5": re.compile(r"[0-9a-f]{32}"),
}


def hash_file(path: Path, algorithm: str) -> str:
    if algorithm not in _CHECKSUM_PATTERNS:
        raise ValueError(f"unsupported checksum algorithm: {algorithm}")
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    return hash_file(path, "sha256")


def _checksum_spec(artifact: dict[str, Any], filename: str) -> tuple[str, str]:
    present = [name for name in _CHECKSUM_PATTERNS if name in artifact]
    if len(present) != 1:
        supported = ", ".join(_CHECKSUM_PATTERNS)
        raise ValueError(f"{filename} must define exactly one checksum ({supported})")
    algorithm = present[0]
    expected = artifact[algorithm]
    if not isinstance(expected, str) or _CHECKSUM_PATTERNS[algorithm].fullmatch(expected) is None:
        raise ValueError(f"invalid {algorithm.upper()} for {filename}")
    return algorithm, expected


def _validated_artifacts(manifest: dict[str, Any]) -> list[dict[str, str]]:
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")
    if not isinstance(manifest.get("dataset_id"), str) or not manifest["dataset_id"]:
        raise ValueError("manifest dataset_id must be a non-empty string")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("manifest artifacts must be a non-empty list")

    validated: list[dict[str, str]] = []
    seen: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("each artifact must be an object")
        filename = artifact.get("filename")
        url = artifact.get("url")
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
            or filename in {".", ".."}
        ):
            raise ValueError(f"unsafe artifact filename: {filename!r}")
        if filename in seen:
            raise ValueError(f"duplicate artifact filename: {filename}")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            raise ValueError(f"artifact URL must use HTTP(S): {url!r}")
        algorithm, expected = _checksum_spec(artifact, filename)
        seen.add(filename)
        validated.append({"filename": filename, "url": url, algorithm: expected})
    return validated


def load_manifest(path: Path) -> tuple[str, list[dict[str, str]]]:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")
    artifacts = _validated_artifacts(manifest)
    return manifest["dataset_id"], artifacts


def _open(url: str, offset: int, timeout: float):
    headers = {"User-Agent": "recursive-atomistic-backbones/0.1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


def _transfer(url: str, partial: Path, timeout: float) -> None:
    offset = partial.stat().st_size if partial.exists() else 0
    try:
        response = _open(url, offset, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code != 416 or offset == 0:
            raise
        response = _open(url, 0, timeout)
        offset = 0

    with response:
        status = getattr(response, "status", response.getcode())
        append = offset > 0 and status == 206
        mode = "ab" if append else "wb"
        with partial.open(mode) as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)


def download_artifact(artifact: dict[str, str], output_dir: Path, timeout: float) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / artifact["filename"]
    partial = output_dir / f"{artifact['filename']}.partial"
    algorithm, expected = _checksum_spec(artifact, artifact["filename"])
    checksum_label = "SHA-256" if algorithm == "sha256" else "MD5"

    if final.exists():
        if not final.is_file() or hash_file(final, algorithm) != expected:
            raise RuntimeError(f"existing artifact has wrong {checksum_label}: {final}")
        return "existing"

    _transfer(artifact["url"], partial, timeout)
    actual = hash_file(partial, algorithm)
    if actual != expected:
        raise RuntimeError(
            f"{checksum_label} mismatch for {artifact['filename']}: "
            f"expected {expected}, got {actual}"
        )
    os.replace(partial, final)
    return "downloaded"


def download_manifest(manifest_path: Path, output_root: Path, timeout: float = 60.0) -> Path:
    dataset_id, artifacts = load_manifest(manifest_path)
    dataset_dir = output_root / dataset_id
    for artifact in artifacts:
        result = download_artifact(artifact, dataset_dir, timeout)
        print(f"{result}: {dataset_dir / artifact['filename']}")
    return dataset_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    download_manifest(args.manifest, args.output_root, args.timeout)


if __name__ == "__main__":
    main()
