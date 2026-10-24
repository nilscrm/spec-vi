#!/usr/bin/env python3
"""LBM correctness and measurement gate (782.lbm_r port).

Builds the pinned upstream kernel with the documented double-precision adaptation
(benchmarks/lbm/reference/double-precision.patch) and the reference driver, then for
every case runs the reference and the Vine application and compares:

  * cell flags (exact),
  * the full distribution state (19 binary64 values per cell) initially and after
    every time step, with fixed tolerances (atol/rtol below); bit-identical values are
    counted separately,
  * the final velocity field file (binary32, as LBM_storeVelocityField writes it).

With --measure it also runs the --checksum driver under `vine run --depth` and in
normal mode and records depth, interactions and heap per case. Depth, work and memory
are reported, never gated (AGENTS.md).
"""
import argparse
import hashlib
import json
import platform
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from evaluate import parse_stats, sha, tree_hash  # noqa: E402

BENCH = ROOT / 'benchmarks/lbm'
UPSTREAM = ROOT / 'upstream/lbm/src'
import os
LIB = Path(os.environ.get('LBM_LIB', BENCH / 'vine'))
APP = BENCH / 'app/lbm_app.vi'
WORK = ROOT / 'work/lbm'

# Fixed before judging any candidate. Values are O(0.01-1); the double-precision
# reference is reproduced expression by expression, so differences are expected to be 0.
ATOL = 1e-13
RTOL = 1e-12
VELOCITY_ATOL = 0.0  # binary32 output of identical binary64 values must be identical

# (name, sx, sy, sz, steps, channel, obstacle pattern)
CASES = {
    'ldc-8': (8, 8, 8, 4, False, 'none'),
    'ldc-12x10x16-sphere': (12, 10, 16, 3, False, 'sphere'),
    'channel-8x8x12-random': (8, 8, 12, 4, True, 'random'),
    'channel-12x12x16-sphere': (12, 12, 16, 3, True, 'sphere'),
    'ldc-16-random-10': (16, 16, 16, 10, False, 'random'),
    'channel-10x14x18-sphere-8': (10, 14, 18, 8, True, 'sphere'),
}
MEASURE = {
    # Depth-scaling series: cubes, lid-driven cavity without obstacles. Step counts 0, 1
    # and 2 separate construction from the per-step cost.
    **{f'ldc-{n}-s{s}': (n, n, n, s, False, 'none') for n in (8, 12, 16, 24, 32) for s in (0, 1, 2)},
    # Longer run: per-step depth over many steps.
    'ldc-16-s8': (16, 16, 16, 8, False, 'none'),
    # Channel flow with the sphere obstacle (in/outflow and vacated-entry handling).
    **{f'channel-sphere-{n}-s{s}': (n, n, n, s, True, 'sphere') for n in (8, 16) for s in (1, 2)},
}


def run(argv, cwd, timeout, log=None):
    argv = [str(a) for a in argv]
    start = time.time()
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    rec = {'argv': [str(a) for a in argv], 'cwd': str(cwd), 'returncode': p.returncode,
           'seconds': round(time.time() - start, 3)}
    if log is not None:
        log.mkdir(parents=True, exist_ok=True)
        (log / 'stdout.txt').write_text(p.stdout)
        (log / 'stderr.txt').write_text(p.stderr)
        rec['log'] = str(log)
    if p.returncode != 0:
        raise RuntimeError(f'command failed ({p.returncode}): {argv}\n{p.stderr[-2000:]}')
    return p, rec


def prepare_source():
    src = WORK / 'src'
    if src.exists():
        shutil.rmtree(src)
    src.mkdir(parents=True)
    for f in ('lbm.c', 'lbm.h', 'lbm_1d_array.h', 'config.h'):
        shutil.copy(UPSTREAM / f, src / f)
    subprocess.run(['patch', '-p1', '-s', '-i', str(BENCH / 'reference/double-precision.patch')],
                   cwd=src, check=True)
    return src


