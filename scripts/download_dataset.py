#!/usr/bin/env python3
"""Download dataset artifacts from a versioned manifest with SHA-256 gating."""

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

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        expected = artifact.get("sha256")
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
        if not isinstance(expected, str) or _SHA256_RE.fullmatch(expected) is None:
            raise ValueError(f"invalid SHA-256 for {filename}")
        seen.add(filename)
        validated.append({"filename": filename, "url": url, "sha256": expected})
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
    expected = artifact["sha256"]

    if final.exists():
        if not final.is_file() or sha256_file(final) != expected:
            raise RuntimeError(f"existing artifact has wrong SHA-256: {final}")
        return "existing"

    _transfer(artifact["url"], partial, timeout)
    actual = sha256_file(partial)
    if actual != expected:
        raise RuntimeError(
            f"SHA-256 mismatch for {artifact['filename']}: expected {expected}, got {actual}"
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
