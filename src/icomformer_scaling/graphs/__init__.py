"""Official periodic lattice graphs, bound to the existing dataset and task splits."""

from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import importlib.metadata
import multiprocessing
from pathlib import Path

import torch

from self_evolution.data.prepare import load_records
from self_evolution.io import atomic_write, digest, file_hash, load_tensor, read_json
from icomformer_scaling.source import audit, graph_components


def geometry_identity(config):
    return {
        "graph_config": config,
        "official_graph_sha256": audit()["files"]["graphs.py"]["sha256"],
        "adapter_sha256": digest(Path(__file__).read_text(encoding="utf-8")),
        "jarvis_tools": importlib.metadata.version("jarvis-tools"),
        "numpy": importlib.metadata.version("numpy"),
        "pyg": importlib.metadata.version("torch-geometric"),
    }


def make_graph(record, config):
    from jarvis.core.atoms import Atoms

    value = record["atoms"]
    atoms = Atoms(
        lattice_mat=value["lattice_mat"],
        coords=value["coords"],
        elements=value["elements"],
        cartesian=value.get("cartesian", False),
        props=value.get("props"),
    )
    data = graph_components().atom_dgl_multigraph(
        atoms=atoms,
        cutoff=config["cutoff"],
        max_neighbors=config["neighbors"],
        atom_features="cgcnn",
        use_lattice=True,
        use_canonize=False,
        compute_line_graph=False,
    )
    n, e = len(atoms.elements), data.edge_index.shape[1]
    if (
        data.x.shape != (n, 92)
        or data.edge_attr.shape != (e, 3)
        or data.edge_nei.shape != (e, 3, 3)
    ):
        raise ValueError("official graph dimensions mismatch")
    if (
        not all(torch.isfinite(x).all() for x in [data.x, data.edge_attr, data.edge_nei])
        or (data.edge_attr.norm(dim=-1) <= 0).any()
    ):
        raise ValueError("non-finite or zero-length official edge")
    if data.edge_index.min() < 0 or data.edge_index.max() >= n:
        raise ValueError("official graph index outside atoms")
    return {
        "jid": record["jid"],
        "atom_features": data.x,
        "edge_index": data.edge_index,
        "edge_attr": data.edge_attr,
        "edge_nei": data.edge_nei,
        "atom_lat": data.atom_lat,
        "elements": atoms.elements,
        "structure_sha256": digest(record["atoms"]),
    }


def _worker_init():
    torch.set_num_threads(1)


def _prepare_one(arguments):
    record, directory, config = arguments
    path = Path(directory) / (record["jid"] + ".pt")
    try:
        if path.exists():
            graph = load_tensor(path)
            if (
                graph["structure_sha256"] != digest(record["atoms"])
                or graph["jid"] != record["jid"]
            ):
                raise ValueError("partial graph belongs to another structure")
        else:
            graph = make_graph(record, config)
            atomic_write(path, graph, tensor=True)
        return (
            record["jid"],
            {
                "file": path.name,
                "atoms": len(graph["atom_features"]),
                "edges": graph["edge_index"].shape[1],
                "sha256": file_hash(path),
                "structure_sha256": graph["structure_sha256"],
            },
            None,
        )
    except Exception as exc:
        return record["jid"], None, {"type": type(exc).__name__, "message": str(exc)}


def prepare(
    archive,
    old_prepared,
    output,
    config,
    workers=4,
    source_manifest=Path("data/manifests/self_evolution/jarvis_2021.json"),
):
    old_prepared, output = Path(old_prepared), Path(output)
    source = read_json(source_manifest)
    records, _ = load_records(Path(archive), source)
    original = read_json(old_prepared / "graphs/manifest.json")
    if original["status"] != "complete" or original["failures"]:
        raise ValueError("unaccepted source prepared library")
    expected = {
        **geometry_identity(config),
        "dataset_sha256": original["identity"]["dataset_sha256"],
        "source_graphs_sha256": file_hash(old_prepared / "graphs/manifest.json"),
    }
    root = output / "graphs"
    root.mkdir(parents=True, exist_ok=True)
    protocol = root / "protocol.json"
    if protocol.exists() and read_json(protocol) != expected:
        raise ValueError("graph geometry/version changed; use a new prepared root")
    atomic_write(protocol, expected)
    prior = root / "manifest.json"
    if prior.exists():
        existing = read_json(prior)
        if existing["identity"] != expected:
            raise ValueError("existing graph identity mismatch")
        if existing["status"] == "complete":
            return existing
    if set(original["entries"]) != {r["jid"] for r in records}:
        raise ValueError("library IDs differ from the completed CGCNN experiment")
    entries, failures = {}, {}
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=_worker_init,
    ) as pool:
        for i, (jid, entry, error) in enumerate(
            pool.map(_prepare_one, ((r, root, config) for r in records), chunksize=16)
        ):
            if error:
                failures[jid] = error
            else:
                if entry["atoms"] != original["entries"][jid]["atoms"]:
                    raise ValueError("atom ordering/count changed")
                entries[jid] = entry
            if i % 500 == 0:
                print("PREPARED", i + 1, "/", len(records), "failures", len(failures), flush=True)
    result = {
        "schema": 1,
        "status": "failed" if failures else "complete",
        "identity": expected,
        "entries": entries,
        "failures": failures,
        "record_count": len(records),
        "ids_hash": digest(sorted(entries)),
    }
    atomic_write(prior, result)
    if failures:
        raise ValueError("unresolved native graph errors; see graph manifest")
    atomic_write(
        output / "source_tasks.json",
        {"root": str(old_prepared.resolve()), "graphs_sha256": expected["source_graphs_sha256"]},
    )
    return result


class GraphStore:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = read_json(self.root / "manifest.json")
        if self.manifest["status"] != "complete" or self.manifest["failures"]:
            raise ValueError("incomplete invariant graph library")
        self.identity = file_hash(self.root / "manifest.json")
        self.entries = self.manifest["entries"]
        self.ids = sorted(self.entries)

    @lru_cache(maxsize=None)
    def get(self, jid):
        entry = self.entries[jid]
        path = self.root / entry["file"]
        if path.name != entry["file"] or file_hash(path) != entry["sha256"]:
            raise ValueError("graph path/checksum mismatch")
        value = load_tensor(path)
        if value["jid"] != jid or len(value["atom_features"]) != entry["atoms"]:
            raise ValueError("graph atom identity mismatch")
        return value


def collate_graphs(graphs, device="cpu"):
    from torch_geometric.data import Batch, Data

    values = [
        Data(
            x=g["atom_features"],
            edge_index=g["edge_index"],
            edge_attr=g["edge_attr"],
            edge_nei=g["edge_nei"],
            atom_lat=g["atom_lat"],
        )
        for g in graphs
    ]
    data = Batch.from_data_list(values).to(device)
    return {"ids": [g["jid"] for g in graphs], "atom_features": data.x, "data": data}
