import importlib.util
from pathlib import Path
import shutil

import pytest
import torch

from self_evolution.backbones.cgcnn import CGCNNStage, ModelConfig
from self_evolution.data.graphs import GraphConfig, collate_graphs, make_graph, structure_group
from self_evolution.io import file_hash, read_json


def record(jid="silicon", length=5.4):
    return {
        "jid": jid,
        "atoms": {
            "lattice_mat": [[length, 0, 0], [0, length, 0], [0, 0, length]],
            "elements": ["Si", "Si"],
            "cartesian": False,
            "coords": [[0, 0, 0], [0.25, 0.25, 0.25]],
        },
    }


def test_pinned_source_integrity():
    root = Path(__file__).parents[2] / "src/self_evolution/backbones/cgcnn/upstream"
    source = read_json(root / "source.json")
    assert source["commit"] == "f42ab233c4ee0c416879d6bc2d22a264418413ad"
    for name, checksum in source["files"].items():
        assert file_hash(root / name) == checksum


def test_native_forward_and_cached_projection_gradients():
    torch.set_num_threads(1)
    torch.manual_seed(123)
    batch = collate_graphs(
        [make_graph(record(), GraphConfig()), make_graph(record("second", 5.6), GraphConfig())]
    )
    config = ModelConfig(hidden=8, convolutions=2, head_hidden=12, head_layers=2)
    model = CGCNNStage(config).eval()
    torch.testing.assert_close(model(batch), model.forward_native(batch), rtol=0, atol=0)
    features = model.encode_nodes(batch).detach().requires_grad_(True)
    newer = CGCNNStage(config, recursive=True).train()
    before = newer.projection.weight.detach().clone()
    optimizer = torch.optim.Adam(newer.parameters())
    newer(batch, features).square().mean().backward()
    assert features.grad is None
    assert newer.projection.weight.grad is not None
    optimizer.step()
    assert not torch.equal(before, newer.projection.weight)
    assert all(parameter.grad is None for parameter in model.parameters())
    with pytest.raises(ValueError, match="requires"):
        newer(batch)
    with pytest.raises(ValueError, match="native stage"):
        model(batch, features)


def test_geometry_matches_reference_cifdata(tmp_path):
    root = Path(__file__).parents[2] / "src/self_evolution/backbones/cgcnn/upstream"
    # The separately fetched pinned data module is an independent graph oracle.
    spec = importlib.util.spec_from_file_location("upstream_cgcnn_data", root / "data.py")
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    from self_evolution.data.graphs import structure_from_record

    data = record()
    structure_from_record(data["atoms"]).to(filename=tmp_path / "silicon.cif")
    (tmp_path / "id_prop.csv").write_text("silicon,0\n")
    shutil.copyfile(root / "atom_init.json", tmp_path / "atom_init.json")
    expected, _, _ = reference.CIFData(str(tmp_path))[0]
    actual = make_graph(data, GraphConfig())
    torch.testing.assert_close(actual["atom_features"], expected[0], rtol=0, atol=0)
    torch.testing.assert_close(actual["neighbor_features"], expected[1], rtol=0, atol=1e-5)
    torch.testing.assert_close(actual["neighbor_indices"], expected[2], rtol=0, atol=0)


def test_periodic_group_and_sparse_padding():
    from self_evolution.data.graphs import structure_from_record

    crystal = structure_from_record(record()["atoms"])
    translated = crystal.copy()
    translated.translate_sites(range(len(crystal)), [0.32, 0.18, 0.6], frac_coords=True)
    assert structure_group(crystal) == structure_group(translated)
    assert structure_group(crystal) == structure_group(
        crystal.__class__.from_sites(list(crystal)[::-1])
    )
    graph = make_graph(record(length=30), GraphConfig())
    assert graph["valid_neighbor_counts"].eq(0).all()
    assert graph["neighbor_indices"].eq(0).all()
    assert graph["neighbor_features"].shape == (2, 12, 41)