def build_reference(src, sx, sy, sz, cc):
    out = WORK / 'build' / f'{sx}x{sy}x{sz}'
    out.mkdir(parents=True, exist_ok=True)
    binary = out / 'lbm_ref'
    argv = [cc, '-std=c99', '-O2', '-ffp-contract=off', f'-DSIZE_X={sx}', f'-DSIZE_Y={sy}',
            f'-DSIZE_Z={sz}', f'-I{src}', str(src / 'lbm.c'), str(BENCH / 'reference/ref_main.c'),
            '-lm', '-o', str(binary)]
    subprocess.run(argv, check=True, capture_output=True)
    return binary, argv


def obstacle_file(pattern, sx, sy, sz, directory):
    if pattern == 'none':
        return None
    path = directory / f'{pattern}.of'
    subprocess.run([sys.executable, str(BENCH / 'reference/gen_obstacles.py'), pattern,
                    str(sx), str(sy), str(sz), str(path)], check=True)
    return path


def read_reference_dump(path, cells, steps):
    data = path.read_bytes()
    flags = list(struct.unpack(f'<{cells}I', data[:4 * cells]))
    per_state = cells * 19 * 8
    if len(data) != 4 * cells + (steps + 1) * per_state:
        raise ValueError('reference dump has unexpected size')
    states = []
    for k in range(steps + 1):
        off = 4 * cells + k * per_state
        states.append(struct.unpack(f'<{cells * 19}d', data[off:off + per_state]))
    return flags, states


def read_vine_dump(text, cells, steps):
    lines = text.splitlines()
    if not lines or not lines[0].startswith('F'):
        raise ValueError('Vine dump has no flag line')
    flags = [int(v) for v in lines[0].split()[1:]]
    states = []
    i = 1
    for _ in range(steps + 1):
        if lines[i] != 'S':
            raise ValueError(f'expected state header at line {i + 1}')
        values = []
        for line in lines[i + 1:i + 1 + cells]:
            words = [int(v) for v in line.split()]
            if len(words) != 38:
                raise ValueError('cell record must have 19 binary64 values')
            for j in range(0, 38, 2):
                values.append(struct.unpack('<d', struct.pack('<II', words[j], words[j + 1]))[0])
        states.append(values)
        i += 1 + cells
    if len(flags) != cells:
        raise ValueError('flag count mismatch')
    return flags, states


DIRS = ('C', 'N', 'S', 'E', 'W', 'T', 'B', 'NE', 'NW', 'SE', 'SW', 'NT', 'NB', 'ST', 'SB', 'ET', 'EB', 'WT', 'WB')


def compare_states(ref, cand, sx, sy):
    out = []
    for step, (a, b) in enumerate(zip(ref, cand)):
        identical = sum(x == y or (x != x and y != y) for x, y in zip(a, b))
        errors = [abs(x - y) for x, y in zip(a, b)]
        failures = [k for k, (x, y) in enumerate(zip(a, b)) if not abs(x - y) <= ATOL + RTOL * abs(x)]
        first = []
        for k in failures[:5]:
            cell, d = divmod(k, 19)
            x, rest = cell % sx, cell // sx
            first.append({'x': x, 'y': rest % sy, 'z': rest // sy, 'dir': DIRS[d],
                          'reference': a[k], 'candidate': b[k]})
        out.append({'step': step, 'values': len(a), 'bit_identical': identical,
                    'failures': len(failures), 'max_abs_error': max(errors), 'first_failures': first})
    return out


def vine_cmd(args, extra):
    return [sys.executable, str(ROOT / 'tools/vine_exec.py'), 'run', '--lib', f'lbm={LIB}',
            '--heap', f'{args.heap_gib}G', *extra, str(APP), '--']


def case_args(sx, sy, sz, steps, channel, obstacles):
    a = ['-x', str(sx), '-y', str(sy), '-z', str(sz), '-n', str(steps)]
    if channel:
        a.append('--channel')
    if obstacles is not None:
        a += ['--obstacles', str(obstacles)]
    return a


