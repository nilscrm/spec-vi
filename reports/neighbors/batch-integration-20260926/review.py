"""Review integration invariants and evaluator evidence; no acceptance override."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from evaluate import sha, write_json
from neighbors_gate import driver, synthetic
out = Path(__file__).resolve().parent
run = ROOT/'reports/runs/20260926T152748Z-33131'
old = ROOT/'reports/neighbors/batch-integration/before'
spec = importlib.util.spec_from_file_location('original_neighbor_gate', old/'tools/neighbors_gate.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
assert (ROOT/'evaluations/sph-exa/neighbors-policy.json').read_bytes() == (out/'policy-before.json').read_bytes()
prior = json.loads((ROOT/'reports/runs/20260923T154358Z-6786/neighbors/provenance.json').read_text())
assert sha(ROOT/'evaluations/sph-exa/neighbors-policy.json') == prior['policy_sha256']
for name in ['neighbors.vi', 'tree.vi', 'pilot.vi']:
    assert sha(ROOT/'benchmarks/sph-exa/vine'/name) == prior['candidate']['files'][name], name
assert (ROOT/'benchmarks/sph-exa/vine/grid.vi').read_bytes() == (ROOT/'reports/neighbors/grid-clean/clean/sph/neighbors.vi').read_bytes()
with tempfile.TemporaryDirectory() as temp:
    a, b = Path(temp)/'a.vi', Path(temp)/'b.vi'
    for _, points, queries in synthetic():
        for mode in ('correctness', 'candidate', 'serial'):
            original.driver(points, queries, a, mode)
            driver(points, queries, b, mode)
            assert a.read_bytes() == b.read_bytes(), mode
            if mode == 'serial':
                driver(points, queries, b, mode, candidate='grid')
                assert a.read_bytes() == b.read_bytes()
bootstrap = json.loads((run/'bootstrap/result.json').read_text())
pilot = json.loads((run/'pilot/result.json').read_text())
neighbor = json.loads((run/'neighbors/result.json').read_text())
assert bootstrap['passed'] and pilot['passed']
assert neighbor['candidate'] == 'grid' and neighbor['api'] == 'batch'
checks = neighbor['correctness']
assert len(checks) == 72 and all(x['passed'] for x in checks)
assert len({(x['case'], x['candidate'], x['api']) for x in checks}) == 72
assert {x['case'] for x in checks} == {x['name'] for x in json.loads((run/'neighbors/fixtures.json').read_text())}
previous = json.loads((ROOT/'reports/neighbors/grid-clean/full.json').read_text())
for actual in neighbor['experiments']:
    expected = next(m for m in previous['metrics'] if m['case'] == 'scaling_'+str(actual['count']) and m['mode'] == 'depth')
    for key in ['depth','interactions','heap_bytes','allocated_bytes']:
        assert actual['candidate'][key] == expected[key], key
    assert actual['parallel_process_seconds'] > 0
assert neighbor['passed'] is False and neighbor['port_complete'] is False
assert [name for name, check in neighbor['budgets'].items() if not check['passed']] == ['depth_ratio']
write_json(out/'review.json', {
    'integration_verified': True, 'accepted_neighbor_milestone': False,
    'port_complete': False, 'runner': str(run.relative_to(ROOT)),
    'unit_tests': 24, 'membership_checks': len(checks),
    'policy_unchanged': True, 'legacy_driver_and_modules_unchanged': True,
    'grid_matches_clean_candidate': True, 'metrics_reproduced': True,
    'budgets': neighbor['budgets'],
    'result_sha256': {name: sha(run/name/'result.json') for name in ('bootstrap','pilot','neighbors')},
})
print((out/'review.json').read_text())
