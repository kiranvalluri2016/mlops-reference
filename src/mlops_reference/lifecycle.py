from __future__ import annotations
from .governance import Audit,Catalog,TrustedOperator,operation_key
from .pipeline import Manifest
class Lifecycle:
 def __init__(self,root):
  self.audit=Audit(root/'audit.db');self.catalog=Catalog(root/'audit.db');self.manifest=Manifest(root/'deployment.json')
 def deploy(self,operator,version):
  if not self.catalog.approved(operator.tenant_id,version): raise PermissionError('candidate is not registered and approved')
  prior=self.manifest.read().get('active_version');key=operation_key(operator.tenant_id,'DEPLOY',version,prior)
  self.audit.record(key,operator.tenant_id,'DEPLOY','INTENT',{'version':version,'prior':prior})
  record,created=self.manifest.deploy(operator.tenant_id,version,key);self.audit.record(key,operator.tenant_id,'DEPLOY','COMPLETED',record);return record,created
 def rollback(self,operator):
  if not operator.can_rollback: raise PermissionError('trusted operator authorization required')
  current=self.manifest.read();key=operation_key(operator.tenant_id,'ROLLBACK',current.get('previous_version'),current.get('active_version'))
  self.audit.record(key,operator.tenant_id,'ROLLBACK','INTENT',current);record,created=self.manifest.rollback(operator.tenant_id,key,True);self.audit.record(key,operator.tenant_id,'ROLLBACK','COMPLETED',record);return record,created
