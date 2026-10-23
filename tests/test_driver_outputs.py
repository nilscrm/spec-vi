import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from driver_gate import expected_dump

class DriverOutputTests(unittest.TestCase):
    def test_original_column_order_and_radial_quantities(self):
        p=[0.0]*30
        p[0:3]=[3.0,4.0,0.0]
        p[6:9]=[2.0,1.0,0.0]
        p[9]=11.0;p[11]=12.0;p[12]=13.0;p[14]=14.0;p[16]=16.0
        p[17:20]=[17.0,18.0,19.0]
        self.assertEqual(expected_dump([p]),[[3.0,4.0,0.0,2.0,1.0,0.0,14.0,11.0,12.0,13.0,16.0,17.0,18.0,19.0,5.0,2.0]])
