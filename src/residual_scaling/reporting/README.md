# Validation reports

summarize(output, study) verifies complete branch identities, rounds, exact budgets,
checkpoint and paired-cache SHA/contents. It writes original-unit validation MAE curves,
validation_metrics.csv and JSON coverage. Missing/failed branches remain incomplete, not zero.
Round-zero cost is inherited; historical direct wall time and new measured wall time
have different scopes. Update counts match, input adapter parameter counts may differ.
Prior report directories are archived; no test metrics or uncertainty bands are invented.
