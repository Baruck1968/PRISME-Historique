"""Copy a private snapshot to an explicitly supplied storage path, verify hashes.

This does not provision storage or establish durability. Never run on public storage.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pilot

def archive(source,destination):
    source,destination=source.resolve(),destination.resolve()
    repo=Path(__file__).resolve().parents[3]
    if destination==repo or repo in destination.parents or destination==source or source in destination.parents:
        raise ValueError('Archive destination must be outside this repository and source')
    if not destination.is_dir():raise ValueError('An existing private storage directory is required')
    if destination.stat().st_mode & 0o077:raise ValueError('Storage directory must be accessible to owner only')
    target=destination/('prisme_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    with pilot.locked(source):
        pilot.verify(source)
        files=[]
        for f in source.iterdir():
            if f.name=='.lock':continue
            if f.is_symlink() or not f.is_file():raise ValueError('Unexpected private entry')
            if f.name!='journal.jsonl' and not re.fullmatch(r'(?:manifest_\d{8}T\d{12}Z|\d{8}T\d{12}Z_[a-f0-9]{32})\.json',f.name):
                raise ValueError('Unexpected private filename')
            files.append(f)
        target.mkdir(mode=0o700)
        hashes={}
        for f in sorted(files):
            data=f.read_bytes()
            with (target/f.name).open('xb') as stream:
                os.chmod(target/f.name,0o600);stream.write(data);stream.flush();os.fsync(stream.fileno())
            hashes[f.name]=hashlib.sha256(data).hexdigest()
        with (target/'inventory.json').open('x') as stream:
            os.chmod(target/'inventory.json',0o600);json.dump(hashes,stream,sort_keys=True,indent=2);stream.flush();os.fsync(stream.fileno())
        for name,sha in hashes.items():
            if hashlib.sha256((target/name).read_bytes()).hexdigest()!=sha:raise ValueError('Copy verification failed')
        pilot.verify(target)
    return {'snapshot_directory':str(target),'files_verified':len(hashes),'durability_confirmed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    args=p.parse_args()
    print(json.dumps(archive(args.source,args.destination),indent=2))
