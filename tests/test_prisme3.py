"""PRISME 3 integration tests using collected real records, not simulated markets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/prisme3'


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'experiments/prisme3' / (name+'.py'))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def candidates():
    with zipfile.ZipFile(OUT / 'calendar_candidates.zip') as z:
        return [json.loads(line) for line in z.read('calendar_candidates.jsonl').decode().splitlines()]


class CalendarFeasibility(unittest.TestCase):
    def test_grid_and_unique_primary_observations(self):
        audit = module('calendar_audit')
        plan = json.loads((ROOT / 'experiments/prisme3/sampling_plan.json').read_text())
        grid = audit.calendar(plan)
        self.assertEqual(len(grid), 78)
        self.assertTrue(all(b-a == 7*24*audit.HOUR for a,b in zip(grid,grid[1:])))
        rows = candidates()
        self.assertEqual(len(rows), len({r['id'] for r in rows}))
        for r in rows:
            self.assertEqual(r['t_ms'], audit.primary_time(r, grid))
            self.assertEqual(r['previous_t_ms'], r['t_ms']-24*audit.HOUR)
            self.assertGreaterEqual(r['previous_t_ms'], r['createdTime'])
            self.assertGreater(r['snapshot_closeTime'], r['t_ms'])
            if r['snapshot_resolutionTime'] is not None:
                self.assertGreater(r['snapshot_resolutionTime'], r['t_ms'])

    def test_time_selection_cannot_read_final_outcomes_or_closure(self):
        audit = module('calendar_audit')
        grid = audit.calendar(json.loads((ROOT / 'experiments/prisme3/sampling_plan.json').read_text()))
        for item in json.loads((OUT / 'manual_audit_markets.json').read_text()):
            raw = item['snapshot']
            # Remove future-state information from an actual record, never invent an outcome.
            redacted = {k:v for k,v in raw.items() if k not in ('resolution', 'resolutionTime', 'isResolved', 'closeTime', 'prob', 'p')}
            self.assertEqual(audit.primary_time(raw,grid), audit.primary_time(redacted,grid))
            if raw.get('resolutionTime'):
                self.assertEqual(audit.state_proxy(raw,raw['resolutionTime']), 'already_resolved_proxy')

    def test_flow_and_manual_ranking(self):
        report = json.loads((OUT / 'feasibility.json').read_text())
        c = report['counts']
        self.assertEqual(c['binary']+c['excluded_nonbinary'],c['all_markets'])
        self.assertEqual(c['with_primary_grid_date']+c['no_primary_grid_date'],c['binary'])
        self.assertEqual(sum(c.get(k,0) for k in ['already_resolved_proxy','closed_in_final_snapshot_proxy',
                                                'open_unresolved_proxy_only','resolution_chronology_unknown',
                                                'closure_chronology_unknown','not_created_or_missing_creation']),c['with_primary_grid_date'])
        for point in json.loads((OUT / 'calendar_flow.json').read_text()):
            self.assertEqual(sum(point['counts'].values()),c['binary'])
        ranked=sorted(candidates(),key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())[:20]
        manual=json.loads((OUT / 'manual_audit_markets.json').read_text())
        self.assertEqual([r['id'] for r in ranked],[i['observation']['id'] for i in manual])
        self.assertEqual(report['model_fits'],0)
        self.assertIsNone(report['statistical_result'])

    def test_cached_price_replay_and_cutoff_exclusion(self):
        probe=module('price_probe')
        report=json.loads((OUT / 'price_probe.json').read_text())
        with zipfile.ZipFile(OUT / 'price_probe_responses.zip') as z:
            for observation in report['observations']:
                for result in observation['snapshots'].values():
                    cutoff=result['cutoff_ms']
                    metadata=next(m for m in report['responses'] if
                                  'contractId='+observation['market_id'] in m['url'] and
                                  'beforeTime='+str(cutoff+1)+'&' in m['url'])
                    name=hashlib.sha256(metadata['url'].encode()).hexdigest()+'.json'
                    body=z.read(name)
                    self.assertEqual(hashlib.sha256(body).hexdigest(),metadata['sha256'])
                    bets=json.loads(body)
                    self.assertEqual(probe.asof_proxy(bets,cutoff),result)
                    if bets:
                        # All actual records must be excluded before the earliest recorded creation.
                        before_first=min(b['createdTime'] for b in bets)-1
                        early=probe.asof_proxy(bets,before_first)
                        self.assertNotIn('probability',early)
                    if 'executed_ms' in result:
                        self.assertLessEqual(result['executed_ms'],cutoff)
                    self.assertFalse(result['historical_quote_certified'])

    def test_event_links_are_partial_not_a_verified_partition(self):
        event=json.loads((OUT / 'event_grouping_audit.json').read_text())
        self.assertEqual(event['markets_in_repeated_title_groups'],sum(map(len,event['groups'].values())))
        self.assertEqual(event['verified_common_event_keys'],0)
        schedule=json.loads((OUT / 'external_schedule_check.json').read_text())
        self.assertEqual(len(schedule['records']),2)
        for row in schedule['records']:
            self.assertGreater(row['schedule_start_ms'],row['observation_t_ms'])
            self.assertFalse(row['exchange_open_at_t_verified'])

    def test_complete_frozen_archive_replay(self):
        archive=ROOT / 'data/prisme2/markets.zip'
        if not archive.exists():
            self.skipTest('Fetch the pinned archive to run the complete replay')
        with tempfile.TemporaryDirectory() as temp:
            run=subprocess.run([sys.executable,str(ROOT / 'experiments/prisme3/calendar_audit.py'),
                                '--archive',str(archive),'--output',temp],capture_output=True,text=True,timeout=120)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            actual=json.loads((Path(temp)/'feasibility.json').read_text())
            expected=json.loads((OUT/'feasibility.json').read_text())
            for key in ['counts','grid_dates','plan_sha256','script_sha256','archive_sha256','snapshot_fields']:
                self.assertEqual(actual[key],expected[key],key)
            for name in ['calendar_flow.json','manual_audit_markets.json','event_grouping_audit.json']:
                self.assertEqual((Path(temp)/name).read_bytes(),(OUT/name).read_bytes(),name)
            with zipfile.ZipFile(Path(temp)/'calendar_candidates.zip') as a,zipfile.ZipFile(OUT/'calendar_candidates.zip') as b:
                self.assertEqual(a.read('calendar_candidates.jsonl'),b.read('calendar_candidates.jsonl'))


if __name__=='__main__':
    unittest.main()
