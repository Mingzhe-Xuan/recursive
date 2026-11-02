# Three-arm pipeline

prepare_task imports frozen legacy rounds 0..2 into paired archives using cached nodes
and historical readouts, checks original validation values and direct-chain parity.
run_variant trains raw_residual or feature_residual through rounds 1..2, with identical
recorded update budgets and seeds. All arms share one imported round-zero archive.
verify_chain recomputes fixed structures from raw graph inputs and compares each node
representation and cumulative prediction to its archive with predeclared atol+rtol.
Old artifacts remain immutable; all new artifacts use a separate root and guarded identities.
