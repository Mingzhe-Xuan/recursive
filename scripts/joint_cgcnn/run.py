"""Slurm-only joint CGCNN gates and four-property study."""

import argparse
import copy
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import torch
from joint_cgcnn.model import DoubleCGCNN
from joint_cgcnn.study import implementation_identity, inputs, run_task, summarize
from joint_cgcnn.training import gradients, train
from self_evolution.backbones.cgcnn import ModelConfig
from self_evolution.data.graphs import collate_graphs
from self_evolution.io import atomic_write, digest, file_hash, read_json
from self_evolution.pipeline.chain import task_lock


def provenance(args, cfg):
    return {task: inputs(args.prepared, args.cached, task, cfg)[3] for task in cfg["tasks"]}


def validate_gate(args, cfg):
    gate = read_json(args.output / "acceptance.json")
    if (
        gate["status"] != "passed"
        or gate["config_sha256"] != digest(cfg)
        or gate["implementation_hash"] != implementation_identity()
        or gate["sources"] != provenance(args, cfg)
        or gate["cpu_proof_sha256"] != file_hash(args.output / "cpu-proof.json")
        or gate["script_sha256"] != file_hash(Path(__file__))
        or not all(v > 0 for v in gate["gradient_l1"].values())
        or gate["diagnostic_only"] is not True
        or gate["test_labels_used"]
    ):
        raise ValueError("joint GPU acceptance/source/config mismatch")
    return gate


def accept(args, cfg):
    if not torch.cuda.is_available():
        raise RuntimeError("real GPU required")
    sources = provenance(args, cfg)
    cpu = read_json(args.output / "cpu-proof.json")
    if cpu["sources"] != sources or cpu["status"] != "passed":
        raise ValueError("CPU acceptance changed")
    task, graphs, norm, identity, _ = inputs(args.prepared, args.cached, cfg["tasks"][0], cfg)
    ids = sorted(graphs.ids, key=lambda jid: (-graphs.entries[jid]["atoms"], jid))[
        : cfg["training"]["batch_size"]
    ]
    model = DoubleCGCNN(ModelConfig(**cfg["model"]), identity["seeds"]).cuda().train()
    batch = collate_graphs([graphs.get(jid) for jid in ids], "cuda")
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["training"]["learning_rate"])
    torch.cuda.reset_peak_memory_stats()
    optimizer.zero_grad(set_to_none=True)
    model(batch).square().mean().backward()
    norms = gradients(model)
    if not all(v > 0 for v in norms.values()):
        raise ValueError("end-to-end gradient is blocked")
    optimizer.step()
    model.eval()
    with torch.no_grad():
        actual = model(batch)
        native = model.second(batch, model.first(batch))
        torch.testing.assert_close(actual, native, **cfg["verification"])
    peak = torch.cuda.max_memory_reserved()
    total = torch.cuda.get_device_properties(0).total_memory
    if peak > total * 0.90:
        raise ValueError("joint worst batch exceeds GPU headroom")
    del model, optimizer, batch
    torch.cuda.empty_cache()
    diagnostic_task = copy.deepcopy(task)
    diagnostic_task["split"]["ids"]["train"] = task["split"]["ids"]["train"][:128]
    diagnostic_task["split"]["ids"]["val"] = task["split"]["ids"]["val"][:64]
    diagnostic_cfg = copy.deepcopy(cfg)
    diagnostic_cfg["training"].update(epochs=2, patience=2)
    diagnostic_root = args.output / "diagnostics" / ("gpu-" + digest(identity)[:12])
    done = train(
        diagnostic_root,
        diagnostic_cfg,
        diagnostic_task,
        graphs,
        norm,
        {**identity, "diagnostic": True},
        "cuda",
    )
    gate = {
        "status": "passed",
        "config_sha256": digest(cfg),
        "implementation_hash": implementation_identity(),
        "sources": sources,
        "script_sha256": file_hash(Path(__file__)),
        "cpu_proof_sha256": file_hash(args.output / "cpu-proof.json"),
        "gradient_l1": norms,
        "peak_reserved_bytes": peak,
        "device_memory_bytes": total,
        "worst_batch_structures": len(ids),
        "worst_batch_atoms": sum(graphs.entries[jid]["atoms"] for jid in ids),
        "diagnostic_steps": done["optimizer_steps"],
        "diagnostic_only": True,
        "test_labels_used": False,
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
    }
    atomic_write(args.output / "acceptance.json", gate)
    print("JOINT_GPU_ACCEPTED", gate, flush=True)


