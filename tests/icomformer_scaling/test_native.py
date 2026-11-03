import copy
from pathlib import Path

import pytest
import torch

from self_evolution.io import atomic_write, file_hash
from icomformer_scaling.source import audit, graph_components
from icomformer_scaling.graphs import GraphStore, collate_graphs, make_graph
from icomformer_scaling.model import IComformerStage, ModelConfig


@pytest.fixture
def graphs():
    torch.set_num_threads(1)
    return [
        make_graph(
            {
                "jid": f"tiny-{i}",
                "atoms": {
                    "lattice_mat": [[3 + i * 0.1, 0, 0], [0, 3.2, 0], [0, 0, 3.4]],
                    "coords": [[0, 0, 0], [0.25, 0.25, 0.25]][: i + 1],
                    "elements": ["Si", "Ge"][: i + 1],
                    "cartesian": False,
                },
            },
            {"cutoff": 4.0, "neighbors": 25},
        )
        for i in range(2)
    ]


def small_model(recursive=False):
    return IComformerStage(
        ModelConfig(hidden=8, edge_features=8, triplet_features=8, head_hidden=8), recursive
    )


def test_exact_upstream_audit():
    source = audit()
    assert source["commit"] == "594e8bad8cd0b24a207c818e09b39ccc0aebcd4d"
    assert len(source["files"]) == 5
    assert (
        "GNU GENERAL PUBLIC LICENSE"
        in Path("src/icomformer_scaling/source/upstream/LICENSE").read_text()
    )


def test_native_forward_gradient_and_buffers(graphs):
    torch.manual_seed(4)
    wrapped = small_model().train()
    reference = copy.deepcopy(wrapped).train()
    batch = collate_graphs(graphs)
    actual, expected = wrapped(batch), reference.forward_native(batch)
    torch.testing.assert_close(actual, expected, atol=2e-5, rtol=1e-4)
    actual.square().sum().backward()
    expected.square().sum().backward()
    for (_, a), (_, b) in zip(wrapped.named_parameters(), reference.named_parameters()):
        if a.grad is None:
            assert b.grad is None
        else:
            torch.testing.assert_close(a.grad, b.grad, atol=2e-5, rtol=1e-4)
    for name, buffer in wrapped.named_buffers():
        torch.testing.assert_close(buffer, dict(reference.named_buffers())[name])


def test_batch_single_rotation_and_native_geometry(graphs):
    model = small_model().eval()
    batch = collate_graphs(graphs)
    with torch.no_grad():
        expected = model(batch)
        torch.testing.assert_close(
            expected, torch.cat([model(collate_graphs([g])) for g in graphs]), atol=2e-5, rtol=1e-4
        )
        rotation = torch.tensor([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        rotated = copy.deepcopy(graphs)
        for g in rotated:
            g["edge_attr"] = g["edge_attr"] @ rotation
            g["edge_nei"] = g["edge_nei"] @ rotation
        torch.testing.assert_close(model(collate_graphs(rotated)), expected, atol=2e-5, rtol=1e-4)
    from jarvis.core.atoms import Atoms

    atoms = Atoms(
        lattice_mat=[[3, 0, 0], [0, 3.2, 0], [0, 0, 3.4]],
        coords=[[0, 0, 0]],
        elements=["Si"],
        cartesian=False,
    )
    native = graph_components().atom_dgl_multigraph(
        atoms=atoms,
        cutoff=4.0,
        max_neighbors=25,
        use_lattice=True,
        use_canonize=False,
        compute_line_graph=False,
    )
    torch.testing.assert_close(native.edge_index, graphs[0]["edge_index"], atol=0, rtol=0)
    torch.testing.assert_close(native.edge_attr, graphs[0]["edge_attr"], atol=0, rtol=0)
    torch.testing.assert_close(native.edge_nei, graphs[0]["edge_nei"], atol=0, rtol=0)
    assert native.x.shape == (1, 92)


def test_projection_detaches_parent_and_preserves_raw_graph(graphs):
    model = small_model(True).train()
    batch = collate_graphs(graphs)
    raw = batch["data"].x.clone()
    parent = torch.randn(len(raw), 8, requires_grad=True)
    model(batch, parent).sum().backward()
    assert parent.grad is None and model.projection.weight.grad is not None
    torch.testing.assert_close(batch["data"].x, raw)
    with pytest.raises(ValueError):
        model(batch, torch.randn(len(raw), 9))


def test_tensor_only_graph_store_checksums(graphs, tmp_path):
    entries = {}
    for i, value in enumerate(graphs):
        path = tmp_path / f"{i}.pt"
        atomic_write(path, value, tensor=True)
        entries[value["jid"]] = {
            "file": path.name,
            "atoms": len(value["atom_features"]),
            "sha256": file_hash(path),
        }
    atomic_write(
        tmp_path / "manifest.json", {"status": "complete", "entries": entries, "failures": {}}
    )
    store = GraphStore(tmp_path)
    assert len(store.get("tiny-0")["atom_features"]) == 1
    bad = tmp_path / "1.pt"
    bad.write_bytes(bad.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        store.get("tiny-1")
