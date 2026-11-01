# Linear seam

`LinearProjection(in_features, out_features)` is an ordinary trainable affine `nn.Linear`.
It maps each previous-stage scalar atom vector into the native descriptor width.
It is included in the current model optimizer and checkpoint, with no norm alignment or labels.
Previous-stage node values are detached at the backbone interface.