def check_case(name, spec, src, args, out):
    sx, sy, sz, steps, channel, pattern = spec
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    binary, build = build_reference(src, sx, sy, sz, args.cc)
    obst = obstacle_file(pattern, sx, sy, sz, d)
    _, ref_rec = run([binary, steps, d / 'reference.dat', 2, int(channel), obst or '-', '--dump',
                      d / 'reference.bin'], d, args.timeout, d / 'reference')
    p, vine_rec = run(vine_cmd(args, []) + case_args(sx, sy, sz, steps, channel, obst)
                      + ['--dump', '--result', str(d / 'candidate.dat')], d, args.timeout, d / 'candidate')
    cells = sx * sy * sz
    rflags, rstates = read_reference_dump(d / 'reference.bin', cells, steps)
    vflags, vstates = read_vine_dump(p.stdout, cells, steps)
    # The dumps are large; keep their digests, not the files.
    vine_rec['stdout_sha256'] = hashlib.sha256(p.stdout.encode()).hexdigest()
    ref_rec['dump_sha256'] = sha(d / 'reference.bin')
    (d / 'candidate' / 'stdout.txt').unlink()
    states = compare_states(rstates, vstates, sx, sy)
    rv = (d / 'reference.dat').read_bytes()
    cv = (d / 'candidate.dat').read_bytes()
    n = len(rv) // 4
    ru = struct.unpack(f'<{n}f', rv)
    cu = struct.unpack(f'<{len(cv) // 4}f', cv) if len(cv) == len(rv) else ()
    velocity = {'values': n, 'size_matches': len(cv) == len(rv),
                'bit_identical': rv == cv,
                'max_abs_error': max((abs(x - y) for x, y in zip(ru, cu)), default=None)}
    velocity['passed'] = velocity['size_matches'] and velocity['max_abs_error'] <= VELOCITY_ATOL
    passed = rflags == vflags and all(s['failures'] == 0 for s in states) and velocity['passed']
    (d / 'reference.bin').unlink()
    return {'case': name, 'size': [sx, sy, sz], 'steps': steps, 'channel': channel,
            'obstacles': pattern, 'passed': passed, 'flags_identical': rflags == vflags,
            'states': states, 'velocity': velocity,
            'commands': {'build': build, 'reference': ref_rec, 'candidate': vine_rec}}


DRIVER = """use #lbm::{{obstacles, sim}};

pub fn main(&io: &IO) {{
  let size = {{ sx: {sx}, sy: {sy}, sz: {sz} }};
  let state = sim::run(sim::new(size, {channel}, obstacles::{pattern}(size)), {steps});
  let N64(lo, hi) = sim::checksum(state.cells).to_bits();
  io.println("{{lo}} {{hi}}");
}}
"""


def braun_reduce(values):
    """Array::reduce_unordered order: even indices form the left subtree, odd the right."""
    if len(values) == 1:
        return values[0]
    return braun_reduce(values[0::2]) + braun_reduce(values[1::2])


def reference_checksum(state, sx, sy, sz):
    cell_sums = []
    for k in range(sx * sy * sz):
        acc = state[19 * k]
        for v in state[19 * k + 1:19 * k + 19]:
            acc += v
        cell_sums.append(acc)
    rows = [braun_reduce(cell_sums[r * sx:(r + 1) * sx]) for r in range(sy * sz)]
    planes = [braun_reduce(rows[z * sy:(z + 1) * sy]) for z in range(sz)]
    total = braun_reduce(planes)
    lo, hi = struct.unpack('<II', struct.pack('<d', total))
    return f'{lo} {hi}'


