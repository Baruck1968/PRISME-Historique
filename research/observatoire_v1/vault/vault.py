"""Offline OpenPGP archive preparation and safe SHA-256 checked restore.

No network, API calls, scheduling, passphrases or private keys required to encrypt.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pilot

MANIFEST='manifest_20261021T151728267195Z.json'
MANIFEST_HASH='627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d'
NAME=re.compile(r'(?:manifest_\d{8}T\d{12}Z|\d{8}T\d{12}Z_[a-f0-9]{32})\.json')

def allowed(name):
    return name=='journal.jsonl' or bool(NAME.fullmatch(name))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def validate(files):
    if MANIFEST not in files or sha(files[MANIFEST])!=MANIFEST_HASH:
        raise ValueError('Original prospective manifest absent or changed')
    if 'journal.jsonl' not in files:raise ValueError('Journal missing')
    previous=None; referenced=set()
    for line in files['journal.jsonl'].decode().splitlines():
        entry=json.loads(line);claimed=entry.pop('entry_sha256');name=entry['file']
        if entry['previous']!=previous or sha(pilot.encoded(entry))!=claimed:
            raise ValueError('Journal chain mismatch')
        if name not in files or sha(files[name])!=entry['sha256']:raise ValueError('Capture mismatch')
        envelope=json.loads(files[name])
        if envelope['status']=='captured' and sha(envelope['raw_utf8'].encode())!=envelope['body_sha256']:
            raise ValueError('Body mismatch')
        previous=claimed;referenced.add(name)
    for name in files:
        if name!='journal.jsonl' and not name.startswith('manifest_') and name not in referenced:
            raise ValueError('Unjournaled capture; preserve and investigate before archiving')
    return len(referenced)

def package(source):
    source=source.resolve()
    with pilot.locked(source):
        files={}
        for path in source.iterdir():
            if path.name=='.lock':continue
            if path.is_symlink() or not path.is_file() or not allowed(path.name):
                raise ValueError('Unexpected private entry')
            files[path.name]=path.read_bytes()
        validate(files)
        # Explicit selection only; never package a checkout, process environment or credentials.
        for keyname in ('THE_ODDS_API_KEY','GH_TOKEN','GITHUB_TOKEN'):
            value=os.environ.get(keyname)
            if value and any(value.encode() in data for data in files.values()):
                raise ValueError('Bound credential found; archive refused')
        inventory={name:sha(data) for name,data in files.items()}
        files['inventory.json']=pilot.encoded(inventory)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
            for name,data in sorted(files.items()):
                item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));item.external_attr=0o100600<<16
                z.writestr(item,data)
        return buf.getvalue()

def encrypt(source,public_key,recipient,output):
    if not re.fullmatch(r'[A-Fa-f0-9]{40}|[A-Fa-f0-9]{64}',recipient):raise ValueError('Full recipient fingerprint required')
    key=public_key.read_bytes()
    if b'PRIVATE KEY' in key:raise ValueError('Public key required, never a private key')
    if b'BEGIN PGP PUBLIC KEY BLOCK' not in key:raise ValueError('Armored public key required')
    if output.exists() or output.with_suffix(output.suffix+'.sha256').exists():raise ValueError('Output already exists')
    repo=Path(__file__).resolve().parents[3]
    if repo==output.resolve() or repo in output.resolve().parents:raise ValueError('Output must be outside public repository')
    data=package(source)
    with tempfile.TemporaryDirectory(prefix='prisme-public-key-') as d:
        cmd=['gpg','--homedir',d,'--batch','--no-auto-key-retrieve','--no-auto-key-import']
        subprocess.run(cmd+['--import'],input=key,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        listing=subprocess.check_output(cmd+['--with-colons','--list-keys'],stderr=subprocess.DEVNULL).decode()
        fingerprints=[line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:')]
        if recipient.upper() not in fingerprints:raise ValueError('Recipient fingerprint mismatch')
        raw=subprocess.check_output(cmd+['--trust-model','always','--recipient',recipient,'--encrypt'],input=data,stderr=subprocess.DEVNULL)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as f:
        os.chmod(output,0o600);f.write(raw);f.flush();os.fsync(f.fileno())
    side=output.with_suffix(output.suffix+'.sha256')
    with side.open('x') as f:f.write(sha(raw)+'  '+output.name+'\n')
    return {'ciphertext_sha256':sha(raw),'ciphertext_bytes':len(raw),'manifest_sha256':MANIFEST_HASH}

def restore(zip_path,destination):
    # Read and verify everything before writing any file. Never ZipFile.extractall.
    with zipfile.ZipFile(zip_path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(not allowed(n) and n!='inventory.json' for n in names):
            raise ValueError('Unexpected or duplicate archive member')
        if sum(i.file_size for i in z.infolist())>100*1024*1024:raise ValueError('Pilot archive exceeds size budget')
        files={n:z.read(n) for n in names}
    inventory=json.loads(files.pop('inventory.json'))
    if set(files)!=set(inventory) or any(sha(data)!=inventory[n] for n,data in files.items()):
        raise ValueError('Inventory mismatch')
    count=validate(files)
    if destination.exists():raise ValueError('Restore destination must be new')
    destination.mkdir(parents=True,mode=0o700)
    for name,data in files.items():
        with (destination/name).open('xb') as f:os.chmod(destination/name,0o600);f.write(data)
    return {'restored_files':len(files),'verified_captures':count,'manifest_sha256':MANIFEST_HASH}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    e=sub.add_parser('encrypt');e.add_argument('--source',type=Path,required=True);e.add_argument('--public-key',type=Path,required=True);e.add_argument('--recipient',required=True);e.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('restore');r.add_argument('zip',type=Path);r.add_argument('destination',type=Path)
    a=p.parse_args()
    result=encrypt(a.source,a.public_key,a.recipient,a.output) if a.command=='encrypt' else restore(a.zip,a.destination)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
