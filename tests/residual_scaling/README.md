# Residual validation tests

CPU tests use real tiny crystal graphs and native CGCNN. They cover original-unit
residual arithmetic, detached/frozen parents, full paired archives, corruption/resume,
three arms through round two, exact update/seed matching, deterministic optimizer resume,
test-label non-use and validation-only reporting. Synthetic accuracy is not GPU acceptance.
