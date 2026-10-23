"""Replicate tests.nix `program` snapshots for tests/programs without nix.

usage: snapcheck.py <vine-checkout> [name ...]   (no names = all programs)
"""
import re, subprocess, sys, tempfile
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
vine, ivm = repo/'target/release/vine', repo/'target/release/ivm'
progs = repo/'tests/programs'
wanted = set(sys.argv[2:])


def directive(src, key, default):
    text = (src/f'{src.name}.vi' if src.is_dir() else src).read_text()
    m = re.search(rf'^(?://|#) @{key} ?([^\n]*)$', text, re.M)
    return m.group(1) if m else default


bad = 0
for path in sorted(progs.iterdir()):
    name = path.stem if path.is_file() else path.name
    if wanted and name not in wanted:
        continue
    build = directive(path, 'build', '').split()
    run = directive(path, 'run', '').split()
    inp = repo/'tests/input'/directive(path, 'input', 'empty')
    ext = directive(path, 'output', 'txt')
    fail = directive(path, 'fail', None) is not None
    with tempfile.TemporaryDirectory() as d:
        iv = Path(d)/'compiled.iv'
        b = subprocess.run([vine, 'build', path, *build], stdout=open(iv, 'w'), stderr=subprocess.PIPE)
        if b.returncode:
            print('BUILD-FAIL', name, b.stderr.decode()[-300:]); bad += 1; continue
        r = subprocess.run([ivm, 'run', iv, '--no-perf', *run], stdin=open(inp),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if (r.returncode != 0) != fail:
            print('EXIT', name, r.returncode); bad += 1
        snap = repo/'tests/snaps/programs'/name
        for fname, got in ((f'output.{ext}', r.stdout), ('stats', r.stderr)):
            exp = snap/fname
            if not exp.exists():
                if got:
                    print('MISSING', name, fname); bad += 1
            elif exp.read_bytes() != got:
                print('DIFF', name, fname); bad += 1
print('checked; mismatches:', bad)
sys.exit(1 if bad else 0)
