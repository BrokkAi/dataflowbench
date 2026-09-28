#!/usr/bin/env python3
"""Focused contract tests for the non-scored Swift entry observation classifier."""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name('swift_entry_observation.py')
SPEC = importlib.util.spec_from_file_location('swift_entry_observation', SCRIPT)
classifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(classifier)


class SwiftEntryObservationTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            ['/tmp/main.swift', 'Fixture', 0, 3, 1, 4],
            ['/tmp/main.swift', 'Fixture', 1, 9, 1, 4],
        ]
        self.endpoints = [
            ['main.swift', 4, 12, 'source', 1, 1, 1, 1, 1, 'DataFlowBenchTaintSwift:dfb_source()'],
            ['main.swift', 14, 8, 'sink', 1, 1, 1, 1, 1, 'DataFlowBenchTaintSwift:dfb_sink(_:)'],
        ]
        self.flow = [['main.swift', 4, 'main.swift', 14, 8]]

    def classify(self, entries=None, endpoints=None, flows=None):
        return classifier.classify(
            self.entries if entries is None else entries,
            self.endpoints if endpoints is None else endpoints,
            self.flow if flows is None else flows,
        )

    def test_exact_anchored_positive_is_diagnostic_and_never_scored(self):
        result = self.classify()
        self.assertEqual((result['status'], result['diagnostic']), ('DIAGNOSTIC', 'reached'))
        self.assertFalse(result['scored'])

    def test_empty_flow_is_a_diagnostic_negative_with_complete_bindings(self):
        result = self.classify(flows=[])
        self.assertEqual((result['status'], result['diagnostic']), ('DIAGNOSTIC', 'not-reached'))
        self.assertFalse(result['scored'])

    def test_call_and_argument_columns_are_distinct(self):
        self.assertEqual(self.classify(flows=[['main.swift', 4, 'main.swift', 14, 17]])['diagnostic'], 'reached')

    def test_foreign_flow_does_not_match_only_the_sink_or_source(self):
        result = self.classify(flows=[['other.swift', 4, 'main.swift', 14, 8]])
        self.assertEqual(result['diagnostic'], 'not-reached')
        result = self.classify(flows=[['main.swift', 4, 'other.swift', 14, 8]])
        self.assertEqual(result['diagnostic'], 'not-reached')

    def test_missing_entry_sequence_is_typed_incomplete(self):
        result = classifier.classify(None, self.endpoints, self.flow)
        self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', 'missing-sequence'))

    def test_gap_in_dense_indices_is_typed_incomplete(self):
        result = self.classify(entries=[self.entries[0], [*self.entries[1][:2], 2, *self.entries[1][3:]]])
        self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', 'invalid-dense-index'))

    def test_duplicate_owner_row_and_duplicate_index_are_rejected(self):
        duplicate_row = self.classify(entries=[*self.entries, self.entries[0]])
        self.assertEqual(duplicate_row['reason'], 'duplicate-owner-rows')
        duplicate_index = self.classify(entries=[self.entries[0], [
            '/tmp/main.swift', 'Fixture', 0, 10, 1, 4]])
        self.assertEqual(duplicate_index['reason'], 'duplicate-indices')

    def test_multiple_sourcefiles_or_modules_are_incomplete(self):
        other_file = self.classify(entries=[self.entries[0], ['/tmp/other.swift', 'Fixture', 1, 9, 1, 4]])
        self.assertEqual(other_file['reason'], 'multiple-entry-owners')
        other_module = self.classify(entries=[self.entries[0], ['/tmp/main.swift', 'Other', 1, 9, 1, 4]])
        self.assertEqual(other_module['reason'], 'multiple-entry-owners')

    def test_exact_source_and_sink_are_both_required(self):
        for index, reason in ((0, 'missing-exact-source'), (1, 'missing-exact-sink')):
            with self.subTest(reason=reason):
                result = self.classify(endpoints=[self.endpoints[1 - index]])
                self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', reason))

    def test_missing_cfg_and_dataflow_coverage_are_not_negative_results(self):
        for index, reason in ((0, 'missing-cfg'), (1, 'missing-df')):
            with self.subTest(reason=reason):
                endpoints = [row[:] for row in self.endpoints]
                endpoints[0][7 + index] = 0
                result = self.classify(endpoints=endpoints)
                self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', reason))

    def test_conflicting_endpoint_rows_are_incomplete(self):
        conflict = self.endpoints[0][:]
        conflict[7] = 0
        result = self.classify(endpoints=[*self.endpoints, conflict])
        self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', 'conflicting-endpoint-rows'))

    def test_boolean_is_not_accepted_as_integer_evidence(self):
        entries = [row[:] for row in self.entries]
        entries[0][2] = True
        result = self.classify(entries=entries)
        self.assertEqual((result['status'], result['reason']), ('INCOMPLETE', 'malformed-entry-row'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
