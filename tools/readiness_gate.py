#!/usr/bin/env python3
"""Configuration/aggregate-width checks; never evidence of large simulation feasibility."""
import argparse
import json
import sys
from pathlib import Path
from evaluate import ROOT, run, write_json, tree_hash, sha, parse_stats, add_resource_args, resources
from toolchain import verify

LIB = ROOT / 'benchmarks/sph-exa/vine'
APP = ROOT / 'benchmarks/sph-exa/app/square_patch.vi'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    add_resource_args(ap, 600)
    args = ap.parse_args()
    out = Path(args.output).resolve()
    out.mkdir(parents=True)
    report = dict(passed=False, port_complete=False, pin=verify(), library=tree_hash(LIB),
                  app_sha256=sha(APP), resources=resources(args), evaluator_sha256=sha(Path(__file__)), cases=[])
    command = [sys.executable, str(ROOT / 'tools/vine_exec.py'), 'run', '--heap', f'{args.heap_gib}G', '--lib', 'sph=' + str(LIB)]
    try:
        # No large tree allocation: production capacity helper and N64 carry/format path.
        values = [0, 1, 6607641, 6607642, 9261000, 1625**3, 2**32-1]
        src = out / 'counts.vi'
        src.write_text('use #sph::ordered; pub fn main(&io:&IO){\n' + ''.join(
            f'let v=ordered::row_capacity(black_box({n}));io.println("{{v}}");\n' for n in values) + '}\n')
        r = run(command + ['--depth', str(src)], ROOT, out/'counts', args.timeout)
        actual = list(map(int, Path(r['stdout']).read_text().split()))
        if actual != [n*650 for n in values]:
            raise ValueError('Aggregate capacity arithmetic mismatch')
        report['capacity'] = dict(values=values, actual=actual, stats=parse_stats(Path(r['stderr']).read_text()), process=r)
        for side, last, freq in [(12,0,1),(50,7,5),(100,0,1),(210,24,7),(1625,4294967294,-1)]:
            case = out / f'side{side}'
            case.mkdir()
            r = run(command + [str(APP), '--', '--describe', '-n', str(side), '-s', str(last), '-w', str(freq)], case, case/'run', args.timeout)
            lines = Path(r['stdout']).read_text().splitlines()
            got = dict(line.split(': ', 1) for line in lines if ': ' in line)
            expected = dict(particles=side**3, updates=last+1, write_frequency=max(freq,0),
                            neighbor_capacity_bound=side**3*650, particle_field_bytes_lower_bound=side**3*240)
            if any(int(got[k]) != v for k,v in expected.items()):
                raise ValueError('Preflight arithmetic mismatch')
            if (case/'constants.txt').exists() or list(case.glob('dump*.txt')):
                raise ValueError('Preflight created simulation output')
            report['cases'].append(dict(side=side, expected=expected, process=r, stats=parse_stats(Path(r['stderr']).read_text(), require_depth=False)))
        for name, arguments in [
            ('unknown', ['--bogus']), ('missing', ['-n']),
            ('side_low', ['--describe', '-n', '9']),
            ('side_high', ['--describe', '-n', '1626']),
            ('step_high', ['--describe', '-s', '4294967295']),
            ('frequency', ['-w', 'no']), ('negative_step', ['-s', '-1'])
        ]:
            case = out / name
            case.mkdir()
            r = run(command + [str(APP), '--', *arguments], case, case/'run', args.timeout)
            if 'ERROR:' not in Path(r['stdout']).read_text() or list(case.glob('*.txt')):
                raise ValueError('Invalid argument did not stop before simulation: ' + name)
            report['cases'].append(dict(rejection=name, process=r))
        if tree_hash(LIB) != report['library'] or sha(APP) != report['app_sha256']:
            raise ValueError('Source changed during checks')
        report['passed'] = True
    except Exception as exc:
        report['error'] = str(exc)
    write_json(out/'result.json', report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library','cases')}, indent=2))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
