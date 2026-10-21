"""Offline portability tests; Windows APIs are simulated on this Linux host."""
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OBS=ROOT/'research/observatoire_v1';WIN=OBS/'windows'
sys.path.insert(0,str(OBS))
import file_lock

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

tasks=load('windows_tasks',WIN/'tasks.py')
check=load('windows_check',WIN/'offline_check.py')

class WindowsPreparationTests(unittest.TestCase):
 def task(self):return {'id':'T1','target':'2026-10-21T23:10:00+00:00'}
 def xml(self):return tasks.document(self.task(),r'C:\Private Space\config.json',r'C:\Code Space\Run-Slot.ps1','S-1-5-21-123-456-789-1001')
 def test_xml_disabled_once_utc_no_catchup(self):
  doc=ET.fromstring(self.xml());ns={'t':tasks.NS}
  self.assertEqual(doc.find('t:Settings/t:Enabled',ns).text,'false')
  self.assertEqual(doc.find('t:Settings/t:StartWhenAvailable',ns).text,'false')
  self.assertEqual(doc.find('t:Settings/t:MultipleInstancesPolicy',ns).text,'IgnoreNew')
  self.assertEqual(doc.find('t:Settings/t:WakeToRun',ns).text,'true')
  self.assertEqual(doc.find('t:Triggers/t:TimeTrigger/t:StartBoundary',ns).text,'2026-10-21T23:10:00Z')
  self.assertIsNone(doc.find('.//t:Repetition',ns));self.assertIsNone(doc.find('.//t:RestartOnFailure',ns))
 def test_sid_and_argument_escaping(self):
  text=self.xml();self.assertIn('InteractiveToken',text);self.assertIn('LeastPrivilege',text)
  for bad in ['bad','S-1-5-21\nmalicious']:
   with self.assertRaises(ValueError):tasks.document(self.task(),r'C:\c.json',r'C:\r.ps1',bad)
  with self.assertRaises(ValueError):tasks.document(self.task(),'C:\\bad".json',r'C:\r.ps1','S-1-5-21-1')
 def test_elapsed_not_recoverable_no_xml(self):
  manifest={'tasks':[self.task()]}
  rows=tasks.prepare(manifest,r'C:\c.json',r'C:\r.ps1','S-1-5-21-1',datetime(2026,10,22,tzinfo=timezone.utc))
  self.assertEqual(rows[0]['status'],'non_recoverable');self.assertIsNone(rows[0]['xml'])
  self.assertFalse(check.expired(self.task()['target'],'2026-10-21T23:15:00Z'))
  self.assertTrue(check.expired(self.task()['target'],'2026-10-21T23:15:00.000001Z'))
 def test_no_activation_command_in_installation(self):
  text=(WIN/'Install-Tasks.ps1').read_text()
  self.assertNotIn('Enable-ScheduledTask',text);self.assertNotIn('Start-ScheduledTask',text)
  self.assertIn('[switch]$RegisterDisabled',text);self.assertIn('Disable-ScheduledTask',text)
  self.assertNotIn('Enable-ScheduledTask',(WIN/'Uninstall-Tasks.ps1').read_text())
 def test_current_six_dates_are_unchanged(self):
  manifest=json.loads((OBS/'campaign1/manifest_redacted.json').read_text())
  rows=tasks.prepare(manifest,r'C:\c.json',r'C:\r.ps1','S-1-5-21-1',datetime(2026,10,21,16,tzinfo=timezone.utc))
  self.assertEqual(len(rows),6)
  self.assertEqual([r['target_utc'] for r in rows],[r['target'] for r in manifest['tasks']])
 def test_msvcrt_byte_lock_release_after_exception(self):
  calls=[]
  def fake(fd,mode,n):calls.append((mode,n,os.lseek(fd,0,os.SEEK_CUR)))
  module=types.SimpleNamespace(LK_NBLCK=1,LK_UNLCK=2,locking=fake)
  with tempfile.TemporaryDirectory() as d,patch.object(file_lock,'IS_WINDOWS',True),patch.dict(sys.modules,{'msvcrt':module}):
   with self.assertRaises(RuntimeError):
    with file_lock.locked(Path(d)):raise RuntimeError('unit fixture')
  self.assertEqual(calls,[(1,1,0),(2,1,0)])
 def test_windows_contention_times_out_fail_closed(self):
  def busy(*args):raise PermissionError(13,'unit contention')
  module=types.SimpleNamespace(LK_NBLCK=1,LK_UNLCK=2,locking=busy)
  with tempfile.TemporaryDirectory() as d,patch.object(file_lock,'IS_WINDOWS',True),patch.dict(sys.modules,{'msvcrt':module}):
   with self.assertRaises(TimeoutError):
    with file_lock.locked(Path(d),timeout=0):pass
 def test_real_cross_process_lock_release_on_exit(self):
  with tempfile.TemporaryDirectory() as d:
   code='import sys,time;sys.path.insert(0,sys.argv[1]);from file_lock import locked;from pathlib import Path\nwith locked(Path(sys.argv[2])):\n print("held",flush=True);time.sleep(10)'
   proc=subprocess.Popen([sys.executable,'-c',code,str(OBS),d],stdout=subprocess.PIPE,text=True)
   try:
    self.assertEqual(proc.stdout.readline().strip(),'held')
    with self.assertRaises(TimeoutError):
     with file_lock.locked(Path(d),timeout=.1):pass
   finally:
    proc.terminate();proc.wait(timeout=5);proc.stdout.close()
   with file_lock.locked(Path(d),timeout=.1):pass
 def test_secure_input_not_task_argument(self):
  text=(WIN/'Set-LocalCredential.ps1').read_text();self.assertIn('-AsSecureString',text);self.assertIn('Export-Clixml',text)
  text=(WIN/'Run-Slot.ps1').read_text();self.assertIn('ZeroFreeBSTR',text);self.assertIn('Remove-Item Env:THE_ODDS_API_KEY',text)
  self.assertNotIn('THE_ODDS_API_KEY',self.xml())
  with patch.dict(os.environ,{'SystemRoot':r'D:\Windows'}):self.assertIn(r'D:\Windows\System32',self.xml())

 def test_windows_paths_are_not_shell_escaped_twice(self):
  import ntpath
  config=json.loads((WIN/'config.example.json').read_text())
  for value in config.values():self.assertEqual(value,ntpath.normpath(value))
  for name in ('Install-Tasks.ps1','Uninstall-Tasks.ps1'):
   text=(WIN/name).read_text()
   self.assertNotIn(chr(92)*2,text)
   self.assertIn("-TaskPath '"+chr(92)+"'",text)

if __name__=='__main__':unittest.main()
