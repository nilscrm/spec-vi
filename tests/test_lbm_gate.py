import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'benchmarks/lbm/reference'))

import gen_obstacles  # noqa: E402
import lbm_gate  # noqa: E402


class BraunReduceTest(unittest.TestCase):
    def test_order_matches_array_layout(self):
        # Array stores even indices in the left subtree and odd ones in the right.
        class S(str):
            def __add__(self, other):
                return S(f'({self}+{other})')
        values = [S(c) for c in 'abcde']
        self.assertEqual(lbm_gate.braun_reduce(values), '(((a+e)+c)+(b+d))')

    def test_single(self):
        self.assertEqual(lbm_gate.braun_reduce([2.5]), 2.5)


class DumpTest(unittest.TestCase):
    def test_vine_dump_roundtrip(self):
        cells, steps = 2, 1
        values = [0.1 * k for k in range(cells * 19 * (steps + 1))]
        lines = ['F 1 0']
        it = iter(values)
        for _ in range(steps + 1):
            lines.append('S')
            for _ in range(cells):
                words = []
                for _ in range(19):
                    lo, hi = struct.unpack('<II', struct.pack('<d', next(it)))
                    words += [str(lo), str(hi)]
                lines.append(' ' + ' '.join(words))
        flags, states = lbm_gate.read_vine_dump('\n'.join(lines) + '\n', cells, steps)
        self.assertEqual(flags, [1, 0])
        self.assertEqual(states[0] + states[1], values)

    def test_reference_dump_size_checked(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.bin'
            p.write_bytes(b'\0' * 10)
            with self.assertRaises(ValueError):
                lbm_gate.read_reference_dump(p, 1, 0)


class ObstacleTest(unittest.TestCase):
    def test_format_size(self):
        for pattern in ('none', 'sphere', 'random'):
            text = gen_obstacles.render(pattern, 5, 4, 3)
            self.assertEqual(len(text), 5 * 4 * 3 + (4 + 1) * 3)

    def test_random_is_reproducible(self):
        self.assertEqual(gen_obstacles.render('random', 6, 6, 6), gen_obstacles.render('random', 6, 6, 6))


class CompareTest(unittest.TestCase):
    def test_failure_location(self):
        a = [1.0] * (19 * 4)
        b = list(a)
        b[19 * 3 + 5] = 1.5  # cell 3 = (1, 1, 0) in a 2x2 plane, direction T
        res = lbm_gate.compare_states([a], [b], 2, 2)[0]
        self.assertEqual(res['failures'], 1)
        self.assertEqual(res['first_failures'][0], {'x': 1, 'y': 1, 'z': 0, 'dir': 'T',
                                                    'reference': 1.0, 'candidate': 1.5})


if __name__ == '__main__':
    unittest.main()
