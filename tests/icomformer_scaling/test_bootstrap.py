import hashlib
import importlib.util
from pathlib import Path
import subprocess

import pytest


def loader():
    spec = importlib.util.spec_from_file_location(
        "icom_bootstrap", Path("scripts/icomformer_scaling/bootstrap.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def artifact():
    content = b"verified complete wheel"
    return content, {
        "filename": "tiny.whl",
        "url": "https://files.pythonhosted.org/tiny.whl",
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def test_completed_partial_reuses_checksum_without_network(tmp_path, monkeypatch):
    module = loader()
    content, metadata = artifact()
    (tmp_path / "tiny.whl.partial").write_bytes(content)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **kw: pytest.fail("already complete artifact redownloaded"),
    )
    target = module.ensure_artifact(metadata, tmp_path, "unused")
    assert target.read_bytes() == content and not (tmp_path / "tiny.whl.partial").exists()


def test_transport_eof_cannot_override_content_integrity(tmp_path, monkeypatch):
    module = loader()
    content, metadata = artifact()

    def download(command, **kwargs):
        (tmp_path / "tiny.whl.partial").write_bytes(content)
        return subprocess.CompletedProcess(command, 56)

    monkeypatch.setattr(module.subprocess, "run", download)
    assert module.ensure_artifact(metadata, tmp_path, "unused").read_bytes() == content
    (tmp_path / "tiny.whl").unlink()

    def corrupt(command, **kwargs):
        (tmp_path / "tiny.whl.partial").write_bytes(b"corrupt")
        return subprocess.CompletedProcess(command, 56)

    monkeypatch.setattr(module.subprocess, "run", corrupt)
    with pytest.raises(subprocess.CalledProcessError):
        module.ensure_artifact(metadata, tmp_path, "unused")
    assert not (tmp_path / "tiny.whl").exists()
