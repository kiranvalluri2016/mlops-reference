from __future__ import annotations
from pathlib import Path
import mlflow,mlflow.sklearn
from .pipeline import metrics
def track_and_register(root,model,validation,name='churn_candidate'):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);mlflow.set_tracking_uri(f"sqlite:///{root/'mlflow.db'}");mlflow.set_experiment('churn-local')
    with mlflow.start_run() as run:
        values=metrics(model,validation);mlflow.log_metrics(values);info=mlflow.sklearn.log_model(model,'model',registered_model_name=name)
    version=mlflow.MlflowClient().search_model_versions(f"name='{name}'")[-1].version
    loaded=mlflow.sklearn.load_model(f'models:/{name}/{version}');return run.info.run_id,str(version),loaded,values
