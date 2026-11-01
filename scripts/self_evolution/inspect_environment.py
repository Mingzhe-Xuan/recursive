"""Lightweight metadata inspection, with optional GPU diagnostics inside Slurm."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import site
import sys

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("--output", type=Path)
parser.add_argument("--gpu", action="store_true")
args = parser.parse_args()
names = ["torch", "numpy", "pymatgen", "matplotlib", "pytest", "scipy", "pandas", "PySocks"]
versions = {}
for name in names:
    try:
        versions[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        versions[name] = None
result = {
    "python": sys.version,
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "user_site_enabled": site.ENABLE_USER_SITE,
    "sys_path": sys.path,
    "platform": platform.platform(),
    "packages": versions,
}
if args.gpu:
    for name, expected in {
        "numpy": "2.2.6",
        "pymatgen": "2025.10.7",
        "matplotlib": "3.10.3",
        "pytest": "8.3.5",
    }.items():
        assert versions[name] == expected, f"unexpected {name}: {versions[name]}"
    import torch

    assert torch.cuda.is_available(), "no CUDA device"
    assert torch.__version__.startswith("2.8.0"), "unexpected torch version"
    assert torch.version.cuda == "12.8", "expected Blackwell-compatible CUDA 12.8"
    torch.ones((4, 4), device="cuda").square().sum().item()
    result["gpu"] = torch.cuda.get_device_name()
    result["cuda"] = torch.version.cuda
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
