import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate import compare, parse_stats, run
from runner import accept_gate, status


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.a = self.path/'a'
        self.b = self.path/'b'
        self.a.write_text('1 2\n3 4\n')
        self.b.write_text('1 2\n3 4\n')

    def test_exact_and_tolerance(self):
        self.assertTrue(compare(self.a, self.b, 0, 0)['passed'])
        self.b.write_text('1.001 2\n3 4\n')
        self.assertFalse(compare(self.a, self.b, 0, 0)['passed'])
        self.assertTrue(compare(self.a, self.b, .002, 0)['passed'])

    def test_malformed_outputs_fail(self):
        for text in ('', '1 2\n', '1 2\n3\n', 'nan 2\n3 4\n', 'inf 2\n3 4\n', 'oops'):
            with self.subTest(text=text):
                self.b.write_text(text)
                with self.assertRaises(ValueError):
                    compare(self.a, self.b, 0, 0)

    def test_wrong_shape_and_invalid_tolerance(self):
        with self.assertRaises(ValueError):
            compare(self.a, self.b, 0, 0, rows=3)
        for tol in (-1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                compare(self.a, self.b, tol, 0)

    def test_metrics_are_section_aware(self):
        text = 'Interactions\n  Total  1_234\nParallelism\n  Depth  50\nMemory\n  Heap  8_000 B\n  Allocated  16_000 B\n'
        self.assertEqual(parse_stats(text), {'interactions': 1234, 'depth': 50, 'heap_bytes': 8000, 'allocated_bytes': 16000})
        with self.assertRaises(ValueError):
            parse_stats(text.replace('  Depth  50\n', ''))
        with self.assertRaises(ValueError):
            parse_stats(text.replace('Depth  50', 'Depth  0'))

    def test_gate_rejects_missing_false_or_wrong_report(self):
        for data in ({}, {'passed': False, 'milestone': 'pilot'}, {'passed': True, 'milestone': 'other'}, {'passed': 'true', 'milestone': 'pilot'}):
            with self.assertRaises(ValueError):
                accept_gate(data, 'pilot')
        accept_gate({'passed': True, 'milestone': 'pilot'}, 'pilot')

    def test_timeout_is_failure_and_preserves_logs(self):
        with self.assertRaises(RuntimeError):
            run([sys.executable, '-c', 'import time; time.sleep(30)'], self.path, self.path/'sleep', timeout=.05)
        data = json.loads((self.path/'sleep.json').read_text())
        self.assertTrue(data['timed_out'])
        self.assertNotEqual(data['exit_code'], 0)

    def test_stale_running_status_is_not_completion(self):
        state = self.path/'status.json'
        state.write_text(json.dumps({'state': 'running', 'pid': 123, 'port_complete': False,
                                    'milestones': [{'state': 'running'}]}))
        with patch('runner.STATE', state), patch('runner.alive', return_value=False):
            result = status()
        self.assertEqual(result['state'], 'interrupted')
        self.assertFalse(result['port_complete'])
        self.assertEqual(result['milestones'][0]['state'], 'interrupted')

if __name__ == '__main__':
    unittest.main()
