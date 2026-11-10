from __future__ import annotations
from .pipeline import metrics,drift
from .governance import Audit,operation_key,delayed_performance
def evaluate(tenant,model,reference_features,monitoring_data,active_metrics,audit):
 signal=drift(reference_features,monitoring_data[0]);observed=metrics(model,monitoring_data);review=delayed_performance(active_metrics,observed)
 key=operation_key(tenant,'MONITOR',str(observed['recall']),'')
 audit.record(key,tenant,'MONITOR',review,{'drift':signal,'metrics':observed})
 return {'drift':signal,'performance':review,'metrics':observed,'operation_key':key}
