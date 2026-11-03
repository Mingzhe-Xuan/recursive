# Official iComformer source boundary

`upstream/` contains unchanged AIRS files pinned by SHA256 and commit. `audit()` checks canonical LF bytes. The loader executes only the official invariant model, its two layer classes, RBF and graph functions, avoiding unused eComformer/training imports. The official RBF, layers, forward and geometry statements are preserved.

Compatibility repairs are explicit: the undefined superclass name `MatformerConv` inside `ComformerConv.__init__` becomes `ComformerConv` (exactly one AST name). Broken `comforemr` imports and unused e3nn/torch_sparse imports are bypassed by supplying the audited dependencies directly. Pydantic's legacy settings frontend is replaced by a plain configuration namespace; the experiment model config validates the invariant architecture dimensions. These changes do not alter forward mathematics, trainable tensors or state names. Native forward is executed directly and compared to the wrapper, including gradients and buffers.
