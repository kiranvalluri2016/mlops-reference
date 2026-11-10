from __future__ import annotations
import argparse,json
from pathlib import Path
from .pipeline import generate,split,train,metrics
from .tracking import track_and_register
from .lifecycle import Lifecycle
from .governance import TrustedOperator,trusted_local_operator
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='.local');s=p.add_subparsers(dest='command',required=True);t=s.add_parser('train');t.add_argument('--qualified',action='store_true');s.add_parser('inspect');d=s.add_parser('deploy');d.add_argument('version');d.add_argument('--tenant',default='tenant-acme');r=s.add_parser('rollback');r.add_argument('--tenant',default='tenant-acme')
 a=p.parse_args();root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
 if a.command=='train':
  tr,val,test=split(generate(seed=9,class_sep=3) if a.qualified else generate());model=train(tr);run,version,_,v=track_and_register(root,model,val);life=Lifecycle(root);decision='PROMOTION_APPROVED' if v['roc_auc']>=.75 and v['recall']>=.65 and v['f1']>=.65 else 'PROMOTION_REJECTED';life.catalog.register('tenant-acme',version,run,'dataset+pipeline');life.catalog.decide('tenant-acme',version,decision);print(json.dumps({'run_id':run,'version':version,'promotion':decision,'validation':v,'test_report':metrics(model,test)}))
 if a.command=='inspect':print(json.dumps(Lifecycle(root).manifest.read()))
 if a.command=='deploy':print(json.dumps(Lifecycle(root).deploy(TrustedOperator(a.tenant,'cli'),a.version)[0]))
 if a.command=='rollback':print(json.dumps(Lifecycle(root).rollback(trusted_local_operator(a.tenant))[0]))
if __name__=='__main__':main()
