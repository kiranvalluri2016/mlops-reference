from __future__ import annotations
import argparse,json
from pathlib import Path
from .pipeline import generate,split,train,metrics,Manifest
from .tracking import track_and_register
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='.local');s=p.add_subparsers(dest='command',required=True);s.add_parser('train');s.add_parser('inspect');d=s.add_parser('deploy');d.add_argument('version');d.add_argument('--tenant',default='tenant-acme');r=s.add_parser('rollback');r.add_argument('--tenant',default='tenant-acme');r.add_argument('--authorized',action='store_true')
 a=p.parse_args();root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
 if a.command=='train':
  tr,val,test=split(generate());run,version,_,v=track_and_register(root,train(tr),val);print(json.dumps({'run_id':run,'version':version,'validation':v,'test_report':metrics(train(tr),test)}))
 if a.command=='inspect':print(json.dumps(Manifest(root/'deployment.json').read()))
 if a.command=='deploy':print(json.dumps(Manifest(root/'deployment.json').deploy(a.tenant,a.version,f'deploy:{a.tenant}:{a.version}')[0]))
 if a.command=='rollback':print(json.dumps(Manifest(root/'deployment.json').rollback(a.tenant,f'rollback:{a.tenant}',a.authorized)[0]))
if __name__=='__main__':main()
