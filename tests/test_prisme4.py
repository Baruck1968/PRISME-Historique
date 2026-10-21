"""Real-capture replay/integrity tests; no fabricated market observations."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta
import hashlib
import email.utils
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT/'results/prisme4/store'
spec = importlib.util.spec_from_file_location('prisme4_collector',ROOT/'experiments/prisme4/collector.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class ProspectiveCapture(unittest.TestCase):
    def test_actual_capture_offline_replay_and_chain(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('Network forbidden in replay')):
            state=collector.verify_store(STORE)
            self.assertGreaterEqual(len(state['runs']),1)
            self.assertEqual(len(state['cohort_ids']),30)
            for relative in state['runs']:
                rows=collector.replay(STORE/relative)
                self.assertEqual([r['market_id'] for r in rows],state['cohort_ids'])
                self.assertTrue(all(r['predictive_eligible'] is False for r in rows))

    def test_real_request_utc_and_read_only_methods(self):
        state=json.loads((STORE/'state.json').read_text())
        for relative in state['runs']:
            m=json.loads((STORE/relative/'manifest.json').read_text())
            self.assertGreaterEqual(len(m['requests']),60)
            for request in m['requests']:
                self.assertEqual(request['method'],'GET')
                self.assertTrue(request['url'].startswith('https://api.manifold.markets/v0/'))
                start=datetime.fromisoformat(request['request_started_utc'])
                end=datetime.fromisoformat(request['received_utc'])
                self.assertEqual(end.utcoffset(),timedelta(0))
                self.assertGreaterEqual(end,start)
                if request['headers'].get('date'):
                    server=email.utils.parsedate_to_datetime(request['headers']['date'])
                    self.assertTrue(-2 <= (end-server).total_seconds() <= 120)

    def test_tampered_capture_is_rejected(self):
        state=json.loads((STORE/'state.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)/'copy'
            shutil.copytree(STORE/state['runs'][0],run)
            with (run/'observations.json').open('ab') as f:f.write(b' ')
            with self.assertRaisesRegex(RuntimeError,'Integrity mismatch'):
                collector.verify_run(run)

    def test_tampered_chain_tip_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            copy=Path(temp)/'store';shutil.copytree(STORE,copy)
            state=json.loads((copy/'state.json').read_text());state['previous_manifest_sha256']=''
            (copy/'state.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(RuntimeError,'chain tip'):
                collector.verify_store(copy)

    def test_expiry_prevents_network_and_new_capture(self):
        # Advance only the clock derived from real expiry; no synthetic market rows.
        with tempfile.TemporaryDirectory() as temp:
            copy=Path(temp)/'store';shutil.copytree(STORE,copy)
            state=json.loads((copy/'state.json').read_text())
            clock=datetime.fromisoformat(state['expires_utc'])+timedelta(seconds=1)
            before=sorted(str(p.relative_to(copy)) for p in copy.rglob('*'))
            with patch.object(collector,'now',return_value=clock),patch('urllib.request.urlopen',side_effect=AssertionError('Expired capture requested network')),redirect_stdout(io.StringIO()):
                self.assertEqual(collector.capture(copy,'daily'),0)
            self.assertEqual(before,sorted(str(p.relative_to(copy)) for p in copy.rglob('*')))

    def test_completed_daily_slot_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            copy=Path(temp)/'store';shutil.copytree(STORE,copy)
            state=json.loads((copy/'state.json').read_text())
            clock=datetime.fromisoformat(state['first_successful_capture_utc'])+timedelta(minutes=1)
            state['completed_daily_slots']=[clock.date().isoformat()]
            (copy/'state.json').write_text(json.dumps(state));before=(copy/'state.json').read_bytes()
            with patch.object(collector,'now',return_value=clock),patch('urllib.request.urlopen',side_effect=AssertionError('Duplicate daily slot requested network')),redirect_stdout(io.StringIO()):
                self.assertEqual(collector.capture(copy,'daily'),0)
            self.assertEqual(before,(copy/'state.json').read_bytes())

    def test_failed_attempt_is_preserved_and_not_counted_as_success(self):
        state=json.loads((STORE/'state.json').read_text())
        failed=[]
        for path in (STORE/'runs').glob('*/manifest.json'):
            m=collector.verify_run(path.parent)
            if m['status']=='failed':
                failed.append(m)
                self.assertNotIn(str(path.parent.relative_to(STORE)),state['runs'])
        self.assertGreaterEqual(len(failed),1)
        self.assertTrue(all(m['error'] is not None for m in failed))

    def test_fixed_rules_and_expiry_duration(self):
        state=json.loads((STORE/'state.json').read_text())
        plan=(ROOT/'experiments/prisme4/collection_plan.json').read_bytes()
        self.assertEqual(hashlib.sha256(plan).hexdigest(),state['plan_sha256'])
        self.assertEqual(datetime.fromisoformat(state['expires_utc'])-datetime.fromisoformat(state['first_successful_capture_utc']),timedelta(days=56))
        ids=state['cohort_ids']
        self.assertEqual(len(ids),len(set(ids)))


if __name__=='__main__':
    unittest.main()
