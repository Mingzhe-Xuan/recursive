"""Validation-selected supervised stages; labels never enter the feature cache."""

from __future__ import annotations

from dataclasses import asdict
import math
import random
import time
from pathlib import Path

import torch

from self_evolution.backbones.cgcnn import CGCNNStage, ModelConfig
from self_evolution.cache import FeatureStore
from self_evolution.data.graphs import GraphStore, collate_graphs
from self_evolution.io import (
    atomic_write,
    code_identity,
    code_revision,
    derived_seed,
    digest,
    file_hash,
    load_tensor,
    read_json,
)


def synchronize(device):
    if torch.device(device).type == "cuda":
        torch.cuda.synchronize(device)


def batches(ids: list[str], batch_size: int, *, seed: int | None = None):
    order = list(ids)
    if seed is not None:
        random.Random(seed).shuffle(order)
    chunks = [order[i : i + batch_size] for i in range(0, len(order), batch_size)]
    # The reference has node BatchNorm. Merge a final singleton graph, not drop it.
    if seed is not None and len(chunks) > 1 and len(chunks[-1]) == 1:
        chunks[-2].extend(chunks.pop())
    return chunks


def input_batch(graphs: GraphStore, ids: list[str], device, parent: FeatureStore | None):
    values = [graphs.get(jid) for jid in ids]
    batch = collate_graphs(values, device)
    features = (
        None
        if parent is None
        else torch.cat(
            [parent.get(jid, len(graph["atom_features"])) for jid, graph in zip(ids, values)]
        ).to(device)
    )
    return batch, features


def normalization(labels: dict, ids: list[str]) -> dict:
    values = torch.tensor([labels[jid] for jid in ids], dtype=torch.float64)
    if len(values) < 2 or not torch.isfinite(values).all():
        raise ValueError("invalid training targets")
    std = values.std().item()
    return {
        "mean": values.mean().item(),
        "std": std if std > 1e-12 else 1.0,
        "training_ids_hash": digest(sorted(ids)),
    }


@torch.no_grad()
def evaluate(
    model: CGCNNStage,
    graphs: GraphStore,
    ids: list[str],
    labels: dict,
    norm: dict,
    parent: FeatureStore | None,
    device,
    batch_size: int,
) -> dict:
    model.eval()
    results = []
    absolute = 0.0
    for chunk in batches(ids, batch_size):
        batch, features = input_batch(graphs, chunk, device, parent)
        predictions = (model(batch, features) * norm["std"] + norm["mean"]).cpu().tolist()
        for jid, prediction in zip(chunk, predictions):
            truth = labels[jid]
            if not math.isfinite(prediction):
                raise FloatingPointError(f"non-finite prediction: {jid}")
            absolute += abs(prediction - truth)
            results.append({"jid": jid, "prediction": prediction, "target": truth})
    if not results:
        raise ValueError("empty evaluation set")
    return {"mae": absolute / len(results), "count": len(results), "predictions": results}


def load_stage(path: Path, device="cpu") -> tuple[CGCNNStage, dict]:
    checkpoint = load_tensor(path)
    model = CGCNNStage(ModelConfig(**checkpoint["model_config"]), checkpoint["recursive"])
    model.load_state_dict(checkpoint["model"])
    model.to(device).eval()
    return model, checkpoint


