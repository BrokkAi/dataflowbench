#!/usr/bin/env python3
"""Full-run verifier regressions; run only after the 108-case run completes."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from swift_normal_reports_v1 import ROOT, bound_file, read

spec = importlib.util.spec_from_file_location(
    'codeql_current108_replay',
    Path(__file__).with_name('check-codeql-current108-results-v1.py'),
)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class Current108Results(unittest.TestCase):
    def test_complete_run_is_108_attempts_and_unscored(self):
        result = replay.verify()
        self.assertEqual(result['rows'], 108)
        self.assertEqual(result['attempted'], 108)
        self.assertFalse(result['scored_activation'])

    def test_missing_run_row_is_rejected(self):
        run_path = ROOT / replay.RUN / 'run.json'
        original = replay.read

        def altered(path):
            value = original(path)
            if path == run_path:
                value['results'] = value['results'][:-1]
            return value

        with patch.object(replay, 'read', side_effect=altered):
            with self.assertRaisesRegex(ValueError, '108 run membership'):
                replay.verify()

    def test_promoted_exported_outcome_is_rejected(self):
        original = replay.read

        def altered(path):
            value = original(path)
            if path.name.startswith('report-') and value.get('results'):
                value['results'][0]['outcome'] = 'not-reached'
            return value

        with patch.object(replay, 'read', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'normal report drift'):
                replay.verify()

    def test_altered_decoded_rows_are_rejected(self):
        run = read(ROOT / replay.RUN / 'run.json')
        plan = read(ROOT / replay.PLAN)
        contract = read(bound_file(ROOT, plan['execution_contract']))
        _, cases, _ = replay.load_population(ROOT)
        target = None
        for row in run.get('results', []):
            raw = read(bound_file(ROOT, row['raw']))
            case_id = row['case_id']
            sequence = replay.phase_sequence(
                contract, plan['cases'][case_id]['phase_sequence'],
            )
            phases = [read(bound_file(ROOT, ref)) for ref in raw.get('commands', [])]
            if (len(phases) == len(sequence)
                    and 'IncompleteExecution' not in raw.get('diagnostics', [])
                    and 'BudgetExhausted' not in raw.get('diagnostics', [])
                    and raw.get('analysis_elapsed_seconds', 76) <= 75 and all(
                phase.get('exit_status') == 0
                and phase.get('timed_out') is False
                and phase.get('cleanup_status') == 'tracked-processes-stopped'
                for phase in phases
            ) and raw.get('raw_outcome') != 'runner-error'):
                target = case_id
                break
        self.assertIsNotNone(target, 'completed run must contain a successful full phase sequence')

        original = replay.decoded_rows

        def altered(root, raw, name, case_id):
            if case_id == target and name == 'roles':
                return []
            return original(root, raw, name, case_id)

        with patch.object(replay, 'decoded_rows', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'decoded evidence/raw outcome mismatch'):
                replay.verify()

    def test_missing_exact_endpoints_remains_runner_error(self):
        case_id = 'dfb-taint-swift-infeasible-branch-negative'
        run = read(ROOT / replay.RUN / 'run.json')
        row = next(item for item in run['results'] if item['case_id'] == case_id)
        raw = read(bound_file(ROOT, row['raw']))
        self.assertEqual(raw['raw_outcome'], 'runner-error')
        self.assertIn('MissingExactEndpoints', raw['diagnostics'])

        plan = read(ROOT / replay.PLAN)
        contract = read(bound_file(ROOT, plan['execution_contract']))
        case = replay.load_population(ROOT)[1][case_id]
        sequence = replay.phase_sequence(contract, plan['cases'][case_id]['phase_sequence'])
        phases = [read(bound_file(ROOT, reference)) for reference in raw['commands']]
        self.assertEqual(len(phases), len(sequence))
        self.assertTrue(all(
            phase.get('exit_status') == 0
            and phase.get('timed_out') is False
            and phase.get('cleanup_status') == 'tracked-processes-stopped'
            for phase in phases
        ))

        outcome, diagnostics = replay.rederive_outcome(
            ROOT, raw, case, sequence, raw['commands'],
        )
        self.assertEqual(outcome, 'runner-error')
        self.assertIn('MissingExactEndpoints', diagnostics)

        # Some runner revisions return ('runner-error', diagnostic) from
        # observe; others can raise the same typed observation failure. Replay
        # must preserve the runner's recorded state in either case.
        with patch.object(replay, 'decoded_rows', return_value=[]), patch.object(
                replay, 'observe', side_effect=ValueError('MissingExactEndpoints')):
            outcome, diagnostics = replay.rederive_outcome(
                ROOT, raw, case, sequence, raw['commands'],
            )
        self.assertEqual(outcome, 'runner-error')
        self.assertEqual(diagnostics, ['MissingExactEndpoints'])


if __name__ == '__main__':
    unittest.main()
