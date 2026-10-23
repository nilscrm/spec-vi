#!/usr/bin/env python3
"""Independent evaluation utilities. Never infer port completion from smoke checks."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hash(path):
    files = {str(p.relative_to(path)): sha(p) for p in sorted(Path(path).rglob('*'))
             if p.is_file() and '.git' not in p.relative_to(path).parts}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {'sha256': digest, 'files': files}


def run(command, cwd, prefix, timeout=120):
    """Capture exact argv and raw logs; timeout kills the whole child process group."""
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with prefix.with_suffix('.stdout').open('w') as out, prefix.with_suffix('.stderr').open('w') as err:
        owns_group = os.environ.get('SPEC_VI_CHILD_PROCESS_GROUP') != '1'
        child_env = dict(os.environ, SPEC_VI_CHILD_PROCESS_GROUP='1')
        process = subprocess.Popen(command, cwd=cwd, stdout=out, stderr=err,
                                   start_new_session=owns_group, env=child_env)
        timed_out = False
        usage = None
        try:
            deadline = time.monotonic() + timeout
            while True:
                waited, status, usage = os.wait4(process.pid, os.WNOHANG)
                if waited:
                    code = os.waitstatus_to_exitcode(status)
                    process.returncode = code
                    break
                usage = None
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.02)
        except subprocess.TimeoutExpired:
            timed_out = True
            if owns_group:
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            code = process.wait()
        except BaseException:
            try:
                if owns_group:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.wait()
            raise
    result = {'argv': list(map(str, command)), 'cwd': str(cwd), 'exit_code': code,
              'timed_out': timed_out, 'peak_rss_bytes': (int(usage.ru_maxrss) * (1 if sys.platform == 'darwin' else 1024)) if usage else None, 'wall_seconds': time.monotonic() - started,
              'stdout': str(prefix.with_suffix('.stdout')), 'stderr': str(prefix.with_suffix('.stderr'))}
    write_json(prefix.with_suffix('.json'), result)
    if code != 0 or timed_out:
        raise RuntimeError(f'Command failed: {command}; see {prefix}.stderr')
    return result


def compare(reference, candidate, atol, rtol, rows=None, columns=None):
    """Compare numeric tables with exact shape and finite-value validation."""
    if not math.isfinite(atol) or not math.isfinite(rtol) or min(atol, rtol) < 0:
        raise ValueError('Tolerances must be finite and nonnegative')
    def load(path):
        lines = Path(path).read_text().splitlines()
        data = [[float(x) for x in line.split()] for line in lines if line.strip()]
        if not data or not data[0] or any(len(row) != len(data[0]) for row in data):
            raise ValueError(f'Empty or ragged numeric table: {path}')
        if any(not math.isfinite(x) for row in data for x in row):
            raise ValueError(f'Nonfinite numeric value: {path}')
        return data
    a, b = load(reference), load(candidate)
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError('Output shape mismatch')
    if rows is not None and len(a) != rows:
        raise ValueError('Unexpected row count')
    if columns is not None and len(a[0]) != columns:
        raise ValueError('Unexpected column count')
    errors = [abs(x-y) for ra, rb in zip(a, b) for x, y in zip(ra, rb)]
    failures = sum(abs(x-y) > atol + rtol*abs(x) for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    return {'passed': failures == 0, 'failures': failures, 'rows': len(a), 'columns': len(a[0]),
            'max_absolute_error': max(errors), 'atol': atol, 'rtol': rtol}


def parse_stats(text, require_depth=True):
    sections = {}
    section = None
    for line in text.splitlines():
        s = line.strip()
        if s in ('Interactions', 'Parallelism', 'Memory', 'Performance', 'Workload'):
            section = s
            continue
        m = re.fullmatch(r'\s*(.+?)\s+([\d_]+)(?:\s+(\S+))?\s*', line)
        if section and m:
            sections[(section, m[1].strip())] = int(m[2].replace('_', ''))
    fields = {'depth': ('Parallelism', 'Depth'), 'interactions': ('Interactions', 'Total'),
              'heap_bytes': ('Memory', 'Heap'), 'allocated_bytes': ('Memory', 'Allocated')}
    if not require_depth:
        del fields['depth']
        fields['runtime_ms'] = ('Performance', 'Time')
    result = {}
    for key, location in fields.items():
        if location not in sections:
            raise ValueError(f'Missing runtime metric: {key}')
        result[key] = sections[location]
    if result['interactions'] <= 0 or (require_depth and result['depth'] <= 0):
        raise ValueError('Depth and work must be positive')
    return result


def bootstrap(output):
    """Validate infrastructure and upstream smoke cases, NOT a Vine SPH port."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT/'benchmarks/sph-exa/source.json').read_text())
    pinned = json.loads((ROOT/'evaluations/upstream-files.json').read_text())
    actual = tree_hash(ROOT/'upstream/sph-exa')
    if actual != pinned:
        raise RuntimeError('Upstream source changed relative to the pinned file manifest')
    vine = Path(manifest['vine_checkout'])
    binary = Path(os.environ.get('VINE_BIN', str(vine/'target/release/vine')))
    records = []
    records.append(run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT, output/'tests'))
    for label, argv in [('vine-head', ['git', '-C', str(vine), 'rev-parse', 'HEAD']),
                        ('vine-diff', ['git', '-C', str(vine), 'diff', 'HEAD', '--binary']),
                        ('vine-status', ['git', '-C', str(vine), 'status', '--porcelain']),
                        ('compiler-version', [os.environ.get('CXX', 'c++'), '--version'])]:
        records.append(run(argv, ROOT, output/label))
    # A binary hash identifies what actually ran; the source hash does not prove it was rebuilt.
    write_json(output/'provenance.json', {'upstream_commit': manifest['commit'],
        'upstream_tree': actual['sha256'], 'vine_binary': str(binary), 'vine_binary_sha256': sha(binary),
        'vine_source': tree_hash(vine/'root'),
        'binary_matches_current_checkout': 'not established; existing binary used for infrastructure probe'})
    records.append(run(['make', 'sph-exa-build'], ROOT, output/'build'))
    cases = []
    for side in (12, 16):
        cwd = output/f'reference-n{side}'
        cwd.mkdir()
        records.append(run([str(ROOT/'work/build/sph-exa'), '-n', str(side), '-s', '1', '-w', '1'], cwd, cwd/'run'))
        for step in (0, 1):
            table = cwd/f'dump{step}.txt'
            shape = compare(table, table, 0, 0, rows=side**3, columns=16)
            cases.append({'side': side, 'iteration_label': step, 'shape_and_finiteness': shape,
                          'file': str(table), 'sha256': sha(table)})
    # Force every term through a sum. This is only a diagnostic of the stats pipeline.
    probe = output/'probe.vi'
    probe.write_text('use #root::data::Array;\npub fn main(&io: &IO) {\n'
        '  let values = Array::new(64, 1);\n'
        '  let total = values.reduce_unordered(fn* (a: N32, b: N32) { a + b });\n'
        '  if total is Some(n) { io.println("{n}"); }\n}\n')
    depth = run([str(binary), 'run', '--depth', str(probe)], ROOT, output/'probe-depth')
    records.append(depth)
    if Path(depth['stdout']).read_text().strip() != '64':
        raise RuntimeError('Depth probe produced unexpected output')
    metrics = parse_stats(Path(depth['stderr']).read_text())
    timed = run([str(binary), 'run', '--workers', '2', str(probe)], ROOT, output/'probe-workers')
    records.append(timed)
    if Path(timed['stdout']).read_text().strip() != '64':
        raise RuntimeError('Worker probe produced unexpected output')
    result = {'schema_version': 1, 'milestone': 'bootstrap', 'passed': True, 'port_complete': False,
              'reference_cases': cases, 'depth_probe': metrics, 'commands': records,
              'limitations': ['Reference dumps have upstream default precision; numerical oracle instrumentation is pending.',
                'The Vine probe is not SPH-EXA and does not establish port performance.',
                'No process peak-memory measurement is implemented yet.',
                'Existing Vine binary build provenance is not established.']}
    write_json(output/'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    boot = sub.add_parser('bootstrap')
    boot.add_argument('--output', required=True)
    comp = sub.add_parser('compare')
    comp.add_argument('reference')
    comp.add_argument('candidate')
    comp.add_argument('--atol', type=float, required=True)
    comp.add_argument('--rtol', type=float, required=True)
    comp.add_argument('--rows', type=int)
    comp.add_argument('--columns', type=int)
    args = parser.parse_args()
    try:
        result = bootstrap(args.output) if args.action == 'bootstrap' else compare(
            args.reference, args.candidate, args.atol, args.rtol, args.rows, args.columns)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['passed'] else 1
    except Exception as exc:
        print(f'Evaluation failed: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
