# CGCNN seed-123 protocol

`cgcnn_seed123.json` locks rounds 0..5, architecture, optimizer, normalization, batch size,
cache precision, numerical tolerances, split seed, controls and test-access policy.
Do not edit after a run begins: the pipeline rejects mismatched protocol hashes.
Pilot may stop at round 1 under the same protocol and resume without changing it.
Synthetic unit tests use their own smaller config and are not benchmark results.
