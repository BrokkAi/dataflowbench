"""Prospective Swift v3 admission boundary; consumes evidence, never grants activation.

Resource certificates are deliberately not supported until an aggregate process
containment verifier exists. Per-process RSS and phase deadlines are diagnostic.
"""
from swift_persistence_coverage import assess_coverage, CoverageStatus

OUTCOMES = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}


def normalize(case, observation):
    """Keep observations distinct from admissible outcomes at the canonical budget.

This version admits no definitive result: the available Darwin runner cannot
prove aggregate memory containment. Retain actual findings and coverage reasons
so later resource qualification cannot hide semantic incompleteness.
"""
    raw = observation.get('outcome')
    reasons = []
    semantic_coverage = 'NotAssessed'
    if raw not in OUTCOMES:
        raw = 'runner-error'
        reasons.append('MalformedOutcome')
    if observation.get('case_id') != case['id']:
        reasons.append('CaseIdentityMismatch')
    if observation.get('execution_budget') != case['execution_budget']:
        reasons.append('ResourceContractMismatch')
    # The current runner has no independent aggregate-containment certificate.
    # Never accept a caller-supplied "qualified" boolean or scalar RSS as proof.
    reasons.append('AggregateResourceQualificationUnavailable')
    if case['template_id'] == 'dfb-template-native-persistence':
        scopes = observation.get('expected_scopes')
        if (not isinstance(scopes, list) or not scopes or
                any(type(s) is not int or s < 1 for s in scopes)):
            reasons.append('MissingScopeInventory')
            scopes = None
        rows = observation.get('coverage')
        if not isinstance(rows, list):
            rows = []
        try:
            coverage = assess_coverage(rows, scopes)
        except (TypeError, ValueError):
            coverage = assess_coverage([])
        semantic_coverage = coverage.status.value if scopes else 'Incomplete'
        if coverage.status is CoverageStatus.INCOMPLETE:
            reasons.extend(coverage.reasons)
    if observation.get('endpoints_verified') is not True:
        reasons.append('MissingExactEndpoints')
    if observation.get('extraction_complete') is not True:
        reasons.append('IncompleteExtraction')
    phases = observation.get('phases')
    if not isinstance(phases, list) or not phases:
        reasons.append('MissingExecutionEvidence')
    elif any(not isinstance(p, dict) or type(p.get('exit_status')) is not int or
             (p['exit_status'] != 0 and p.get('timed_out') is not True) or
             type(p.get('timed_out')) is not bool or
             p.get('cleanup_status') != 'tracked-processes-stopped' for p in phases):
        reasons.append('ExecutionFailedOrIncomplete')
    if isinstance(phases, list) and any(isinstance(p, dict) and p.get('timed_out') is True for p in phases):
        reasons.append('BudgetExhausted')
    # Unsupported needs an independently validated prospective partition, which
    # this observation boundary does not implement. Never invent that decision.
    if raw == 'unsupported':
        reasons.append('UnsupportedPartitionNotVerified')
    errors = {'MalformedOutcome', 'CaseIdentityMismatch', 'MissingExecutionEvidence',
              'ExecutionFailedOrIncomplete', 'MissingExactEndpoints', 'IncompleteExtraction'}
    outcome = 'runner-error' if raw == 'runner-error' or errors.intersection(reasons) else 'inconclusive'
    return {'case_id': case['id'], 'raw_outcome': raw, 'outcome': outcome,
            'coverage_status': semantic_coverage,
            'diagnostics': sorted(set(reasons)), 'scored_activation': False,
            'execution_budget': case['execution_budget'], 'observation': observation}


def normalize_population(cases, observations):
    """Every selected case survives; reject duplicate and foreign evidence."""
    selected = {c['id']: c for c in cases}
    if len(selected) != len(cases):
        raise ValueError('duplicate selected case')
    indexed = {}
    for row in observations:
        if row.get('case_id') not in selected:
            raise ValueError('foreign observation')
        if row['case_id'] in indexed:
            raise ValueError('duplicate observation')
        indexed[row['case_id']] = row
    return [normalize(case, indexed.get(case['id'], {})) for case in cases]
