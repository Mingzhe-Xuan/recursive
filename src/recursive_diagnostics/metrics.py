"""Signed residual diagnostics in original property units."""

import numpy as np


def vector(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("expected a finite, nonempty one-dimensional vector")
    return values


def correlation(a, b):
    a, b = vector(a), vector(b)
    if a.shape != b.shape:
        raise ValueError("vector sizes differ")
    a, b = a - a.mean(), b - b.mean()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.clip(a @ b / denominator, -1, 1)) if denominator > 0 else None


def ranks(values):
    _, inverse, counts = np.unique(vector(values), return_inverse=True, return_counts=True)
    return (np.cumsum(counts) - (counts - 1) / 2)[inverse]


def residual_summary(residual, scale=1.0):
    e = vector(residual)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("invalid normalization scale")
    return {
        "n": len(e),
        "mae": float(np.abs(e).mean()),
        "mse": float(np.mean(e**2)),
        "rmse": float(np.sqrt(np.mean(e**2))),
        "bias_y_minus_prediction": float(e.mean()),
        "std": float(e.std()),
        "normalized_rmse": float(np.sqrt(np.mean(e**2)) / scale),
    }


def correction_summary(previous_residual, correction, tie_atol=1e-8):
    e, delta = vector(previous_residual), vector(correction)
    if e.shape != delta.shape or tie_atol < 0:
        raise ValueError("invalid correction dimensions or tie tolerance")
    after = e - delta
    gain = np.abs(e) - np.abs(after)
    improved, worse = gain > tie_atol, gain < -tie_atol
    tied = ~(improved | worse)
    directional = (e * delta > 0) & (np.abs(e) > tie_atol) & (np.abs(delta) > tie_atol)
    nonzero_delta = np.abs(delta) > tie_atol
    harmful_overshoot = directional & (np.abs(delta) > 2 * np.abs(e)) & worse
    before_metrics, after_metrics = residual_summary(e), residual_summary(after)
    delta_square = float(np.mean(delta**2))
    cross = float(2 * np.mean(e * delta))
    np.testing.assert_allclose(
        before_metrics["mse"] - after_metrics["mse"], cross - delta_square, atol=1e-12, rtol=1e-10
    )
    denominator = np.linalg.norm(e) * np.linalg.norm(delta)
    return {
        "n": len(e),
        "tie_atol": tie_atol,
        "pearson": correlation(e, delta),
        "spearman": correlation(ranks(e), ranks(delta)),
        "uncentered_cosine": float(e @ delta / denominator) if denominator > 0 else None,
        "improved_count": int(improved.sum()),
        "worse_count": int(worse.sum()),
        "unchanged_count": int(tied.sum()),
        "improved_fraction": float(improved.mean()),
        "worse_fraction": float(worse.mean()),
        "unchanged_fraction": float(tied.mean()),
        "direction_correct_fraction": float(directional.mean()),
        "nonzero_correction_fraction": float(nonzero_delta.mean()),
        "harmful_overshoot_fraction": float(harmful_overshoot.mean()),
        "before": before_metrics,
        "after": after_metrics,
        "correction_rmse": float(np.sqrt(delta_square)),
        "correction_bias": float(delta.mean()),
        "correction_to_parent_rmse": float(np.sqrt(delta_square) / before_metrics["rmse"])
        if before_metrics["rmse"]
        else None,
        "mae_gain": float(gain.mean()),
        "mae_gain_percent": float(100 * gain.mean() / before_metrics["mae"])
        if before_metrics["mae"]
        else None,
        "benefit_contribution": float(gain[improved].sum() / len(e)),
        "harm_contribution": float(-gain[worse].sum() / len(e)),
        "tie_contribution": float(gain[tied].sum() / len(e)),
        "mse_cross_term": cross,
        "mse_correction_penalty": delta_square,
        "mse_gain": cross - delta_square,
        "least_squares_multiplier_diagnostic_only": float(np.mean(e * delta) / delta_square)
        if delta_square
        else None,
    }


def split_metrics(task, predictions, scale):
    result = {}
    for split in ["train", "val"]:
        ids = task["split"]["ids"][split]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate split ID")
        residual = np.array([task["labels"][jid] - predictions[jid] for jid in ids])
        result[split] = residual_summary(residual, scale)
    return result


def curve_summary(history):
    if not history:
        raise ValueError("empty history")
    key = (
        "train_normalized_ensemble_mse"
        if "train_normalized_ensemble_mse" in history[0]
        else "train_normalized_mse"
    )
    train = vector([row[key] for row in history])
    val = vector([row["val_mae"] for row in history])
    best = int(np.argmin(val))
    width = min(20, max(1, len(history) // 4))

    def decline(values):
        if len(values) < 2 * width:
            return None
        previous = values[-2 * width : -width].mean()
        return float(100 * (previous - values[-width:].mean()) / previous) if previous else None

    return {
        "epochs": len(history),
        "train_metric": key,
        "train_curve_mode": "online train-mode MSE, not fixed-checkpoint eval MSE",
        "validation_metric": "eval MAE in original units",
        "best_epoch": history[best]["epoch"],
        "best_val_mae": float(val[best]),
        "last_val_mae": float(val[-1]),
        "last_train_normalized_mse": float(train[-1]),
        "train_mse_at_best_val_epoch": float(train[best]),
        "late_window_epochs": width,
        "late_train_mse_decline_percent": decline(train),
        "late_val_mae_decline_percent": decline(val),
        "last_val_above_best_percent": float(100 * (val[-1] - val[best]) / val[best])
        if val[best]
        else None,
    }
