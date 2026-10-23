import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import runner


class RunnerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'evaluations').mkdir()
        self.workflow = self.root/'evaluations/workflow.json'
        for name, value in [('ROOT', self.root), ('STATE', self.root/'reports/status.json'),
                            ('LOCK', self.root/'work/lock'), ('WORKFLOW', self.workflow)]:
            patcher = patch.object(runner, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.ids = ['bootstrap', 'pilot', 'neighbors', 'physics', 'integration', 'workloads']

    def configure(self, gate_ids=(), passed=True):
        tasks = []
        for name in self.ids:
            task = {'id': name, 'title': name, 'gate': None, 'next_action': 'Check required.'}
            if name in gate_ids:
                source = "import json,pathlib,sys; pathlib.Path(sys.argv[1],'result.json').write_text(json.dumps(" + repr({'passed': passed, 'milestone': name}) + '))'
                task['gate'] = ['{python}', '-c', source, '{output}']
            tasks.append(task)
        self.workflow.write_text(json.dumps({'milestones': tasks}))

    def execute(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return runner.execute()

    def test_missing_gate_waits_and_never_starts_agent(self):
        self.configure(['bootstrap'])
        self.assertEqual(self.execute(), 3)
        state = runner.status()
        self.assertEqual(state['state'], 'waiting')
        self.assertFalse(state['port_complete'])
        self.assertEqual(state['milestones'][0]['state'], 'passed')
        self.assertEqual(state['milestones'][1]['state'], 'needs_acceptance_check')
        self.assertIsNone(state['pid'])

    def test_gate_failure_marks_failed(self):
        self.configure(['bootstrap'], passed=False)
        self.assertEqual(self.execute(), 1)
        self.assertEqual(runner.status()['state'], 'failed')
        self.assertFalse(runner.status()['port_complete'])

    def test_complete_requires_every_gate(self):
        self.configure(self.ids)
        self.assertEqual(self.execute(), 0)
        self.assertTrue(runner.status()['port_complete'])
        self.assertTrue(all(t['state'] == 'passed' for t in runner.status()['milestones']))

    def test_agent_claim_cannot_override_failed_gate(self):
        self.configure(['bootstrap'], passed=False)
        data = json.loads(self.workflow.read_text())
        data['milestones'][0]['prompt'] = 'prompt.md'
        self.workflow.write_text(json.dumps(data))
        (self.root/'prompt.md').write_text('Work on the component.')
        calls = []
        def fake_run(command, cwd, prefix, timeout):
            calls.append(command[0])
            if command[0] != 'codex':
                (prefix.parent/'result.json').write_text(json.dumps({'passed': False, 'milestone': 'bootstrap'}))
            return {}
        with patch.object(runner, 'run', side_effect=fake_run), patch.object(runner, 'acceptance_fingerprint', return_value='fixed'):
            with contextlib.redirect_stdout(io.StringIO()):
                code = runner.execute(port=True, max_attempts=2)
        self.assertEqual(code, 1)
        self.assertEqual(calls.count('codex'), 2)
        self.assertFalse(runner.status()['port_complete'])

    def test_agent_cannot_change_acceptance_inputs(self):
        self.configure(['bootstrap'], passed=False)
        data = json.loads(self.workflow.read_text())
        data['milestones'][0]['prompt'] = 'prompt.md'
        self.workflow.write_text(json.dumps(data))
        (self.root/'prompt.md').write_text('Work on the component.')
        def fake_run(command, cwd, prefix, timeout):
            if command[0] != 'codex':
                (prefix.parent/'result.json').write_text(json.dumps({'passed': False, 'milestone': 'bootstrap'}))
            return {}
        with patch.object(runner, 'run', side_effect=fake_run), patch.object(runner, 'acceptance_fingerprint', side_effect=['old', 'changed']):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.execute(port=True), 1)
        self.assertIn('Acceptance inputs changed', runner.status()['message'])
        self.assertFalse(runner.status()['port_complete'])

    def test_removed_milestones_are_rejected(self):
        self.configure(['bootstrap'])
        data = json.loads(self.workflow.read_text())
        data['milestones'] = data['milestones'][:1]
        self.workflow.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            runner.load_workflow()

    def test_interrupt_records_stopped(self):
        self.configure(['bootstrap'])
        with patch.object(runner, 'run', side_effect=KeyboardInterrupt):
            self.assertEqual(self.execute(), 130)
        self.assertEqual(runner.status()['state'], 'stopped')
        self.assertFalse(runner.status()['port_complete'])

if __name__ == '__main__':
    unittest.main()
