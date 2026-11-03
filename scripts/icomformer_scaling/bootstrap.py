"""Lightweight venv creation and fixed-wheel download; installation/tests run in Slurm."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--runtime", type=Path, default=Path("outputs/icomformer_scaling/runtime/seed123")
    )
    parser.add_argument("--proxy", default="socks5h://127.0.0.1:1080")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    runtime = args.runtime.resolve()
    if not runtime.is_relative_to(repo / "outputs/icomformer_scaling/runtime"):
        raise ValueError("bootstrap must use this task's independent runtime directory")
    runtime.mkdir(parents=True, exist_ok=True)
    if not (runtime / "venv/bin/python").exists():
        subprocess.run(
            [sys.executable, "-m", "venv", "--system-site-packages", str(runtime / "venv")],
            check=True,
        )
    wheelhouse = runtime / "wheelhouse"
    wheelhouse.mkdir(exist_ok=True)
    manifest = json.loads(Path(__file__).with_name("runtime_wheels.json").read_text())
    for artifact in manifest["wheels"]:
        name = artifact["filename"]
        if (
            Path(name).name != name
            or urlparse(artifact["url"]).hostname != "files.pythonhosted.org"
        ):
            raise ValueError("unexpected wheel path or source")
        target = wheelhouse / name
        if not target.exists():
            partial = target.with_suffix(target.suffix + ".partial")
            subprocess.run(
                [
                    "curl",
                    "--proxy",
                    args.proxy,
                    "--fail",
                    "--location",
                    "--connect-timeout",
                    "15",
                    "--max-time",
                    "300",
                    "--retry",
                    "3",
                    "--retry-delay",
                    "1",
                    "--continue-at",
                    "-",
                    "--output",
                    str(partial),
                    artifact["url"],
                ],
                check=True,
            )
            data = partial.read_bytes()
            if (
                len(data) != artifact["bytes"]
                or hashlib.sha256(data).hexdigest() != artifact["sha256"]
            ):
                raise ValueError("downloaded wheel checksum/size mismatch")
            partial.replace(target)
        data = target.read_bytes()
        if len(data) != artifact["bytes"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise ValueError("existing wheel checksum/size mismatch")
        print("VERIFIED", name, len(data), flush=True)
    print("BOOTSTRAP_READY; install only through the Slurm check job", flush=True)


if __name__ == "__main__":
    main()
