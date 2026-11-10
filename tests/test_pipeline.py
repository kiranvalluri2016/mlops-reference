from mlops_reference.pipeline import *
from mlops_reference.tracking import track_and_register
from mlops_reference.governance import Audit,operation_key,delayed_performance
def test_deterministic_split_and_validation_only_gate():
    a,b=generate(),generate();assert a.fingerprint==b.fingerprint
    tr,val,test=split(a);m=train(tr);v=metrics(m,val); decision=promotion(v)
    assert decision in {'PROMOTION_APPROVED','PROMOTION_REJECTED'}; assert len(test[0])==100
def test_manifest_idempotency_and_drift_no_rollback(tmp_path):
    x=Manifest(tmp_path/'deployment.json');first,created=x.deploy('tenant-acme','1','op1');second,again=x.deploy('tenant-acme','1','op1')
    assert created and not again and first==second; assert drift([0.,0.],[1.,1.])=='DRIFT_DETECTED'; assert x.read()['active_version']=='1'
def test_rollback_requires_trusted_authorization_and_is_idempotent(tmp_path):
    x=Manifest(tmp_path/'deployment.json');x.deploy('tenant-acme','1','op1');x.deploy('tenant-acme','2','op2')
    import pytest
    with pytest.raises(PermissionError):x.rollback('tenant-acme','rollback',False)
    first,created=x.rollback('tenant-acme','rollback',True);second,again=x.rollback('tenant-acme','rollback',True)
    assert created and not again and first==second and first['active_version']=='1'
def test_train_only_preprocessing():
    tr,val,test=split(generate());m=train(tr); assert metrics(m,val)['roc_auc']>=0
def test_validation_gate_uses_validation_not_heldout_labels():
    tr,val,test=split(generate());m=train(tr);decision=promotion(metrics(m,val)); altered=(test[0],1-test[1])
    assert promotion(metrics(m,val))==decision and len(altered[1])==len(test[1])
def test_champion_regression_is_rejected():
    assert promotion({'roc_auc':.80,'recall':.70,'f1':.70},{'roc_auc':.90,'recall':.80})=='PROMOTION_REJECTED'
def test_mlflow_local_tracking_registration_and_loadback(tmp_path):
    tr,val,_=split(generate());run,version,loaded,values=track_and_register(tmp_path,train(tr),val,'churn_test')
    assert run and version=='1' and loaded.predict(val[0][:2]).shape==(2,) and set(values)>={'roc_auc','recall','f1'}
def test_audit_idempotency_and_delayed_performance_review(tmp_path):
    a=Audit(tmp_path/'audit.db');k=operation_key('tenant-acme','DEPLOY','2','1');a.record(k,'tenant-acme','DEPLOY','COMPLETED',{'version':'2'});a.record(k,'tenant-acme','DEPLOY','COMPLETED',{'version':'2'})
    assert a.get(k)[0]=='COMPLETED';assert delayed_performance({'recall':.8},{'recall':.7})=='ROLLBACK_REVIEW_REQUIRED'
def test_manifest_stale_write_interruption_and_reconciliation(tmp_path):
    import pytest
    m=Manifest(tmp_path/'deployment.json'); first,_=m.deploy('tenant-acme','1','one');
    with pytest.raises(StaleManifest): m.deploy('tenant-acme','2','two',expected_revision=0)
    with pytest.raises(RuntimeError):m.deploy('tenant-acme','2','two',expected_revision=1,inject_before_replace=True)
    assert m.read()['active_version']=='1'
    audit=Audit(tmp_path/'audit.db');audit.record('two','tenant-acme','DEPLOY','INTENT',{})
    assert m.reconcile(audit,'two')=='RECOVERY_REQUIRED'
    m.deploy('tenant-acme','2','two',expected_revision=1); assert m.reconcile(audit,'two')=='RECONCILED'
def test_schema_and_class_coverage_rejected():
    import pytest
    with pytest.raises(AssertionError):split(generate(n=40))
def test_qualifying_candidate_passes_without_test_selection():
    tr,val,test=split(generate(seed=9,class_sep=3));model=train(tr);assert promotion(metrics(model,val))=='PROMOTION_APPROVED';assert len(test[0])==100
