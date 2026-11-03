# Double native CGCNN

Input: an existing collated CGCNN graph batch. Output: one normalized scalar per crystal. `DoubleCGCNN(ModelConfig, [seed0, seed1])` contains an encoder without its unused readout and a second full CGCNN with linear projection. Both are fresh, independently initialized with the exact seeds used by cached R0/R1. It uses the native layers and final readout while bypassing the existing cached-stage detach boundary. Parameters: 159,197 for the fixed study defaults.
