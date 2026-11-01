# CGCNN correctness tests

Run `python -m pytest tests/self_evolution -p no:cacheprovider --basetemp tmp/pytest-self-evolution`.
Tests compare the pinned native model and independent CIFData graph builder, check label filtering
and group-isolated splits, exercise affine seam gradients and cache interruption/corruption,
and train a tiny three-stage chain with both controls, deferred evaluation and plotting.
Synthetic graphs/metrics validate behavior; they do not replace full JARVIS or CUDA acceptance.

The pipeline integration also removes the task-label file while measuring two copied stages,
checks resource metadata and protocol rejection, and verifies checkpoint/manifest/shard hashes
remain unchanged. CPU runs leave GPU peak fields null; real GPU measurements run in Slurm.

Pool tests run real short-lived Python subprocesses to check bounded overlap, failure isolation,
the barrier between training and evaluation, serial evaluation, retained reports, full 29-task
coverage and source-bound resource gates. They do not replace real CUDA resource measurements.

Delivery-audit coverage checks full configurations/source metadata, shard byte counts/checksums,
idempotent supplement publication and unchanged checkpoints/base manifests. Missing controls,
cross-task control metadata, wrong source/configuration and corrupt shards are rejected before
publication/test evaluation. The CLI environment-gate test simulates inspection failure and proves
that CUDA training is not called; CPU tests do not access a GPU for this negative case.

Schedule tests verify complete task coverage, protected wave membership, source/configuration
rejection and actual dispatcher task selection. Candidate validation also works before publication,
without creating a runtime schedule. They do not estimate actual GPU speed.
