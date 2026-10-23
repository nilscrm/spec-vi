import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate import parse_stats

class RuntimeStatsModeTests(unittest.TestCase):
    normal='Interactions\n  Total 100\nMemory\n  Heap 200 B\n  Allocated 300 B\nPerformance\n  Time 4 ms\n'
    def test_normal_run_requires_work_memory_time_without_inventing_depth(self):
        self.assertEqual(parse_stats(self.normal,require_depth=False),dict(interactions=100,heap_bytes=200,allocated_bytes=300,runtime_ms=4))
        with self.assertRaisesRegex(ValueError,'Missing runtime metric: depth'):parse_stats(self.normal)
        with self.assertRaisesRegex(ValueError,'Missing runtime metric: runtime_ms'):parse_stats(self.normal.replace('  Time 4 ms',''),require_depth=False)
