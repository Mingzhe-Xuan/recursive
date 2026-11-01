"""Supplement immutable feature manifests with complete, checksum-bound delivery metadata."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from self_evolution.io import (
    atomic_write,
    checked_path,
    code_identity,
    digest,
    file_hash,
    read_json,
)
from self_evolution.pipeline.chain import task_lock

SOURCE = Path(__file__).resolve().parents[2] / "data/manifests/self_evolution/jarvis_2021.json"


def training_metadata(stage, config_hash, graphs_hash, mode, round_index):
    path = stage / "training.json"
    if not path.is_file():
        raise ValueError(f"required training is incomplete: {stage}")
    done = read_json(path)
    identity = done["identity"]
    if (
        identity["config_hash"] != config_hash
        or identity["graphs_hash"] != graphs_hash
        or identity["code_hash"] != code_identity()
        or identity["mode"] != mode
        or identity["round"] != round_index
        or file_hash(stage / "best.pt") != done["checkpoint_sha256"]
    ):
        raise ValueError("training/checkpoint provenance does not match audit protocol")
    return done


def audit_task(root, prepared, config, source_path=SOURCE, *, require_complete=False):
    root, prepared = Path(root), Path(prepared)
    config_hash = digest(config)
    with task_lock(root / ".lock"):
        chain_path = root / "chain_manifest.json"
        chain = read_json(chain_path)
        if (
            read_json(root / "protocol.json") != config
            or chain["config_hash"] != config_hash
            or chain["seed"] != config["seed"]
            or chain["target_max_round"] != config["max_round"]
            or root.parent.name != chain["task"]
            or root.name != f"seed_{config['seed']}"
        ):
            raise ValueError("chain does not match audit protocol")
        stages = chain["stages"]
        if (
            not stages
            or len(stages) > config["max_round"] + 1
            or [row["round"] for row in stages] != list(range(len(stages)))
        ):
            raise ValueError("audit requires contiguous completed stages")
        if require_complete and (
            chain["status"] != "complete" or len(stages) != config["max_round"] + 1
        ):
            raise ValueError("audit requires the complete predeclared chain")
        graphs_path = prepared / "graphs/manifest.json"
        graphs_hash = file_hash(graphs_path)
        graphs = read_json(graphs_path)
        graph_identity = graphs["identity"]
        if graphs["status"] != "complete" or graphs["failures"]:
            raise ValueError("audit requires a complete graph library")
        source_path = Path(source_path)
        if (
            file_hash(source_path) != graph_identity["source_sha256"]
            or graph_identity["graph_config"] != config["graph"]
        ):
            raise ValueError("source/geometry metadata does not match audit protocol")
        source = read_json(source_path)
        task_hash = read_json(root / "round_000/training.json")["identity"]["task_hash"]
        if require_complete:
            for row in stages[1:]:
                for mode in ["original", "cumulative"]:
                    done = training_metadata(
                        root / "controls" / mode / f"round_{row['round']:03d}",
                        config_hash,
                        graphs_hash,
                        mode,
                        row["round"],
                    )
                    if (
                        done["identity"]["parent_cache"] is not None
                        or done["identity"]["task_hash"] != task_hash
                    ):
                        raise ValueError(
                            "raw-input control does not match this task/cache protocol"
                        )
                    if mode == "cumulative" and (
                        done["optimizer_steps"] != row["cumulative_steps"]
                        or done["identity"]["target_steps"] != row["cumulative_steps"]
                    ):
                        raise ValueError("cumulative control does not match actual optimizer steps")
        prepared_audits = []
        previous = None
        for row in stages:
            r = row["round"]
            stage = root / f"round_{r:03d}"
            done = training_metadata(stage, config_hash, graphs_hash, "evolution", r)
            cache_root = stage / "cache"
            base_path = cache_root / "manifest.json"
            base_hash = file_hash(base_path)
            base = read_json(base_path)
            identity = base["identity"]
            if (
                base["status"] != "complete"
                or base["dtype"] != "float32"
                or base["width"] != config["model"]["hidden"]
                or base_hash != row["cache_sha256"]
                or done["checkpoint_sha256"] != row["checkpoint_sha256"]
                or identity["checkpoint_sha256"] != done["checkpoint_sha256"]
                or identity["graphs_sha256"] != graphs_hash
                or identity["config_hash"] != config_hash
                or identity["code_hash"] != code_identity()
                or identity["parent_cache_sha256"] != previous
                or done["identity"]["parent_cache"] != previous
                or done["identity"]["task_hash"] != task_hash
                or identity["task"] != chain["task"]
                or identity["backbone"] != config["backbone"]
                or identity["seed"] != config["seed"]
                or identity["round"] != r
            ):
                raise ValueError("cache provenance does not match its completed chain")
            ids, shards = [], []
            for shard in base["shards"]:
                path = checked_path(cache_root, shard["file"])
                if file_hash(path) != shard["sha256"]:
                    raise ValueError("cache shard checksum mismatch during delivery audit")
                if len(shard["ids"]) != len(shard["atoms"]) or any(
                    jid not in graphs["entries"] or graphs["entries"][jid]["atoms"] != atoms
                    for jid, atoms in zip(shard["ids"], shard["atoms"])
                ):
                    raise ValueError("cache atom counts/order binding do not match graph metadata")
                ids.extend(shard["ids"])
                shards.append(
                    {
                        "file": "cache/" + shard["file"],
                        "bytes": path.stat().st_size,
                        "sha256": shard["sha256"],
                        "structures": len(shard["ids"]),
                        "atoms": sum(shard["atoms"]),
                    }
                )
            if (
                len(ids) != len(set(ids))
                or set(ids) != set(graphs["entries"])
                or digest(sorted(ids)) != base["ids_hash"]
            ):
                raise ValueError("cache audit requires complete, unique library coverage")
            audit = {
                "schema": 1,
                "status": "complete",
                "labels_read": False,
                "base_manifest": "cache/manifest.json",
                "base_manifest_sha256": base_hash,
                "base_identity": identity,
                "training_identity": done["identity"],
                "configuration": config,
                "dataset_sha256": graph_identity["dataset_sha256"],
                "source_metadata": source,
                "graph_identity": graph_identity,
                "graphs_manifest_sha256": graphs_hash,
                "structure_ids_hash": base["ids_hash"],
                "atom_order_binding": "per-structure graph file SHA256 in the graph manifest",
                "feature_boundary": identity["boundary"],
                "dtype": base["dtype"],
                "width": base["width"],
                "structures": len(ids),
                "atoms": sum(shard["atoms"] for shard in shards),
                "successful_ids": ids,
                "failed_ids": [],
                "shards": shards,
                "auditor_source_sha256": file_hash(Path(__file__)),
            }
            prepared_audits.append((stage / "cache_provenance.json", audit))
            previous = base_hash
        references = []
        for path, audit in prepared_audits:
            atomic_write(path, audit)
            references.append(
                {
                    "round": audit["base_identity"]["round"],
                    "file": path.relative_to(root).as_posix(),
                    "sha256": file_hash(path),
                }
            )
        chain["cache_provenance"] = {"schema": 1, "stages": references}
        atomic_write(chain_path, chain)
        return chain["cache_provenance"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/self_evolution/cgcnn_seed123.json")
    )
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("full-cache delivery audits require a Slurm allocation")
    print(audit_task(args.root, args.prepared, read_json(args.config)))
