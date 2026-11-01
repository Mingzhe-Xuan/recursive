# CGCNN correctness tests

Run `python -m pytest tests/self_evolution -p no:cacheprovider --basetemp tmp/pytest-self-evolution`.
Tests compare the pinned native model and independent CIFData graph builder, check label filtering
and group-isolated splits, exercise affine seam gradients and cache interruption/corruption,
and train a tiny three-stage chain with both controls, deferred evaluation and plotting.
Synthetic graphs/metrics validate behavior; they do not replace full JARVIS or CUDA acceptance.
