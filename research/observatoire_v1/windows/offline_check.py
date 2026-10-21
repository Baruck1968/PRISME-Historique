"""Offline Windows readiness/expiry report. Does not change private manifests."""
import argparse
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'campaign1'))
import campaign

def expired(target,asof):
    return campaign.pilot.iso(asof)>campaign.pilot.iso(target)+timedelta(minutes=5)

def check(root,key,asof):
    campaign.check_key(key)
    count=campaign.pilot.verify(root)
    original=root/campaign.vault.MANIFEST
    if hashlib.sha256(original.read_bytes()).hexdigest()!=campaign.vault.MANIFEST_HASH:
        raise ValueError('Initial manifest mismatch')
    states=[]
    for path in root.glob('manifest_*.json'):
        state=json.loads(path.read_text())
        if state.get('type')=='prisme_campaign1':states.append((path,state))
    if not states:raise ValueError('Campaign state missing')
    path,state=max(states,key=lambda pair:pair[0])
    tasks=[{'id':t['id'],'target_utc':t['target'],'status':('non_recoverable' if expired(t['target'],asof) and t['status']=='pending' else t['status'])} for t in state['tasks']]
    return {'asof':asof,'platform':os.name,'journal_entries':count,'initial_manifest_sha256':campaign.vault.MANIFEST_HASH,
            'campaign_state_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tasks':tasks,
            'network_used':False,'scheduler_enabled':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private-root',required=True,type=Path);p.add_argument('--public-key',required=True,type=Path)
    a=p.parse_args();print(json.dumps(check(a.private_root,a.public_key,datetime.now(timezone.utc).isoformat()),indent=2))
