import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from stage_reference import load_fields, FIELDS, STAGES
from initial_physics_gate import check_checksum
import struct


class StageSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'state.tsv'

    def test_complete_state_and_identity_required(self):
        row = ' '.join(['1']*30)
        self.path.write_text('0 '+row+'\n1 '+row+'\n')
        self.assertEqual(load_fields(self.path,2), [[1.]*30]*2)
        for text in ['0 '+row+'\n', '1 '+row+'\n0 '+row+'\n',
                     '0 '+row+'\n0 '+row+'\n', '0 1\n1 1\n', '']:
            with self.subTest(text=text[:20]), self.assertRaises(ValueError):
                self.path.write_text(text)
                load_fields(self.path,2)

    def test_nonfinite_and_nonintegral_identity_rejected(self):
        for value in ('nan', 'inf', '-inf'):
            self.path.write_text('0 '+' '.join(['1']*29+[value])+'\n')
            with self.assertRaises(ValueError): load_fields(self.path,1)
        self.path.write_text('0.5 '+' '.join(['1']*30)+'\n')
        with self.assertRaises(ValueError): load_fields(self.path,1)

    def test_checksum_rejects_missing_state_and_nonfinite_result(self):
        policy={'atol':1e-9,'rtol':5e-12}
        for value in (30., 29., float('nan')):
            lo,hi=struct.unpack('<II',struct.pack('<d',value))
            self.path.write_text(f'{lo} {hi}\n')
            if value==30.: check_checksum(self.path,[[1.]*30],policy)
            else:
                with self.assertRaises(ValueError): check_checksum(self.path,[[1.]*30],policy)
