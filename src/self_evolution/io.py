"""Content identities and atomic publication of experiment artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_write(path: str | Path, value: Any, *, tensor: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            if tensor:
                torch.save(value, f)
            else:
                f.write(
                    (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
                )
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def checked_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"artifact outside root: {relative}")
    return path


def load_tensor(path: str | Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=True)


def derived_seed(*parts: Any) -> int:
    return int(digest(parts)[:8], 16) % (2**31)


@lru_cache(maxsize=1)
def code_revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2], text=True
    ).strip()


@lru_cache(maxsize=1)
def code_identity() -> str:
    root = Path(__file__).resolve().parent
    files = sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and (p.suffix in {".py", ".json"} or p.name == "LICENSE")
    )
    return digest({p.relative_to(root).as_posix(): file_hash(p) for p in files})
