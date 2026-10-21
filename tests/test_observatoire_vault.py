"""Offline archive tests. Temporary test keys never serve as user recovery keys."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vault',ROOT/'research/observatoire_v1/vault/vault.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
SOURCE=ROOT/'research/observatoire_v1/private'

@unittest.skipUnless((SOURCE/v.MANIFEST).exists(),'Private real capture not distributed in public repository')
class VaultTests(unittest.TestCase):
 def test_real_offline_encrypt_decrypt_restore(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);home=root/'keys';home.mkdir(mode=0o700)
   cmd=['gpg','--homedir',str(home),'--batch','--pinentry-mode','loopback','--passphrase','']
   subprocess.run(cmd+['--quick-generate-key','PRISME temporary test key','rsa2048','encr','1d'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   listing=subprocess.check_output(cmd+['--with-colons','--list-keys'],stderr=subprocess.DEVNULL).decode()
   fp=next(x.split(':')[9] for x in listing.splitlines() if x.startswith('fpr:'))
   pub=root/'public.asc';pub.write_bytes(subprocess.check_output(cmd+['--armor','--export',fp]))
   out=root/'archive.gpg';result=v.encrypt(SOURCE,pub,fp,out)
   self.assertEqual(v.sha(out.read_bytes()),result['ciphertext_sha256'])
   decrypted=subprocess.check_output(cmd+['--decrypt',str(out)],stderr=subprocess.DEVNULL)
   z=root/'snapshot.zip';z.write_bytes(decrypted);restore=root/'restore';verified=v.restore(z,restore)
   self.assertEqual(verified['manifest_sha256'],v.MANIFEST_HASH)
   self.assertEqual(verified['verified_captures'],2)
   self.assertEqual((restore/v.MANIFEST).read_bytes(),(SOURCE/v.MANIFEST).read_bytes())
   for f in restore.iterdir():self.assertEqual(f.read_bytes(),(SOURCE/f.name).read_bytes())
   corrupted=bytearray(out.read_bytes());corrupted[len(corrupted)//2]^=1
   self.assertNotEqual(v.sha(corrupted),result['ciphertext_sha256'])
   bad=root/'corrupt.gpg';bad.write_bytes(corrupted)
   proc=subprocess.run(cmd+['--decrypt',str(bad)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   self.assertNotEqual(proc.returncode,0)
 def test_pinned_manifest_and_capture_integrity(self):
  with zipfile.ZipFile(io.BytesIO(v.package(SOURCE))) as z:files={n:z.read(n) for n in z.namelist() if n!='inventory.json'}
  files[v.MANIFEST]+=b' '
  with self.assertRaises(ValueError):v.validate(files)
 def test_no_path_traversal_or_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);z=root/'bad.zip'
   with zipfile.ZipFile(z,'w') as f:f.writestr('../escape','bad')
   with self.assertRaises(ValueError):v.restore(z,root/'restore')
   self.assertFalse((root/'restore').exists())
 def test_unexpected_secret_filename_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'.env').write_text('artificial unit fixture, not a credential')
   with self.assertRaises(ValueError):v.package(root)

if __name__=='__main__':unittest.main()
