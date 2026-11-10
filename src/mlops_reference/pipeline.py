from __future__ import annotations
import hashlib,json,os,tempfile,fcntl
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,precision_score,recall_score,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

@dataclass(frozen=True)
class Dataset: X: np.ndarray; y: np.ndarray; fingerprint: str
def generate(seed=17,n=500,class_sep=1.0)->Dataset:
    X,y=make_classification(n_samples=n,n_features=8,n_informative=5,weights=[.7,.3],class_sep=class_sep,random_state=seed)
    payload=X.tobytes()+y.tobytes(); return Dataset(X,y,hashlib.sha256(payload).hexdigest())
def split(data:Dataset):
    X_train,X_other,y_train,y_other=train_test_split(data.X,data.y,test_size=.4,stratify=data.y,random_state=17)
    X_val,X_test,y_val,y_test=train_test_split(X_other,y_other,test_size=.5,stratify=y_other,random_state=17)
    assert min(y_train.sum(),y_val.sum(),y_test.sum())>=20
    return (X_train,y_train),(X_val,y_val),(X_test,y_test)
def train(train): return Pipeline([('scale',StandardScaler()),('model',LogisticRegression(random_state=17,max_iter=500))]).fit(*train)
def metrics(model,data):
    X,y=data; p=model.predict_proba(X)[:,1]; q=(p>=.5).astype(int)
    return {'roc_auc':roc_auc_score(y,p),'precision':precision_score(y,q,zero_division=0),'recall':recall_score(y,q,zero_division=0),'f1':f1_score(y,q,zero_division=0)}
def promotion(validation,champion=None):
    ok=validation['roc_auc']>=.75 and validation['recall']>=.65 and validation['f1']>=.65
    if champion: ok=ok and validation['roc_auc']>=champion['roc_auc']-.02 and validation['recall']>=champion['recall']-.03
    return 'PROMOTION_APPROVED' if ok else 'PROMOTION_REJECTED'
class StaleManifest(RuntimeError): pass
class Manifest:
    def __init__(self,path): self.path=Path(path)
    def read(self): return json.loads(self.path.read_text()) if self.path.exists() else {}
    def write(self,record,expected_revision=None,inject_before_replace=False,locked=False):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with open(self.path.with_suffix('.lock'),'a+') as lock:
            if not locked: fcntl.flock(lock,fcntl.LOCK_EX)
            current=self.read(); revision=current.get('revision',0)
            if expected_revision is not None and revision!=expected_revision: raise StaleManifest('manifest revision changed')
            record={**record,'revision':revision+1}
            fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix='.manifest-',text=True)
            try:
                with os.fdopen(fd,'w') as f: json.dump(record,f,sort_keys=True);f.flush();os.fsync(f.fileno())
                if inject_before_replace: raise RuntimeError('injected interruption before replace')
                os.replace(tmp,self.path)
            except Exception:
                if os.path.exists(tmp): os.unlink(tmp)
                raise
            finally:
                if not locked: fcntl.flock(lock,fcntl.LOCK_UN)
        return record
    def deploy(self,tenant,version,key,expected_revision=None,inject_before_replace=False):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with open(self.path.with_suffix('.lock'),'a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);old=self.read()
            if old and old.get('tenant_id')!=tenant: raise PermissionError('cross-tenant manifest mutation')
            if old.get('operation_key')==key:return old,False
            record={'tenant_id':tenant,'active_version':version,'previous_version':old.get('active_version'),'operation_key':key}
            return self.write(record,expected_revision,inject_before_replace,locked=True),True
    def rollback(self,tenant,key,authorized=False,expected_revision=None):
        with open(self.path.with_suffix('.lock'),'a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);old=self.read()
            if old.get('tenant_id')!=tenant or not authorized or not old.get('previous_version'): raise PermissionError('rollback not authorized')
            if old.get('operation_key')==key:return old,False
            record={'tenant_id':tenant,'active_version':old['previous_version'],'previous_version':old['active_version'],'operation_key':key}
            return self.write(record,expected_revision,locked=True),True
    def reconcile(self,audit,key):
        row=audit.get(key); current=self.read()
        if row and current.get('operation_key')==key:return 'RECONCILED'
        if row:return 'RECOVERY_REQUIRED'
        return 'NO_OPERATION'
def drift(reference,current):
    return 'DRIFT_DETECTED' if abs(float(np.mean(reference))-float(np.mean(current)))>.2 else 'HEALTHY'
