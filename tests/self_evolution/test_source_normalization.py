from copy import deepcopy
import hashlib
import json
import zipfile

import pytest

from self_evolution.data.normalize import canonicalize_records
from self_evolution.data.prepare import load_records
from self_evolution.data.tasks import select_labels


def rows():
    values = [
        {
            "jid": f"id{i}",
            "atoms": {"elements": ["Si"], "coords": [[0, 0, 0]]},
            "formation_energy_peratom": float(i),
            "optb88vdw_bandgap": "na",
        }
        for i in range(10)
    ]
    values.append(deepcopy(values[0]))
    conflict = deepcopy(values[1])
    conflict["formation_energy_peratom"] = -5.0
    conflict["optb88vdw_bandgap"] = 0.0
    values.append(conflict)
    return values


def test_duplicate_labels_are_audited_without_arbitrary_selection():
    canonical, audit = canonicalize_records(rows())
    assert len(canonical) == 10
    assert audit["raw_records"] == 12 and audit["duplicate_rows_removed"] == 2
    assert audit["label_conflicts"] == {
        "formation_energy_peratom": [{"jid": "id1", "values": [-5.0, 1.0]}]
    }
    energy, _ = select_labels(canonical, "formation_energy_peratom")
    gap, _ = select_labels(canonical, "optb88vdw_bandgap")
    assert "id1" not in energy and energy["id0"] == 0
    assert gap == {"id1": 0.0}
    original = rows()
    canonicalize_records(original)
    assert original[1]["formation_energy_peratom"] == 1.0


def test_conflicting_structures_are_not_merged():
    values = rows()
    values[-1]["atoms"]["coords"] = [[0.25, 0, 0]]
    with pytest.raises(ValueError, match="conflicting structures"):
        canonicalize_records(values)


def test_snapshot_raw_and_unique_gates(tmp_path):
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("records.json", json.dumps(rows()))
    source = {
        "artifacts": [
            {"size_bytes": path.stat().st_size, "md5": hashlib.md5(path.read_bytes()).hexdigest()}
        ],
        "json_member": "records.json",
        "expected_raw_records": 12,
        "expected_structures": 10,
    }
    canonical, audit = load_records(path, source)
    assert len(canonical) == 10 and audit["raw_records"] == 12
    with pytest.raises(ValueError, match="raw snapshot"):
        load_records(path, {**source, "expected_raw_records": 11})
    with pytest.raises(ValueError, match="normalized structure"):
        load_records(path, {**source, "expected_structures": 11})
    with pytest.raises(ValueError, match="duplicate-ID"):
        load_records(path, {**source, "expected_duplicate_ids": 3})
    with pytest.raises(ValueError, match="label conflicts"):
        load_records(path, {**source, "expected_label_conflicts": {}})
