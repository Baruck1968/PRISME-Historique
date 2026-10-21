"""Documentary access safeguards and real artifact checks; no odds simulation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'research/sports_odds_audit'
spec=importlib.util.spec_from_file_location('sports_source_audit',AUDIT/'audit_sources.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SourceAudit(unittest.TestCase):
    def test_no_football_data_or_unapproved_host_request(self):
        for url in ['https://www.football-data.co.uk/downloadm.php',
                    'https://football-data.co.uk/mmz4281/2324/F1.csv',
                    'https://example.org/football-data-mirror.csv']:
            with self.assertRaises(PermissionError):module.guard(url)
        module.guard('https://the-odds-api.com/terms-and-conditions.html')

    def test_no_paid_or_credential_bearing_api_request(self):
        for url in ['https://api.the-odds-api.com/v4/historical/sports/soccer_france_ligue_one/odds',
                    'https://the-odds-api.com/?apiKey=FORBIDDEN_PLACEHOLDER',
                    'https://the-odds-api.com/?api_key=FORBIDDEN_PLACEHOLDER',
                    'https://user:password@the-odds-api.com/']:
            with self.assertRaises(PermissionError):module.guard(url)

    def test_real_results_file_matches_verified_source_hash(self):
        report=json.loads((AUDIT/'evidence/2026-10-21-verified/access_report.json').read_text())
        record=next(r for r in report['checks'] if r['id']=='results_france_2023_24')
        raw=(AUDIT/'evidence/2026-10-21-verified/openfootball_france_2023_24.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),record['sha256'])
        data=json.loads(raw)
        self.assertEqual(len(data['matches']),report['real_results_check']['matches'])
        self.assertEqual(sum('ft' in m.get('score',{}) for m in data['matches']),306)
        self.assertFalse(any('timezone' in m for m in data['matches']))

    def test_actual_access_log_has_no_football_data_call_or_paid_response(self):
        report=json.loads((AUDIT/'evidence/2026-10-21-verified/access_report.json').read_text())
        for record in report['checks']:
            if record['id']=='football_data':
                self.assertNotIn('http_status',record)
                self.assertTrue(record['status'].startswith('not_requested'))
            else:
                module.guard(record['url'])
                self.assertEqual(record['method'],'GET')
                self.assertEqual(record['status'],'retrieved')
        self.assertEqual(report['purchases'],0)
        self.assertEqual(report['subscriptions'],0)
        self.assertIsNone(report['statistical_results'])
        sample=json.loads((AUDIT/'evidence/public_sample_check.json').read_text())
        self.assertEqual(sample['status'],'inspected_provider_sample')
        self.assertFalse(sample['raw_publication'])
        self.assertFalse(sample['statistical_test_performed'])
        findings=json.loads((AUDIT/'findings.json').read_text())
        self.assertFalse(findings['historical_samples']['national_fr_historical_coverage_validated'])
        self.assertIsNone(findings['predictive_results'])
        self.assertIsNone(findings['economic_results'])


if __name__=='__main__':unittest.main()
