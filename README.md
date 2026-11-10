# MLOps Reference

Local-only synthetic churn MLOps reference POC: deterministic data, leakage-free training, validation-only promotion gates, MLflow tracking/registry, simulated atomic deployment, drift evidence, and rollback review. It is not a production deployment.

Verified baseline: Python 3.12.11, scikit-learn 1.9.1, MLflow 3.18.0, Pydantic 2.14.3, pytest 8.4.2. No GitHub Actions workflow is included.

## Local commands
`mlops-reference --root .local train`, `deploy <version>`, `rollback --authorized`, and `inspect` execute only local SQLite/MLflow and manifest behavior. Drift produces review evidence; it never automatically rolls back.

See [architecture](docs/architecture.md) and [governance](docs/governance.md).
