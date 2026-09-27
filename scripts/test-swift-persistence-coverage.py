#!/usr/bin/env python3
import unittest
from swift_persistence_coverage import assess_coverage, finding_interpretation, CoverageStatus

class Coverage(unittest.TestCase):
    def test_explicit_admission(self):self.assertEqual(assess_coverage([[3,'Complete','AdmittedClosedScope',3]]).status,CoverageStatus.COMPLETE)
    def test_empty_is_incomplete(self):self.assertEqual(finding_interpretation([],[])['status'],'Incomplete')
    def test_incomplete_empty_not_clean(self):self.assertEqual(finding_interpretation([[3,'Incomplete','UnmodeledCallEffect',9]],[])['status'],'Incomplete')
    def test_incomplete_preserves_findings(self):
        rows=[[3,'Incomplete','IncompleteReceiverOrigin',8]];findings=[{'source':7,'sink':10}]
        self.assertEqual(finding_interpretation(rows,findings)['findings'],findings)
        self.assertEqual(finding_interpretation(rows,findings)['status'],'Incomplete')
    def test_mixed_scope_not_complete(self):self.assertEqual(assess_coverage([[3,'Complete','AdmittedClosedScope',3],[12,'Incomplete','DynamicKey',15]]).status,CoverageStatus.INCOMPLETE)
    def test_unknown_status(self):self.assertEqual(assess_coverage([[3,'Clean','AdmittedClosedScope',3]]).status,CoverageStatus.INCOMPLETE)
    def test_malformed(self):self.assertEqual(assess_coverage([[3,'Complete']]).status,CoverageStatus.INCOMPLETE)
    def test_missing_expected_scope(self):self.assertEqual(assess_coverage([[3,'Complete','AdmittedClosedScope',3]],expected_scopes=[3,12]).status,CoverageStatus.INCOMPLETE)
    def test_no_scored_claim(self):self.assertEqual(finding_interpretation([[3,'Complete','AdmittedClosedScope',3]],[])['status'],'NoFindingsInAdmittedScope')
if __name__=='__main__':unittest.main(verbosity=2)
