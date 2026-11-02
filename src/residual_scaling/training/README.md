# Residual stages

train_stage receives a frozen parent archive, fixed round-zero normalization, exact
legacy optimizer-step budget and legacy stage seed. Native random initialization is kept.
F = parent_prediction + eta * sigma * new_model; loss = mean(((F-y)/sigma)^2).
Validation/selection use F in original units, exclusively on validation IDs. Epoch zero
is not eligible; curves can worsen. last.pt contains model/Adam/RNG/history for exact resume.
Residual best.pt predicts a delta and requires its parent ensemble; never interpret it
as a standalone property model. Test targets are not used.
