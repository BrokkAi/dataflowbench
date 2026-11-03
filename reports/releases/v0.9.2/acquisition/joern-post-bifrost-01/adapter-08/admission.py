"""Production markers and actual inherited runner acquisition gate."""
from __future__ import annotations
import contextlib
import os
from pathlib import Path
from typing import Any
from packet import ROOT as PACKET_ROOT, missing_prerequisites, read_ref, require
from protocol import EXPERIMENT_ENV, FIXTURE_ENV, GROUP

NATIVE_DECISION_SCHEMA = 'v092-joern05-native-execution-decision-review/v1'
NATIVE_DECISION_STATUS = 'approved-for-single-group-semantic-execution-only'
NATIVE_BINDING_REFS = (
    'native_control_request', 'native_invocation_review', 'native_parent_started',
    'native_worker_invocation', 'native_exit', 'native_control_result',
    'native_startup_sidecar_manifest', 'native_capture_review',
    'native_finalization_receipt', 'native_finalizer_diagnostic_review',
    'eligible_joern_plan', 'current_core', 'current_manifest', 'current_contract',
)
SEMANTIC_SCOPE = {
    'evaluation_scope': 'semantic-only',
    'uncontended_timing_certified': False,
    'relative_performance_conclusions_authorized': False,
    'publication_hold': True,
    'full_model_qualification': False,
    'scored_activation': False,
    'publication_approved': False,
    'official_semantic_run_conditionally_approved': True,
}
ELIGIBLE_RUNNER_ROLE = 'nested_037_joern_normal_runner_v092_repair_pinned'
DIAGNOSTIC_ADMISSION_ROLE = 'local_005_joern_diagnostic_admission_v092'
HISTORICAL_EXECUTION_PLAN_PATH = 'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json'


@contextlib.contextmanager
def _eligible_plan_validation_scope(root: Path, plan_ref: dict[str, str], runner: Any,
                                    *, graph: Any, runner_role: str,
                                    runner_ref: dict[str, str], diagnostic_role: str,
                                    diagnostic_ref: dict[str, str]):
    """Expose the bound current plan only to its graph-pinned runner validator.

    The pinned diagnostic reviewer independently checks a preserved historical
    archive whose plan path is the immutable plan-v092-01 path.  Its original
    function is wrapped only for this exact graph call, and sees the historical
    constant while it runs.  All other roots/plans/controls escape closed.
    """
    import copy
    from packet import document
    from stage_runtime import _pinned_member

    root = Path(root).resolve()
    require(root == Path(PACKET_ROOT).resolve(),
            'eligible plan scope root differs from the pinned repository')
    require(runner_role == ELIGIBLE_RUNNER_ROLE,
            'eligible plan scope runner role differs')
    require(diagnostic_role == DIAGNOSTIC_ADMISSION_ROLE,
            'eligible plan scope diagnostic role differs')
    pinned_runner = _pinned_member(root, graph, runner_role, runner_ref)
    diagnostic = _pinned_member(root, graph, diagnostic_role, diagnostic_ref)
    require(pinned_runner is runner and getattr(runner, '__graph_role__', None) == runner_role,
            'eligible plan validator is not the exact graph-owned runner object')
    require(getattr(diagnostic, '__graph_role__', None) == diagnostic_role,
            'diagnostic admission validator is not the exact graph-owned object')
    require(hasattr(diagnostic, 'validate_control_plan_admission') and
            callable(diagnostic.validate_control_plan_admission),
            'graph-owned diagnostic admission function is missing')

    plan_raw = read_ref(root, plan_ref)
    bound_plan = document(root, plan_ref)
    require(type(bound_plan) is dict and bound_plan.get('status') == 'execution-eligible' and
            bound_plan.get('execution_eligible') is True and
            bound_plan.get('full_model_qualification') is False and
            bound_plan.get('scored_activation') is False,
            'bound current eligible plan has an unsupported scope')
    control_ref = bound_plan.get('qualification_control_plan')
    require(type(control_ref) is dict and set(control_ref) == {'path', 'sha256'},
            'current eligible plan control ref is malformed')
    control_raw = read_ref(root, control_ref)
    bound_control = document(root, control_ref)

    old_plan_path = getattr(runner, 'EXECUTION_PLAN_PATH', None)
    require(old_plan_path == HISTORICAL_EXECUTION_PLAN_PATH,
            'graph-owned runner historical plan constant changed before scope')
    eligible_path = plan_ref.get('path')
    require(type(eligible_path) is str and eligible_path and
            eligible_path != HISTORICAL_EXECUTION_PLAN_PATH,
            'eligible plan must be a separately bound successor path')
    original_diagnostic = diagnostic.validate_control_plan_admission

    def historical_archive_gate(call_root: Path, plan: dict, control: dict) -> dict:
        call_root = Path(call_root).resolve()
        require(call_root == root and plan == bound_plan and control == bound_control,
                'diagnostic admission scope escaped exact root/plan/control bytes')
        require(read_ref(root, plan_ref) == plan_raw and
                read_ref(root, control_ref) == control_raw,
                'eligible plan or control bytes changed inside validation scope')
        require(getattr(runner, 'EXECUTION_PLAN_PATH', None) == eligible_path,
                'diagnostic admission scope escaped eligible runner path')
        runner.EXECUTION_PLAN_PATH = old_plan_path
        try:
            result = original_diagnostic(call_root, plan, control)
        finally:
            # The old value is exposed only to the original historical archive
            # gate; do not leave it active for current plan processing.
            changed = getattr(runner, 'EXECUTION_PLAN_PATH', None) != old_plan_path
            runner.EXECUTION_PLAN_PATH = eligible_path
            require(not changed,
                    'historical diagnostic changed the pinned runner path')
        return result

    runner.EXECUTION_PLAN_PATH = eligible_path
    diagnostic.validate_control_plan_admission = historical_archive_gate
    try:
        yield
    finally:
        # Restore only the objects/values this scope installed.  Unexpected
        # mutation is an error and is never silently accepted as authority.
        diagnostic_changed = diagnostic.validate_control_plan_admission is not historical_archive_gate
        runner_changed = getattr(runner, 'EXECUTION_PLAN_PATH', None) != eligible_path
        graph_runner_changed = graph.module(runner_role) is not runner
        graph_diagnostic_changed = graph.module(diagnostic_role) is not diagnostic
        diagnostic.validate_control_plan_admission = original_diagnostic
        runner.EXECUTION_PLAN_PATH = old_plan_path
        require(not diagnostic_changed and not runner_changed and
                not graph_runner_changed and not graph_diagnostic_changed,
                'eligible plan scope globals changed before identity-safe restore')


