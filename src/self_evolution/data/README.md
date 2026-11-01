# JARVIS data and geometry

`tasks.py` declares the 29 published regression fields and native reporting units.
`select_labels(records, task)` keeps finite numeric scalar targets, including zero, and audits
all exclusion reasons. `grouped_split` depends on IDs/groups/seed, not numeric target values.
`canonicalize_records` first resolves repeated source IDs: exact same structures are merged,
unique finite task values fill missing labels, conflicting finite labels become missing for that task.
Different structures under one repeated ID are rejected. Raw positions, full row hashes and
conflicting numeric values are retained in the audit. No arbitrary first/last target wins.
Equivalent same-cell structures stay in the same split; IDs and membership hash are persisted.

`prepare_dataset` verifies official ZIP size/MD5, records local SHA-256, checks the exact JSON
member and library count, constructs graphs with a process pool and publishes a manifest.
Any unresolved graph error prevents full-library acceptance. Existing task labels/splits cannot
be replaced with different content at the same output path.

`make_graph` follows pinned CGCNN: radius 8 angstrom, nearest 12 periodic neighbors,
Gaussian distance expansion at step 0.2, and original zero-index/radius+1 padding.
Node ordering stays unchanged. Padding is retained exactly rather than introducing a changed
masked convolution. The official descriptor table is a source resource, not learned data.

`GraphStore` takes a completed directory and returns verified tensors keyed by structure ID.
Verified graphs are memoized in RAM per task process to avoid reloading 55k files every epoch;
production Slurm jobs request 48 GiB. Run each task in a separate process.
