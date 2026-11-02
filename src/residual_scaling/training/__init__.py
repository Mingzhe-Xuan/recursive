"""Exact-budget residual stages selected on cumulative validation predictions."""

from dataclasses import asdict
import math
from pathlib import Path
import time

import torch

from self_evolution.backbones.cgcnn import CGCNNStage, ModelConfig
from self_evolution.data.graphs import collate_graphs
from self_evolution.io import atomic_write, derived_seed, file_hash, load_tensor, read_json
from self_evolution.training.stage import batches, synchronize


def compose_prediction(parent, delta, norm, eta=1.0):
    return parent.detach() + eta * norm["std"] * delta


def forward(model, batch, nodes, previous, norm, eta):
    hidden = model.encode_nodes(batch, nodes)
    return hidden, compose_prediction(previous, model.readout(hidden, batch), norm, eta)


@torch.no_grad()
def validation(model, graphs, task, parent, norm, variant, eta, batch_size, device):
    model.eval()
    error, count = 0.0, 0
    for ids in batches(task["split"]["ids"]["val"], batch_size):
        batch = collate_graphs([graphs.get(jid) for jid in ids], device)
        nodes, predictions = parent.batch(ids, graphs, device, variant == "feature_residual")
        _, predictions = forward(model, batch, nodes, predictions, norm, eta)
        for jid, value in zip(ids, predictions.cpu().tolist()):
            if not math.isfinite(value):
                raise FloatingPointError("non-finite ensemble validation prediction")
            error += abs(value - task["labels"][jid])
            count += 1
    return error / count


def train_stage(
    output,
    base,
    task,
    graphs,
    parent,
    norm,
    variant,
    eta,
    budget,
    seed,
    identity,
    device,
    interrupt_after_epochs=None,
):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if variant not in ["raw_residual", "feature_residual"] or budget < 1:
        raise ValueError("invalid residual stage")
    if (output / "training.json").exists():
        done = read_json(output / "training.json")
        if (
            done["identity"] != identity
            or done["optimizer_steps"] != budget
            or file_hash(output / "best.pt") != done["checkpoint_sha256"]
        ):
            raise ValueError("completed residual stage identity/budget changed")
        return done
    torch.manual_seed(seed)
    if torch.device(device).type == "cuda":
        torch.cuda.manual_seed_all(seed)
    cfg = ModelConfig(**base["model"])
    model = CGCNNStage(cfg, recursive=variant == "feature_residual").to(device)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=base["training"]["learning_rate"],
        weight_decay=base["training"]["weight_decay"],
    )
    epoch, steps, best, elapsed, history = 0, 0, math.inf, 0.0, []
    last_path = output / "last.pt"
    if last_path.exists():
        saved = load_tensor(last_path)
        if saved["identity"] != identity:
            raise ValueError("residual resume identity mismatch")
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        epoch, steps, best, elapsed, history = [
            saved[k] for k in ["epoch", "steps", "best", "elapsed", "history"]
        ]
        torch.set_rng_state(saved["torch_rng"])
        if saved["cuda_rng"] and torch.device(device).type == "cuda":
            torch.cuda.set_rng_state_all(saved["cuda_rng"])
    atomic_write(
        output / "config.json",
        {
            "identity": identity,
            "base": base,
            "normalization": norm,
            "eta": eta,
            "budget_steps": budget,
            "stage_seed": seed,
        },
    )
    synchronize(device)
    started = time.perf_counter()
    while steps < budget:
        model.train()
        loss_sum, count = 0.0, 0
        for ids in batches(
            task["split"]["ids"]["train"],
            base["training"]["batch_size"],
            seed=derived_seed(seed, epoch),
        ):
            if steps >= budget:
                break
            batch = collate_graphs([graphs.get(jid) for jid in ids], device)
            nodes, previous = parent.batch(ids, graphs, device, variant == "feature_residual")
            _, prediction = forward(model, batch, nodes, previous, norm, eta)
            truth = torch.tensor([task["labels"][jid] for jid in ids], device=device)
            loss = (((prediction - truth) / norm["std"]) ** 2).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite residual loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if not torch.stack(
                [torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]
            ).all():
                raise FloatingPointError("non-finite residual gradient")
            optimizer.step()
            steps += 1
            loss_sum += loss.item() * len(ids)
            count += len(ids)
        epoch += 1
        val = validation(
            model, graphs, task, parent, norm, variant, eta, base["training"]["batch_size"], device
        )
        if val < best:
            best = val
            atomic_write(
                output / "best.pt",
                {
                    "model": model.state_dict(),
                    "model_config": asdict(cfg),
                    "recursive": variant == "feature_residual",
                    "identity": identity,
                    "norm": norm,
                    "prediction_role": "residual_delta",
                    "ensemble_required": True,
                    "eta": eta,
                    "epoch": epoch,
                    "val_mae": val,
                },
                tensor=True,
            )
        synchronize(device)
        duration = elapsed + time.perf_counter() - started
        history.append(
            {
                "epoch": epoch,
                "optimizer_steps": steps,
                "train_normalized_ensemble_mse": loss_sum / count,
                "val_mae": val,
                "elapsed_seconds": duration,
            }
        )
        atomic_write(
            last_path,
            {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "identity": identity,
                "epoch": epoch,
                "steps": steps,
                "best": best,
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
            f"{task['task']} {variant} r={identity['round']} epoch={epoch} steps={steps}/{budget} val_mae={val:.9g}",
            flush=True,
        )
        if (
            interrupt_after_epochs is not None
            and epoch >= interrupt_after_epochs
            and steps < budget
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
        "parameters": sum(p.numel() for p in model.parameters()),
        "normalization": norm,
        "training_and_validation_seconds": elapsed + time.perf_counter() - started,
        "stop_reason": "matched_direct_stage_steps",
        "history": history,
    }
    atomic_write(output / "training.json", done)
    return done
