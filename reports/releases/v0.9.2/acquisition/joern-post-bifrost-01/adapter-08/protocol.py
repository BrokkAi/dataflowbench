"""Strict Joern-only contract delta and source roster derivation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any
from packet import document, inherited_core, read_ref, require
GROUP = 'joern-swift-common108'
ATTEMPT = GROUP + '-attempt-05-series-02'
EXPERIMENT_ENV = 'DATAFLOWBENCH_V092_JOERN_POST_BIFROST01_EXPERIMENT'
FIXTURE_ENV = 'DATAFLOWBENCH_V092_JOERN_POST_BIFROST01_FIXTURE'

def dispatch_groups(core: dict[str, Any]) -> tuple[str]:
    require(core.get('dispatch_groups') == [GROUP], 'only singleton Joern05 dispatch is allowed')
    return (GROUP,)

def source_roster(root: Path, additions: list[dict[str, str]]) -> list[dict[str, str]]:
    """Derive inherited records from immutable contract26, never old counts."""
    old = inherited_core(root)
    contract = document(root, old['contract'])
    inherited = contract['source_inputs']
    require(inherited == old['source_inputs'], 'core/contract inherited source roster differs')
    result = copy.deepcopy(inherited)
    seen = {record['path'] for record in result}
    require(len(seen) == len(result), 'duplicate inherited source path')
    for record in additions:
        require(set(record) == {'path', 'sha256', 'role'} and record['role'] == 'release-input', 'typed new source record required')
        require(record['path'] not in seen, 'new source cannot replace inherited input')
        require(record['path'].startswith('reports/releases/v0.9.2/acquisition/') or record['path'].startswith('reports/releases/v0.9.2/qualification/'), 'new source outside reviewed input namespaces')
        read_ref(root, {k: record[k] for k in ('path', 'sha256')})
        result.append(copy.deepcopy(record))
        seen.add(record['path'])
    return result

def contract_delta(old: dict[str, Any], new: dict[str, Any], reviewed_joern: dict[str, Any]) -> None:
    """Exact reviewed group is an input, not a fabricated qualification claim."""
    require([g['id'] for g in old['groups']] == [g['id'] for g in new['groups']] and len(new['groups']) == 84, 'full84 group roster changed')
    require(new.get('execution_series') == old.get('execution_series') == 2, 'series changed')
    allowed = {'source_commit', 'source_inputs', 'tools', 'groups'}
    require(set(old) == set(new), 'contract root fields changed')
    for key in set(old) - allowed:
        require(new[key] == old[key], 'frozen contract field changed: ' + key)
    expected_tools = copy.deepcopy(old['tools'])
    expected_tools['runner'] = new['tools']['runner']
    require(new['tools'] == expected_tools, 'engine tool pins changed')
    for (before, after) in zip(old['groups'], new['groups']):
        if before['id'] != GROUP:
            require(before == after, 'retained group changed: ' + before['id'])
            continue
        require(after == reviewed_joern, 'Joern group differs from reviewed packet')
        require(type(after['maximum_attempts']) is int and after['maximum_attempts'] == 5, 'Joern global cap must be five')
        require(before['maximum_attempts'] == 2, 'unexpected historical Joern cap')
        for key in ('id', 'tool', 'family', 'case_ids', 'deadline_seconds'):
            require(before[key] == after[key], 'Joern frozen case/deadline field changed: ' + key)
        require(len(after['case_ids']) == 108 and len(after['reports']) == 5, 'Joern108/5 partitions changed')
        require(set(before) == set(after), 'Joern group fields changed')
        data_root = 'reports/raw/joern-common-v2/current108-v092-01'
        require(before['output_roots'] == [data_root] and
                after['output_roots'] == [data_root, data_root + '.startup-observation'],
                'Joern output roots must retain the original data and exact observer sibling')
        mutable = {'maximum_attempts', 'argv', 'environment', 'reports', 'output_roots'}
        require(all((before[key] == after[key] for key in set(before) - mutable)), 'unreviewed Joern group field changed')
        for (before_report, after_report) in zip(before['reports'], after['reports']):
            require(set(before_report) == set(after_report), 'Joern report fields changed')
            require(all((before_report[key] == after_report[key] for key in set(before_report) - {'source_path'})), 'Joern report partition changed')
            require(isinstance(after_report.get('source_path'), str) and bool(after_report['source_path']), 'reviewed report source path missing')
    before_inputs = {r['path']: r for r in old['source_inputs']}
    after_inputs = {r['path']: r for r in new['source_inputs']}
    require(len(after_inputs) == len(new['source_inputs']) and all((after_inputs.get(path) == record for (path, record) in before_inputs.items())), 'inherited source input replaced or dropped')

def derive_next_global_attempt_number(annex_rows: list[dict[str, Any]]) -> int:
    """Derive global132 from the exact 21-row annex, outside the frozen row."""
    require(type(annex_rows) is list and len(annex_rows) == 21,
            'exact archived C5 annex21 is required to derive the next global attempt')
    numbers = [row.get('global_attempt_number') if type(row) is dict else None
               for row in annex_rows]
    require(numbers == list(range(111, 132)),
            'archived C5 annex global attempts must be the exact111..131 prefix')
    return numbers[-1] + 1

def require_terminal_tail(rows: list[dict[str, Any]], current: dict[str, Any]) -> None:
    require(len(rows) in (130, 131), 'only exact130 or one physical row131 is allowed')
    if len(rows) == 130:
        return
    row = rows[-1]
    global_attempt_number = derive_next_global_attempt_number(rows[109:130])
    require(row.get('group_id') == GROUP and row.get('attempt_id') == ATTEMPT,
            'physical row131 is not the exact Joern05 attempt')
    require(global_attempt_number == 132 and 'global_attempt_number' not in row,
            'physical row131 must retain the frozen recorder schema; global132 is derived from the exact prefix')
    require(row.get('contract_sha256') == current['contract']['sha256'] and row.get('source_commit') == current['source_commit'] and (row.get('plan_commit') == current['plan_commit']), 'tail context changed')
    _terminal_identity(row, group_id=GROUP, attempt_id=ATTEMPT,
                       source_commit=current['source_commit'],
                       plan_commit=current['plan_commit'],
                       contract_sha256=current['contract']['sha256'],
                       execution_series=2, label='physical row131')


def joern108_operational_completion(current: dict[str, Any], row: dict[str, Any],
                                    report_bindings: list[dict[str, Any]],
                                    outcomes: dict[str, int],
                                    native_acceptance: dict[str, Any], *,
                                    tail_proof: dict[str, Any]) -> dict[str, Any]:
    """Validate one actual completed physical131 against the normalized current plan.

    This gate proves operational report completeness only. It deliberately
    leaves the independent full-target/publication gate false when C5 remains
    incomplete and does not grade the semantic outcomes.
    """
    from pathlib import PurePosixPath
    import re

    normalized = current.get('validated')
    require(type(normalized) is dict and type(normalized.get('plan')) is dict,
            'actual graph-normalized current contract is required')
    plan = normalized['plan']
    contract_sha = normalized.get('bytes_sha256')
    source_commit = plan.get('source_commit')
    plan_commit = current.get('plan_commit')
    require(type(contract_sha) is str and re.fullmatch(r'[0-9a-f]{64}', contract_sha) and
            type(source_commit) is str and re.fullmatch(r'[0-9a-f]{40}', source_commit) and
            type(plan_commit) is str and re.fullmatch(r'[0-9a-f]{40}', plan_commit),
            'normalized current source/plan/contract identity is malformed')
    require(type(tail_proof) is dict and set(tail_proof) == {
                'row', 'physical_ledger_row', 'global_attempt_number',
                'status', 'completion_claim', 'eligible'} and
            tail_proof.get('row') == row and
            tail_proof.get('physical_ledger_row') == 131 and
            tail_proof.get('global_attempt_number') == 132 and
            tail_proof.get('status') == row.get('status') and
            tail_proof.get('completion_claim') is False and
            tail_proof.get('eligible') is False and
            'global_attempt_number' not in row,
            'adapter-derived physical/global attempt provenance is absent or mismatched')
    require(row.get('group_id') == GROUP and row.get('attempt_id') == ATTEMPT and
            row.get('execution_series') == 2 and
            row.get('source_commit') == source_commit and row.get('plan_commit') == plan_commit and
            row.get('contract_sha256') == contract_sha and row.get('status') == 'completed' and
            type(row.get('exit_code')) is int and row.get('exit_code') == 0 and
            row.get('timed_out') is False and row.get('capacity_loss') is None and
            row.get('recorder_error') is None,
            'physical row131 is not the exact successful current Joern05 terminal')
    groups = [group for group in plan.get('groups', [])
              if type(group) is dict and group.get('id') == GROUP and group.get('tool') == 'joern']
    require(len(groups) == 1, 'normalized current contract lacks one exact Joern108 group')
    group = groups[0]
    case_ids = group.get('case_ids')
    report_specs = group.get('reports')
    require(type(case_ids) is list and len(case_ids) == 108 and
            all(type(value) is str and value for value in case_ids) and
            len(set(case_ids)) == 108 and type(report_specs) is list and
            len(report_specs) == len(report_bindings) == 5,
            'normalized Joern group does not contain the exact five-report/108-case roster')
    flattened: list[str] = []
    checked_reports = []
    for expected, actual in zip(report_specs, report_bindings):
        expected_cases = expected.get('case_ids')
        require(type(expected_cases) is list and expected_cases and
                all(type(value) is str and value for value in expected_cases),
                'normalized Joern report case partition is malformed')
        flattened.extend(expected_cases)
        require(type(actual) is dict and set(actual) == {
            'adapter', 'staged_path', 'sha256', 'rows', 'attempt_id',
            'attempt_number', 'evidence_contract_sha256'},
            'actual Joern report binding fields differ')
        staged = actual.get('staged_path')
        staged_path = PurePosixPath(staged) if type(staged) is str else None
        require(actual.get('adapter') == expected.get('path') and
                type(staged) is str and staged_path is not None and
                not staged_path.is_absolute() and '..' not in staged_path.parts and
                staged_path.as_posix() == staged and
                type(actual.get('sha256')) is str and
                re.fullmatch(r'[0-9a-f]{64}', actual['sha256']) and
                type(actual.get('rows')) is int and actual['rows'] == len(expected_cases) and
                actual.get('attempt_id') == ATTEMPT and
                type(actual.get('attempt_number')) is int and actual['attempt_number'] == 5 and
                actual.get('evidence_contract_sha256') == contract_sha,
                'actual Joern report path/hash/partition/attempt binding differs')
        checked_reports.append({
            'path': expected['path'], 'sha256': actual['sha256'],
            'rows': actual['rows'], 'case_ids': list(expected_cases),
        })
    require(flattened == case_ids and sum(item['rows'] for item in checked_reports) == 108,
            'normalized Joern report partitions do not cover the exact 108 case IDs')
    allowed_outcomes = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}
    require(type(outcomes) is dict and set(outcomes) <= allowed_outcomes and
            all(type(value) is int and value >= 0 for value in outcomes.values()) and
            sum(outcomes.values()) == 108,
            'actual checker returned malformed typed Joern outcome counts')

    require(type(native_acceptance) is dict and
            type(native_acceptance.get('eligible_plan')) is dict and
            type(native_acceptance.get('qualification')) is dict,
            'accepted post-capture qualification evidence is required')
    native_plan = native_acceptance['eligible_plan']
    qualification = native_acceptance['qualification']
    require(native_plan.get('status') == 'execution-eligible' and
            native_plan.get('execution_eligible') is True and
            native_plan.get('diagnostic_execution_eligible') is True and
            native_plan.get('full_model_qualification') is False and
            native_plan.get('scored_activation') is False and
            type(native_plan.get('identity')) is dict and
            native_plan['identity'].get('tool_version') == '4.0.660' and
            native_plan.get('fresh_qualification') ==
            native_acceptance.get('finalization', {}).get('qualification_receipt') and
            qualification.get('control_run') ==
            native_acceptance.get('diagnostic_review', {}).get('control_run') and
            qualification.get('diagnostic_admission_review') ==
            native_acceptance.get('diagnostic_review_ref'),
            'current native qualification identity is not the exact accepted semantic-only result')
    native_capture = qualification.get('native_capture')
    require(type(native_capture) is dict and native_capture.get('control_arms') == 12 and
            native_capture.get('phase_invocations') == 36 and
            native_capture.get('full_model_qualification') is False and
            native_capture.get('scored_activation') is False,
            'current native qualification receipt lost its 12-arm/36-phase semantic boundary')
    return {
        'status': 'joern108-operationally-complete',
        'group_id': GROUP,
        'attempt_id': ATTEMPT,
        'physical_ledger_row': 131,
        'global_attempt_number': tail_proof['global_attempt_number'],
        'source_commit': source_commit,
        'plan_commit': plan_commit,
        'contract_sha256': contract_sha,
        'case_count': 108,
        'report_count': 5,
        'reports': checked_reports,
        'typed_outcomes': dict(sorted(outcomes.items())),
        'eligible_plan': native_acceptance['eligible_plan_ref'],
        'qualification_receipt': native_plan['fresh_qualification'],
        'current_target_full': False,
        'configuration_ready': False,
        'full_model_qualification': False,
        'scored_activation': False,
        'publication_approved': False,
    }

def contract_delta_from_review(root: Path, old: dict[str, Any], new: dict[str, Any], review_ref: dict[str, str]) -> None:
    """Bind reviewed argv/env/observer/source inputs, not an untrusted group map.

    No actual review of this shape exists yet. Its absence is intentional and
    blocks prospective source integration; tests use isolated synthetic docs.
    """
    review = document(root, review_ref)
    require(set(review) == {'schema', 'status', 'automatic_retry', 'predecessor_contract', 'joern_group', 'additional_source_inputs'}, 'group review fields differ')
    require(review['schema'] == 'v092-joern05-group-contract-review/v1' and review['status'] == 'approved-for-contract-only' and (review['automatic_retry'] is False), 'group contract review is not approved')
    require(review['predecessor_contract'] == inherited_core(root)['contract'], 'group review predecessor differs')
    additions = review['additional_source_inputs']
    require(new['source_inputs'] == source_roster(root, additions), 'group reviewed source closure differs')
    contract_delta(old, new, review['joern_group'])


def _hex(value: object, length: int, label: str) -> None:
    import re
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{%d}' % length, value), label + ' malformed')


def _relative(value: str, label: str):
    from pathlib import PurePosixPath
    require(isinstance(value, str), label + ' malformed')
    path = PurePosixPath(value)
    require(bool(value) and not path.is_absolute() and '..' not in path.parts and str(path) == value,
            label + ' escapes canonical relative namespace')
    return path


def _terminal_identity(value: dict[str, Any], *, group_id: str, attempt_id: str,
                       source_commit: str, plan_commit: str, contract_sha256: str,
                       execution_series: int, label: str) -> None:
    """Accept a truthful terminal row, never a capacity/integrity/recorder error."""
    _hex(source_commit, 40, f"{label} source")
    _hex(plan_commit, 40, f"{label} plan")
    _hex(contract_sha256, 64, f"{label} contract")
    status = value.get("status")
    code = value.get("exit_code")
    require(status in {"completed", "failed", "timed-out"} and type(code) is int and
            ((status == "completed" and code == 0 and value.get("timed_out") is False) or
             (status == "failed" and code != 0 and value.get("timed_out") is False) or
             (status == "timed-out" and code == 124 and value.get("timed_out") is True)) and
            value.get("capacity_loss") is None and not value.get("disk_guard_error") and
            not value.get("recorder_error") and value.get("tool") == "joern" and
            value.get("group_id") == group_id and value.get("attempt_id") == attempt_id and
            value.get("source_commit") == source_commit and value.get("plan_commit") == plan_commit and
            value.get("contract_sha256") == contract_sha256 and
            value.get("execution_series") == execution_series,
            f"{label} is not a contained ordinary terminal attempt")
    ownership = value.get("process_ownership")
    require(isinstance(ownership, dict) and
            ownership.get("cleanup_status") == "tracked-processes-stopped" and
            not ownership.get("cleanup_error") and not ownership.get("tracking_error") and
            type(ownership.get("root_pid")) is int and ownership["root_pid"] > 0 and
            isinstance(ownership.get("tracked_processes"), list) and ownership["tracked_processes"],
            f"{label} has no complete exact-birth process containment")
    tracked = ownership["tracked_processes"]
    require(ownership.get("schema") == "invocation-process-ownership/v1" and
            ownership.get("descendant_containment") == "unproven" and
            ownership.get("tracking_interval_seconds") == 2.0 and
            all(isinstance(item, dict) and set(item) == {"pid", "start_identity"} and
                type(item["pid"]) is int and item["pid"] > 0 and
                isinstance(item["start_identity"], str) and item["start_identity"] for item in tracked) and
            len({item["pid"] for item in tracked}) == len(tracked) and
            ownership["root_pid"] in {item["pid"] for item in tracked},
            f"{label} exact tracked process roster is incomplete or relabeled")

