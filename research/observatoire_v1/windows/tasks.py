"""Offline generation of disabled native Windows once-only task XML."""
import argparse
from datetime import datetime,timezone,timedelta
import json
import ntpath
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

NS='http://schemas.microsoft.com/windows/2004/02/mit/task'
ET.register_namespace('',NS)

def document(task,config_path,runner_path,user_sid):
    if not re.fullmatch(r'S-1-\d+(?:-\d+)+',user_sid):raise ValueError('Windows SID required')
    if task['id'] not in ['T1','T2','T3','T4','T5','T6']:raise ValueError('Unexpected task')
    if any('"' in p or '\n' in p or '\r' in p for p in (config_path,runner_path)):raise ValueError('Unsafe argument path')
    if not ntpath.isabs(config_path) or not ntpath.isabs(runner_path):raise ValueError('Absolute Windows paths required')
    target=datetime.fromisoformat(task['target'].replace('Z','+00:00'))
    if target.utcoffset()!=timedelta(0):raise ValueError('UTC target required')
    def add(parent,name,text=None,**attr):
        node=ET.SubElement(parent,'{'+NS+'}'+name,attr)
        if text is not None:node.text=text
        return node
    root=ET.Element('{'+NS+'}Task',{'version':'1.2'})
    registration=add(root,'RegistrationInfo');add(registration,'Description','PRISME campaign1 one-shot '+task['id']+'; disabled preparation')
    triggers=add(root,'Triggers');trigger=add(triggers,'TimeTrigger')
    add(trigger,'StartBoundary',target.isoformat().replace('+00:00','Z'))
    add(trigger,'EndBoundary',(target+timedelta(minutes=5)).isoformat().replace('+00:00','Z'))
    add(trigger,'Enabled','true')
    principals=add(root,'Principals');principal=add(principals,'Principal',id='PrismeUser')
    add(principal,'UserId',user_sid);add(principal,'LogonType','InteractiveToken');add(principal,'RunLevel','LeastPrivilege')
    settings=add(root,'Settings')
    for name,text in [('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','false'),('StopIfGoingOnBatteries','false'),
                      ('StartWhenAvailable','false'),('RunOnlyIfNetworkAvailable','true'),('AllowHardTerminate','true'),
                      ('Enabled','false'),('WakeToRun','true'),('ExecutionTimeLimit','PT3M')]:add(settings,name,text)
    actions=add(root,'Actions',Context='PrismeUser');action=add(actions,'Exec')
    system_root=os.environ.get('SystemRoot',r'C:\Windows')
    if not ntpath.isabs(system_root):raise ValueError('Absolute Windows SystemRoot required')
    add(action,'Command',ntpath.join(system_root,'System32','WindowsPowerShell','v1.0','powershell.exe'))
    add(action,'Arguments','-NoProfile -NonInteractive -File "'+runner_path+'" -ConfigPath "'+config_path+'" -TaskId '+task['id'])
    return ET.tostring(root,encoding='unicode')

def prepare(manifest,config_path,runner_path,sid,asof):
    result=[]
    for task in manifest['tasks']:
        target=datetime.fromisoformat(task['target'].replace('Z','+00:00'))
        expired=asof>target+timedelta(minutes=5)
        result.append({'id':task['id'],'target_utc':task['target'],'status':'non_recoverable' if expired else 'prepared_disabled',
                       'xml':None if expired else document(task,config_path,runner_path,sid)})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--config',required=True)
    p.add_argument('--runner',required=True);p.add_argument('--sid',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();rows=prepare(json.loads(a.manifest.read_text()),a.config,a.runner,a.sid,datetime.now(timezone.utc))
    a.output.mkdir(parents=True,exist_ok=True)
    for row in rows:
        xml=row.pop('xml')
        if xml:
            with (a.output/('PRISME-Campaign1-'+row['id']+'.xml')).open('x',encoding='utf-16') as f:f.write(xml)
    with (a.output/'preparation.json').open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2)
