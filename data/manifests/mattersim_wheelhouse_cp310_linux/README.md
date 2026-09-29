# MatterSim CPython 3.10 Linux wheelhouse

This directory pins the binary-only offline dependency closure used by the MatterSim experiments.
The target is CPython 3.10 on Linux x86-64 (glibc/manylinux), with these top-level versions:

- `mattersim==1.2.3`
- `torch==2.8.0`
- `torchvision==0.23.0`
- `torchaudio==2.8.0`

`PYPI_URLS` contains `SHA256`, safe wheel basename, and the official PyPI file URL separated by
two spaces. `SHA256SUMS` contains the same digest and basename in `sha256sum -c` format. Both files
must contain exactly the same 162 unique wheels.

To stage or update a task-local wheelhouse, copy these two text files into that directory and run
the download job. Existing wheels whose hashes match are skipped, and incomplete downloads remain
as `.partial` files until a later Slurm retry:

```bash
cp data/manifests/mattersim_wheelhouse_cp310_linux/{PYPI_URLS,SHA256SUMS} \
  /dev/shm/xmz-recursive/wheelhouse/mattersim/
sbatch --nodelist=node221 \
  --export=ALL,RECURSIVE_WHEELHOUSE=/dev/shm/xmz-recursive/wheelhouse/mattersim,\
RECURSIVE_WHEEL_COUNT=162 \
  scripts/slurm/download_mattersim_wheelhouse.sbatch
```

Never commit the wheel files. When changing a dependency, regenerate the complete target-platform
closure, verify every digest against PyPI metadata and the downloaded file, and repeat the offline
resolver check before replacing these manifests.
