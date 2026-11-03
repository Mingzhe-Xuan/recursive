"""Independent stage initialization, fixed R0 units, exact-budget residual updates."""

from dataclasses import asdict
import math
from pathlib import Path
import time

import torch

from self_evolution.io import atomic_write, derived_seed, file_hash, load_tensor, read_json
from self_evolution.training.stage import batches, synchronize
from icomformer_scaling.graphs import collate_graphs
from icomformer_scaling.model import IComformerStage, ModelConfig


def load_stage(path, device="cpu"):
    checkpoint = load_tensor(Path(path))
    model = IComformerStage(ModelConfig(**checkpoint["model_config"]), checkpoint["recursive"])
    model.load_state_dict(checkpoint["model"])
    return model.to(device).eval(), checkpoint


def prediction(model, batch, nodes, previous, norm, variant):
    hidden = model.encode_nodes(batch, nodes)
    value = norm["std"] * model.readout(hidden, batch)
    return hidden, value + (norm["mean"] if variant == "direct" else previous.detach())


def input_batch(ids, graphs, parent, variant, device):
    batch = collate_graphs([graphs.get(jid) for jid in ids], device)
    nodes, previous = (
        (None, None)
        if parent is None
        else parent.batch(ids, graphs, device, variant != "raw_residual")
    )
    return batch, nodes, previous


@torch.no_grad()
def evaluate(model, graphs, task, parent, norm, variant, batch_size, device, split="val"):
    model.eval()
    error, count = 0.0, 0
    for ids in batches(task["split"]["ids"][split], batch_size):
        batch, nodes, previous = input_batch(ids, graphs, parent, variant, device)
        _, values = prediction(model, batch, nodes, previous, norm, variant)
        if not torch.isfinite(values).all():
            raise FloatingPointError("non-finite iComformer validation")
        error += sum(
            abs(value - task["labels"][jid]) for jid, value in zip(ids, values.cpu().tolist())
        )
        count += len(ids)
    return error / count


def train_stage(
    output,
    config,
    task,
    graphs,
    parent,
    norm,
    variant,
    round_index,
    identity,
    device="cuda",
    budget=None,
    interrupt_after_epochs=None,
):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if variant not in config["variants"] or (round_index == 0 and variant != "direct"):
        raise ValueError("invalid iComformer branch")
    if variant != "direct" and (parent is None or budget is None or budget < 1):
        raise ValueError("residual stage requires its own parent and matched update budget")
    if (output / "training.json").exists():
        done = read_json(output / "training.json")
        if (
            done["identity"] != identity
            or file_hash(output / "best.pt") != done["checkpoint_sha256"]
            or (budget is not None and done["optimizer_steps"] != budget)
        ):
            raise ValueError("completed stage identity/budget mismatch")
        return done
    training = config["training"]
    seed = identity["stage_seed"]
    torch.manual_seed(seed)
    if torch.device(device).type == "cuda":
        torch.cuda.manual_seed_all(seed)
    recursive = parent is not None and variant != "raw_residual"
    model = IComformerStage(ModelConfig(**config["model"]), recursive).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=training["learning_rate"], weight_decay=training["weight_decay"]
    )
    epoch, steps, best, stale, elapsed, history = 0, 0, math.inf, 0, 0.0, []
    if (output / "last.pt").exists():
        state = load_tensor(output / "last.pt")
        if state["identity"] != identity:
            raise ValueError("iComformer resume identity changed")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        epoch, steps, best, stale, elapsed, history = [
            state[k] for k in ["epoch", "steps", "best", "stale", "elapsed", "history"]
        ]
        torch.set_rng_state(state["torch_rng"])
        if state["cuda_rng"] and torch.device(device).type == "cuda":
            torch.cuda.set_rng_state_all(state["cuda_rng"])
    atomic_write(
        output / "config.json",
        {
            "identity": identity,
            "config": config,
            "normalization": norm,
            "eta": 1.0,
            "budget_steps": budget,
        },
    )
    synchronize(device)
    started = time.perf_counter()
    while (
        steps < budget
        if budget is not None
        else epoch < training["epochs"] and stale < training["patience"]
    ):
        model.train()
        loss_sum, count = 0.0, 0
        for ids in batches(
            task["split"]["ids"]["train"], training["batch_size"], seed=derived_seed(seed, epoch)
        ):
            if budget is not None and steps >= budget:
                break
            batch, nodes, previous = input_batch(ids, graphs, parent, variant, device)
            _, values = prediction(model, batch, nodes, previous, norm, variant)
            truth = torch.tensor([task["labels"][jid] for jid in ids], device=device)
            loss = (((values - truth) / norm["std"]) ** 2).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite iComformer training loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if not torch.stack(
                [torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]
            ).all():
                raise FloatingPointError("non-finite iComformer gradient")
            optimizer.step()
            steps += 1
            loss_sum += loss.item() * len(ids)
            count += len(ids)
        epoch += 1
        val = evaluate(model, graphs, task, parent, norm, variant, training["batch_size"], device)
        if val < best:
            best, stale = val, 0
            atomic_write(
                output / "best.pt",
                {
                    "model": model.state_dict(),
                    "model_config": asdict(model.config),
                    "recursive": recursive,
                    "identity": identity,
                    "norm": norm,
                    "prediction_role": "absolute" if variant == "direct" else "residual_delta",
                    "eta": 1.0,
                    "ensemble_required": variant != "direct",
                    "epoch": epoch,
                    "val_mae": val,
                },
                tensor=True,
            )
        else:
            stale += 1
        synchronize(device)
        duration = elapsed + time.perf_counter() - started
        history.append(
            {
                "epoch": epoch,
                "optimizer_steps": steps,
                "train_normalized_mse"
                if variant == "direct"
                else "train_normalized_ensemble_mse": loss_sum / count,
                "val_mae": val,
                "elapsed_seconds": duration,
            }
        )
        atomic_write(
            output / "last.pt",
            {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "identity": identity,
                "epoch": epoch,
                "steps": steps,
                "best": best,
                "stale": stale,
                "elapsed": duration,
                "history": history,
                "torch_rng": torch.get_rng_state(),
                "cuda_rng": torch.cuda.get_rng_state_all()
                if torch.device(device).type == "cuda"
                else [],
            },
            tensor=True,
        )
        atomic_write(output / "history.json", history)
        print(
            f"{task['task']} {variant} r={round_index} epoch={epoch} steps={steps}/{budget or 'early-stop'} val_mae={val:.9g}",
            flush=True,
        )
        if (
            interrupt_after_epochs is not None
            and epoch >= interrupt_after_epochs
            and (budget is None or steps < budget)
        ):
            return None
    done = {
        "identity": identity,
        "epochs": epoch,
        "optimizer_steps": steps,
        "budget_steps": budget,
        "stage_seed": seed,
        "best_val_mae": best,
        "checkpoint_sha256": file_hash(output / "best.pt"),
        "normalization": norm,
        "parameters": sum(p.numel() for p in model.parameters()),
        "training_and_validation_seconds": elapsed + time.perf_counter() - started,
        "stop_reason": "matched_direct_updates"
        if budget is not None
        else "validation_patience"
        if stale >= training["patience"]
        else "epoch_limit",
        "history": history,
    }
    atomic_write(output / "training.json", done)
    return done
