import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate import add_resource_args, resources, metrics, compare_baseline
import neighbors_gate
import pilot_gate
from stage_reference import verify_reference, ORACLE_KEYS
from evaluate import ROOT, sha

def stats(depth, work, heap=10):
    return {'depth': depth, 'interactions': work, 'heap_bytes': heap, 'allocated_bytes': 2*heap}


class ResourceArgumentTests(unittest.TestCase):
    def parse(self, *argv):
        ap = argparse.ArgumentParser()
        add_resource_args(ap, 180)
        return ap.parse_args(argv)

    def test_defaults_are_recorded(self):
        self.assertEqual(resources(self.parse()), {'heap_gib': 2, 'heap_limit_bytes': 2*1024**3, 'command_timeout_seconds': 180})

    def test_any_positive_profile_is_accepted(self):
        self.assertEqual(resources(self.parse('--heap-gib', '48', '--timeout', '7200'))['heap_limit_bytes'], 48*1024**3)

    def test_nonpositive_rejected(self):
        for argv in (['--heap-gib', '0'], ['--timeout', '-1'], ['--heap-gib', 'x']):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.parse(*argv)


class ReportedScalingTests(unittest.TestCase):
    def test_neighbor_scaling_reports_ratios_that_used_to_fail(self):
        # Ratios beyond the retired budgets (0.7, 1.5, 10, 3) are reported, never raised.
        first = {'count': 64, 'candidate': stats(100, 1000), 'serial': stats(50, 500)}
        last = {'count': 256, 'candidate': stats(400, 20000), 'serial': stats(200, 2000)}
        self.assertEqual(neighbors_gate.scaling(first, last), {
            'counts': [64, 256], 'depth_vs_serial': 2.0, 'work_vs_serial': 10.0,
            'depth_growth': 4.0, 'work_growth': 20.0})

    def test_pilot_scaling(self):
        values = [{'count': 1, 'balanced': stats(10, 100), 'serial': stats(10, 100)},
                  {'count': 32, 'balanced': stats(30, 330), 'serial': stats(60, 300)}]
        self.assertEqual(pilot_gate.scaling(values), {'counts': [1, 32], 'depth_vs_serial': 0.5,
                                                      'work_vs_serial': 1.1, 'depth_growth': 3.0})


class BaselineComparisonTests(unittest.TestCase):
    def test_metrics_flatten_nested_sections(self):
        found = metrics([{'count': 64, 'candidate': stats(5, 6), 'peak_rss_bytes': 9}])
        self.assertEqual(found, {'0/candidate/depth': 5, '0/candidate/interactions': 6,
                                 '0/candidate/heap_bytes': 10, '0/candidate/allocated_bytes': 20})

    def test_ratios_and_toolchain_identity(self):
        tool = {'commit': 'a', 'binary_sha256': 'b'}
        current = {'toolchain': tool, 'experiments': [{'candidate': stats(50, 300)}]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'result.json'
            path.write_text(json.dumps({'toolchain': tool, 'experiments': [{'candidate': stats(100, 200)}]}))
            result = compare_baseline(current, path, ['experiments'])
            self.assertTrue(result['same_toolchain'])
            self.assertEqual(result['ratios']['experiments/0/candidate/depth'], 0.5)
            self.assertEqual(result['ratios']['experiments/0/candidate/interactions'], 1.5)
            # Historical reports have no toolchain identity: never claimed comparable.
            path.write_text(json.dumps({'experiments': [{'candidate': stats(100, 200)}]}))
            self.assertFalse(compare_baseline(current, path, ['experiments'])['same_toolchain'])


class ReferenceProvenanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.ref = Path(temp.name)
        (self.ref/'side12').mkdir()
        (self.ref/'side12/init.tsv').write_text('0 1\n')
        self.policy = json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
        # Shaped like the committed oracle, which still records the retired resource fields.
        original = dict(self.policy, heap_limit_bytes=2*1024**3, command_timeout_seconds=600)
        (self.ref/'result.json').write_text(json.dumps({
            'reference_verified': True, 'policy': original,
            'source_sha256': sha(ROOT/'benchmarks/sph-exa/reference/stages.cpp'),
            'snapshots': {'side12/init.tsv': sha(self.ref/'side12/init.tsv')}}))

    def test_resource_fields_are_not_part_of_the_oracle(self):
        self.assertNotIn('heap_limit_bytes', self.policy)
        self.assertNotIn('command_timeout_seconds', self.policy)
        verify_reference(self.ref, self.policy)

    def test_oracle_fields_still_fail_closed(self):
        self.assertEqual(set(ORACLE_KEYS), {'sides', 'updates', 'atol', 'rtol'})
        for key, value in [('atol', 1e-6), ('rtol', 1e-9), ('updates', 1), ('sides', [12])]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'provenance'):
                verify_reference(self.ref, dict(self.policy, **{key: value}))

    def test_changed_snapshot_fails(self):
        (self.ref/'side12/init.tsv').write_text('0 2\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            verify_reference(self.ref, self.policy)


class PolicyTests(unittest.TestCase):
    def test_no_performance_budgets_remain_in_policies(self):
        for path in (ROOT/'evaluations/sph-exa').glob('*-policy.json'):
            policy = json.loads(path.read_text())
            with self.subTest(policy=path.name):
                self.assertFalse([k for k in policy if k.startswith('max_') or k in ('heap_limit_bytes', 'command_timeout_seconds')])

if __name__ == '__main__':
    unittest.main()
