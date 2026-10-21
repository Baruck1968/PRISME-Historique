"""Artificial unit fixtures only: never real sports observations or pilot results."""
import copy
import importlib.util
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'research/observatoire_v1/pilot.py'
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location('observatoire', MODULE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class ObservatoireTests(unittest.TestCase):
    def pair(self):
        base = dict(source='unit_fixture', event='fixture', sport='fixture', bookmaker='same', market='h2h',
                    rules_id='test_rules', anchor_type='scheduled_start_proxy', commence_time='2030-01-02T12:00:00Z',
                    requested_at='2030-01-01T12:00:00Z', received_at='2030-01-01T12:00:01Z',
                    last_update='2030-01-01T11:59:30Z', open_status='open', prices={'A':'2.00','B':'2.00'})
        other = copy.deepcopy(base)
        other.update(requested_at='2030-01-02T11:00:00Z', received_at='2030-01-02T11:00:01Z',
                     last_update='2030-01-02T10:59:30Z', prices={'A':'2.40','B':'1.60'})
        return base, other

    def test_exact_twenty_both_directions(self):
        a, b = self.pair()
        result = p.compare(a,b)
        self.assertTrue(result['valid'])
        self.assertEqual(result['alerts'], ['A','B'])
        self.assertFalse(p.variation('2','2.399999')['threshold_reached'])

    def test_reject_cross_book_rules_market_outcome_reschedule(self):
        for field, value in [('bookmaker','other'),('rules_id','other'),('market','other'),
                             ('event','other'),('commence_time','2030-01-02T13:00:00Z'),
                             ('prices',{'X':'2','B':'1.6'})]:
            a,b = self.pair(); b[field] = value
            with self.subTest(field=field):
                r=p.compare(a,b);self.assertFalse(r['valid']);self.assertEqual(r['alerts'],[])

    def test_unknown_suspended_stale_missing_future_and_delay(self):
        for field, value in [('open_status','unknown'),('open_status','suspended'),
                             ('last_update',None),('last_update','2030-01-02T10:00:00Z'),
                             ('last_update','2030-01-02T11:00:01Z'),
                             ('received_at','2030-01-02T11:10:00Z')]:
            a,b=self.pair();b[field]=value
            with self.subTest(field=field,value=value):
                self.assertFalse(p.compare(a,b)['valid'])

    def test_keep_nonalerts(self):
        a,b=self.pair();b['prices']={'A':'2.1','B':'1.9'}
        r=p.compare(a,b)
        self.assertTrue(r['valid']);self.assertEqual(r['alerts'],[])
        self.assertEqual(len(r['candidate_changes']),2)

    def test_duplicate_and_unknown_rules(self):
        a,b=self.pair()
        self.assertFalse(p.compare(a,a)['valid'])
        a['rules_id']=b['rules_id']=''
        self.assertIn('unverified_rules',p.compare(a,b)['exclusions'])

    def test_nan_and_nonodds(self):
        for v in ['NaN','Infinity','1','0','-2']:
            with self.assertRaises(ValueError):p.variation(v,'2')

    def test_chain_tamper_and_duplicates_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); first=p.store(root,{'unit_fixture':True});p.store(root,{'unit_fixture':True})
            self.assertEqual(p.verify(root),2)
            (root/first).write_text('{}')
            with self.assertRaises(ValueError):p.verify(root)

    def test_missing_key_no_network_no_storage(self):
        import argparse
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{},clear=True), patch.object(p,'build_opener') as net:
            with self.assertRaises(ValueError):p.capture(argparse.Namespace(sport='x',bookmaker='y',output=Path(d)/'unused'))
            net.assert_not_called();self.assertFalse((Path(d)/'unused').exists())

    def test_extract_no_open_inference_and_no_bookmaker_timestamp_fallback(self):
        event={'id':'fixture','sport_key':'fixture','commence_time':'2030-01-02T12:00:00Z','home_team':'A','away_team':'B',
               'bookmakers':[{'key':'same','last_update':'2030-01-01T12:00:00Z','markets':[{'key':'h2h','outcomes':[{'name':'A','price':2},{'name':'B','price':2}]}]}]}
        body=json.dumps([event]);envelope={'status':'captured','raw_utf8':body,'body_sha256':p.digest(body.encode()),
                                          'source':'unit_fixture','requested_at':'2030-01-01T12:00:00Z','received_at':'2030-01-01T12:00:01Z'}
        row=p.extract(envelope,'fixture','same','')
        self.assertEqual(row['open_status'],'unknown');self.assertIsNone(row['last_update'])
        event['bookmakers'][0]['markets'][0]['outcomes'].append({'name':'Draw','price':3})
        envelope['raw_utf8']=json.dumps([event]);envelope['body_sha256']=p.digest(envelope['raw_utf8'].encode())
        with self.assertRaises(ValueError):p.extract(envelope,'fixture','same','')

if __name__=='__main__':unittest.main()
