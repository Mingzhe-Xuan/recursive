import math

import pytest
import torch

from self_evolution.cache import FeatureStore, publish_cache
from self_evolution.data.tasks import TASKS, grouped_split, select_labels
from self_evolution.io import atomic_write, load_tensor
from self_evolution.training.stage import normalization


def test_all_tasks_labels_and_isolated_splits():
    assert len(TASKS) == 29
    assert {"max_efg", "avg_elec_mass", "avg_hole_mass"}.issubset(TASKS)
    values = [0, 1.2, "0", "na", None, math.nan, math.inf, [2], True]
    selected, audit = select_labels(
        [{"jid": str(i), "ehull": v} for i, v in enumerate(values)], "ehull"
    )
    assert selected == {"0": 0, "1": 1.2, "2": 0}
    assert sum(audit.values()) == len(values)
    with pytest.raises(ValueError, match="duplicate"):
        select_labels([{"jid": "same"}, {"jid": "same"}], "ehull")
    labels = {str(i): float(i) for i in range(100)}
    groups = {str(i): str(i // 2) for i in range(100)}
    split = grouped_split(labels, groups)
    assert split == grouped_split({k: 1e6 - v for k, v in labels.items()}, groups)
    assert sorted(sum(split["ids"].values(), [])) == sorted(labels)
    group_sets = [{groups[jid] for jid in ids} for ids in split["ids"].values()]
    assert all(not a & b for i, a in enumerate(group_sets) for b in group_sets[i + 1 :])
    norm = normalization(labels, split["ids"]["train"])
    changed = dict(labels)
    for jid in split["ids"]["test"] + split["ids"]["val"]:
        changed[jid] = 1e20
    assert norm == normalization(changed, split["ids"]["train"])


def test_cache_identity_integrity_and_resume(tmp_path):
    identity = {"task": "ehull", "round": 0, "parent_cache_sha256": None}
    values = {"b": torch.ones(3, 4), "a": torch.arange(8).reshape(2, 4).float()}
    calls = []

    def produce(ids):
        calls.extend(ids)
        return [values[jid] for jid in ids]

    cache = publish_cache(tmp_path, identity, values, produce, shard_size=1)
    assert calls == ["a", "b"]
    torch.testing.assert_close(cache.get("a", 2), values["a"])
    calls.clear()
    publish_cache(tmp_path, identity, values, produce, shard_size=1)
    assert not calls
    with pytest.raises(ValueError, match="mismatch"):
        FeatureStore(tmp_path, {**identity, "task": "other"})
    with pytest.raises(ValueError, match="count"):
        cache.get("a", 3)
    path = tmp_path / "nodes_00000.pt"
    payload = load_tensor(path)
    payload["nodes"][0, 0] += 5
    atomic_write(path, payload, tensor=True)
    with pytest.raises(ValueError, match="checksum"):
        cache.verify_all()
    with pytest.raises(ValueError, match="checksum"):
        FeatureStore(tmp_path).get("a")


def test_interrupted_cache_and_untrusted_paths(tmp_path):
    identity = {"task": "ehull", "round": 1}

    def interrupted(ids):
        if ids == ["b"]:
            raise RuntimeError("simulated interruption")
        return [torch.ones(2, 3)]

    with pytest.raises(RuntimeError):
        publish_cache(tmp_path, identity, ["a", "b"], interrupted, shard_size=1)
    assert not (tmp_path / "manifest.json").exists()
    calls = []

    def resumed(ids):
        calls.extend(ids)
        return [torch.ones(2, 3)]

    cache = publish_cache(tmp_path, identity, ["a", "b"], resumed, shard_size=1)
    assert calls == ["b"]
    assert cache.get("b").shape == (2, 3)
