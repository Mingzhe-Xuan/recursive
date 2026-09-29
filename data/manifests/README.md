# Data manifests

Only small text manifests and checksums belong in Git. Datasets, checkpoints, extracted archives,
logs, and predictions are ignored and live in task-specific server directories.

Each JSON manifest uses schema version 1 and records dataset/task metadata plus one or more
artifacts with a safe basename, an HTTP(S) source, and an expected SHA-256. Download and verify a
manifest atomically with:

```bash
python scripts/download_dataset.py data/manifests/matbench_phonons.json /path/to/data
```

`matbench_phonons.json` follows the official matminer metadata: 1265 structures, target
`last phdos peak` in cm^-1, and the checksum published for the Materials Project JSON gzip.
