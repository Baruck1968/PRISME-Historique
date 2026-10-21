"""One finite campaign task on a configured durable Linux host; never a scheduler."""
import argparse
import json
from pathlib import Path
from campaign import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-root',required=True,type=Path)
    p.add_argument('--public-key',required=True,type=Path)
    p.add_argument('--task',required=True,choices=['T1','T2','T3','T4','T5','T6'])
    p.add_argument('--durable-host-confirmed',action='store_true')
    a=p.parse_args()
    states=[]
    for path in a.private_root.glob('manifest_*.json'):
        if json.loads(path.read_text()).get('type')=='prisme_campaign1':states.append(path)
    if not states:raise SystemExit('No private campaign state; no API request permitted')
    print(json.dumps(run(a.private_root,max(states),a.task,a.public_key,a.durable_host_confirmed),indent=2))
