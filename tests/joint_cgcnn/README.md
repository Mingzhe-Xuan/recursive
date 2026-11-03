# Joint CGCNN checks

Use `python -m pytest tests/joint_cgcnn`. The fixture generates a real tiny three-round cached CGCNN chain and both residual branches, not mocked training. Tests verify native composition, all-stage gradient flow, independent initializations, original-unit selection, exact CPU/Adam/RNG recovery, unused test labels, immutable provenance, validation comparison artifacts, partial-result handling, production parameter count and acceptance rejection. Real GPU and largest-structure checks run only in Slurm.
