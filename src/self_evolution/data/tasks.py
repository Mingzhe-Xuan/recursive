"""The 29 scalar regression tasks in the original ALIGNN JARVIS table."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from typing import Any

from self_evolution.io import digest

# Order follows the official published regression table, not train_all_jv.py.
TASKS = {
    "formation_energy_peratom": "eV/atom",
    "optb88vdw_bandgap": "eV",
    "optb88vdw_total_energy": "eV/atom",
    "ehull": "eV",
    "mbj_bandgap": "eV",
    "bulk_modulus_kv": "GPa",
    "shear_modulus_gv": "GPa",
    "magmom_oszicar": "mu_B",
    "slme": "%",
    "spillage": "dimensionless",
    "kpoint_length_unit": "angstrom",
    "encut": "eV",
    "epsx": "dimensionless",
    "epsy": "dimensionless",
    "epsz": "dimensionless",
    "mepsx": "dimensionless",
    "mepsy": "dimensionless",
    "mepsz": "dimensionless",
    "dfpt_piezo_max_dielectric": "dimensionless",
    "dfpt_piezo_max_dij": "dataset_native_C/N",
    "dfpt_piezo_max_eij": "C/m^2",
    "exfoliation_energy": "meV/atom",
    "max_efg": "10^21 V/m^2",
    "avg_elec_mass": "electron_mass",
    "avg_hole_mass": "electron_mass",
    "n-Seebeck": "microV/K",
    "n-powerfact": "microW/(m K^2)",
    "p-Seebeck": "microV/K",
    "p-powerfact": "microW/(m K^2)",
}


def numeric_label(value: Any) -> tuple[float | None, str]:
    if value is None or value in ("na", "NA", "", "None"):
        return None, "missing"
    if isinstance(value, (bool, list, dict, tuple)):
        return None, "non_scalar"
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None, "non_numeric"
    return (result, "valid") if math.isfinite(result) else (None, "non_finite")


def select_labels(records: list[dict], task: str) -> tuple[dict[str, float], dict]:
    if task not in TASKS:
        raise ValueError(f"unknown task: {task}")
    labels, counts = {}, Counter()
    seen = set()
    for row in records:
        jid = row["jid"]
        if not isinstance(jid, str) or not jid or jid in seen:
            raise ValueError(f"invalid or duplicate structure ID: {jid}")
        seen.add(jid)
        value, reason = numeric_label(row.get(task))
        counts[reason] += 1
        if value is not None:
            labels[jid] = value
    return labels, dict(counts)


def grouped_split(labels: dict[str, float], groups: dict[str, str], seed: int = 123) -> dict:
    """Split equivalent-structure groups without consulting numeric label values."""
    if not set(labels).issubset(groups):
        raise ValueError("missing structure-group identities")
    members = defaultdict(list)
    for jid in sorted(labels):
        members[groups[jid]].append(jid)
    keys = sorted(members)
    if len(keys) < 10:
        raise ValueError("at least ten independent groups required for 80/10/10 split")
    random.Random(seed).shuffle(keys)
    ntest, nval = max(1, int(len(keys) * 0.1)), max(1, int(len(keys) * 0.1))
    slices = {
        "train": keys[: -(ntest + nval)],
        "val": keys[-(ntest + nval) : -ntest],
        "test": keys[-ntest:],
    }
    result = {
        k: sorted(jid for group in values for jid in members[group]) for k, values in slices.items()
    }
    return {
        "schema": 1,
        "source": "project_grouped_80_10_10",
        "seed": seed,
        "ids": result,
        "groups_hash": digest(groups),
        "membership_hash": digest(result),
        "counts": {k: len(v) for k, v in result.items()},
    }
