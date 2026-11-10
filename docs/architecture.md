# Architecture

```mermaid
flowchart LR
Data --> Split[60/20/20 stratified split]
Split --> Train[Train-only preprocessing]
Train --> Validation[Validation evaluation]
Validation --> Registry[MLflow candidate registration]
Registry --> Gate[Deterministic promotion gate]
Gate --> Deploy[Atomic simulated manifest deployment]
Deploy --> Test[Held-out test report]
Test --> Monitor[Drift and delayed-label monitoring]
Monitor --> Review[Rollback review]
Review -->|Trusted authorization| Rollback[Simulated rollback]
```

Validation selects/promotes candidates; the held-out test is final reporting only. Manifest writes use a process-level file lock, revision check, fsync, and atomic replace. Audit, registry, and manifest are reconciled on restart; disagreement fails closed as `RECOVERY_REQUIRED`.