def train_stage(
    output: Path,
    config: dict,
    task: dict,
    graphs: GraphStore,
    parent: FeatureStore | None,
    round_index: int,
    mode: str,
    device: str,
    target_steps: int | None = None,
) -> dict:
    training = config["training"]
    model_config = ModelConfig(**config["model"])
    seed = derived_seed(config["seed"], "cgcnn", task["task"], round_index, mode)
    identity = {
        "config_hash": digest(config),
        "graphs_hash": graphs.identity,
        "task_hash": digest(task),
        "mode": mode,
        "round": round_index,
        "stage_seed": seed,
        "parent_cache": None if parent is None else parent.identity,
        "target_steps": target_steps,
        "code_hash": code_identity(),
    }
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "training.json"
    if metrics_path.exists():
        done = read_json(metrics_path)
        if done["identity"] != identity:
            raise ValueError("completed training belongs to a different configuration")
        if file_hash(output / "best.pt") != done["checkpoint_sha256"]:
            raise ValueError("completed checkpoint checksum mismatch")
        return done
    torch.manual_seed(seed)
    if torch.device(device).type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = CGCNNStage(model_config, recursive=parent is not None).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=training["learning_rate"], weight_decay=training["weight_decay"]
    )
    split, labels = task["split"]["ids"], task["labels"]
    norm = normalization(labels, split["train"])
    epoch, steps, best, stale, elapsed = 0, 0, math.inf, 0, 0.0
    history = []
    if target_steps is not None and target_steps < 1:
        raise ValueError("target_steps must be positive")
    last_path = output / "last.pt"
    if last_path.exists():
        last = load_tensor(last_path)
        if last["identity"] != identity:
            raise ValueError("resume checkpoint identity mismatch")
        model.load_state_dict(last["model"])
        optimizer.load_state_dict(last["optimizer"])
        epoch, steps, best, stale = last["epoch"], last["steps"], last["best"], last["stale"]
        elapsed, history = last["elapsed"], last["history"]
        torch.set_rng_state(last["torch_rng"])
        if last["cuda_rng"] and torch.device(device).type == "cuda":
            torch.cuda.set_rng_state_all(last["cuda_rng"])
    atomic_write(output / "config.json", {"config": config, "identity": identity, "norm": norm})
    parent_hash = None if parent is None else file_hash(parent.root / "manifest.json")
    synchronize(device)
    started = time.perf_counter()
    stop_reason = "max_epochs"
    max_epochs = training["epochs"] if target_steps is None else target_steps + 1
    if target_steps is None and stale >= training["patience"]:
        max_epochs, stop_reason = epoch, "validation_patience"
    for epoch_index in range(epoch, max_epochs):
        if target_steps is not None and steps >= target_steps:
            stop_reason = "matched_optimizer_steps"
            break
        model.train()
        loss_sum, count = 0.0, 0
        for chunk in batches(
            split["train"], training["batch_size"], seed=derived_seed(seed, epoch_index)
        ):
            if target_steps is not None and steps >= target_steps:
                break
            batch, features = input_batch(graphs, chunk, device, parent)
            if len(batch["atom_features"]) < 2:
                raise ValueError("training BatchNorm requires at least two atoms")
            target = torch.tensor([labels[jid] for jid in chunk], device=device)
            target = (target - norm["mean"]) / norm["std"]
            optimizer.zero_grad(set_to_none=True)
            prediction = model(batch, features)
            loss = torch.nn.functional.mse_loss(prediction, target)
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite training loss")
            loss.backward()
            if not torch.stack(
                [torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]
            ).all():
                raise FloatingPointError("non-finite training gradient")
            optimizer.step()
            steps += 1
            loss_sum += loss.item() * len(chunk)
            count += len(chunk)
        validation = evaluate(
            model, graphs, split["val"], labels, norm, parent, device, training["batch_size"]
        )
        val = validation["mae"]
        if val < best:
            best, stale = val, 0
            atomic_write(
                output / "best.pt",
                {
                    "model": model.state_dict(),
                    "model_config": asdict(model_config),
                    "recursive": parent is not None,
                    "identity": identity,
                    "norm": norm,
                    "epoch": epoch_index + 1,
                    "val_mae": val,
                    "code_commit": code_revision(),
                },
                tensor=True,
            )
        else:
            stale += 1
        synchronize(device)
        duration = elapsed + time.perf_counter() - started
        history.append(
            {
                "epoch": epoch_index + 1,
                "optimizer_steps": steps,
                "train_normalized_mse": loss_sum / max(count, 1),
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
                "epoch": epoch_index + 1,
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
            f"{task['task']} {mode} r={round_index} epoch={epoch_index + 1} "
            f"steps={steps} val_mae={val:.7g}",
            flush=True,
        )
        if target_steps is None and stale >= training["patience"]:
            stop_reason = "validation_patience"
            break
        if target_steps is not None and steps >= target_steps:
            stop_reason = "matched_optimizer_steps"
            break
    if parent is not None and file_hash(parent.root / "manifest.json") != parent_hash:
        raise ValueError("historical cache mutated during training")
    done = {
        "identity": identity,
        "checkpoint_sha256": file_hash(output / "best.pt"),
        "optimizer_steps": steps,
        "epochs": len(history),
        "best_val_mae": best,
        "training_and_validation_seconds": history[-1]["elapsed_seconds"],
        "stop_reason": stop_reason,
        "parameters": sum(p.numel() for p in model.parameters()),
        "normalization": norm,
        "history": history,
        "torch_version": str(torch.__version__),
        "device": str(device),
        "code_commit": code_revision(),
    }
    atomic_write(metrics_path, done)
    return done
