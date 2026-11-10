from __future__ import annotations
from pathlib import Path
import mlflow
import mlflow.sklearn
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

def run(root: str) -> dict[str, str]:
    base=Path(root); base.mkdir(parents=True,exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{base/'mlflow.db'}")
    mlflow.set_experiment("phase0")
    X,y=make_classification(n_samples=120,n_features=6,n_informative=4,random_state=17)
    with mlflow.start_run() as active:
        model=LogisticRegression(random_state=17,max_iter=500).fit(X[:90],y[:90])
        info=mlflow.sklearn.log_model(model,"model",registered_model_name="churn_phase0")
        mlflow.log_metric("accuracy",float(model.score(X[90:],y[90:])))
        run_id=active.info.run_id
    version=mlflow.MlflowClient().search_model_versions("name='churn_phase0'")[-1].version
    loaded=mlflow.sklearn.load_model(f"models:/churn_phase0/{version}")
    assert loaded.predict(X[90:92]).shape==(2,)
    return {"run_id":run_id,"model_version":str(version),"model_id":info.model_id}
