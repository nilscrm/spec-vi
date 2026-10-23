"""Run unchanged pilot policy on the isolated sine-hoist candidate."""
import sys
sys.path.insert(0,'tools')
import pilot_gate
from evaluate import ROOT
pilot_gate.LIB=ROOT/'reports/pilot/sine-hoist/sph'
sys.argv=['pilot_gate.py','--output','reports/pilot/sine-hoist/evaluation']
sys.exit(pilot_gate.main())
