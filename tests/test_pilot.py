"""Integration checks using only the archived, actually collected public data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PilotReplay(unittest.TestCase):
    def test_archived_real_data_replay(self):
        manifest = json.loads((ROOT / 'data/snapshot.json').read_text())
        archive = ROOT / manifest['file']
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), manifest['sha256'])
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / 'cache'
            output = Path(temp) / 'output'
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(len(z.namelist()), manifest['files'])
                self.assertTrue(all(Path(n).name == n for n in z.namelist()))
                z.extractall(cache)
            run = subprocess.run([sys.executable, str(ROOT / 'experiments/momentum.py'),
                                  '--offline', '--cache', str(cache), '--output', str(output)],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            expected = json.loads((ROOT / 'results/pilot/report.json').read_text())
            actual = json.loads((output / 'report.json').read_text())
            for field in ['status', 'exclusions', 'directions', 'n_eligible', 'analysis', 'responses', 'script_sha256']:
                self.assertEqual(actual[field], expected[field], field)
            rows = json.loads((output / 'observations.json').read_text())
            self.assertEqual(rows, json.loads((ROOT / 'results/pilot/observations.json').read_text()))
            self.assertEqual(len(rows), actual['n_eligible'])
            self.assertEqual(len({r['id'] for r in rows}), len(rows))
            self.assertEqual(sum(actual['exclusions'].values()) + len(rows), actual['unique_markets'])
            for row in rows:
                self.assertEqual(row['final_cutoff'] - row['previous_cutoff'], 86_400_000)
                self.assertLess(row['final_cutoff'], row['resolution_time'])
                for prefix in ['final', 'previous']:
                    age = row[prefix + '_cutoff'] - row[prefix + '_trade_time']
                    self.assertTrue(0 <= age <= 86_400_000)
                    self.assertTrue(0 <= row['p_' + prefix] <= 1)
                self.assertIn(row['outcome'], (0, 1))


if __name__ == '__main__':
    unittest.main()
