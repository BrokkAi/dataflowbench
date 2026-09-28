#!/usr/bin/env python3
import unittest
from swift_endpoint_diagnostic import classify


class EndpointStages(unittest.TestCase):
    anchor = {'file': 'main.swift', 'line': 4, 'role': 'source'}
    bound = ['main.swift', 4, 17, 'source', 1, 1, 1, 1, 1, 'DataFlowBenchTaintSwift:dfb_source()']

    def test_distinct_missing_stages(self):
        self.assertEqual(classify([], [self.anchor])[0]['status'], 'ASTCallMissing')
        for values, expected in [([0,0,1,0,0], 'UnresolvedEndpoint'),
                                 ([1,0,1,1,1], 'NonMatchingDeclaration'),
                                 ([1,1,0,0,0], 'EndpointExpressionMissing'),
                                 ([1,1,1,0,0], 'MissingControlFlow'),
                                 ([1,1,1,1,0], 'MissingDataFlow'),
                                 ([1,1,1,1,1], 'Bound')]:
            row = self.bound[:]; row[4:9] = values
            self.assertEqual(classify([row], [self.anchor])[0]['status'], expected)

    def test_nested_nonmatching_call_cannot_replace_exact_identity(self):
        other=self.bound[:];other[2]=30;other[5]=0;other[9]='Other:dfb_source()'
        self.assertEqual(classify([other,self.bound], [self.anchor])[0]['status'],'Bound')
        other[5]=1
        self.assertEqual(classify([other,self.bound], [self.anchor])[0]['status'],'AmbiguousASTCalls')

    def test_duplicates_and_contradictory_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            classify([self.bound,self.bound],[self.anchor])
        row=self.bound[:];row[7]=0
        with self.assertRaisesRegex(ValueError,'Contradictory'):
            classify([row],[self.anchor])

    def test_malformed_and_cross_location_evidence(self):
        row=self.bound[:];row[4]=True
        with self.assertRaisesRegex(ValueError,'Malformed'):
            classify([row],[self.anchor])
        other=dict(self.anchor,line=5)
        self.assertEqual(classify([self.bound],[other])[0]['status'],'ASTCallMissing')


if __name__ == '__main__': unittest.main(verbosity=2)
