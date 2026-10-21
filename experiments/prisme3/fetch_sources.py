#!/usr/bin/env python3
"""Restore missing pinned public sources; preserve every existing file."""
import hashlib
import json
from pathlib import Path
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def main():
    manifest = json.loads((ROOT / 'experiments/prisme3/source_manifest.json').read_text())
    for source in manifest['sources']:
        path = ROOT / source['path']
        if not path.resolve().is_relative_to(ROOT):
            raise RuntimeError('Source path escapes repository')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + '.partial.' + uuid.uuid4().hex)
            with urllib.request.urlopen(source['url'], timeout=90) as response, partial.open('xb') as f:
                while block := response.read(1024*1024):
                    f.write(block)
            if partial.stat().st_size != source['bytes'] or digest(partial) != source['sha256']:
                raise RuntimeError('Source changed; downloaded bytes retained at ' + str(partial))
            if path.exists():
                raise RuntimeError('Destination appeared concurrently; preserve both files')
            partial.rename(path)
        if path.stat().st_size != source['bytes'] or digest(path) != source['sha256']:
            raise RuntimeError('Existing source mismatch; no overwrite: ' + str(path))
        print('Verified:', source['path'])


if __name__ == '__main__':
    main()
