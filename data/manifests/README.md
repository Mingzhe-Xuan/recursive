# Data manifests

Only small text manifests and checksums belong in Git. Datasets, checkpoints, extracted archives,
logs, and predictions are ignored and live in task-specific server directories.

Each JSON manifest uses schema version 1 and records dataset/task metadata plus one or more
artifacts with a safe basename, an HTTP(S) source, and exactly one published checksum (`sha256` or
`md5`). Download and verify a manifest atomically with:

```bash
python scripts/download_dataset.py data/manifests/matbench_phonons.json /path/to/data
```

`matbench_phonons.json` follows the official matminer metadata: 1265 structures, target
`last phdos peak` in cm^-1, and the checksum published for the Materials Project JSON gzip.

`mace_phonondb_97.json` pins the MACE-MP paper's linked ffonons repository and the exact 97
Materials Project IDs represented in its MACE-MP0 PhononDB figure directory. It includes the
verified summary/mapping artifacts and the official NIMS PhononDB download template. The 97 ZIP
files have no published checksums; record their local SHA-256 values after the first server
download rather than inventing pre-download hashes.

`dpa2_sse_pbe_d.json` pins Zenodo record 10461723 and its `data-v1.3.tgz` archive for the DPA-2
SSE-PBE-D downstream task. Zenodo publishes MD5 for this 17 GB file; the downloader verifies that
official checksum, and the server workflow records an additional local SHA-256 after download.

`mattersim_wheelhouse_cp310_linux/` versions the 162-entry, binary-only Linux/CPython 3.10
MatterSim dependency closure. It stores only official PyPI URLs and SHA-256 metadata; the wheel
files remain ignored and live in the task runtime directory.
