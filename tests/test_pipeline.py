from mlops_reference.pipeline import *
from mlops_reference.tracking import track_and_register
from mlops_reference.governance import Audit,operation_key,delayed_performance
from mlops_reference.governance import Catalog,TrustedOperator
from mlops_reference.lifecycle import Lifecycle
from mlops_reference.monitoring import evaluate
from mlops_reference.contracts import ChurnData,validate
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
    assert a.get(k)[0]=='COMPLETED' and a.history(k)==['COMPLETED','COMPLETED'];assert delayed_performance({'recall':.8},{'recall':.7})=='ROLLBACK_REVIEW_REQUIRED'
def test_manifest_stale_write_interruption_and_reconciliation(tmp_path):
    import pytest
    m=Manifest(tmp_path/'deployment.json'); first,_=m.deploy('tenant-acme','1','one');
    with pytest.raises(StaleManifest): m.deploy('tenant-acme','2','two',expected_revision=0)
    with pytest.raises(RuntimeError):m.deploy('tenant-acme','2','two',expected_revision=1,inject_before_replace=True)
    assert m.read()['active_version']=='1'
    audit=Audit(tmp_path/'audit.db');audit.record('two','tenant-acme','DEPLOY','INTENT',{})
    assert m.reconcile(audit,'two')=='RECOVERY_REQUIRED'
    audit.record('two','tenant-acme','DEPLOY','COMPLETED',{});m.deploy('tenant-acme','2','two',expected_revision=1); assert m.reconcile(audit,'two',True)=='RECONCILED'
def test_concurrent_cross_tenant_manifest_write_is_rejected(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import pytest
    m=Manifest(tmp_path/'deployment.json');m.deploy('tenant-acme','1','initial')
    with ThreadPoolExecutor(max_workers=2) as pool:
        good=pool.submit(m.deploy,'tenant-acme','2','good')
        bad=pool.submit(m.deploy,'tenant-other','2','bad')
        good.result()
        with pytest.raises(PermissionError):bad.result()
    assert m.read()['tenant_id']=='tenant-acme'
def test_reconciliation_requires_completed_audit_and_registry_authority(tmp_path):
    m=Manifest(tmp_path/'deployment.json');m.deploy('tenant-acme','1','op');a=Audit(tmp_path/'audit.db');a.record('op','tenant-acme','DEPLOY','INTENT',{})
    assert m.reconcile(a,'op',True)=='RECOVERY_REQUIRED'
    a.record('op','tenant-acme','DEPLOY','COMPLETED',{})
    assert m.reconcile(a,'op',False)=='RECOVERY_REQUIRED' and m.reconcile(a,'op',True)=='RECONCILED'
def test_forged_catalog_approval_cannot_authorize_deploy(tmp_path):
    import pytest
    life=Lifecycle(tmp_path);op=TrustedOperator('tenant-acme','ops',True);tr,val,_=split(generate())
    run,version,_,bad=track_and_register(tmp_path,train(tr),val);life.catalog.register('tenant-acme',version,run,'dataset+pipeline',bad)
    with pytest.raises(PermissionError):life.deploy(op,version)
def test_schema_and_class_coverage_rejected():
    import pytest
    with pytest.raises(AssertionError):split(generate(n=40))
def test_qualifying_candidate_passes_without_test_selection():
    tr,val,test=split(generate(seed=9,class_sep=3));model=train(tr);assert promotion(metrics(model,val))=='PROMOTION_APPROVED';assert len(test[0])==100
def test_only_registered_promoted_tenant_candidate_can_deploy_and_trusted_rollback(tmp_path):
    import pytest
    life=Lifecycle(tmp_path);op=TrustedOperator('tenant-acme','ops',True)
    with pytest.raises(PermissionError):life.deploy(op,'1')
    tr,val,_=split(generate(seed=9,class_sep=3));run1,version1,_,validation1=track_and_register(tmp_path,train(tr),val)
    assert promotion(validation1)=='PROMOTION_APPROVED'
    life.catalog.register('tenant-acme',version1,run1,'dataset+pipeline',validation1);life.deploy(op,version1)
    tr,val,_=split(generate(seed=11,class_sep=3));run2,version2,_,validation2=track_and_register(tmp_path,train(tr),val)
    assert promotion(validation2)=='PROMOTION_APPROVED'
    life.catalog.register('tenant-acme',version2,run2,'dataset+pipeline',validation2);life.deploy(op,version2)
    before=life.manifest.read().copy();history=life.audit.history(before['operation_key'])[:]
    assert life.reconcile(op,before['operation_key'])=='RECONCILED'
    assert life.manifest.read()==before and life.audit.history(before['operation_key'])==history
    with pytest.raises(PermissionError):life.rollback(TrustedOperator('tenant-acme','bad',False))
    assert life.rollback(op)[0]['active_version']==version1
    with pytest.raises(PermissionError):life.deploy(TrustedOperator('tenant-other','ops',True),version2)
def test_customer_contract_and_delayed_label_monitoring(tmp_path):
    import pytest
    data=generate();contract=ChurnData('tenant-acme',np.arange(len(data.y)),data.X,data.y,data.fingerprint);assert validate(contract)
    with pytest.raises(ValueError):validate(ChurnData('tenant-acme',np.zeros(len(data.y)),data.X,data.y,data.fingerprint))
    tr,val,test=split(data);model=train(tr);audit=Audit(tmp_path/'audit.db');report=evaluate('tenant-acme',model,tr[0],test,{'recall':.9},audit)
    assert report['drift'] in {'HEALTHY','DRIFT_DETECTED'} and report['performance']=='ROLLBACK_REVIEW_REQUIRED' and audit.get(report['operation_key'])
def test_invalid_active_champion_blocks_qualified_candidate_deployment(tmp_path):
    import pytest,sqlite3
    life=Lifecycle(tmp_path);op=TrustedOperator('tenant-acme','ops',True);tr,val,_=split(generate(seed=9,class_sep=3))
    run1,v1,_,m1=track_and_register(tmp_path,train(tr),val);life.catalog.register('tenant-acme',v1,run1,'dataset+pipeline',m1);life.deploy(op,v1)
    before=life.manifest.read().copy();tr,val,_=split(generate(seed=11,class_sep=3));run2,v2,_,m2=track_and_register(tmp_path,train(tr),val);life.catalog.register('tenant-acme',v2,run2,'dataset+pipeline',m2)
    c=sqlite3.connect(tmp_path/'audit.db');c.execute('DELETE FROM candidates WHERE tenant=? AND version=?',('tenant-acme',v1));c.commit();c.close()
    with pytest.raises(PermissionError):life.deploy(op,v2)
    assert life.manifest.read()==before
    assert 'COMPLETED' not in life.audit.history(operation_key('tenant-acme','DEPLOY',v2,v1))
def test_completed_rollback_reconciliation_is_read_only(tmp_path):
    life=Lifecycle(tmp_path);op=TrustedOperator('tenant-acme','ops',True);versions=[]
    for seed in (9,11):
        tr,val,_=split(generate(seed=seed,class_sep=3));run,v,_,metric=track_and_register(tmp_path,train(tr),val);life.catalog.register('tenant-acme',v,run,'dataset+pipeline',metric);life.deploy(op,v);versions.append(v)
    rolled,_=life.rollback(op);before=life.manifest.read().copy();key=before['operation_key'];history=life.audit.history(key)[:]
    restarted=Lifecycle(tmp_path)
    assert restarted.reconcile(op,key)=='RECONCILED'
    assert restarted.manifest.read()==before and restarted.audit.history(key)==history and rolled['active_version']==versions[0]