def validate_native_execution_decision(root: Path, refs: dict[str, Any],
                                        current: dict[str, Any]) -> dict[str, Any]:
    """Bind accepted capture/finalization evidence to the conditional decision.

    The decision is not itself sufficient to launch: the external review,
    current graph, eligible runner plan, and fresh runtime admission remain
    independent required gates.
    """
    from packet import document
    import re

    decision = document(root, refs['native_decision_review'])
    require(type(decision) is dict and set(decision) == {
        'schema', 'status', 'automatic_retry', 'bindings', 'scope'},
        'native execution decision fields differ')
    require(decision.get('schema') == NATIVE_DECISION_SCHEMA and
            decision.get('status') == NATIVE_DECISION_STATUS and
            decision.get('automatic_retry') is False,
            'native execution decision is not approved for the exact semantic-only scope')
    bindings = decision.get('bindings')
    expected_binding_keys = {*NATIVE_BINDING_REFS, 'source_commit', 'plan_commit',
                             'current_target_full'}
    require(type(bindings) is dict and set(bindings) == expected_binding_keys,
            'native execution decision binding set differs')
    require(all(bindings.get(name) == refs.get(name) for name in NATIVE_BINDING_REFS),
            'native execution decision artifact refs differ')
    for name in ('source_commit', 'plan_commit'):
        value = bindings.get(name)
        require(type(value) is str and re.fullmatch(r'[0-9a-f]{40}', value),
                'native execution decision ' + name + ' is not a full commit SHA')
        require(value == current.get(name),
                'native execution decision ' + name + ' differs from current core')
    require(bindings.get('current_target_full') is False and
            decision.get('scope') == SEMANTIC_SCOPE,
            'native execution decision overstates target, scoring, timing, or publication scope')

    capture = document(root, refs['native_capture_review'])
    require(capture.get('schema') == 'v092-native-capture-independent-review/v1' and
            capture.get('status') == 'approved-for-post-capture-diagnostic-replay-only' and
            capture.get('full_model_qualification') is False and
            capture.get('scored_activation') is False and
            capture.get('publication_approved') is False and
            capture.get('publication_hold') is True,
            'native capture review lacks replay-only approval or publication hold')
    capture_bindings = capture.get('bindings')
    expected_capture = {
        'request': refs['native_control_request'],
        'invocation_review': refs['native_invocation_review'],
        'native_parent_started': refs['native_parent_started'],
        'worker_invocation': refs['native_worker_invocation'],
        'native_exit': refs['native_exit'],
        'control_result': refs['native_control_result'],
        'startup_sidecar_manifest': refs['native_startup_sidecar_manifest'],
    }
    require(type(capture_bindings) is dict and
            all(capture_bindings.get(key) == value
                for key, value in expected_capture.items()) and
            capture_bindings.get('startup_sidecar_manifest_sha256') ==
            refs['native_startup_sidecar_manifest']['sha256'],
            'native capture review does not bind all exact native inputs')

    native_exit = document(root, refs['native_exit'])
    exit_result = native_exit.get('result')
    require(native_exit.get('request') == refs['native_control_request'] and
            native_exit.get('ledger_unchanged') is True and
            native_exit.get('automatic_retry') is False and
            type(exit_result) is dict and exit_result.get('status') == 'process-returned' and
            type(exit_result.get('exit_code')) is int and exit_result['exit_code'] == 0 and
            exit_result.get('failure') is None and
            all(exit_result.get(k) == v for k, v in {
                'evaluation_scope': 'semantic-only',
                'uncontended_timing_certified': False,
                'relative_performance_conclusions_authorized': False,
            }.items()),
            'native wrapper exit does not bind an actual successful semantic-only return')
    phases = exit_result.get('phases')
    require(type(phases) is list and len(phases) == 3 and
            [item.get('phase') for item in phases if type(item) is dict] ==
            ['ready', 'controls-started', 'controls-returned'],
            'native wrapper did not return from controls')

    control = document(root, refs['native_control_result'])
    run = control.get('run')
    startup = control.get('startup_observation')
    require(control.get('request') == refs['native_control_request'] and
            type(run) is dict and run.get('identity') ==
            document(root, refs['eligible_joern_plan']).get('identity') and
            type(run.get('records')) is list and len(run['records']) == 12 and
            type(run.get('phase_invocation_count')) is int and
            run['phase_invocation_count'] == 36 and
            type(startup) is dict and startup.get('qualification_safe') is True,
            'native control result lacks the exact 12-arm/36-phase safe-startup capture')

    finalization = document(root, refs['native_finalization_receipt'])
    expected_finalization = {
        'schema': 'v092-joern-post-capture-finalization/v1',
        'status': 'diagnostic-replay-complete-publication-held',
        'request': refs['native_control_request'],
        'invocation_review': refs['native_invocation_review'],
        'native_parent_started': refs['native_parent_started'],
        'worker_invocation': refs['native_worker_invocation'],
        'native_exit': refs['native_exit'],
        'control_result': refs['native_control_result'],
        'capture_review': refs['native_capture_review'],
        'startup_sidecar_manifest': refs['native_startup_sidecar_manifest'],
        'diagnostic_review': refs['native_finalizer_diagnostic_review'],
        'eligible_plan': refs['eligible_joern_plan'],
        'control_arms': 12,
        'phase_invocations': 36,
        'full_model_qualification': False,
        'scored_activation': False,
        'publication_approved': False,
        'analyzer_invoked_by_finalizer': False,
    }
    require(all(finalization.get(k) == v for k, v in expected_finalization.items()) and
            all(finalization.get(k) == v for k, v in {
                'evaluation_scope': 'semantic-only',
                'uncontended_timing_certified': False,
                'relative_performance_conclusions_authorized': False,
            }.items()),
            'native post-capture finalization receipt differs from accepted evidence')
    diagnostic = document(root, refs['native_finalizer_diagnostic_review'])
    qualification = document(root, finalization.get('qualification_receipt', {}))
    require(diagnostic.get('status') == 'measurement-with-known-limits' and
            diagnostic.get('full_model_qualification') is False and
            diagnostic.get('scored_activation') is False and
            diagnostic.get('diagnostic_execution_eligible') is True and
            diagnostic.get('control_run') == qualification.get('control_run') and
            qualification.get('diagnostic_admission_review') ==
            refs['native_finalizer_diagnostic_review'],
            'native finalizer diagnostic review is not the accepted known-limits replay')
    plan = document(root, refs['eligible_joern_plan'])
    require(plan.get('status') == 'execution-eligible' and
            plan.get('execution_eligible') is True and
            plan.get('diagnostic_execution_eligible') is True and
            plan.get('full_model_qualification') is False and
            plan.get('scored_activation') is False and
            plan.get('fresh_qualification') == finalization.get('qualification_receipt'),
            'post-capture eligible plan does not preserve its diagnostic-only qualification')
    return {
        'decision': decision,
        'finalization': finalization,
        'diagnostic_review': diagnostic,
        'diagnostic_review_ref': refs['native_finalizer_diagnostic_review'],
        'eligible_plan': plan,
        'eligible_plan_ref': refs['eligible_joern_plan'],
        'qualification': qualification,
    }