def study(args, cfg):
    gate = validate_gate(args, cfg)
    gib = 1024**3
    workers = max(
        1,
        min(
            4,
            int(os.environ["SLURM_CPUS_PER_TASK"]) // cfg["threads"],
            int(gate["device_memory_bytes"] * 0.75) // int(2 * gate["peak_reserved_bytes"] + gib),
        ),
    )
    pool = args.output / "pool"
    pool.mkdir(parents=True, exist_ok=True)
    state = {
        "status": "running",
        "workers": workers,
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "config_sha256": digest(cfg),
        "implementation_hash": implementation_identity(),
        "tasks": {},
    }
    pending, active = list(cfg["tasks"]), {}
    with task_lock(pool / ".lock"):
        ledger = pool / "execution.json"
        if ledger.exists():
            old = read_json(ledger)
            if (
                old["config_sha256"] != state["config_sha256"]
                or old["implementation_hash"] != state["implementation_hash"]
            ):
                raise ValueError("joint execution identity changed")
            ledger.replace(pool / f"execution-attempt-{time.time_ns()}.json")
        try:
            while pending or active:
                while pending and len(active) < workers:
                    name = pending.pop(0)
                    log = (pool / f"{name}-{time.time_ns()}.out").open("w")
                    cmd = [
                        sys.executable,
                        str(Path(__file__)),
                        "task",
                        "--task",
                        name,
                        "--config",
                        str(args.config),
                        "--prepared",
                        str(args.prepared),
                        "--cached",
                        str(args.cached),
                        "--output",
                        str(args.output),
                    ]
                    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                    active[name] = p, log
                    state["tasks"][name] = {"status": "running", "pid": p.pid, "log": log.name}
                for name, (p, log) in list(active.items()):
                    code = p.poll()
                    if code is not None:
                        state["tasks"][name].update(
                            status="complete" if code == 0 else "failed", exit_code=code
                        )
                        log.close()
                        del active[name]
                atomic_write(ledger, state)
                if pending or active:
                    time.sleep(5)
            report = summarize(args.prepared, args.cached, args.output, cfg)
            state["status"] = report["status"]
            atomic_write(ledger, state)
            if report["status"] != "complete":
                raise RuntimeError("incomplete joint results; inspect per-task logs")
        except BaseException as exc:
            state.update(status="failed", error=str(exc))
            atomic_write(ledger, state)
            raise
        finally:
            for p, log in active.values():
                p.terminate()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
                log.close()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=["cpu-proof", "accept", "study", "task"])
    parser.add_argument("--config", type=Path, default=Path("configs/joint_cgcnn/seed123.json"))
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--cached", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task")
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("joint server compute requires Slurm")
    cfg = read_json(args.config)
    torch.set_num_threads(cfg["threads"])
    torch.use_deterministic_algorithms(True)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.action == "cpu-proof":
        proof = {
            "status": "passed",
            "sources": provenance(args, cfg),
            "slurm_job_id": os.environ["SLURM_JOB_ID"],
            "test_labels_used": False,
        }
        atomic_write(args.output / "cpu-proof.json", proof)
        print("JOINT_CPU_ACCEPTED", flush=True)
    elif args.action == "accept":
        accept(args, cfg)
    elif args.action == "study":
        study(args, cfg)
    else:
        validate_gate(args, cfg)
        run_task(args.prepared, args.cached, args.output, args.task, cfg, "cuda")


if __name__ == "__main__":
    main()
