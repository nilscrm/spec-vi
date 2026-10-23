"""Ordered-neighbor validation must reject equal sets in the wrong order."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ordered_evolution_evaluator',ROOT/'tools/physics_gate.py')
evaluator=importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluator)

class OrderedEvolutionEvaluatorTests(unittest.TestCase):
    def test_equal_membership_with_changed_order_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reference=root/'reference'/'side2';reference.mkdir(parents=True)
            lines=[]
            # Eight zero-valued records are a parser fixture, not physics coverage.
            for name in ['init']+['i0-'+s for s in evaluator.STAGES]:
                (reference/(name+'.tsv')).write_text(''.join(str(i)+' '+' '.join(['0']*30)+'\n' for i in range(8)))
                (reference/(name+'.meta')).write_text(' '.join(['0']*10)+'\n')
                lines+=['STAGE '+name]+['P '+str(i)+' '+' '.join(['0']*60) for i in range(8)]+['META '+' '.join(['0']*20)]
                if name.endswith('geometry'):
                    lines+=['N 0 1 2']+['N '+str(i) for i in range(1,8)]+['COUNT 2']
            (reference/'i0-neighbors.tsv').write_text('0 1 2\n'+''.join(str(i)+'\n' for i in range(1,8)))
            raw=root/'raw';raw.write_text('\n'.join(lines)+'\n')
            with patch.object(evaluator,'ref',reference.parent):
                self.assertEqual(len(evaluator.validate(raw,2,1,root/'valid')),10)
                raw.write_text('\n'.join('N 0 2 1' if l=='N 0 1 2' else l for l in lines)+'\n')
                with self.assertRaisesRegex(ValueError,'Neighbor order differs'):
                    evaluator.validate(raw,2,1,root/'invalid')