def require_markers(environment: dict[str, str]) -> None:
    require(environment.get(EXPERIMENT_ENV) == '1', 'current outer marker missing')
    require(environment.get(FIXTURE_ENV) != '1', 'fixture marker forbidden in production')
    require(environment.get('DATAFLOWBENCH_V092_RELEASE_EXECUTION') == '1' and environment.get('DATAFLOWBENCH_V092_GROUP_ID') == GROUP, 'inner runner markers differ')

def validate_prerequisites(root: Path, refs: dict[str, Any], runner: Any,
                           eligible_plan_path: str, *, graph: Any,
                           runner_role: str, runner_ref: dict[str, str],
                           diagnostic_ref: dict[str, str],
                           purpose: str='execution') -> tuple[Any, Any, Any]:
    missing = missing_prerequisites(root, refs, purpose=purpose)
    require(not missing, 'missing actual artifacts: ' + ','.join(missing))
    from packet import document
    current = document(root, refs['current_core'])
    manifest = document(root, refs['current_manifest'])
    review = document(root, refs['external_launch_review']) if purpose == 'execution' else None
    require(manifest['core_identity'] == refs['current_core'] and current['contract'] == refs['current_contract'] and (current['source_evidence'] == refs['current_source_evidence']), 'current manifest/core/source refs differ')
    if purpose == 'execution':
        require(review.get('status') == 'approved' and review.get('automatic_retry') is False, 'actual external execution review is not approved')
        bindings = review.get('bindings', {})
        require(bindings.get('manifest_sha256') == refs['current_manifest']['sha256'] and bindings.get('core_identity_sha256') == refs['current_core']['sha256'] and (bindings.get('contract_sha256') == current['contract']['sha256']) and (bindings.get('source_commit') == current['source_commit']) and (bindings.get('plan_commit') == current['plan_commit']), 'external execution review identity differs')
    require(eligible_plan_path == refs['eligible_joern_plan']['path'], 'eligible plan ref/path differs')
    with _eligible_plan_validation_scope(
            root, refs['eligible_joern_plan'], runner, graph=graph,
            runner_role=runner_role, runner_ref=runner_ref,
            diagnostic_role=DIAGNOSTIC_ADMISSION_ROLE,
            diagnostic_ref=diagnostic_ref):
        (plan, evidence, context) = runner.validate_plan(root, eligible_plan_path)
    eligible = document(root, refs['eligible_joern_plan'])
    require(plan == eligible, 'actual runner plan differs from the bound eligible-plan bytes')
    require(plan.get('execution_eligible') is True and plan.get('status') == 'execution-eligible', 'Joern plan is not eligible')
    require(evidence, 'actual accepted qualification evidence required')
    require(plan.get('full_model_qualification') is False and
            plan.get('scored_activation') is False,
            'native post-capture plan exceeds semantic-only qualification scope')
    validate_native_execution_decision(root, refs, current)
    if purpose == 'execution':
        require_markers(dict(os.environ))
        runner._require_launch_guard(GROUP)
    return (plan, evidence, context)

