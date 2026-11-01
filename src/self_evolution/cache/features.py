"""Immutable, label-free node feature shards linked to a checkpoint and parent cache."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

import torch

from self_evolution.io import atomic_write, checked_path, digest, file_hash, load_tensor, read_json


class FeatureStore:
    def __init__(self, root: str | Path, expected: dict | None = None):
        self.root = Path(root)
        path = self.root / "manifest.json"
        self.manifest = read_json(path)
        if self.manifest.get("status") != "complete":
            raise ValueError("incomplete feature cache")
        if expected is not None and self.manifest["identity"] != expected:
            raise ValueError("feature cache identity/parent/checkpoint mismatch")
        self.identity = file_hash(path)
        self._location = {}
        self._verified = set()
        for shard in self.manifest["shards"]:
            for jid, count in zip(shard["ids"], shard["atoms"]):
                if jid in self._location:
                    raise ValueError("duplicate feature ID")
                self._location[jid] = (shard, count)
        if digest(sorted(self._location)) != self.manifest["ids_hash"]:
            raise ValueError("cache ID set mismatch")

    @lru_cache(maxsize=None)
    def _shard(self, relative: str) -> dict:
        path = checked_path(self.root, relative)
        shard = next(s for s in self.manifest["shards"] if s["file"] == relative)
        if file_hash(path) != shard["sha256"]:
            raise ValueError(f"feature checksum mismatch: {relative}")
        contents = load_tensor(path)
        if contents["identity"] != self.manifest["identity"] or contents["ids"] != shard["ids"]:
            raise ValueError("feature shard identity mismatch")
        nodes, offsets = contents["nodes"], contents["offsets"]
        if (
            nodes.dtype != torch.float32
            or nodes.ndim != 2
            or not torch.isfinite(nodes).all()
            or nodes.shape[1] != self.manifest["width"]
            or offsets != [0, *torch.tensor(shard["atoms"]).cumsum(0).tolist()]
            or offsets[-1] != len(nodes)
        ):
            raise ValueError("feature shard dimensions/count/dtype mismatch")
        return {jid: nodes[offsets[i] : offsets[i + 1]] for i, jid in enumerate(shard["ids"])}

    def get(self, jid: str, atoms: int | None = None) -> torch.Tensor:
        shard, count = self._location[jid]
        if atoms is not None and atoms != count:
            raise ValueError(f"node count mismatch: {jid}")
        return self._shard(shard["file"])[jid]

    def verify_all(self) -> None:
        for shard in self.manifest["shards"]:
            if file_hash(checked_path(self.root, shard["file"])) != shard["sha256"]:
                raise ValueError(f"feature checksum mismatch: {shard['file']}")
            self._shard(shard["file"])


def publish_cache(
    root: Path,
    identity: dict,
    ids: Iterable[str],
    produce: Callable[[list[str]], list[torch.Tensor]],
    shard_size: int = 256,
) -> FeatureStore:
    ids = sorted(ids)
    if not ids or len(ids) != len(set(ids)) or shard_size < 1:
        raise ValueError("invalid cache IDs or shard size")
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        cache = FeatureStore(root, identity)
        if cache.manifest["ids_hash"] != digest(ids):
            raise ValueError("cache library ID set changed")
        cache.verify_all()
        return cache
    shards, width = [], None
    for i in range(0, len(ids), shard_size):
        batch = ids[i : i + shard_size]
        path = root / f"nodes_{i // shard_size:05d}.pt"
        receipt = path.with_suffix(".json")
        if path.exists() and receipt.exists():
            if file_hash(path) != read_json(receipt)["sha256"]:
                raise ValueError("resumed shard checksum mismatch")
            data = load_tensor(path)
            if data["identity"] != identity or data["ids"] != batch:
                raise ValueError("partial cache belongs to a different run")
        else:
            tensors = [x.detach().cpu().float() for x in produce(batch)]
            if len(tensors) != len(batch) or any(x.ndim != 2 or len(x) < 1 for x in tensors):
                raise ValueError("invalid produced feature batch")
            atoms = [len(x) for x in tensors]
            offsets = [0, *torch.tensor(atoms).cumsum(0).tolist()]
            data = {
                "ids": batch,
                "nodes": torch.cat(tensors),
                "offsets": offsets,
                "identity": identity,
            }
            atomic_write(path, data, tensor=True)
            atomic_write(receipt, {"sha256": file_hash(path)})
        nodes, offsets = data["nodes"], data["offsets"]
        if (
            nodes.ndim != 2
            or nodes.dtype != torch.float32
            or not torch.isfinite(nodes).all()
            or len(offsets) != len(batch) + 1
            or offsets[0] != 0
            or offsets[-1] != len(nodes)
            or any(b <= a for a, b in zip(offsets, offsets[1:]))
        ):
            raise ValueError("invalid resumed node shard")
        if width is not None and width != nodes.shape[1]:
            raise ValueError("cache feature width changed")
        width = nodes.shape[1]
        shards.append(
            {
                "file": path.name,
                "sha256": file_hash(path),
                "ids": batch,
                "atoms": [b - a for a, b in zip(offsets, offsets[1:])],
            }
        )
        if i % (shard_size * 10) == 0:
            print(f"cache {i + len(batch)}/{len(ids)}", flush=True)
    manifest = {
        "schema": 1,
        "status": "complete",
        "identity": identity,
        "ids_hash": digest(ids),
        "width": width,
        "dtype": "float32",
        "shards": shards,
    }
    atomic_write(manifest_path, manifest)
    cache = FeatureStore(root, identity)
    cache.verify_all()
    return cache
