"""CGCNN periodic geometry; preserve the reference's distance and padding semantics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from self_evolution.io import checked_path, digest, file_hash, load_tensor, read_json


@dataclass(frozen=True)
class GraphConfig:
    radius: float = 8.0
    neighbors: int = 12
    step: float = 0.2

    def __post_init__(self):
        if self.radius <= self.step or self.step <= 0 or self.neighbors < 1:
            raise ValueError("invalid graph configuration")


def structure_from_record(atoms: dict):
    from pymatgen.core import Structure

    return Structure(
        atoms["lattice_mat"],
        atoms["elements"],
        atoms["coords"],
        coords_are_cartesian=atoms.get("cartesian", False),
    )


def structure_group(structure) -> str:
    """Exact same-cell identity, invariant to atom order and fractional translation."""
    numbers = np.array([site.specie.Z for site in structure])
    frac = np.asarray(structure.frac_coords) % 1.0
    origins = frac[numbers == numbers.min()]
    representations = []
    for origin in origins:
        positions = np.round((frac - origin) % 1.0, 7) % 1.0
        representations.append(
            sorted([int(z), *xyz.tolist()] for z, xyz in zip(numbers, positions))
        )
    return digest(
        {"cell": np.round(structure.lattice.matrix, 7).tolist(), "sites": min(representations)}
    )


@lru_cache(maxsize=1)
def atom_embeddings() -> dict:
    path = Path(__file__).parents[1] / "backbones/cgcnn/upstream/atom_init.json"
    return json.loads(path.read_text())


def make_graph(record: dict, config: GraphConfig) -> dict:
    crystal = structure_from_record(record["atoms"])
    if not len(crystal) or not crystal.is_ordered:
        raise ValueError("empty or disordered crystal")
    original = [site.specie.Z for site in crystal]
    embeddings = atom_embeddings()
    atom = torch.tensor([embeddings[str(z)] for z in original], dtype=torch.float32)
    all_neighbors = crystal.get_all_neighbors(config.radius, include_index=True)
    indices, distances, valid_counts = [], [], []
    for neighbors in all_neighbors:
        neighbors = sorted(neighbors, key=lambda x: x[1])[: config.neighbors]
        valid_counts.append(len(neighbors))
        indices.append([int(n[2]) for n in neighbors] + [0] * (config.neighbors - len(neighbors)))
        distances.append(
            [float(n[1]) for n in neighbors]
            + [config.radius + 1.0] * (config.neighbors - len(neighbors))
        )
    centers = np.arange(0, config.radius + config.step, config.step)
    features = np.exp(-(((np.asarray(distances)[..., None] - centers) / config.step) ** 2))
    if not np.isfinite(features).all() or not torch.isfinite(atom).all():
        raise ValueError("non-finite graph features")
    return {
        "jid": record["jid"],
        "atom_features": atom,
        "neighbor_features": torch.tensor(features, dtype=torch.float32),
        "neighbor_indices": torch.tensor(indices, dtype=torch.long),
        "valid_neighbor_counts": torch.tensor(valid_counts),
        "structure_hash": digest(record["atoms"]),
        "group": structure_group(crystal),
        "atomic_numbers": original,
        "config": asdict(config),
    }


class GraphStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.manifest = read_json(self.root / "manifest.json")
        if self.manifest.get("status") != "complete":
            raise ValueError("incomplete graph store")
        if self.manifest.get("failures"):
            raise ValueError("full-library graph store has unresolved failures")
        self.entries = self.manifest["entries"]
        self.ids = sorted(self.entries)
        self.identity = file_hash(self.root / "manifest.json")
        self._verified = set()

    @lru_cache(maxsize=None)
    def get(self, jid: str) -> dict:
        entry = self.entries[jid]
        path = checked_path(self.root, entry["file"])
        if jid not in self._verified:
            if file_hash(path) != entry["sha256"]:
                raise ValueError(f"graph checksum mismatch: {jid}")
            self._verified.add(jid)
        graph = load_tensor(path)
        if graph["jid"] != jid or len(graph["atom_features"]) != entry["atoms"]:
            raise ValueError(f"graph metadata mismatch: {jid}")
        return graph


def collate_graphs(graphs: list[dict], device: str | torch.device = "cpu") -> dict:
    if not graphs:
        raise ValueError("cannot collate empty batch")
    atom, edge, index, crystals, ids, offset = [], [], [], [], [], 0
    for graph in graphs:
        n = len(graph["atom_features"])
        atom.append(graph["atom_features"])
        edge.append(graph["neighbor_features"])
        index.append(graph["neighbor_indices"] + offset)
        crystals.append(torch.arange(offset, offset + n, device=device))
        ids.append(graph["jid"])
        offset += n
    return {
        "ids": ids,
        "atom_features": torch.cat(atom).to(device),
        "neighbor_features": torch.cat(edge).to(device),
        "neighbor_indices": torch.cat(index).to(device),
        "crystal_atom_indices": crystals,
    }
