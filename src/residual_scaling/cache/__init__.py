"""Paired immutable node features and original-unit ensemble predictions."""

from pathlib import Path
import torch

from self_evolution.io import atomic_write, checked_path, digest, file_hash, load_tensor, read_json


def validate_payload(data, identity, ids, atoms, width):
    offsets = [0, *torch.tensor(atoms).cumsum(0).tolist()]
    if (
        data["identity"] != identity
        or data["ids"] != ids
        or len(atoms) != len(ids)
        or any(n < 1 for n in atoms)
        or data["offsets"] != offsets
        or data["nodes"].shape != (offsets[-1], width)
        or data["predictions"].shape != (len(ids),)
        or data["nodes"].dtype != torch.float32
        or data["predictions"].dtype != torch.float32
        or not torch.isfinite(data["nodes"]).all()
        or not torch.isfinite(data["predictions"]).all()
    ):
        raise ValueError("invalid paired archive dimensions/identity/dtype")


class Archive:
    def __init__(self, root, expected=None):
        self.root = Path(root)
        self.manifest = read_json(self.root / "manifest.json")
        m = self.manifest
        if (
            m["schema"] != 1
            or m["dtype"] != "float32"
            or m["width"] < 1
            or m["failed_ids"]
            or m["status"] != "complete"
            or (expected is not None and m["identity"] != expected)
        ):
            raise ValueError("incomplete or mismatched paired archive")
        self.identity = file_hash(self.root / "manifest.json")
        self.locations, self.decoded = {}, {}
        for shard in m["shards"]:
            if len(shard["ids"]) != len(shard["atoms"]):
                raise ValueError("archive ID/atom count mismatch")
            for i, jid in enumerate(shard["ids"]):
                if jid in self.locations:
                    raise ValueError("duplicate archive ID")
                self.locations[jid] = (shard, i)
        if (
            digest(sorted(self.locations)) != m["ids_hash"]
            or m["structures"] != len(self.locations)
            or m["atoms"] != sum(sum(s["atoms"]) for s in m["shards"])
        ):
            raise ValueError("archive ID coverage mismatch")

    def shard(self, row, force=False):
        name = row["file"]
        if name not in self.decoded or force:
            path = checked_path(self.root, name)
            if file_hash(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
                raise ValueError("paired archive shard checksum/bytes mismatch")
            data = load_tensor(path)
            validate_payload(
                data, self.manifest["identity"], row["ids"], row["atoms"], self.manifest["width"]
            )
            self.decoded[name] = data
        return self.decoded[name]

    def get(self, jid, atoms=None):
        row, i = self.locations[jid]
        if atoms is not None and row["atoms"][i] != atoms:
            raise ValueError("paired archive atom count mismatch")
        data = self.shard(row)
        return data["nodes"][data["offsets"][i] : data["offsets"][i + 1]], data["predictions"][i]

    def batch(self, ids, graphs, device, with_nodes):
        values = [self.get(jid, graphs.entries[jid]["atoms"]) for jid in ids]
        nodes = torch.cat([v[0] for v in values]).to(device) if with_nodes else None
        return nodes, torch.stack([v[1] for v in values]).to(device)

    def verify_all(self):
        for row in self.manifest["shards"]:
            self.shard(row, force=True)


def publish(root, identity, ids, width, producer, shard_size=256):
    root = Path(root)
    ids = sorted(ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("invalid paired archive IDs")
    if (root / "manifest.json").exists():
        archive = Archive(root, identity)
        if sorted(archive.locations) != ids:
            raise ValueError("paired archive library changed")
        archive.verify_all()
        return archive
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for start in range(0, len(ids), shard_size):
        chunk = ids[start : start + shard_size]
        path = root / f"paired_{start // shard_size:05d}.pt"
        receipt = path.with_suffix(".json")
        if path.exists():
            if receipt.exists() and file_hash(path) != read_json(receipt)["sha256"]:
                raise ValueError("partial paired archive checksum mismatch")
            data = load_tensor(path)
            if data["identity"] != identity or data["ids"] != chunk:
                raise ValueError("partial archive belongs to another checkpoint/parent")
        else:
            values = producer(chunk)
            if len(values) != len(chunk):
                raise ValueError("producer omitted structures")
            nodes = [v[0].detach().cpu().float() for v in values]
            predictions = torch.stack(
                [torch.as_tensor(v[1]).detach().cpu().reshape(()) for v in values]
            ).float()
            if any(n.ndim != 2 or n.shape[1] != width or len(n) < 1 for n in nodes):
                raise ValueError("producer returned invalid nodes")
            offsets = [0, *torch.tensor([len(n) for n in nodes]).cumsum(0).tolist()]
            data = {
                "identity": identity,
                "ids": chunk,
                "offsets": offsets,
                "nodes": torch.cat(nodes),
                "predictions": predictions,
            }
            if not torch.isfinite(data["nodes"]).all() or not torch.isfinite(predictions).all():
                raise ValueError("non-finite paired archive")
            atomic_write(path, data, tensor=True)
            atomic_write(receipt, {"sha256": file_hash(path)})
        offsets = data["offsets"]
        validate_payload(
            data, identity, chunk, [b - a for a, b in zip(offsets, offsets[1:])], width
        )
        if not receipt.exists():
            atomic_write(receipt, {"sha256": file_hash(path)})
        rows.append(
            {
                "file": path.name,
                "sha256": file_hash(path),
                "bytes": path.stat().st_size,
                "ids": chunk,
                "atoms": [b - a for a, b in zip(offsets, offsets[1:])],
            }
        )
    manifest = {
        "schema": 1,
        "status": "complete",
        "identity": identity,
        "ids_hash": digest(ids),
        "width": width,
        "dtype": "float32",
        "prediction_units": "original_property_units",
        "structures": len(ids),
        "atoms": sum(sum(r["atoms"]) for r in rows),
        "failed_ids": [],
        "shards": rows,
    }
    atomic_write(root / "manifest.json", manifest)
    archive = Archive(root, identity)
    archive.verify_all()
    return archive