def child_environment(reviewed_group: dict[str, Any]) -> dict[str, str]:
    """Compose only reviewed group env and required outer/inner guard markers.

    Observer argv/JAVA opts must already be in the exact hash-bound reviewed
    group. This helper does not infer or add a pending observer policy.
    """
    environment = reviewed_group.get('environment')
    require(isinstance(environment, dict) and 'PATH' in environment and all((isinstance(k, str) and isinstance(v, str) for (k, v) in environment.items())), 'complete reviewed group environment required')
    result = dict(environment)
    require(result.get(FIXTURE_ENV) != '1', 'reviewed fixture marker forbidden')
    result.update({EXPERIMENT_ENV: '1', 'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1', 'DATAFLOWBENCH_V092_GROUP_ID': GROUP})
    require_markers(result)
    return result

def eligible_plan_scope(executor: Any, root: Path, reviewed_group: dict[str, Any], plan_ref: dict[str, str], runner: Any, *, graph: Any, runner_role: str, runner_ref: dict[str, str], diagnostic_ref: dict[str, str]):
    """Exact successor-plan boundary; actual runner acquisition gate still runs."""
    import contextlib
    import json
    from packet import read_ref, digest

    @contextlib.contextmanager
    def scope():
        with _eligible_plan_validation_scope(
                root, plan_ref, runner, graph=graph, runner_role=runner_role,
                runner_ref=runner_ref, diagnostic_role=DIAGNOSTIC_ADMISSION_ROLE,
                diagnostic_ref=diagnostic_ref):
            raw = read_ref(root, plan_ref)
            bound = json.loads(raw)
            argv = reviewed_group['argv']
            flags = [i for (i, x) in enumerate(argv) if x == '--plan']
            require(len(flags) == 1 and flags[0] + 1 < len(argv) and (argv[flags[0] + 1] == plan_ref['path']), 'Joern argv/eligible plan differ')
            (actual, evidence, _) = runner.validate_plan(root, plan_ref['path'])
            require(actual == bound and evidence and (actual.get('execution_eligible') is True) and (actual.get('status') == 'execution-eligible'), 'actual eligible plan gate failed')
            original = executor._validate_joern_common_plan
            projected = dict(reviewed_group, maximum_attempts=2)

            def validate(group, repo):
                require(group == projected and Path(repo).resolve() == root.resolve(), 'Joern plan scope escaped reviewed group/root')
                require(read_ref(root, plan_ref) == raw, 'eligible plan changed')
                return (plan_ref['path'], digest(raw))
            executor._validate_joern_common_plan = validate
            try:
                yield
            finally:
                executor._validate_joern_common_plan = original
    return scope()


