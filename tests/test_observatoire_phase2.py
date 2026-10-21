"""Artificial unit fixtures; not actual sports data or scientific results."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import json

ROOT=Path(__file__).resolve().parents[1]/'research/observatoire_v1/phase2'
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
plan=module('plan');archive=module('archive');pilot=plan.pilot

class Phase2Tests(unittest.TestCase):
 def envelope(self):
  event={'id':'fixture','sport_key':'basketball_nba','commence_time':'2030-01-03T12:00:00Z',
         'home_team':'A','away_team':'B','bookmakers':[{'key':'fanduel','markets':[{'key':'h2h','last_update':'2030-01-01T12:00:00Z','outcomes':[{'name':'A','price':2},{'name':'B','price':2}]}]}]}
  body=json.dumps([event]);return {'source':'the-odds-api.com','status':'captured','raw_utf8':body,'body_sha256':pilot.digest(body.encode()),'requested_at':'2030-01-01T12:00:30Z','received_at':'2030-01-01T12:00:31Z'}
 def test_enrollment_before_J1_only(self):
  e=self.envelope();m=plan.build(e,'2030-01-01T12:01:00Z');self.assertTrue(m['rows'][0]['prospective_candidate'])
  later=plan.build(e,'2030-01-02T12:00:00Z');self.assertFalse(later['rows'][0]['prospective_candidate']);self.assertEqual(later['threshold_percent'],'20')
 def test_integrity_and_no_time_travel(self):
  e=self.envelope()
  with self.assertRaises(ValueError):plan.build(e,'2030-01-01T11:00:00Z')
  e['body_sha256']='bad'
  with self.assertRaises(ValueError):plan.build(e,'2030-01-01T13:00:00Z')
 def slot_capture(self):
  e=self.envelope();data=json.loads(e['raw_utf8']);data[0]['bookmakers'][0]['markets'][0]['last_update']='2030-01-02T11:59:30Z';e['raw_utf8']=json.dumps(data);e['body_sha256']=pilot.digest(e['raw_utf8'].encode());e.update(requested_at='2030-01-02T12:00:00Z',received_at='2030-01-02T12:00:01Z');return e
 def test_missing_and_indicative(self):
  m=plan.build(self.envelope(),'2030-01-01T12:01:00Z');row=m['rows'][0]
  self.assertEqual(plan.assess(m,row,None,'J1')['status'],'missing')
  r=plan.assess(m,row,self.slot_capture(),'J1');self.assertEqual(r['status'],'indicative');self.assertFalse(r['validated'])
 def test_reschedule_and_staleness_excluded(self):
  m=plan.build(self.envelope(),'2030-01-01T12:01:00Z');e=self.slot_capture();data=json.loads(e['raw_utf8']);data[0]['commence_time']='2030-01-03T13:00:00Z';data[0]['bookmakers'][0]['markets'][0]['last_update']='2030-01-02T11:00:00Z';e['raw_utf8']=json.dumps(data);e['body_sha256']=pilot.digest(e['raw_utf8'].encode());r=plan.assess(m,m['rows'][0],e,'J1');self.assertIn('rescheduled',r['reasons']);self.assertIn('stale_or_future_price',r['reasons'])
 def test_archive_copy_permissions_and_tamper(self):
  with tempfile.TemporaryDirectory() as s,tempfile.TemporaryDirectory() as d:
   src,dst=Path(s),Path(d);pilot.store(src,self.envelope());r=archive.archive(src,dst);target=Path(r['snapshot_directory']);self.assertEqual(pilot.verify(target),1);self.assertFalse(r['durability_confirmed'])
   filename=json.loads((target/'journal.jsonl').read_text())['file'];(target/filename).write_text('{}')
   with self.assertRaises(ValueError):pilot.verify(target)
 def test_pair_requires_both_slots_and_remains_indicative(self):
  m=plan.build(self.envelope(),'2030-01-01T12:01:00Z');a=self.slot_capture();b=self.slot_capture()
  data=json.loads(b['raw_utf8']);data[0]['bookmakers'][0]['markets'][0]['last_update']='2030-01-03T10:59:30Z';data[0]['bookmakers'][0]['markets'][0]['outcomes'][0]['price']=2.4
  b['raw_utf8']=json.dumps(data);b['body_sha256']=pilot.digest(b['raw_utf8'].encode());b.update(requested_at='2030-01-03T11:00:00Z',received_at='2030-01-03T11:00:01Z')
  result=plan.compare_pair(m,m['rows'][0],a,b);self.assertTrue(result['candidate_changes']['A']['threshold_reached']);self.assertFalse(result['validated']);self.assertEqual(result['alerts'],[])
  self.assertEqual(plan.compare_pair(m,m['rows'][0],a,None)['candidate_changes'],{})
 def test_public_destination_rejected(self):
  with tempfile.TemporaryDirectory() as s:
   with self.assertRaises(ValueError):archive.archive(Path(s),ROOT)

if __name__=='__main__':unittest.main()
