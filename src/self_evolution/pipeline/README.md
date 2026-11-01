# Sequential task pipeline

`run_task(prepared, run, task_name, config, device)` runs CGCNN seed 123 stage chains.
The task lock is an OS lock released on process exit, so a stale file does not block resumption.
The immutable protocol lives beside rounds; stop-round only limits current progress, not scope.
Each `train_r -> cache_r` step is followed by direct-chain versus cache parity verification.
New structures require all stage checkpoints in order. Only full declared depth is marked complete.

`cache_stage` runs the validation-selected frozen model in eval/no_grad on the whole library,
including structures without the task label. It verifies unchanged checkpoint and BN buffers.
`benchmark_chain` warms up twice and synchronizes before timing five repeats, distinguishing
full-chain deployment from a forward assisted by precomputed atom features.
Read the full-chain benchmark labels carefully: model loading is excluded, geometry loading is
reported separately, and graph construction is measured in preprocessing.
