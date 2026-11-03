"""Load the audited invariant branch without unused training/equivariant dependencies."""

import ast
from collections import defaultdict
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import sys
import types
from typing import Optional, Tuple, Union

import numpy as np
import torch
from torch import Tensor, nn

from self_evolution.io import read_json

ROOT = Path(__file__).parent / "upstream"


def audit():
    manifest = read_json(ROOT / "manifest.json")
    for name, metadata in manifest["files"].items():
        data = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise ValueError(f"official source checksum mismatch: {name}")
    return manifest


def selected_module(filename, names, namespace, repair_super=False):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    body = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names
    ]
    if {node.name for node in body} != set(names):
        raise ValueError("official declarations changed")
    if repair_super:
        changes = 0
        for node in ast.walk(ast.Module(body=body, type_ignores=[])):
            if isinstance(node, ast.Name) and node.id == "MatformerConv":
                node.id = "ComformerConv"
                changes += 1
        if changes != 1:
            raise ValueError("expected exactly one upstream superclass-name repair")
    name = __name__ + ".loaded_" + filename.replace(".py", "")
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / filename)
    module.__dict__.update(namespace)
    sys.modules[name] = module
    tree = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    exec(compile(tree, module.__file__, "exec"), module.__dict__)
    return module


@lru_cache(maxsize=1)
def model_components():
    audit()
    from torch_geometric.nn.conv import MessagePassing
    from torch_geometric.typing import Adj, OptTensor, PairTensor
    from torch_scatter import scatter

    common = dict(
        torch=torch,
        nn=nn,
        np=np,
        math=math,
        Tensor=Tensor,
        Optional=Optional,
        Tuple=Tuple,
        Union=Union,
        scatter=scatter,
    )
    utils = selected_module("utils.py", ["RBFExpansion"], common)
    layers = selected_module(
        "transformer.py",
        ["ComformerConv", "ComformerConv_edge"],
        {
            **common,
            "MessagePassing": MessagePassing,
            "Adj": Adj,
            "OptTensor": OptTensor,
            "PairTensor": PairTensor,
        },
        repair_super=True,
    )
    defaults = dict(
        atom_input_features=92,
        node_features=256,
        edge_features=256,
        triplet_input_features=256,
        fc_features=256,
        output_features=1,
        conv_layers=4,
        node_layer_head=1,
        classification=False,
        use_angle=False,
        link="identity",
    )

    def configuration(**kwargs):
        return types.SimpleNamespace(**{**defaults, **kwargs})

    model = selected_module(
        "comformer.py",
        ["bond_cosine", "iComformer"],
        {
            **common,
            "RBFExpansion": utils.RBFExpansion,
            "ComformerConv": layers.ComformerConv,
            "ComformerConv_edge": layers.ComformerConv_edge,
            "iComformerConfig": configuration,
        },
    )
    return model.iComformer, configuration


@lru_cache(maxsize=1)
def graph_components():
    audit()
    from jarvis.core.specie import get_node_attributes
    from torch_geometric.data import Data

    names = [
        "angle_from_array",
        "correct_coord_sys",
        "same_line",
        "same_plane",
        "canonize_edge",
        "nearest_neighbor_edges_submit",
        "compute_bond_cosine",
        "build_undirected_edgedata",
        "PygGraph",
    ]
    return selected_module(
        "graphs.py",
        names,
        dict(
            np=np,
            torch=torch,
            defaultdict=defaultdict,
            Optional=Optional,
            Data=Data,
            get_node_attributes=get_node_attributes,
        ),
    ).PygGraph
