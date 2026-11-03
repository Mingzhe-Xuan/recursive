"""Standalone diagnostic figures with explicit metric and mode labels."""

import numpy as np


def plot_all(output, scope, residuals, histories, point_clouds):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    variants = scope["variants"]
    colors = ["#2563eb", "#d97706", "#059669"]
    titles = {
        "formation_energy_peratom": "Formation energy",
        "optb88vdw_bandgap": "Band gap",
        "optb88vdw_total_energy": "Total energy",
        "ehull": "Energy above hull",
    }
    n = len(scope["tasks"])

    def save(fig, name, close=True):
        fig.savefig(output / (name + ".png"), dpi=150, bbox_inches="tight")
        fig.savefig(output / (name + ".pdf"), bbox_inches="tight")
        if close:
            plt.close(fig)

    for r in [0, 1, 2]:
        fig, axes = plt.subplots(n, 2, figsize=(12, 3 * n), squeeze=False)
        zoom_limits = []
        for i, task in enumerate(scope["tasks"]):
            for variant, color in zip(variants, colors):
                found = [
                    h
                    for h in histories
                    if (h["task"], h["variant"], h["round"]) == (task, variant, r)
                ]
                if not found:
                    continue
                history = found[0]["history"]
                key = (
                    "train_normalized_ensemble_mse"
                    if "train_normalized_ensemble_mse" in history[0]
                    else "train_normalized_mse"
                )
                epochs = [h["epoch"] for h in history]
                axes[i, 0].plot(epochs, [h[key] for h in history], color=color, label=variant)
                axes[i, 1].plot(
                    epochs, [h["val_mae"] for h in history], color=color, label=variant, alpha=0.8
                )
                best = min(history, key=lambda h: h["val_mae"])
                axes[i, 1].scatter([best["epoch"]], [best["val_mae"]], color=color, s=24)
            axes[i, 0].set(
                title=titles.get(task, task) + " | online training",
                ylabel="Normalized MSE (train mode)",
                yscale="log",
                xlabel="Epoch within stage",
            )
            axes[i, 1].set(
                title=titles.get(task, task) + " | validation",
                ylabel="MAE (eval mode, original units)",
                xlabel="Epoch within stage",
            )
            vals = [
                row["val_mae"]
                for entry in histories
                if entry["task"] == task and entry["round"] == r
                for row in entry["history"]
            ]
            low, high = np.quantile(vals, [0.0, 0.9])
            padding = max((high - low) * 0.12, 1e-6)
            zoom_limits.append((low - padding, high + padding))
            for ax in axes[i]:
                ax.legend(fontsize=8)
                ax.grid(alpha=0.15)
        fig.suptitle(
            f"Round {r}: historical online training loss and eval validation MAE", fontsize=13
        )
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        save(fig, f"learning_round_{r:03d}", close=False)
        for i, task in enumerate(scope["tasks"]):
            axes[i, 1].set_ylim(*zoom_limits[i])
            axes[i, 1].set_title(titles.get(task, task) + " | validation (zoom to 90th pct.)")
        save(fig, f"learning_round_{r:03d}_zoom")
    for r in [1, 2]:
        fig, axes = plt.subplots(n, 3, figsize=(13, 3 * n), squeeze=False)
        for i, task in enumerate(scope["tasks"]):
            for j, variant in enumerate(variants):
                cloud = next(
                    c
                    for c in point_clouds
                    if (c["task"], c["variant"], c["round"]) == (task, variant, r)
                )
                scale = cloud["metrics"]["before"]["rmse"] or 1
                ax = axes[i, j]
                ax.hexbin(
                    cloud["e"] / scale,
                    cloud["delta"] / scale,
                    gridsize=35,
                    extent=(-3, 3, -3, 3),
                    mincnt=1,
                    bins="log",
                    cmap="Blues",
                )
                ax.plot([-3, 3], [-3, 3], "--", color="#d97706", linewidth=1)
                rho = cloud["metrics"]["pearson"]
                label = f"r={rho:.3f}" if rho is not None else "r=undefined"
                ax.set(
                    title=f"{titles.get(task, task)} | {variant}\n{label}; improved={100 * cloud['metrics']['improved_fraction']:.1f}%",
                    xlim=(-3, 3),
                    ylim=(-3, 3),
                    xlabel="Parent residual / parent RMSE",
                    ylabel="Correction / parent RMSE",
                )
        fig.suptitle(
            f"R{r - 1} to R{r} corrections on validation; axes +/-3 RMSE, metrics use all samples",
            fontsize=12,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        save(fig, f"correction_round_{r:03d}")
    fig, axes = plt.subplots(n, 2, figsize=(12, 3 * n), squeeze=False)
    for i, task in enumerate(scope["tasks"]):
        for j, metric in enumerate(["mae", "rmse"]):
            for variant, color in zip(variants, colors):
                for split, style in [("train", "--"), ("val", "-")]:
                    values = [
                        next(
                            row[metric]
                            for row in residuals
                            if (row["task"], row["variant"], row["round"], row["split"])
                            == (task, variant, r, split)
                        )
                        for r in range(3)
                    ]
                    axes[i, j].plot(
                        [0, 1, 2],
                        values,
                        style,
                        marker="o",
                        color=color,
                        label=f"{variant} / {split}",
                    )
            axes[i, j].set(
                title=titles.get(task, task) + " | " + metric.upper(),
                xlabel="Round",
                ylabel="Best-checkpoint eval " + metric.upper(),
                xticks=[0, 1, 2],
            )
            axes[i, j].legend(fontsize=7)
            axes[i, j].grid(alpha=0.15)
    fig.suptitle(
        "Train vs validation residuals from the SAME best checkpoint in eval mode", fontsize=13
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    save(fig, "train_validation_residuals")
