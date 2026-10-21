"""Checks based on the actually downloaded PRISME 2 records; no invented data."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/prisme2'
spec = importlib.util.spec_from_file_location('prisme2_audit', ROOT / 'experiments/prisme2/audit_archives.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ArchiveAudit(unittest.TestCase):
    def test_real_corpus_accounting_and_no_predictive_claim(self):
        report = json.loads((OUT / 'feasibility.json').read_text())
        c = report['counts']
        self.assertEqual(c['binary'] + c['excluded_nonbinary'], c['all_markets'])
        self.assertEqual(c['candidate_population'] + c['excluded_not_yes_no_resolved'] +
                         c['excluded_resolution_outside_common_coverage'], c['binary'])
        self.assertEqual(sum(c[k] for k in ('closeTime_equals_resolutionTime',
                                          'closeTime_before_resolutionTime',
                                          'closeTime_after_resolutionTime')), c['candidates_with_closeTime'])
        self.assertEqual(report['verified_ex_ante_deadlines'], 0)
        self.assertEqual(report['model_fits'], 0)
        self.assertEqual(report['permutations_executed'], 0)
        self.assertIsNone(report['statistical_result'])
        self.assertEqual(report['script_sha256'], audit.sha(Path(audit.__file__)))

    def test_actual_sample_parser_and_truncation_rejection(self):
        text = (OUT / 'manual_audit_markets.json').read_text()
        self.assertEqual(list(audit.records(io.StringIO(text))), json.loads(text))
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            list(audit.records(io.StringIO(text[:-3])))

    def test_trade_prefix_integrity_and_real_timestamps(self):
        report = json.loads((OUT / 'trade_probe.json').read_text())
        raw = (OUT / 'trade_archive_prefix.bin').read_bytes()
        self.assertEqual(len(raw), report['range_bytes'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), report['range_sha256'])
        rows = json.loads((OUT / 'trade_archive_sample.json').read_text())
        self.assertEqual(len(rows), report['records_examined'])
        for row in rows:
            self.assertIsInstance(row['createdTime'], (int, float))
            self.assertTrue(0 <= row['probAfter'] <= 1)

    def test_all_candidates_fail_closed_and_sample_is_prefixed(self):
        with zipfile.ZipFile(OUT / 'candidate_deadline_audit.zip') as z:
            rows = [json.loads(line) for line in z.read('candidate_deadline_audit.jsonl').decode().splitlines()]
        report = json.loads((OUT / 'feasibility.json').read_text())
        self.assertEqual(len(rows), report['counts']['candidate_population'])
        self.assertEqual(len({r['id'] for r in rows}), len(rows))
        self.assertTrue(all(r['resolutionTime'] < audit.CUTOFF for r in rows))
        self.assertTrue(all(r['predictive_eligible'] is False and r['event_key'] is None for r in rows))
        ranked = sorted(rows, key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest())[:12]
        self.assertEqual([r['id'] for r in ranked], report['manual_audit_sample'])


if __name__ == '__main__':
    unittest.main()
