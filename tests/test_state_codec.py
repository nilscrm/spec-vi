import math
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from state_codec import decode_values


class StateCodecTests(unittest.TestCase):
    def test_finite_binary64_values_round_trip_without_rounding(self):
        values=[0.,-0.,1.,-1.,math.pi,5e-324,-5e-324,float.fromhex('0x1.fffffffffffffp+1023')]
        words=[]
        for x in values: words.extend(map(str,struct.unpack('<II',struct.pack('<d',x))))
        actual=decode_values(words,len(values))
        self.assertEqual([struct.pack('<d',x) for x in actual],[struct.pack('<d',x) for x in values])

    def test_rejects_partial_extra_out_of_range_and_nonfinite_fields(self):
        for words,count in [(['0'],1),(['0','0','0'],1),(['-1','0'],1),
                            ([str(2**32),'0'],1),(['0',str(0x7ff00000)],1),
                            (['1',str(0x7ff80000)],1),(['word','0'],1)]:
            with self.subTest(words=words),self.assertRaises(ValueError):decode_values(words,count)
