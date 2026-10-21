"""Offline campaign safeguards; fixtures are artificial, never sports observations."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('campaign',ROOT/'research/observatoire_v1/campaign1/campaign.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CampaignTests(unittest.TestCase):
 def test_quota_missing_and_noninteger_refused(self):
  for h in [{},{'x-requests-used':'1','x-requests-remaining':None,'x-requests-last':'0'},{'x-requests-used':'1','x-requests-remaining':'1','x-requests-last':'1.5'}]:
   with self.assertRaises(ValueError):c.read_quota(h)
 def test_cap_reset_remaining_and_attempts(self):
  s={'baseline_used':1,'attempts':1,'halted':False}
  self.assertEqual(c.budget(s,{'used':2,'remaining':498}),1)
  for q in [{'used':13,'remaining':400},{'used':0,'remaining':500},{'used':2,'remaining':0}]:
   with self.assertRaises(ValueError):c.budget(s,q)
  with self.assertRaises(ValueError):c.budget(dict(s,attempts=12),{'used':2,'remaining':498})
 def test_window_exact_boundaries_and_return_delay(self):
  target='2030-01-02T12:00:00Z'
  self.assertTrue(c.window(target,c.pilot.iso('2030-01-02T11:55:00Z'),c.pilot.iso('2030-01-02T12:05:00Z')))
  self.assertFalse(c.window(target,c.pilot.iso('2030-01-02T12:00:00Z'),c.pilot.iso('2030-01-02T12:05:01Z')))
 def test_no_host_no_network(self):
  with patch.object(c,'private_repo') as net:
   with self.assertRaises(ValueError):c.run(Path('/tmp'),Path('/tmp/missing'),'T1',Path('/tmp/key'))
   net.assert_not_called()
 def test_public_repo_refused(self):
  with patch.object(c,'gh',return_value={'private':False,'visibility':'public','owner':{'login':'Baruck1968'},'permissions':{'push':True}}):
   with self.assertRaises(ValueError):c.private_repo()
 def test_persist_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   a=c.persist(Path(d),{'type':'unit_fixture'});b=c.persist(Path(d),{'type':'unit_fixture'})
   self.assertNotEqual(a,b);self.assertTrue(a.exists())
 def fixture(self,d,target,status='pending'):
  state={'type':'prisme_campaign1','tasks':[{'id':'T1','target':target,'status':status,'members':[]}],'halted':False,'baseline_used':1,'attempts':1}
  return c.persist(Path(d),state)
 def test_late_slot_saved_missing_without_odds_or_quota(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.fixture(d,'2000-01-01T00:00:00Z')
   with patch.object(c,'check_key'),patch.object(c,'private_repo'),patch.object(c,'backup',return_value={}),patch.object(c,'quota') as quota,patch.object(c.pilot,'capture') as capture:
    c.run(Path(d),p,'T1',Path('/tmp/public.asc'),True)
    quota.assert_not_called();capture.assert_not_called()
    self.assertEqual(json.loads(max(Path(d).glob('manifest_*.json')).read_text())['tasks'][0]['status'],'missing_late')
 def test_replay_refused_without_odds(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.fixture(d,'2030-01-01T00:00:00Z','reserved')
   with patch.object(c,'check_key'),patch.object(c,'private_repo'),patch.object(c.pilot,'capture') as capture:
    with self.assertRaises(ValueError):c.run(Path(d),p,'T1',Path('/tmp/public.asc'),True)
    capture.assert_not_called()
 def test_api_failure_halts_and_has_one_attempt(self):
  with tempfile.TemporaryDirectory() as d:
   target=datetime.now(timezone.utc).isoformat();p=self.fixture(d,target)
   with patch.object(c,'check_key'),patch.object(c,'private_repo'),patch.object(c,'backup',return_value={}),patch.object(c,'quota',return_value={'used':2,'remaining':498,'last':0}),patch.object(c.pilot,'capture',side_effect=RuntimeError('artificial unit failure')) as capture:
    c.run(Path(d),p,'T1',Path('/tmp/public.asc'),True)
    self.assertEqual(capture.call_count,1)
    state=json.loads(max(Path(d).glob('manifest_*.json')).read_text());self.assertTrue(state['halted']);self.assertEqual(state['attempts'],2)

 def test_missing_post_capture_counter_halts_without_replacement(self):
  with tempfile.TemporaryDirectory() as d:
   target=datetime.now(timezone.utc).isoformat();p=self.fixture(d,target)
   def fake_capture(args):
    c.pilot.store(args.output,{'status':'captured','quota':{}})
    return 0
   with patch.object(c,'check_key'),patch.object(c,'private_repo'),patch.object(c,'backup',return_value={}),patch.object(c,'quota',return_value={'used':2,'remaining':498,'last':0}),patch.object(c.pilot,'capture',side_effect=fake_capture) as capture:
    c.run(Path(d),p,'T1',Path('/tmp/public.asc'),True)
    self.assertEqual(capture.call_count,1)
    state=json.loads(max(Path(d).glob('manifest_*.json')).read_text());self.assertTrue(state['halted'])
 def test_timers_are_six_finite_dates_without_catchup(self):
  timers=list((ROOT/'research/observatoire_v1/campaign1/systemd').glob('*.timer'))
  self.assertEqual(len(timers),6)
  for path in timers:
   text=path.read_text();self.assertIn('OnCalendar=2026-10-',text);self.assertIn('Persistent=false',text)
   self.assertNotIn('*',text)

if __name__=='__main__':unittest.main()
