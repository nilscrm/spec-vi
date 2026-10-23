"""Independently inspect evaluator evidence, immutable oracle, and current source hashes."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from evaluate import tree_hash, sha, write_json
from toolchain import verify
HERE=Path(__file__).resolve().parent
checks={}
reports={name:json.loads((HERE/name/'result.json').read_text()) for name in ['full-stages','configuration','native-output']}
lib=tree_hash(ROOT/'benchmarks/sph-exa/vine')
checks['all_evaluators_pass']=all(r['passed'] for r in reports.values())
checks['matching_current_library']=all(r['library']==lib for r in reports.values())
checks['current_driver']=all(reports[name][key]==sha(ROOT/'benchmarks/sph-exa/app/square_patch.vi') for name,key in [('configuration','app_sha256'),('native-output','driver_sha256')])
checks['fixed_stage_coverage']=[(c['side'],len(c['checks'])) for c in reports['full-stages']['cases']]==[(12,28),(16,28)]
checks['fixed_output_coverage']=[(c['side'],c['last_step'],c['frequency']) for c in reports['native-output']['cases']]==[(12,0,1),(16,2,2),(12,0,-1)]
checks['all_stage_fields_scalars']=all(s['fields']['passed'] and s['scalars']['passed'] for c in reports['full-stages']['cases'] for s in c['checks'])
checks['unchanged_upstream']=tree_hash(ROOT/'upstream/sph-exa')==json.loads((ROOT/'evaluations/upstream-files.json').read_text())
reference=ROOT/'reports/physics/first-stages/reference'
original=json.loads((reference/'result.json').read_text())
checks['unchanged_oracle']=all(sha(reference/name)==digest for name,digest in original['snapshots'].items())
checks['unchanged_policy']=reports['full-stages']['policy']==original['policy']==json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
checks['pinned_toolchain']=all(r['pin']==verify() for r in reports.values())
write_json(HERE/'review.json',dict(passed=all(checks.values()),checks=checks,port_complete=False,scope='Counter/configuration change and fixed-domain regressions only'))
print(json.dumps(checks,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
