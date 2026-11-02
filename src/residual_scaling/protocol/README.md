# Protocol and import

validate_config(study, base) locks rounds, eta1, seed, variants and supported optimizer.
source_task(prepared, legacy, task, base, study, graphs) audits original rounds 0..2,
including checkpoint/cache/training SHA, graph/source/task identity, exact global ID and
atom coverage, fixed training normalization and old code hash. It returns immutable references.
Implementation identity covers this separate package; legacy self_evolution source is unchanged.