def validate_execution_authority(root: Path, core: dict[str, Any], manifest_ref: dict,
                                 *, graph: Any) -> dict[str, Any]:
    """Validate derived existing authority; this function never writes a grant."""
    from packet import document
    refs = core['prerequisite_refs']
    require_markers(dict(os.environ))
    runner = graph.module(core['joern_runner_role'])
    validate_prerequisites(
        root, refs, runner, refs['eligible_joern_plan']['path'],
        graph=graph, runner_role=core['joern_runner_role'],
        runner_ref=core['joern_runner_source'],
        diagnostic_ref=core['runtime_module_graph'][DIAGNOSTIC_ADMISSION_ROLE],
        purpose='execution')
    require(refs['current_manifest'] == manifest_ref, 'execution manifest differs')
    require('authorization_bundle' in refs, 'actual derived authorization bundle missing')
    bundle = document(root, refs['authorization_bundle'])
    require(bundle.get('schema') == 'v092-bifrost-v0140-batch-authorization/v1' and
            bundle.get('status') == 'approved' and bundle.get('automatic_retry') is False,
            'derived authorization bundle not approved')
    require(set(bundle.get('groups', {})) == {GROUP}, 'authority is not singleton Joern05')
    review = document(root, refs['external_launch_review'])
    require(review.get('bindings', {}).get('authorization_bundle_sha256') ==
            refs['authorization_bundle']['sha256'], 'external review does not bind authority bundle')
    scope = document(root, bundle['experiment_authorization'])
    require(scope.get('publication_hold') is True,
            'execution authority must preserve publication hold')
    for name, scope_name in (('parent', 'parent'), ('group', 'group')):
        ref = bundle['parent'] if name == 'parent' else bundle['groups'][GROUP]
        value = document(root, ref)
        require(value.get('schema') == 'v092-bifrost-v0140-experiment-authorization/v2' and
                value.get('status') == 'approved' and value.get('human_approved') is True and
                value.get('automatic_retry') is False and value.get('scope') == scope_name,
                'derived authorization payload differs')
        require(value.get('manifest_path') == manifest_ref['path'] and
                value.get('manifest_sha256') == manifest_ref['sha256'] and
                value.get('core_identity') == core['core_identity'] and
                value.get('contract_sha256') == core['contract']['sha256'] and
                value.get('source_commit') == core['source_commit'] and
                value.get('plan_commit') == core['plan_commit'], 'authority context differs')
        require(value.get('group_roster') == [GROUP] and
                value.get('attempt_roster') == {GROUP: GROUP + '-attempt-05-series-02'} and
                value.get('attempt_limits') == {GROUP: 5}, 'authority counters differ')
        require(value.get('hold_supersession') == bundle['experiment_authorization'],
                'authority does not bind reviewed scope amendment')
        require(value.get('original_clock') == {
            'origin_utc': '2026-10-20T00:57:00.680937+00:00',
            'cutoff_utc': None, 'total_wall_budget_seconds': None}, 'authority resets original clock')
        require(value.get('admission_source') == core['adapter_module_refs']['joern05_admission'] and
                value.get('supervisor_source') == core['adapter_module_refs']['joern05_supervisor'],
                'authority source bindings differ')
    return bundle
