# Resumable invariant stages

`train_stage` supports direct normalized-target prediction and two residual modes. Native R0 has raw atom input; direct and feature-residual later stages project their own parent nodes, while raw-residual stages use raw atom input. Residual output is added to the frozen parent's original-unit prediction with fixed R0 sigma, without re-adding the mean.

Direct stages use the locked epoch cap and validation patience. Residual stages run exactly the corresponding direct stage's actual updates, with its same initialization/shuffle seed and constant LR; no residual early stopping or epoch-zero fallback is used. Validation selects only actual trained epochs. Complete-epoch model/Adam/RNG/history snapshots support resume; completed stages reject changed identities, budgets or checkpoint SHA. Historic training values are online normalized MSE; validation values are eval MAE. No test label is accessed.
