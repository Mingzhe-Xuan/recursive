import copy
import gzip
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from self_evolution.io import file_hash
from residual_scaling.pipeline import prepare_task, run_variant
from residual_scaling.reporting import summarize
from recursive_diagnostics.analysis import analyze
from recursive_diagnostics.metrics import (
    correction_summary,
    correlation,
    curve_summary,
    ranks,
    split_metrics,
)


def test_perfect_correction_and_high_correlation_harm():
    e = np.array([-2.0, -1.0, 1.0, 2.0])
    good = correction_summary(e, e / 2)
    assert good["pearson"] == pytest.approx(1)
    assert good["improved_count"] == 4 and good["worse_count"] == 0
    assert good["after"]["mae"] == pytest.approx(0.75)
    assert good["mae_gain_percent"] == pytest.approx(50)
    assert good["least_squares_multiplier_diagnostic_only"] == pytest.approx(2)
    bad = correction_summary(e, 3 * e)
    assert bad["pearson"] == pytest.approx(1) and bad["spearman"] == pytest.approx(1)
    assert bad["worse_count"] == 4 and bad["harmful_overshoot_fraction"] == 1
    assert bad["after"]["mae"] == pytest.approx(3)
    assert bad["least_squares_multiplier_diagnostic_only"] == pytest.approx(1 / 3)
    assert bad["mse_gain"] == pytest.approx(-7.5)
    reversed_ = correction_summary(e, -e)
    assert reversed_["pearson"] == pytest.approx(-1) and reversed_["worse_count"] == 4


def test_degenerate_ties_and_material_accounting():
    assert correlation([1, 1], [2, 3]) is None
    np.testing.assert_equal(ranks([2, 1, 1, 3]), [3, 1.5, 1.5, 4])
    result = correction_summary([1, 1, 1, 1], [0, 0.5, -1, 1e-10])
    assert result["pearson"] is None
    assert (result["improved_count"], result["worse_count"], result["unchanged_count"]) == (1, 1, 2)
    assert result["mae_gain"] == pytest.approx(
        result["benefit_contribution"] - result["harm_contribution"] + result["tie_contribution"]
    )
    zero = correction_summary([0, 0], [0, 0])
    assert zero["unchanged_count"] == 2 and zero["least_squares_multiplier_diagnostic_only"] is None
    with pytest.raises(ValueError):
        correction_summary([1, np.nan], [1, 1])
    with pytest.raises(ValueError):
        correction_summary([1, 2], [1])


def test_test_labels_never_enter_metrics_and_history_modes():
    task = {
        "labels": {"a": 1.0, "b": 2.0, "secret": -1e30},
        "split": {"ids": {"train": ["a"], "val": ["b"], "test": ["secret"]}},
    }
    pred = {"a": 0.0, "b": 0.0}
    before = split_metrics(task, pred, 2)
    changed = copy.deepcopy(task)
    changed["labels"]["secret"] = float("nan")
    assert split_metrics(changed, pred, 2) == before
    assert before["train"]["rmse"] == 1 and before["val"]["rmse"] == 2
    history = [
        {"epoch": i, "train_normalized_ensemble_mse": 1 / i, "val_mae": float(i)}
        for i in range(1, 9)
    ]
    curve = curve_summary(history)
    assert curve["best_epoch"] == 1 and curve["epochs"] == 8
    assert curve["late_train_mse_decline_percent"] > 0 and curve["late_val_mae_decline_percent"] < 0
    assert "online train-mode" in curve["train_curve_mode"]


def test_real_cached_study_readonly_end_to_end(tmp_path_factory):
    spec = importlib.util.spec_from_file_location(
        "residual_fixture", Path("tests/residual_scaling/test_study.py")
    )
    fixture_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_module)
    prepared, legacy, base, study, task = fixture_module.reference.__wrapped__(tmp_path_factory)
    root = tmp_path_factory.mktemp("diagnostic-case")
    completed = root / "study"
    prepare_task(prepared, legacy, completed, task["task"], base, study, "cpu")
    for variant in ["raw_residual", "feature_residual"]:
        run_variant(prepared, legacy, completed, task["task"], variant, base, study, "cpu")
    summarize(completed, study)
    hashes = {
        p: file_hash(p)
        for directory in [prepared, legacy, completed]
        for p in directory.rglob("*")
        if p.is_file()
    }
    output = root / "diagnostic"
    result = analyze(completed, prepared, output, make_plots=True)
    assert result["status"] == "complete" and not result["test_labels_used"]
    assert (
        len(result["residuals"]) == 18
        and len(result["corrections"]) == 12
        and len(result["learning_curves"]) == 7
    )
    for row in result["corrections"]:
        assert row["n"] == len(task["split"]["ids"][row["split"]])
        assert row["n"] == row["improved_count"] + row["worse_count"] + row["unchanged_count"]
    with gzip.open(output / "validation_materials.csv.gz", "rt") as f:
        lines = f.readlines()
    assert len(lines) == 1 + 6 * len(task["split"]["ids"]["val"])
    assert len(list(output.glob("*.png"))) == 9
    assert all(file_hash(p) == expected for p, expected in hashes.items())
    with pytest.raises(ValueError, match="outside"):
        analyze(completed, prepared, completed / "bad", make_plots=False)
