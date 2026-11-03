# Native iComformer acceptance tests

Tests use real PyG, torch-scatter, Jarvis and official invariant model declarations. They audit pinned source, compare wrapper/native outputs, gradients and BN buffers, verify native graph output and batching/rotated geometry, check detached recursive projection, and exercise tensor-only graph persistence and corruption rejection. No stub replaces native dependencies. Full task-chain tests extend this module once training is integrated.
