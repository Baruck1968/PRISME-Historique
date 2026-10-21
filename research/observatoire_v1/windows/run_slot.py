"""Windows manual/task adapter. Never logs secret values or exception messages."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'campaign1'))
import campaign

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--task',choices=['T1','T2','T3','T4','T5','T6'],required=True)
    a=p.parse_args()
    if os.name!='nt':raise SystemExit('Native Windows adapter; use offline tests on Linux')
    config=json.loads(a.config.read_text(encoding='utf-8-sig'));root=Path(config['PrivateRoot'])
    logs=root.parent/'campaign1-logs';logs.mkdir(exist_ok=True)
    result={'at':datetime.now(timezone.utc).isoformat(),'task':a.task}
    try:
        states=[f for f in root.glob('manifest_*.json') if json.loads(f.read_text()).get('type')=='prisme_campaign1']
        if not states:raise ValueError('Private state absent')
        result['receipt']=campaign.run(root,max(states),a.task,Path(config['PublicKey']),durable_host_confirmed=True)
        result['status']='state_archived'
        states=[f for f in root.glob('manifest_*.json') if json.loads(f.read_text()).get('type')=='prisme_campaign1']
        latest=json.loads(max(states).read_text())
        result['task_outcome']=next(t['status'] for t in latest['tasks'] if t['id']==a.task)
        status=1 if latest['halted'] else 0
    except Exception as exc:
        result.update(status='blocked',error_type=type(exc).__name__);status=1
    name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+a.task+'.json'
    with (logs/name).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({'task':a.task,'status':result['status']}))
    return status
if __name__=='__main__':raise SystemExit(main())
