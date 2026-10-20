"""Fail-closed interpretation of structural persistence applicability rows."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class CoverageStatus(str, Enum):
    COMPLETE = 'Complete'
    INCOMPLETE = 'Incomplete'


@dataclass(frozen=True)
class CoverageAssessment:
    status: CoverageStatus
    reasons: Tuple[str, ...]


def assess_coverage(rows, expected_scopes=None):
    """Coverage is independent of finding count and resource qualification."""
    if not rows:
        return CoverageAssessment(CoverageStatus.INCOMPLETE, ('MissingCoverageEvidence',))
    reasons = set()
    observed_scopes = set()
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 4:
            reasons.add('MalformedCoverageEvidence')
            continue
        scope, status, reason, line = row
        if type(scope) is int:
            observed_scopes.add(scope)
        if type(scope) is not int or type(line) is not int or scope < 0 or line < 1 or not isinstance(reason, str):
            reasons.add('MalformedCoverageEvidence')
        elif status == CoverageStatus.INCOMPLETE.value:
            reasons.add(reason or 'UnspecifiedIncompleteCoverage')
        elif status != CoverageStatus.COMPLETE.value or reason != 'AdmittedClosedScope':
            reasons.add('UnknownCoverageStatus')
    if expected_scopes is not None and not set(expected_scopes) <= observed_scopes:
        reasons.add('MissingScopeCoverage')
    if reasons:
        return CoverageAssessment(CoverageStatus.INCOMPLETE, tuple(sorted(reasons)))
    return CoverageAssessment(CoverageStatus.COMPLETE, ())


def finding_interpretation(rows, findings, expected_scopes=None):
    """Never convert empty findings under incomplete coverage into a clean result."""
    coverage = assess_coverage(rows, expected_scopes)
    if coverage.status is CoverageStatus.INCOMPLETE:
        return {'status': 'Incomplete', 'reasons': list(coverage.reasons), 'findings': findings}
    return {'status': 'Findings' if findings else 'NoFindingsInAdmittedScope',
            'reasons': [], 'findings': findings}
