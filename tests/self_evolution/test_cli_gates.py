import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

from self_evolution.io import read_json
from self_evolution.pipeline import chain


def test_environment_failure_prevents_cuda_training_and_is_recorded(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "evolution_cli", Path("scripts/self_evolution/run.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    monkeypatch.setattr(chain, "run_task", lambda *a, **kw: calls.append(a))

    def failed_inspection(command, **kwargs):
        raise subprocess.CalledProcessError(3, command)

    monkeypatch.setattr(module.subprocess, "run", failed_inspection)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "run",
            "--prepared",
            str(tmp_path / "prepared"),
            "--output",
            str(tmp_path / "run"),
            "--task",
            "formation_energy_peratom",
            "--device",
            "cuda",
        ],
    )
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert calls == []
    failure = read_json(tmp_path / "run/cgcnn/formation_energy_peratom/seed_123/failure.json")
    assert failure["type"] == "CalledProcessError" and failure["action"] == "run"
