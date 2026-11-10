from __future__ import annotations
import hashlib,json,sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import UTC,datetime

def operation_key(tenant,operation,version,expected): return hashlib.sha256(f'{tenant}|{operation}|{version}|{expected}'.encode()).hexdigest()
class Audit:
    def __init__(self,path):
        self.path=str(path); conn=sqlite3.connect(self.path);conn.execute('CREATE TABLE IF NOT EXISTS operations (event_id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT,tenant TEXT,operation TEXT,status TEXT,detail TEXT,created_at TEXT)');conn.commit();conn.close()
    def record(self,key,tenant,operation,status,detail):
        conn=sqlite3.connect(self.path);conn.execute('INSERT INTO operations(key,tenant,operation,status,detail,created_at) VALUES(?,?,?,?,?,?)',(key,tenant,operation,status,json.dumps(detail,sort_keys=True),datetime.now(UTC).isoformat()));conn.commit();conn.close()
    def get(self,key):
        conn=sqlite3.connect(self.path);row=conn.execute('SELECT status,detail FROM operations WHERE key=? ORDER BY event_id DESC LIMIT 1',(key,)).fetchone();conn.close();return row
    def history(self,key):
        conn=sqlite3.connect(self.path);rows=conn.execute('SELECT status FROM operations WHERE key=? ORDER BY event_id',(key,)).fetchall();conn.close();return [r[0] for r in rows]
class TrustedOperator:
    """Local trusted context; callers cannot elevate with a boolean flag."""
    def __init__(self,tenant_id,operator_id,can_rollback=False): self.tenant_id=tenant_id;self.operator_id=operator_id;self.can_rollback=can_rollback
def trusted_local_operator(tenant_id):
    if tenant_id!='tenant-acme': raise PermissionError('no trusted operator context for tenant')
    return TrustedOperator(tenant_id,'trusted-local-operator',True)
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
