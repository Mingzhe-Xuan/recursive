# Deferred evaluation and plots

`evaluate_task` requires all declared stages before computing train/validation/test MAE and
per-structure CSV predictions for evolution, raw-input retraining and cumulative-step controls.
The best round uses validation MAE only. Dataset units are restored before computing errors.
`summarize` writes metrics.csv, task curves (PNG/SVG), a relative-improvement heatmap and
summary.json covering all 29 tasks. Missing/failed tasks remain explicit; they are never zero-filled.
One seed is labeled as such, without standard-deviation bands. Relative gains exclude zero baselines.
Training/validation wall time, cache generation and full-chain forward latency are reported separately.
