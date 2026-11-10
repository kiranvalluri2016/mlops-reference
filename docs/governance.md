# Governance

Promotion requires validation ROC-AUC >= .75, recall >= .65, F1 >= .65, and permitted champion regression. Drift alone cannot roll back a model. Rollback requires delayed-label degradation plus trusted local operator authorization and a previous active version. All effects use deterministic operation keys and are idempotent.
