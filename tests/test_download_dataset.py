from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest


def _load_downloader() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts" / "download_dataset.py"
    spec = importlib.util.spec_from_file_location("download_dataset", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


downloader = _load_downloader()


@contextmanager
def _server(payload: bytes, support_range: bool = True) -> Iterator[tuple[str, list[str | None]]]:
    seen_ranges: list[str | None] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            range_header = self.headers.get("Range")
            seen_ranges.append(range_header)
            start = 0
            if support_range and range_header:
                start = int(range_header.removeprefix("bytes=").removesuffix("-"))
                if start >= len(payload):
                    self.send_response(416)
                    self.end_headers()
                    return
                self.send_response(206)
                content_range = f"bytes {start}-{len(payload) - 1}/{len(payload)}"
                self.send_header("Content-Range", content_range)
            else:
                self.send_response(200)
            body = payload[start:] if support_range else payload
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/payload", seen_ranges
    finally:
        server.shutdown()
        thread.join()


def _artifact(url: str, payload: bytes, filename: str = "payload.bin") -> dict[str, str]:
    return {
        "filename": filename,
        "url": url,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def test_download_is_atomic_and_existing_file_is_skipped(tmp_path: Path) -> None:
    payload = b"paper-aligned-data" * 100
    with _server(payload) as (url, seen_ranges):
        artifact = _artifact(url, payload)
        assert downloader.download_artifact(artifact, tmp_path, 2) == "downloaded"
        assert (tmp_path / "payload.bin").read_bytes() == payload
        assert not (tmp_path / "payload.bin.partial").exists()
        assert downloader.download_artifact(artifact, tmp_path, 2) == "existing"
    assert seen_ranges == [None]


@pytest.mark.parametrize("support_range", [True, False])
def test_partial_download_resumes_or_safely_restarts(tmp_path: Path, support_range: bool) -> None:
    payload = b"0123456789" * 200
    partial = tmp_path / "payload.bin.partial"
    partial.write_bytes(payload[:321])
    with _server(payload, support_range=support_range) as (url, seen_ranges):
        assert downloader.download_artifact(_artifact(url, payload), tmp_path, 2) == "downloaded"
    assert (tmp_path / "payload.bin").read_bytes() == payload
    assert seen_ranges == ["bytes=321-"]


def test_bad_hash_keeps_partial_and_never_publishes_final(tmp_path: Path) -> None:
    payload = b"actual"
    with _server(payload) as (url, _):
        artifact = _artifact(url, b"expected")
        with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
            downloader.download_artifact(artifact, tmp_path, 2)
    assert (tmp_path / "payload.bin.partial").read_bytes() == payload
    assert not (tmp_path / "payload.bin").exists()


def test_md5_download_is_gated_and_existing_file_is_skipped(tmp_path: Path) -> None:
    payload = b"zenodo-official-md5" * 100
    with _server(payload) as (url, seen_ranges):
        artifact = {
            "filename": "data.tgz",
            "url": url,
            "md5": hashlib.md5(payload).hexdigest(),  # noqa: S324 - published integrity hash
        }
        assert downloader.download_artifact(artifact, tmp_path, 2) == "downloaded"
        assert downloader.download_artifact(artifact, tmp_path, 2) == "existing"
    assert seen_ranges == [None]


def test_md5_mismatch_keeps_partial_and_never_publishes_final(tmp_path: Path) -> None:
    payload = b"actual"
    with _server(payload) as (url, _):
        artifact = {
            "filename": "data.tgz",
            "url": url,
            "md5": hashlib.md5(b"expected").hexdigest(),  # noqa: S324 - integrity fixture
        }
        with pytest.raises(RuntimeError, match="MD5 mismatch"):
            downloader.download_artifact(artifact, tmp_path, 2)
    assert (tmp_path / "data.tgz.partial").read_bytes() == payload
    assert not (tmp_path / "data.tgz").exists()


def test_manifest_rejects_path_escape_and_invalid_schema(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "dataset_id": "unsafe",
        "artifacts": [_artifact("https://example.invalid/file", b"x", "../escape")],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe artifact filename"):
        downloader.load_manifest(path)

    manifest["schema_version"] = 2
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        downloader.load_manifest(path)


@pytest.mark.parametrize(
    "checksums",
    [
        {},
        {"sha256": "0" * 64, "md5": "0" * 32},
    ],
)
def test_manifest_requires_exactly_one_supported_checksum(
    tmp_path: Path, checksums: dict[str, str]
) -> None:
    artifact = {
        "filename": "payload.bin",
        "url": "https://example.invalid/payload.bin",
        **checksums,
    }
    manifest = {"schema_version": 1, "dataset_id": "checksums", "artifacts": [artifact]}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one checksum"):
        downloader.load_manifest(path)


def test_dpa2_zenodo_manifest_pins_official_archive() -> None:
    path = Path(__file__).parents[1] / "data" / "manifests" / "dpa2_sse_pbe_d.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    dataset_id, artifacts = downloader.load_manifest(path)

    assert dataset_id == "dpa2_sse_pbe_d"
    assert manifest["source"]["record_id"] == 10461723
    assert manifest["source"]["doi"] == "10.5281/zenodo.10461723"
    assert manifest["selection"]["dataset"] == "SSE-PBE-D"
    assert artifacts == [
        {
            "filename": "data-v1.3.tgz",
            "url": "https://zenodo.org/api/records/10461723/files/data-v1.3.tgz/content",
            "md5": "789bedf203d673bdc95a09b582d83823",
        }
    ]


def test_mace_phonondb_manifest_pins_exactly_97_unique_materials() -> None:
    path = Path(__file__).parents[1] / "data" / "manifests" / "mace_phonondb_97.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    dataset_id, artifacts = downloader.load_manifest(path)

    assert dataset_id == "mace_phonondb_97"
    assert manifest["sample_count"] == 97
    assert manifest["imaginary_frequency_tolerance_thz"] == 0.01
    assert len(manifest["phonondb_ids"]) == 97
    assert len(set(manifest["phonondb_ids"].values())) == 97
    assert manifest["source"]["commit"] == "480bc92d6719962b584c98e8bce4ffa1c2d74031"
    assert "{togo_id}" in manifest["source"]["phonondb_download_url_template"]
    assert len(artifacts) == 2
