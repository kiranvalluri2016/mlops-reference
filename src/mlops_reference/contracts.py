from __future__ import annotations
import hashlib
from dataclasses import dataclass
import numpy as np
@dataclass(frozen=True)
class ChurnData:
 tenant_id:str;customer_ids:np.ndarray;X:np.ndarray;y:np.ndarray;fingerprint:str
def validate(data:ChurnData):
 if not data.tenant_id or len(set(data.customer_ids))!=len(data.customer_ids):raise ValueError('tenant and unique customer IDs required')
 if set(np.unique(data.y))!={0,1} or int(data.y.sum())<100:raise ValueError('binary target and class coverage required')
 if not data.fingerprint:raise ValueError('fingerprint required')
 return data
