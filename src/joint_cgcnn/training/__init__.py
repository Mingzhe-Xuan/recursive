"""Joint Adam optimization with validation selection and whole-epoch recovery."""

import math
from pathlib import Path
import time

import torch

from self_evolution.backbones.cgcnn import ModelConfig
from self_evolution.data.graphs import collate_graphs
from self_evolution.io import atomic_write, derived_seed, file_hash, load_tensor, read_json
from self_evolution.training.stage import batches, synchronize
from joint_cgcnn.model import DoubleCGCNN


def gradients(model):
    groups = {"first": [], "bridge": [], "second": []}
    finite = []
    for name, p in model.named_parameters():
        if p.grad is None:
            raise FloatingPointError(f"missing joint gradient: {name}")
        finite.append(torch.isfinite(p.grad).all())
        key = (
            "first"
            if name.startswith("first.")
            else ("bridge" if name.startswith("second.projection.") else "second")
        )
        groups[key].append(p.grad.detach().abs().sum())
    if not torch.stack(finite).all():
        raise FloatingPointError("non-finite joint gradient")
    return {key: float(torch.stack(values).sum()) for key, values in groups.items()}


@torch.no_grad()
def evaluate(model, graphs, task, norm, device, batch_size, split="val"):
    model.eval()
    rows = []
    for ids in batches(task["split"]["ids"][split], batch_size):
        batch = collate_graphs([graphs.get(jid) for jid in ids], device)
        values = (norm["mean"] + norm["std"] * model(batch)).cpu().tolist()
        for jid, value in zip(ids, values):
            if not math.isfinite(value):
                raise FloatingPointError("non-finite joint prediction")
            rows.append({"jid": jid, "target": task["labels"][jid], "prediction": value})
    return {
        "mae": sum(abs(r["target"] - r["prediction"]) for r in rows) / len(rows),
        "predictions": rows,
    }


def load_model(path, device="cpu"):
    state = load_tensor(path)
    model = DoubleCGCNN(ModelConfig(**state["model_config"]), state["seeds"])
    model.load_state_dict(state["model"])
    return model.to(device).eval(), state


def train(output, config, task, graphs, norm, identity, device, interrupt_after=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "training.json").exists():
        done = read_json(output / "training.json")
        if done["identity"] != identity or done["checkpoint_sha256"] != file_hash(
            output / "best.pt"
        ):
            raise ValueError("completed joint identity/checkpoint changed")
        return done
    seeds = identity["seeds"]
    torch.manual_seed(seeds[1])
    model = DoubleCGCNN(ModelConfig(**config["model"]), seeds).to(device)
    cfg = config["training"]
    optimizer = torch.optim.Adam(
        model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"]
    )
    epoch, steps, best, stale, elapsed, history = 0, 0, math.inf, 0, 0.0, []
    if (output / "last.pt").exists():
        old = load_tensor(output / "last.pt")
        if old["identity"] != identity:
            raise ValueError("joint resume identity changed")
        model.load_state_dict(old["model"])
        optimizer.load_state_dict(old["optimizer"])
        epoch, steps, best, stale, elapsed, history = [
            old[k] for k in ["epoch", "steps", "best", "stale", "elapsed", "history"]
        ]
        torch.set_rng_state(old["rng"])
        if old["cuda_rng"] and torch.device(device).type == "cuda":
            torch.cuda.set_rng_state_all(old["cuda_rng"])
    atomic_write(
        output / "protocol.json", {"config": config, "identity": identity, "normalization": norm}
    )
    synchronize(device)
    started = time.perf_counter()
    while epoch < cfg["epochs"] and stale < cfg["patience"]:
        model.train()
        loss_sum, count = 0.0, 0
        for ids in batches(
            task["split"]["ids"]["train"], cfg["batch_size"], seed=derived_seed(seeds[1], epoch)
        ):
            batch = collate_graphs([graphs.get(jid) for jid in ids], device)
            truth = torch.tensor([task["labels"][jid] for jid in ids], device=device)
            loss = (model(batch) - (truth - norm["mean"]) / norm["std"]).square().mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite joint loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            norms = gradients(model)
            optimizer.step()
            loss_sum += float(loss.detach()) * len(ids)
            count += len(ids)
            steps += 1
        epoch += 1
        val = evaluate(model, graphs, task, norm, device, cfg["batch_size"])["mae"]
        if val < best:
            best, stale = val, 0
            atomic_write(
                output / "best.pt",
                {
                    "model": model.state_dict(),
                    "model_config": config["model"],
                    "seeds": seeds,
                    "identity": identity,
                    "normalization": norm,
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
                "train_normalized_mse": loss_sum / count,
                "val_mae": val,
                "gradient_l1_last_batch": norms,
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
                "rng": torch.get_rng_state(),
                "cuda_rng": torch.cuda.get_rng_state_all()
                if torch.device(device).type == "cuda"
                else [],
            },
            tensor=True,
        )
        atomic_write(output / "history.json", history)
        print(f"{task['task']} joint epoch={epoch} steps={steps} val_mae={val:.9g}", flush=True)
        if interrupt_after is not None and epoch >= interrupt_after:
            return None
    done = {
        "identity": identity,
        "normalization": norm,
        "optimizer_steps": steps,
        "epochs": epoch,
        "best_val_mae": best,
        "checkpoint_sha256": file_hash(output / "best.pt"),
        "parameters": sum(p.numel() for p in model.parameters()),
        "training_seconds": elapsed + time.perf_counter() - started,
        "history": history,
        "stop_reason": "patience" if stale >= cfg["patience"] else "epoch_limit",
    }
    atomic_write(output / "training.json", done)
    return done
