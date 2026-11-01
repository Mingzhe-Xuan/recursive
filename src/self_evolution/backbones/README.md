# Trainable backbone contract

CGCNN is implemented; Matformer and iComFormer remain outside this single-backbone task.
Inputs are a collated periodic graph plus optional previous-stage node features.
`forward_native(batch)` is the official predictor path; `encode_nodes(batch, features)`
returns the final pre-pooling nodes; `forward_from_features` runs the projected recursive input.
All stages include their own atom embedding, convolution stack and graph readout.