def measure_case(name, spec, src, args, out):
    """Depth/work/heap of a generated driver: construction, all steps and a balanced
    checksum consumer that forces every distribution value. The printed checksum is
    checked against the reference final state reduced in the same order."""
    sx, sy, sz, steps, channel, pattern = spec
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    driver = d / 'driver.vi'
    driver.write_text(DRIVER.format(sx=sx, sy=sy, sz=sz, steps=steps, channel=str(channel).lower(),
                                    pattern=pattern))
    binary, _ = build_reference(src, sx, sy, sz, args.cc)
    obst = obstacle_file(pattern, sx, sy, sz, d)
    run([binary, steps, d / 'reference.dat', 0, int(channel), obst or '-', '--dump', d / 'reference.bin'],
        d, args.timeout)
    _, states = read_reference_dump(d / 'reference.bin', sx * sy * sz, steps)
    expected = reference_checksum(states[-1], sx, sy, sz)
    (d / 'reference.bin').unlink()
    rec = {'case': name, 'size': [sx, sy, sz], 'cells': sx * sy * sz, 'steps': steps,
           'channel': channel, 'obstacles': pattern, 'driver_sha256': sha(driver),
           'expected_checksum_bits': expected}
    base = [sys.executable, str(ROOT / 'tools/vine_exec.py'), 'run', '--lib', f'lbm={LIB}',
            '--heap', f'{args.heap_gib}G']
    for mode, extra in (('depth_run', ['--depth']), ('normal_run', [])):
        try:
            p, r = run(base + extra + [driver], d, args.timeout, d / mode)
            rec[mode] = {**parse_stats(p.stderr, require_depth=bool(extra)), 'checksum_bits': p.stdout.strip(),
                         'checksum_matches': p.stdout.strip() == expected, 'command': r}
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            rec[mode] = {'error': str(e)[:500]}
    rec['checksums_match'] = all(rec[m].get('checksum_matches') for m in ('depth_run', 'normal_run'))
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--cases', nargs='*', help='subset of correctness cases')
    ap.add_argument('--measure', action='store_true', help='also run the depth/work/heap series')
    ap.add_argument('--measure-cases', nargs='*')
    ap.add_argument('--skip-check', action='store_true')
    ap.add_argument('--heap-gib', type=int, default=4)
    ap.add_argument('--timeout', type=int, default=1800)
    ap.add_argument('--cc', default='cc')
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = prepare_source()
    pin = json.loads((ROOT / 'evaluations/vine-pin.json').read_text())
    report = {
        'tool': 'tools/lbm_gate.py',
        'tolerances': {'atol': ATOL, 'rtol': RTOL, 'velocity_atol': VELOCITY_ATOL},
        'resources': {'heap_gib': args.heap_gib, 'timeout_s': args.timeout},
        'host': {'platform': platform.platform(), 'cc': subprocess.run([args.cc, '--version'], capture_output=True,
                                                                       text=True).stdout.splitlines()[0]},
        'toolchain': {'vine_commit': subprocess.run(['git', '-C', str(ROOT / 'work/vine'), 'rev-parse', 'HEAD'],
                                                    capture_output=True, text=True).stdout.strip(),
                      'vine_pin_commit': pin.get('commit'),
                      'vine_root_tree': tree_hash(ROOT / 'work/vine/root')['sha256'],
                      'vine_root_tree_matches_pin': tree_hash(ROOT / 'work/vine/root')['sha256'] == pin['source']['sha256'],
                      'vine_binary_sha256': sha(ROOT / 'work/bin/vine'),
                      'vine_build': 'cargo build -r --bin vine --bin ivm (binary hash differs from the pin because '
                                    'the build path is embedded; root tree checked instead, README)'},
        'sources': {'library': tree_hash(LIB)['sha256'], 'app': sha(APP), 'upstream': tree_hash(UPSTREAM)['sha256'],
                    'patch': sha(BENCH / 'reference/double-precision.patch'),
                    'reference_main': sha(BENCH / 'reference/ref_main.c')},
        'cases': [], 'measurements': [],
    }
    if not args.skip_check:
        for name in args.cases or CASES:
            res = check_case(name, CASES[name], src, args, out)
            report['cases'].append(res)
            print(f"{name}: {'PASS' if res['passed'] else 'FAIL'}", flush=True)
    if args.measure:
        for name in args.measure_cases or MEASURE:
            rec = measure_case(name, MEASURE[name], src, args, out)
            report['measurements'].append(rec)
            dr = rec['depth_run']
            print(f"{name}: depth={dr.get('depth')} work={dr.get('interactions')} heap={dr.get('heap_bytes')}"
                  f" checksum={'ok' if rec['checksums_match'] else 'MISMATCH'}", flush=True)
    report['passed'] = (all(c['passed'] for c in report['cases'])
                        and all(m['checksums_match'] for m in report['measurements']))
    (out / 'result.json').write_text(json.dumps(report, indent=1) + '\n')
    print('PASS' if report['passed'] else 'FAIL')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
