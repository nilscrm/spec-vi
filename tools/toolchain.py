"""Fail closed if the accepted Vine binary or source changes."""
import json
import subprocess
from evaluate import ROOT, sha, tree_hash


def source_hash(checkout):
    names = subprocess.check_output(['git', '-C', str(checkout), 'ls-files', '-z']).decode().split('\0')
    # Include staged support files, ignore build caches and Git metadata.
    return {name: sha(checkout/name) for name in names if name and (checkout/name).is_file()}


def verify():
    pin = json.loads((ROOT/'evaluations/vine-pin.json').read_text())
    checkout = ROOT/pin['checkout']
    if sha(ROOT/'work/bin/vine') != pin['binary_sha256']:
        raise RuntimeError('Pinned Vine binary changed; rebuild/review before acceptance')
    if tree_hash(checkout/'root') != pin['source'] or source_hash(checkout) != pin['checkout_files']:
        raise RuntimeError('Pinned Vine source changed; rebuild/review before acceptance')
    return pin
