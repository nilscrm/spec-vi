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


class NeighborDriverTests(unittest.TestCase):
    def source(self, candidate='tree', mode='correctness', api=None):
        import tempfile
        from neighbors_gate import driver
        points = [(7, 0., 0., 0.), (9, 1., 0., 0.)]
        # Repeated physical identity must still produce two distinct query rows.
        queries = [(7, 0., 0., 0., 2., 0.), (7, 1., 0., 0., .5, 0.)]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'driver.vi'
            driver(points, queries, path, mode, candidate=candidate, api=api)
            return path.read_text()

    def test_batch_builds_runtime_index_once_and_passes_all_queries(self):
        s = self.source('grid')
        self.assertIn('let points=black_box(', s)
        self.assertIn('let queries=black_box(', s)
        self.assertIn('(0,{id:7', s)
        self.assertIn('(1,{id:7', s)
        self.assertEqual(s.count('grid::build(points)'), 1)
        self.assertIn('grid::find_batch(index,queries)', s)
        self.assertLess(s.index('grid::build(points)'), s.index('grid::find_batch'))
        self.assertIn('emit(output,&io)', s)
        self.assertNotIn('grid::find(index,q)', s)

    def test_single_query_paths_remain_available(self):
        for candidate, module in [('tree', 'neighbors'), ('grid', 'grid')]:
            with self.subTest(candidate=candidate):
                s = self.source(candidate, api='single')
                self.assertIn(f'(i,{module}::find(index,q))', s)
                self.assertNotIn('::find_batch', s)

    def test_measurement_forces_each_neighbor_and_each_query(self):
        s = self.source('grid', 'candidate')
        self.assertIn('grid::build(points)', s)
        self.assertIn('grid::find_batch(index,queries)', s)
        self.assertIn('tree::map(output,fn* ((_,v)) {sum(v)})', s)
        self.assertIn('sum(l)+sum(r)', s)
        self.assertIn('totals(l)+totals(r)', s)
        self.assertIn('io.println("{totals(sums)}")', s)

    def test_serial_control_is_identical_for_both_candidates(self):
        self.assertEqual(self.source('tree', 'serial'), self.source('grid', 'serial'))
        self.assertNotIn('::build(', self.source('grid', 'serial'))

    def test_invalid_selection_fails_instead_of_silently_measuring_other_api(self):
        for candidate, mode, api in [('other','candidate',None), ('tree','correctness','batch'),
                                     ('grid','correctness','other'), ('grid','typo',None)]:
            with self.subTest(candidate=candidate, mode=mode, api=api), self.assertRaises(ValueError):
                self.source(candidate, mode, api)

    def test_repeated_queries_empty_rows_and_reordering(self):
        validate_rows('0 9\n1\n2 9\n', [[9], [], [9]])
        validate_rows('', [])
        for text in ['0 9\n2 9\n1\n', '0 9\n1\n', '0 9\n1\n2 9\n3\n']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_rows(text, [[9], [], [9]])

    def test_promoted_extra_fixtures_preserve_original_oracle(self):
        import json
        root = Path(__file__).resolve().parents[1]
        cases = json.loads((root/'evaluations/sph-exa/neighbors-extra.json').read_text())
        original = json.loads((root/'reports/neighbors/grid-clean/extra/fixtures.json').read_text())
        self.assertEqual(cases, original)
        self.assertEqual(len(cases), 16)
        for case in cases:
            with self.subTest(case=case['name']):
                self.assertEqual(case['expected'], [oracle(case['points'], q) for q in case['queries']])
