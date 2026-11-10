from __future__ import annotations
import hashlib,json,sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import UTC,datetime

def operation_key(tenant,operation,version,expected): return hashlib.sha256(f'{tenant}|{operation}|{version}|{expected}'.encode()).hexdigest()
class Audit:
    def __init__(self,path):
        self.path=str(path); conn=sqlite3.connect(self.path);conn.execute('CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY,tenant TEXT,operation TEXT,status TEXT,detail TEXT,created_at TEXT)');conn.commit();conn.close()
    def record(self,key,tenant,operation,status,detail):
        conn=sqlite3.connect(self.path);conn.execute('INSERT OR IGNORE INTO operations VALUES(?,?,?,?,?,?)',(key,tenant,operation,status,json.dumps(detail,sort_keys=True),datetime.now(UTC).isoformat()));conn.commit();conn.close()
    def get(self,key):
        conn=sqlite3.connect(self.path);row=conn.execute('SELECT status,detail FROM operations WHERE key=?',(key,)).fetchone();conn.close();return row
class TrustedOperator:
    """Local trusted context; callers cannot elevate with a boolean flag."""
    def __init__(self,tenant_id,operator_id,can_rollback=False): self.tenant_id=tenant_id;self.operator_id=operator_id;self.can_rollback=can_rollback
class Catalog:
    def __init__(self,path):
        self.path=str(path);c=sqlite3.connect(self.path);c.execute('CREATE TABLE IF NOT EXISTS candidates (tenant TEXT,version TEXT,run_id TEXT,lineage TEXT,promotion TEXT,PRIMARY KEY(tenant,version))');c.commit();c.close()
    def register(self,tenant,version,run_id,lineage):
        if not all((tenant,version,run_id,lineage)): raise ValueError('complete lineage required')
        c=sqlite3.connect(self.path);c.execute('INSERT OR REPLACE INTO candidates VALUES(?,?,?,?,?)',(tenant,version,run_id,lineage,'PENDING'));c.commit();c.close()
    def decide(self,tenant,version,decision):
        c=sqlite3.connect(self.path);c.execute('UPDATE candidates SET promotion=? WHERE tenant=? AND version=?',(decision,tenant,version));c.commit();c.close()
    def approved(self,tenant,version):
        c=sqlite3.connect(self.path);r=c.execute('SELECT run_id,lineage FROM candidates WHERE tenant=? AND version=? AND promotion="PROMOTION_APPROVED"',(tenant,version)).fetchone();c.close();return r
def delayed_performance(active,candidate):
    return 'ROLLBACK_REVIEW_REQUIRED' if candidate['recall']<active['recall']-.03 else 'HEALTHY'
