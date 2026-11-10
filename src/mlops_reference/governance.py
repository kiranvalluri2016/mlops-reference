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
def delayed_performance(active,candidate):
    return 'ROLLBACK_REVIEW_REQUIRED' if candidate['recall']<active['recall']-.03 else 'HEALTHY'
