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
        mutable = {'maximum_attempts', 'argv', 'environment', 'reports'}
        require(all((before[key] == after[key] for key in set(before) - mutable)), 'unreviewed Joern group field changed')
        for (before_report, after_report) in zip(before['reports'], after['reports']):
            require(set(before_report) == set(after_report), 'Joern report fields changed')
            require(all((before_report[key] == after_report[key] for key in set(before_report) - {'source_path'})), 'Joern report partition changed')
            require(isinstance(after_report.get('source_path'), str) and bool(after_report['source_path']), 'reviewed report source path missing')
    before_inputs = {r['path']: r for r in old['source_inputs']}
    after_inputs = {r['path']: r for r in new['source_inputs']}
    require(len(after_inputs) == len(new['source_inputs']) and all((after_inputs.get(path) == record for (path, record) in before_inputs.items())), 'inherited source input replaced or dropped')

def require_terminal_tail(rows: list[dict[str, Any]], current: dict[str, Any]) -> None:
    require(len(rows) in (109, 110), 'only zero or one Joern terminal tail allowed')
    if len(rows) == 109:
        return
    row = rows[-1]
    require(row.get('group_id') == GROUP and row.get('attempt_id') == ATTEMPT, 'unexpected tail attempt')
    require(row.get('contract_sha256') == current['contract']['sha256'] and row.get('source_commit') == current['source_commit'] and (row.get('plan_commit') == current['plan_commit']), 'tail context changed')
    require(row.get('status') in {'completed', 'failed', 'timed-out', 'capacity-lost', 'recorder-error'}, 'tail is not an actual terminal')

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

