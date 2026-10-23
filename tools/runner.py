#!/usr/bin/env python3
"""Local milestone runner with durable status, locking, logs, and fail-closed gates."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from evaluate import ROOT, write_json, run, sha, tree_hash

STATE = ROOT/'reports/status.json'
LOCK = ROOT/'work/runner.lock'
WORKFLOW = ROOT/'evaluations/workflow.json'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def load_workflow():
    tasks = json.loads(WORKFLOW.read_text())['milestones']
    if not tasks or len({t['id'] for t in tasks}) != len(tasks):
        raise ValueError('Workflow must contain uniquely named milestones')
    required = {'bootstrap', 'pilot', 'neighbors', 'physics', 'integration', 'workloads'}
    if not required.issubset({t['id'] for t in tasks}):
        raise ValueError('Workflow is missing required port acceptance milestones')
    return tasks


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, TypeError):
        return False
    except PermissionError:
        return True


def locked():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


def initial():
    return {'schema_version': 1, 'state': 'not_started', 'port_complete': False,
            'pid': None, 'updated_at': now(), 'current': None, 'run_id': None,
            'message': 'No run started.',
            'milestones': [{'id': t['id'], 'title': t['title'], 'state': 'pending'} for t in load_workflow()]}


def status():
    value = json.loads(STATE.read_text()) if STATE.exists() else initial()
    if value['state'] == 'running' and (not alive(value.get('pid')) or not locked()):
        value.update(state='interrupted', port_complete=False,
                     message='Runner is no longer active. Review the logs and restart.', updated_at=now())
        for task in value['milestones']:
            if task['state'] == 'running':
                task['state'] = 'interrupted'
    return value


def render(value):
    rows = ['# SPH-EXA runner status', '', f"**Runner: {value['state']}**",
            f"**Full port complete: {'yes' if value['port_complete'] else 'no'}**", '',
            value['message'], '', f"Updated: {value['updated_at']}",
            f"Run: {value.get('run_id') or 'none'}", '', '| Milestone | State |', '|---|---|']
    rows += [f"| {t['title']} | {t['state']} |" for t in value['milestones']]
    rows += ['', 'Live status: `make status` or `make watch`.',
             'Reports and raw logs: `reports/runs/<run-id>/`.',
             'STATUS.md is a snapshot; the status command also detects a crashed runner.',
             '']
    return '\n'.join(rows)


def save(value):
    value['updated_at'] = now()
    write_json(STATE, value)
    target = ROOT/'STATUS.md'
    temp = target.with_suffix('.md.tmp')
    temp.write_text(render(value))
    temp.replace(target)


def accept_gate(result, milestone):
    if not isinstance(result, dict) or result.get('passed') is not True:
        raise ValueError('Gate did not explicitly pass')
    if result.get('milestone') != milestone:
        raise ValueError('Gate report belongs to another milestone')


def acceptance_fingerprint():
    return {'evaluations': tree_hash(ROOT/'evaluations')['sha256'],
            'gate_tools': {p.name: sha(p) for p in sorted((ROOT/'tools').glob('*.py'))},
            'reference': tree_hash(ROOT/'benchmarks/sph-exa/reference')['sha256'],
            'vine_source': tree_hash(ROOT/json.loads((ROOT/'evaluations/vine-pin.json').read_text())['checkout']/'root')['sha256'],
            'vine_binary': sha(ROOT/'work/bin/vine'),
            'upstream': tree_hash(ROOT/'upstream/sph-exa')['sha256']}


def execute(port=False, max_attempts=3, agent_timeout=1200):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('A runner is already active.', file=sys.stderr)
            return 2
        tasks = load_workflow()
        value = initial()
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'
        directory = ROOT/'reports/runs'/run_id
        directory.mkdir(parents=True)
        value.update(state='running', pid=os.getpid(), run_id=run_id, message='Starting acceptance checks.')
        save(value)
        def stop_handler(signum, frame):
            raise KeyboardInterrupt
        old_handler = signal.signal(signal.SIGTERM, stop_handler)
        try:
            for task, task_state in zip(tasks, value['milestones']):
                if not task.get('gate'):
                    task_state['state'] = 'needs_acceptance_check'
                    value.update(state='waiting', current=task['id'], message=task['next_action'])
                    save(value)
                    return 3
                output = directory/task['id']
                output.mkdir()
                value.update(current=task['id'], message=f"Checking: {task['title']}")
                task_state['state'] = 'running'
                save(value)
                command = [part.replace('{python}', sys.executable).replace('{output}', str(output)) for part in task['gate']]
                result_path = output/'result.json'
                def verify():
                    # Remove a previous report: a successful exit without a fresh report is failure.
                    result_path.unlink(missing_ok=True)
                    run(command, ROOT, output/'gate', timeout=task.get('timeout_seconds', 300))
                    result = json.loads(result_path.read_text())
                    accept_gate(result, task['id'])
                try:
                    verify()
                except Exception:
                    if not port or not task.get('prompt'):
                        raise
                    baseline = acceptance_fingerprint()
                    for attempt in range(1, max_attempts + 1):
                        trial = output/f'attempt-{attempt}'
                        trial.mkdir()
                        # Preserve failed verification evidence before the next attempt overwrites logs.
                        import shutil
                        for existing in output.glob('gate.*'):
                            shutil.copy2(existing, trial/existing.name)
                        value.update(message=f"Implementing {task['title']}, attempt {attempt}/{max_attempts}")
                        save(value)
                        prompt = (ROOT/task['prompt']).read_text() + (
                            f"\nActive milestone: {task['id']}.\nFailure evidence: {trial}.\n"
                            'Read AGENTS.md and the active plan. Complete this milestone with measured evidence. '
                            'Update the Markdown guidance for every useful lesson. Do not change upstream, '
                            'evaluations/, tools/, reference instrumentation, pinned Vine, or acceptance requirements. '
                            'Your final report is informational: an independent gate decides acceptance. '
                            'If those fixed checks need legitimate changes, report the issue and stop.')
                        agent = ['codex', 'exec', '--sandbox', 'workspace-write', '--skip-git-repo-check',
                                 '-C', str(ROOT), '--json', '--output-schema', str(ROOT/'evaluations/agent-report.schema.json'),
                                 '-o', str(trial/'agent-report.json'), prompt]
                        run(agent, ROOT, trial/'agent', timeout=agent_timeout)
                        if acceptance_fingerprint() != baseline:
                            raise RuntimeError('Acceptance inputs changed during agent work; review required.')
                        value.update(message=f"Independently verifying {task['title']}, attempt {attempt}")
                        save(value)
                        try:
                            verify()
                            break
                        except Exception:
                            if attempt == max_attempts:
                                raise
                task_state.update(state='passed', report=str(result_path.relative_to(ROOT)))
                save(value)
            value.update(state='complete', port_complete=True, current=None,
                         message='Every configured port acceptance milestone passed.')
            save(value)
            return 0
        except KeyboardInterrupt:
            value.update(state='stopped', message='Stopped; unfinished milestones remain pending.')
            for task in value['milestones']:
                if task['state'] == 'running':
                    task['state'] = 'interrupted'
            save(value)
            return 130
        except Exception as exc:
            value.update(state='failed', message=str(exc))
            for task in value['milestones']:
                if task['state'] == 'running':
                    task['state'] = 'failed'
            save(value)
            return 1
        finally:
            signal.signal(signal.SIGTERM, old_handler)
            value['pid'] = None
            save(value)
            write_json(directory/'status.json', value)
            print(render(value), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'run', 'status', 'watch', 'stop'))
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--port', action='store_true', help='Permit bounded Codex work on failed milestones with registered gates')
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--agent-timeout', type=int, default=1200)
    args = parser.parse_args()
    if args.max_attempts < 1 or args.agent_timeout < 1:
        parser.error('Attempt and timeout limits must be positive')
    if args.action == 'run':
        return execute(args.port, args.max_attempts, args.agent_timeout)
    if args.action == 'start':
        if locked():
            print('A runner is already active.')
            return 2
        path = ROOT/'reports/runner.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as log:
            argv = [sys.executable, str(Path(__file__).resolve()), 'run', '--max-attempts', str(args.max_attempts), '--agent-timeout', str(args.agent_timeout)]
            if args.port:
                argv.append('--port')
            child = subprocess.Popen(argv, cwd=ROOT,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        print(f'Started runner PID {child.pid}. Use make status or make watch. Log: {path}')
        return 0
    if args.action == 'stop':
        value = status()
        if value['state'] == 'running' and locked() and alive(value.get('pid')):
            os.kill(value['pid'], signal.SIGTERM)
            print('Stop requested.')
        else:
            print('No active runner.')
        return 0
    try:
        while True:
            value = status()
            output = json.dumps(value, indent=2) if args.json else render(value)
            if args.action == 'watch' and sys.stdout.isatty():
                print('\033[2J\033[H', end='')
            print(output, flush=True)
            if args.action != 'watch' or value['state'] != 'running':
                return 0
            time.sleep(2)
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    sys.exit(main())
