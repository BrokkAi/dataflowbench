"""Production markers and actual inherited runner acquisition gate."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from packet import missing_prerequisites, require
from protocol import EXPERIMENT_ENV, FIXTURE_ENV, GROUP

def require_markers(environment: dict[str, str]) -> None:
    require(environment.get(EXPERIMENT_ENV) == '1', 'current outer marker missing')
    require(environment.get(FIXTURE_ENV) != '1', 'fixture marker forbidden in production')
    require(environment.get('DATAFLOWBENCH_V092_RELEASE_EXECUTION') == '1' and environment.get('DATAFLOWBENCH_V092_GROUP_ID') == GROUP, 'inner runner markers differ')

def validate_prerequisites(root: Path, refs: dict[str, Any], runner: Any, eligible_plan_path: str, *, purpose: str='execution') -> tuple[Any, Any, Any]:
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
    (plan, evidence, context) = runner.validate_plan(root, eligible_plan_path)
    require(plan.get('execution_eligible') is True and plan.get('status') == 'execution-eligible', 'Joern plan is not eligible')
    require(evidence, 'actual accepted qualification evidence required')
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

def eligible_plan_scope(executor: Any, root: Path, reviewed_group: dict[str, Any], plan_ref: dict[str, str], runner: Any, *, graph: Any, runner_role: str, runner_ref: dict[str, str]):
    """Exact successor-plan boundary; actual runner acquisition gate still runs."""
    import contextlib
    import json
    from packet import read_ref, digest
    from stage_runtime import _pinned_member

    @contextlib.contextmanager
    def scope():
        require(_pinned_member(root, graph, runner_role, runner_ref) is runner, 'eligible plan validator is not exact graph runner')
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
    validate_prerequisites(root, refs, runner, refs['eligible_joern_plan']['path'],
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
