"""Audit a pinned data snapshot, construct shared geometry, and lock task splits."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import zipfile

from self_evolution.io import atomic_write, digest, file_hash, load_tensor, read_json

from .graphs import GraphConfig, builder_identity, make_graph
from .tasks import TASKS, grouped_split, select_labels


def load_records(path: Path, source: dict) -> list[dict]:
    artifact = source["artifacts"][0]
    if path.stat().st_size != artifact["size_bytes"]:
        raise ValueError("dataset byte size mismatch")
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != artifact["md5"]:
        raise ValueError("dataset official MD5 mismatch")
    with zipfile.ZipFile(path) as archive:
        if source["json_member"] not in archive.namelist():
            raise ValueError("expected JSON member missing")
        records = json.loads(archive.read(source["json_member"]))
    if not isinstance(records, list) or len(records) != source["expected_structures"]:
        raise ValueError("unexpected snapshot record count")
    return records


def _prepare_graph(args):
    row, root, config = args
    jid = row["jid"]
    name = digest(jid)
    path = Path(root) / name[:2] / (name + ".pt")
    try:
        if path.exists():
            graph = load_tensor(path)
            if (
                graph["jid"] != jid
                or graph["structure_hash"] != digest(row["atoms"])
                or graph["config"] != asdict(config)
                or graph.get("builder_id") != builder_identity()
            ):
                raise ValueError("existing graph has incompatible structure/config")
        else:
            graph = make_graph(row, config)
            atomic_write(path, graph, tensor=True)
        return (
            jid,
            {
                "file": path.relative_to(root).as_posix(),
                "sha256": file_hash(path),
                "atoms": len(graph["atom_features"]),
                "group": graph["group"],
                "structure_hash": graph["structure_hash"],
            },
            None,
        )
    except Exception as exc:
        return jid, None, f"{type(exc).__name__}: {exc}"


def prepare_dataset(
    archive: Path,
    source_path: Path,
    output: Path,
    config: GraphConfig,
    workers: int = 4,
    split_seed: int = 123,
) -> dict:
    source = read_json(source_path)
    started = time.perf_counter()
    records = load_records(archive, source)
    ids = [r["jid"] for r in records]
    if any(not isinstance(jid, str) or not jid for jid in ids) or len(ids) != len(set(ids)):
        raise ValueError("invalid or duplicate structure IDs")
    dataset_hash = file_hash(archive)
    root = output / "graphs"
    root.mkdir(parents=True, exist_ok=True)
    expected = {
        "dataset_sha256": dataset_hash,
        "graph_config": asdict(config),
        "source_sha256": file_hash(source_path),
        "builder_id": builder_identity(),
    }
    prior = root / "manifest.json"
    if prior.exists():
        old = read_json(prior)
        if old["identity"] != expected:
            raise ValueError("refusing to mix different dataset/graph configurations")
    entries, failures = {}, {}
    arguments = ((row, root, config) for row in records)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, (jid, entry, error) in enumerate(pool.map(_prepare_graph, arguments, chunksize=32)):
            if error:
                failures[jid] = error
            else:
                entries[jid] = entry
            if (i + 1) % 500 == 0:
                print(
                    json.dumps({"prepared": i + 1, "total": len(records), "failed": len(failures)}),
                    flush=True,
                )
    manifest = {
        "schema": 1,
        "status": "failed" if failures else "complete",
        "identity": expected,
        "entries": entries,
        "failures": failures,
        "ids_hash": digest(sorted(ids)),
        "record_count": len(records),
    }
    atomic_write(prior, manifest)
    if failures:
        raise ValueError(f"{len(failures)} unresolved graph failures; see {prior}")
    groups = {jid: entry["group"] for jid, entry in entries.items()}
    coverage = []
    for task, unit in TASKS.items():
        labels, counts = select_labels(records, task)
        task_info = {
            "task": task,
            "unit": unit,
            "label_audit": counts,
            "labels": labels,
            "dataset_sha256": dataset_hash,
        }
        try:
            task_info["split"] = grouped_split(labels, groups, split_seed)
            task_info["status"] = "ready"
        except ValueError as exc:
            task_info.update(status="failed", reason=str(exc))
        task_path = output / "tasks" / (task + ".json")
        if task_path.exists() and read_json(task_path) != task_info:
            raise ValueError(f"immutable task labels/split changed: {task}")
        atomic_write(task_path, task_info)
        coverage.append({k: v for k, v in task_info.items() if k not in {"labels", "split"}})
    audit = {
        "dataset_sha256": dataset_hash,
        "structures": len(records),
        "exact_duplicate_groups": sum(
            v > 1 for v in __import__("collections").Counter(groups.values()).values()
        ),
        "duplicate_scope": "same cell, permutation/translation invariant, 7 decimal rounding",
        "split_source": "project_grouped_80_10_10; not official paper IDs",
        "tasks": coverage,
        "graphs_sha256": file_hash(prior),
        "preparation_wall_seconds": time.perf_counter() - started,
    }
    atomic_write(output / "audit.json", audit)
    return audit
