"""Bounded campaign preparation and manual one-shot runner; no daemon/scheduler.

Requires a durable Linux host sharing the private state directory across runs.
"""
import argparse
from datetime import datetime,timezone,timedelta
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from urllib.request import Request,build_opener
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pilot
sys.path.insert(0,str(ROOT/'phase2'))
import plan
sys.path.insert(0,str(ROOT/'vault'))
import vault

FP='5A14F786E05DFC58C886F0A8D8CAB0E82DA81776'
SUB='558B3344B7FD5DCDDF70E7C30596A55A79FBA862'
REPO='Baruck1968/PRISME-Archives'
CAP=12

def now():return datetime.now(timezone.utc).isoformat()
def gh(*args):return json.loads(subprocess.check_output(['gh','api',*args],stderr=subprocess.DEVNULL))
def private_repo():
    meta=gh('repos/'+REPO)
    if not (meta['private'] is True and meta['visibility']=='private' and meta['owner']['login']=='Baruck1968' and meta['permissions']['push'] is True):
        raise ValueError('Private repository write access not confirmed')
    return meta

def check_key(path):
    with tempfile.TemporaryDirectory() as d:
        result=subprocess.run(['gpg','--homedir',d,'--batch','--with-colons','--import-options','show-only','--dry-run','--import',str(path)],capture_output=True,check=True)
    rows=[]
    for line in result.stdout.decode().splitlines():
        c=line.split(':')
        if c[0] in ('pub','sub'):rows.append({'kind':c[0],'valid':c[1],'created':c[5],'expires':c[6],'caps':c[11]})
        elif c[0]=='fpr':rows[-1]['fp']=c[9]
    timestamp=datetime.now(timezone.utc).timestamp()
    if len([r for r in rows if r['kind']=='pub'])!=1 or rows[0].get('fp')!=FP:
        raise ValueError('Wrong public primary key')
    if not any(r.get('fp')==SUB and r['kind']=='sub' and 'e' in r['caps'] and r['valid'] not in ('r','e','d') and int(r['created'])<=timestamp and (not r['expires'] or timestamp<int(r['expires'])) for r in rows):
        raise ValueError('No current expected encryption subkey')

