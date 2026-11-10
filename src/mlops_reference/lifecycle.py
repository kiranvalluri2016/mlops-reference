from __future__ import annotations
from .governance import Audit,Catalog,TrustedOperator,operation_key
from .pipeline import Manifest
import mlflow
class Lifecycle:
 def __init__(self,root):
  self.audit=Audit(root/'audit.db');self.catalog=Catalog(root/'audit.db');self.manifest=Manifest(root/'deployment.json')
 def deploy(self,operator,version):
  candidate=self.catalog.approved(operator.tenant_id,version)
  if not candidate: raise PermissionError('candidate is not registered and approved')
  mlflow.set_tracking_uri(f"sqlite:///{self.manifest.path.parent/'mlflow.db'}")
  try:
   registered=mlflow.MlflowClient().get_model_version('churn_candidate',str(version));run=mlflow.MlflowClient().get_run(registered.run_id)
  except Exception as exc: raise PermissionError('registry verification failed') from exc
  if registered.run_id!=candidate[0] or run.data.tags.get('lineage')!=candidate[1]: raise PermissionError('registry lineage mismatch')
  prior=self.manifest.read().get('active_version');key=operation_key(operator.tenant_id,'DEPLOY',version,prior)
  self.audit.record(key,operator.tenant_id,'DEPLOY','INTENT',{'version':version,'prior':prior})
  record,created=self.manifest.deploy(operator.tenant_id,version,key);self.audit.record(key,operator.tenant_id,'DEPLOY','COMPLETED',record);return record,created
 def rollback(self,operator):
  if not operator.can_rollback: raise PermissionError('trusted operator authorization required')
  current=self.manifest.read();key=operation_key(operator.tenant_id,'ROLLBACK',current.get('previous_version'),current.get('active_version'))
  self.audit.record(key,operator.tenant_id,'ROLLBACK','INTENT',current);record,created=self.manifest.rollback(operator.tenant_id,key,True);self.audit.record(key,operator.tenant_id,'ROLLBACK','COMPLETED',record);return record,created
