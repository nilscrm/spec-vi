import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from neighbors_gate import oracle, validate_rows, synthetic


class NeighborOracleTests(unittest.TestCase):
    def test_strict_radius_and_self(self):
        _,points,queries=list(synthetic())[1]
        self.assertEqual(oracle(points,queries[0]),[2,4])
        self.assertEqual(oracle(points,queries[1]),[])

    def test_periodic_z_only(self):
        _,points,queries=list(synthetic())[2]
        self.assertEqual(oracle(points,queries[0]),[1])
        self.assertEqual(oracle(points,queries[2]),[])
        self.assertEqual(oracle(points,queries[3]),[])

    def test_missing_duplicate_extra_and_wrong_identity_fail(self):
        for text in ['0 1\n','0 1 1 2\n','0 1 2 3\n','1 1 2\n','']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_rows(text,[[1,2]])
        validate_rows('0 2 1\n',[[1,2]])
        validate_rows('0\n',[[]])