def persist(root,state):
    state=json.loads(json.dumps(state));state['updated_at']=now()
    dest=root/('manifest_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with dest.open('xb') as f:
        os.chmod(dest,0o600);f.write(pilot.encoded(state));f.flush();os.fsync(f.fileno())
    return dest

def backup(root,key):
    check_key(key);meta=private_repo()
    folder=Path('/workspace/prisme-encrypted-staging') if Path('/workspace').exists() else root.parent/'encrypted-staging'
    folder.mkdir(mode=0o700,exist_ok=True)
    filename='campaign1_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+uuid.uuid4().hex[:8]+'.gpg'
    encrypted=folder/filename
    info=vault.encrypt(root,key,FP,encrypted)
    private_repo()
    body={'message':'Preserve encrypted PRISME campaign state','branch':meta['default_branch'],'content':base64.b64encode(encrypted.read_bytes()).decode()}
    with tempfile.NamedTemporaryFile(mode='w',suffix='.json',delete=False) as f:
        json.dump(body,f);tmp=Path(f.name)
    try:result=gh('--method','PUT','repos/'+REPO+'/contents/'+filename,'--input',str(tmp))
    finally:tmp.unlink()
    commit=result['commit']['sha']
    received=gh('repos/'+REPO+'/contents/'+filename+'?ref='+commit)
    downloaded=base64.b64decode(received['content'])
    if hashlib.sha256(downloaded).hexdigest()!=info['ciphertext_sha256']:raise ValueError('Remote archive mismatch')
    private_repo()
    return dict(path=filename,commit=commit,sha256=info['ciphertext_sha256'],bytes=len(downloaded),private=True,retrieval_verified=True)

def quota():
    key=os.environ.get('THE_ODDS_API_KEY')
    if not key:raise ValueError('Missing key')
    req=Request('https://api.the-odds-api.com/v4/sports/?'+urlencode({'apiKey':key}),method='GET')
    try:
        with build_opener(pilot.NoRedirect()).open(req,timeout=20) as response:
            return read_quota({k:response.headers.get(k) for k in ('x-requests-used','x-requests-remaining','x-requests-last')})
    except Exception:
        raise ValueError('Catalog or quota unavailable') from None

def read_quota(headers):
    vals={k:headers.get(k) for k in ('x-requests-used','x-requests-remaining','x-requests-last')}
    if any(not isinstance(v,str) or not v.isdecimal() for v in vals.values()):raise ValueError('Quota missing or invalid')
    return {'used':int(vals['x-requests-used']),'remaining':int(vals['x-requests-remaining']),'last':int(vals['x-requests-last'])}

def budget(state,q):
    delta=q['used']-state['baseline_used']
    if state.get('halted') or delta<0 or delta>=CAP or q['remaining']<1 or state['attempts']>=CAP:
        raise ValueError('Campaign stopped: budget/reset/remaining/attempt limit')
    return delta

def window(target,start,end=None):
    end=end or start
    return end>=start and max(abs((start-pilot.iso(target)).total_seconds()),abs((end-pilot.iso(target)).total_seconds()))<=300

def prepare(envelope,asof,initial,baseline):
    manifest=plan.build(envelope,asof)
    rows=[r for r in manifest['rows'] if r['prospective_candidate']][:3]
    for i,row in enumerate(rows,1):row['alias']='C'+str(i)
    # At most six unique targets, plus discovery = seven normal credits; hard cap remains 12.
    targets=sorted({r[s] for r in rows for s in ('J1','H1')})
    tasks=[]
    for i,target in enumerate(targets,1):
        tasks.append({'id':'T'+str(i),'target':target,'status':'pending','members':[{'event_id':r['event_id'],'alias':r['alias'],'slot':s} for r in rows for s in ('J1','H1') if r[s]==target]})
    old=[]
    current=pilot.iso(asof)
    for row in initial['rows']:
        for slot in ('J1','H1'):
            expired=pilot.iso(row[slot])+timedelta(minutes=5)<current
            old.append({'event_id':row['event_id'],'slot':slot,'target':row[slot],
                        'status':'missing' if expired else 'pending_not_scheduled',
                        'enrolled':row['prospective_candidate'],'discovery_is_observation':False})
    q=read_quota(envelope['quota'])
    if q['used']-baseline!=q['last'] or q['last']!=1:raise ValueError('Unexpected discovery cost/counter')
    return {'type':'prisme_campaign1','version':1,'created_at':asof,'cohort':dict(manifest,rows=rows),
            'initial_manifest_sha256':vault.MANIFEST_HASH,'initial_status':old,
            'baseline_used':baseline,'last_quota':q,'attempts':1,'cap':CAP,
            'discovery_body_sha256':envelope['body_sha256'],'tasks':tasks,'halted':False,
            'scheduler_active':False,'rules_verified':False,'opening_verified':False}

def run(root,state_path,task_id,key,durable_host_confirmed=False):
    if not durable_host_confirmed:raise ValueError('Durable host and exclusive shared state required')
    check_key(key);private_repo()
    # Separate global lock avoids nested collector journal lock deadlocks.
    with pilot.locked(root.parent/'campaign1-control'):
        state=json.loads(state_path.read_text())
        latest=[]
        for path in root.glob('manifest_*.json'):
            obj=json.loads(path.read_text())
            if obj.get('type')=='prisme_campaign1':latest.append(path)
        if not latest or state_path.resolve()!=max(latest).resolve():raise ValueError('Stale state file; replay refused')
        task=next(t for t in state['tasks'] if t['id']==task_id)
        if state['halted'] or task['status']!='pending':raise ValueError('Stopped or already attempted')
        start=datetime.now(timezone.utc)
        if start<pilot.iso(task['target'])-timedelta(minutes=5):raise ValueError('Too early; no network capture')
        if not window(task['target'],start):
            task['status']='missing_late';persist(root,state);return backup(root,key)
        try:
            q=quota();budget(state,q)
            # Reserve exactly one attempt before odds access; never retry after uncertainty.
            state['attempts']+=1;task['status']='reserved';state['last_quota']=q
            reserved=persist(root,state)
            backup(root,key)  # Encrypted recovery evidence before the only odds request.
            if not window(task['target'],datetime.now(timezone.utc)):
                task['status']='missing_late_before_request';persist(root,state);return backup(root,key)
            before=set(root.glob('*_*.json'))
            args=argparse.Namespace(sport='basketball_nba',bookmaker='fanduel',output=root)
            code=pilot.capture(args)
            added=set(root.glob('*_*.json'))-before
            captures=[p for p in added if not p.name.startswith('manifest_')]
            if len(captures)!=1:raise ValueError('Capture evidence ambiguous')
            env=json.loads(captures[0].read_text());task['capture_file']=captures[0].name
            if code!=0:raise ValueError('Odds API failure; no retry')
            after=read_quota(env.get('quota',{}));state['last_quota']=after
            if after['used']<q['used'] or after['used']-q['used']!=after['last'] or after['last']!=1 or after['used']-state['baseline_used']>CAP:
                raise ValueError('Unexpected quota/cost; campaign halted')
            task['status']='captured'
            task['assessments']=[]
            for member in task['members']:
                row=next(r for r in state['cohort']['rows'] if r['event_id']==member['event_id'])
                task['assessments'].append({'alias':member['alias'],**plan.assess(state['cohort'],row,env,member['slot'])})
            if after['used']-state['baseline_used']>=CAP or after['remaining']<1:state['halted']=True
        except Exception as exc:
            state['halted']=True;task['status']='halted';task['error_type']=type(exc).__name__
        saved=persist(root,state)
        receipt=backup(root,key)
        receipt['private_state_file']=saved.name
        return receipt

def aggregate(state,root,asof):
    report={'asof':asof,'candidates':len(state['cohort']['rows']),'complete_indicative_pairs':0,
            'pairs_with_threshold':0,'pairs_without_threshold':0,'missing_or_invalid_pairs':0,
            'pending_pairs':0,'validated_alerts':0,'cap':CAP,'last_known_quota':state['last_quota'],
            'scheduler_active':False}
    for row in state['cohort']['rows']:
        envelopes={}
        pending=False
        for slot in ('J1','H1'):
            task=next(t for t in state['tasks'] if any(m['event_id']==row['event_id'] and m['slot']==slot for m in t['members']))
            if task['status']=='pending' and pilot.iso(asof)<=pilot.iso(task['target'])+timedelta(minutes=5):pending=True
            name=task.get('capture_file')
            envelopes[slot]=json.loads((root/name).read_text()) if name else None
        if pending:
            report['pending_pairs']+=1;continue
        result=plan.compare_pair(state['cohort'],row,envelopes['J1'],envelopes['H1'])
        if result['candidate_changes']:
            report['complete_indicative_pairs']+=1
            report['pairs_with_threshold' if any(v['threshold_reached'] for v in result['candidate_changes'].values()) else 'pairs_without_threshold']+=1
        else:report['missing_or_invalid_pairs']+=1
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private-root',type=Path,default=ROOT/'private')
    p.add_argument('--state',type=Path,required=True);p.add_argument('--task',required=True);p.add_argument('--public-key',type=Path,required=True)
    p.add_argument('--durable-host-confirmed',action='store_true');a=p.parse_args()
    print(json.dumps(run(a.private_root,a.state,a.task,a.public_key,a.durable_host_confirmed),indent=2))
if __name__=='__main__':main()
