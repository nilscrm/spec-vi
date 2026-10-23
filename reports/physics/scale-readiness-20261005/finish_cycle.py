"""Run native output regression after stage regression finishes; avoid timed-run overlap."""
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
while not (HERE/'full-stages/result.json').exists() or not (HERE/'configuration/result.json').exists():
    time.sleep(1)
if not all(json.loads((HERE/p/'result.json').read_text())['passed'] for p in ['full-stages','configuration']):
    raise SystemExit('Prerequisite regression failed; preserve evidence and investigate.')
raise SystemExit(subprocess.call([sys.executable,str(ROOT/'tools/driver_gate.py'),'--output',str(HERE/'native-output'),'--reference',str(ROOT/'reports/physics/first-stages/reference')],cwd=ROOT))
