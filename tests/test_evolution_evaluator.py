"""Structural failures must not pass full-state numerical checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('evolution_evaluator',ROOT/'reports/physics/evolution/evaluate.py')
evaluator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


class EvolutionEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        reference=self.root/'reference'/'side1';reference.mkdir(parents=True)
        self.names=['init']+['i0-'+s for s in evaluator.STAGES]
        self.lines=[]
        # A parser fixture, not a smaller physics acceptance workload.
        for name in self.names:
            (reference/(name+'.tsv')).write_text('0 '+' '.join(['0']*30)+'\n')
            (reference/(name+'.meta')).write_text(' '.join(['0']*10)+'\n')
            self.lines += ['STAGE '+name, 'P 0 '+' '.join(['0']*60), 'META '+' '.join(['0']*20)]
            if name.endswith('geometry'): self.lines += ['N 0','COUNT 0']
        (reference/'i0-neighbors.tsv').write_text('0\n')
        self.patch=patch.object(evaluator,'ref',reference.parent);self.patch.start();self.addCleanup(self.patch.stop)

    def validate(self,lines):
        raw=self.root/'raw';raw.write_text('\n'.join(lines)+'\n')
        return evaluator.validate(raw,1,1,self.root/'decoded')

    def test_all_stages_fields_and_scalars_are_checked(self):
        checks=self.validate(self.lines)
        self.assertEqual(len(checks),10)
        self.assertTrue(all(c['fields']['passed'] and c['scalars']['passed'] for c in checks))

    def test_missing_reordered_or_duplicate_stage_is_rejected(self):
        bad=[self.lines[:-3],self.lines+[self.lines[0]],self.lines[3:]+self.lines[:3]]
        for lines in bad:
            with self.subTest(lines=lines[:1]),self.assertRaises(ValueError):self.validate(lines)

    def test_missing_changed_or_nonfinite_field_is_rejected(self):
        for row in ['P 0 '+' '.join(['0']*59), 'P 1 '+' '.join(['0']*60),
                    'P 0 0 1072693248 '+' '.join(['0']*58),
                    'P 0 0 2146435072 '+' '.join(['0']*58)]:
            lines=self.lines.copy();lines[1]=row
            with self.subTest(row=row[:25]),self.assertRaises(ValueError):self.validate(lines)

    def test_missing_neighbors_and_wrong_total_are_rejected(self):
        for original,replacement in [('N 0','N 0 0'),('COUNT 0','COUNT 1')]:
            lines=[replacement if line==original else line for line in self.lines]
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):self.validate(lines)
