"""Scoped parser projection; actual frozen validators remain the authority.

This is the new-contract parser boundary, not complete historical replay. The
immutable BF24 stage11 cannot be called with a new HEAD/core without an explicit
historical-origin normalization successor. Missing that actual integration must
remain a qualification blocker rather than a serialized context workaround.
"""
from __future__ import annotations
import contextlib
import copy
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterator
from packet import digest, require
from protocol import GROUP

def _lower_sha256(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64 and
            all(character in '0123456789abcdef' for character in value))

@contextlib.contextmanager
def parser_scope(executor: Any, root: Path, contract_ref: dict[str, str], actual_plan: dict[str, Any], actual_raw: bytes) -> Iterator[dict[str, Any]]:
    """Project only known unsupported caps in-memory, restore on every exit.

    Other BF24 qualification/population/resource/noexpiry adapters must already
    be graph-owned and active around this scope. This scope neither installs
    them nor supplies invented recovery/qualification objects.
    """
    require(digest(actual_raw) == contract_ref['sha256'], 'actual contract bytes differ')
    require(json.loads(actual_raw) == actual_plan, 'actual plan differs from bound raw contract')
    require(actual_plan.get('resource_guards') == {'stop_free_gib': 48, 'working_set_gib': 30}, 'actual30/48 guards required')
    projected = copy.deepcopy(actual_plan)
    expected = {GROUP: 5, 'bifrost-c-kernel': 3, 'bifrost-smoke': 3}
    for group in projected['groups']:
        if group['id'] in expected:
            require(type(group.get('maximum_attempts')) is int and group['maximum_attempts'] == expected[group['id']], 'actual attempt cap differs')
            group['maximum_attempts'] = 2
    require(set(expected) <= {g['id'] for g in projected['groups']}, 'projected cap group missing')
    original_path = executor.V4_CONTRACT_PATH
    original_read = executor._read_json
    original_population = executor._population
    path = (root / contract_ref['path']).resolve()

    def read(candidate: Path, label: str):
        if Path(candidate).resolve() == path:
            return (projected, actual_raw)
        return original_read(candidate, label)

    def population(plan: dict[str, Any], selected_path: Path):
        require(plan is projected and Path(selected_path).resolve() == path, 'population scope escaped exact projected contract')
        canonical_path = root / 'reports/releases/v0.9.2/execution-v4/contract.json'
        return original_population(plan, canonical_path)
    executor._population = population
    executor.V4_CONTRACT_PATH = PurePosixPath(contract_ref['path'])
    executor._read_json = read
    try:
        yield projected
    finally:
        executor._read_json = original_read
        executor._population = original_population
        executor.V4_CONTRACT_PATH = original_path

def validate_current(executor: Any, root: Path, contract_ref: dict[str, str], actual_plan: dict[str, Any], actual_raw: bytes) -> dict[str, Any]:
    """Call actual validate_plan, then restore exact returned caps/plan identity."""
    with parser_scope(executor, root, contract_ref, actual_plan, actual_raw) as projected:
        expected_parser_plan = copy.deepcopy(projected)
        normalized = executor.validate_plan(root / contract_ref['path'], repo_root=root)
    require(normalized['bytes_sha256'] == contract_ref['sha256'], 'normalized contract differs')
    require(normalized['plan'] == expected_parser_plan, 'unexpected parser result')
    normalized['plan'] = copy.deepcopy(actual_plan)
    caps = {g['id']: g['maximum_attempts'] for g in actual_plan['groups']}
    for group in normalized['groups']:
        group['maximum_attempts'] = caps[group['id']]
    return normalized

def require_current_head(root: Path, core: dict[str, Any], git: Any) -> None:
    require(git(root, 'rev-parse', 'HEAD') == core['plan_commit'], 'new executable plan must equal HEAD')

def verify_runtime_context_bindings(root: Path, contexts: dict[str, Any], current: dict[str, Any] | None=None) -> None:
    """Check actual normalized objects against every exact bound origin.

    This checker never manufactures normalized contexts. Production historical
    reconstruction must supply graph-owned actual validator results; a metadata
    descriptor alone cannot pass the normalized-plan identity checks.
    """
    from history import context_bindings
    entries = context_bindings(root)
    expected_keys = set(entries)
    if current is not None:
        require(set(current) == {'contract', 'source_commit', 'plan_commit', 'source_evidence'},
                'current context exact fields required')
        current_key = current['contract'].get('sha256')
        require(isinstance(current_key, str) and current_key not in expected_keys,
                'current source context collides with a sealed109 origin')
        expected_keys.add(current_key)
    require(set(contexts) == expected_keys, 'normalized context roster differs')
    for (key, entry) in entries.items():
        value = contexts[key]
        normalized = value.get('validated')
        require(isinstance(normalized, dict) and normalized.get('bytes_sha256') == key, 'actual normalized contract identity missing')
        require(normalized.get('plan', {}).get('source_commit') == entry['source_commit'] and value.get('source_commit') == entry['source_commit'] and (value.get('plan_commit') == entry['plan_commit']), 'normalized historical source/plan relabeled')
    if current is not None:
        value = contexts[current_key]
        normalized = value.get('validated')
        require(isinstance(normalized, dict) and
                normalized.get('bytes_sha256') == current_key and
                value.get('source_commit') == current['source_commit'] and
                value.get('plan_commit') == current['plan_commit'] and
                normalized.get('plan', {}).get('source_commit') == current['source_commit'],
                'current normalized context differs from its separate S/P identity')

def _pinned_member(root: Path, graph: Any, role: str, ref: dict[str, str]) -> Any:
    """Bind one role by name, bytes and object; same-path aliases stay distinct."""
    from packet import read_ref
    read_ref(root, ref)
    members = [m for m in graph.members if m.name == role]
    require(len(members) == 1, 'graph role absent or duplicate: ' + role)
    member = members[0]
    require(member.canonical_path == ref['path'] and member.source_sha256 == ref['sha256'], 'graph source identity changed: ' + role)
    value = graph.module(role)
    require(value is member.module_object, 'graph object identity changed: ' + role)
    graph.assert_member(role, value)
    return value


def current_source_input_closure(core: dict[str, Any], historical_core: dict[str, Any],
                                 resolved_inputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind the exact resolver output and the graph-owned objects that produced it."""
    from packet import canonical
    graph_refs = core.get('runtime_module_graph')
    require(isinstance(graph_refs, dict),
            'current source resolver graph refs are missing')
    require(isinstance(graph_refs, dict) and
            isinstance(graph_refs.get('executor'), dict) and
            isinstance(graph_refs.get('stage_runtime11'), dict),
            'current source resolver graph refs are incomplete')
    require(isinstance(resolved_inputs, list) and resolved_inputs and
            all(isinstance(item, dict) and
                set(item) == {'path', 'sha256', 'role'} and
                isinstance(item.get('path'), str) and item['path'] and
                _lower_sha256(item.get('sha256')) and
                isinstance(item.get('role'), str) and item['role']
                for item in resolved_inputs),
            'frozen current source resolver returned malformed inputs')
    paths = [item['path'] for item in resolved_inputs]
    require(paths == sorted(set(paths)),
            'frozen current source resolver output is not a unique ordered closure')
    value = {
        'schema': 'v092-joern05-resolved-source-input-closure/v1',
        'source_commit': core['source_commit'],
        'plan_commit': core['plan_commit'],
        'contract': copy.deepcopy(core['contract']),
        'qualification': copy.deepcopy(core['qualification']),
        'historical_contract': copy.deepcopy(historical_core['contract']),
        'executor_module': copy.deepcopy(graph_refs['executor']),
        'stage_runtime_module': copy.deepcopy(graph_refs['stage_runtime11']),
        'source_inputs': copy.deepcopy(resolved_inputs),
        'source_inputs_sha256': digest(canonical(resolved_inputs)),
    }
    return value


def _validate_current_source_input_closure(root: Path, core: dict[str, Any],
                                           normalized: dict[str, Any],
                                           closure: dict[str, Any],
                                           source_by_path: dict[str, dict[str, str]]) -> None:
    from packet import canonical, inherited_core
    required = {
        'schema', 'source_commit', 'plan_commit', 'contract', 'qualification',
        'historical_contract', 'executor_module', 'stage_runtime_module',
        'source_inputs', 'source_inputs_sha256',
    }
    require(isinstance(closure, dict) and set(closure) == required and
            closure.get('schema') == 'v092-joern05-resolved-source-input-closure/v1',
            'graph-owned current source resolver closure is absent or malformed')
    graph_refs = core.get('runtime_module_graph')
    require(isinstance(graph_refs, dict) and
            isinstance(graph_refs.get('executor'), dict) and
            isinstance(graph_refs.get('stage_runtime11'), dict),
            'current source resolver graph refs are malformed')
    require(closure.get('source_commit') == core.get('source_commit') and
            closure.get('plan_commit') == core.get('plan_commit') and
            closure.get('contract') == core.get('contract') and
            closure.get('qualification') == core.get('qualification') and
            closure.get('executor_module') == graph_refs.get('executor') and
            closure.get('stage_runtime_module') == graph_refs.get('stage_runtime11') and
            closure.get('historical_contract') == inherited_core(root).get('contract'),
            'source resolver closure is bound to another core or graph')
    inputs = closure.get('source_inputs')
    require(isinstance(inputs, list) and
            digest(canonical(inputs)) == closure.get('source_inputs_sha256') and
            normalized.get('source_inputs') == inputs,
            'normalized source inputs differ from the exact frozen resolver result')
    refs = []
    seen = set()
    for item in inputs:
        require(isinstance(item, dict) and set(item) == {'path', 'sha256', 'role'} and
                isinstance(item.get('path'), str) and
                _lower_sha256(item.get('sha256')) and
                isinstance(item.get('role'), str),
                'resolved source input has an invalid shape')
        require(item['path'] not in seen, 'resolved source input path is duplicated')
        seen.add(item['path'])
        refs.append({'path': item['path'], 'sha256': item['sha256']})
    require(all(source_by_path.get(item['path']) == item for item in refs),
            'resolved source inputs are not all contained by the complete current CAS')


@contextlib.contextmanager
def current_source_snapshot_scope(executor: Any, root: Path, source_commit: str,
                                  runner_source_sha256: str,
                                  normalized: dict[str, Any],
                                  source_proof: dict[str, Any], *,
                                  current_core: dict[str, Any],
                                  source_input_closure: dict[str, Any],
                                  expected_proof_sha256: str | None = None,
                                  expected_closure_sha256: str | None = None) -> Iterator[None]:
    """Retain frozen source validation while serving exactly 96 CAS archive inputs.

    The frozen guard still checks S ancestry, all ordinary diff/status paths,
    runner bytes, and every direct Git source input. Only the exact raw-member
    refs proven by the current source CAS are omitted from its Git-blob list
    and served by the later frozen ``_source_file`` callback from their
    hash-checked worktree bytes. All other ``_source_file`` calls retain their
    original implementation.
    """
    import copy
    from packet import (ROOT, canonical as packet_canonical, read_ref,
                        attach_cleanup_error)

    require(isinstance(source_commit, str) and len(source_commit) == 40 and
            isinstance(runner_source_sha256, str) and len(runner_source_sha256) == 64,
            'current source snapshot identity is malformed')
    require(current_core.get('source_commit') == source_commit,
            'current source snapshot core differs from S')
    require(isinstance(source_proof, dict) and
            source_proof.get('schema') == 'v092-joern05-current-source-proof/v1' and
            source_proof.get('status') == 'verified' and
            source_proof.get('source_commit') == source_commit,
            'archive-aware current source proof is absent or mismatched')
    proof_sha256 = digest(packet_canonical(source_proof))
    if expected_proof_sha256 is not None:
        require(expected_proof_sha256 == proof_sha256,
                'opaque runtime current source proof changed')
    refs = source_proof.get('source_refs')
    paths = source_proof.get('archived_member_paths')
    archived_refs = source_proof.get('archived_member_refs')
    require(isinstance(refs, list) and digest(packet_canonical(refs)) ==
            source_proof.get('source_refs_sha256') and
            source_proof.get('source_ref_count') == len(refs),
            'archive-aware source refs do not match their proof digest')
    require(isinstance(paths, list) and len(paths) == 96 and
            paths == sorted(set(paths)) and
            isinstance(archived_refs, list) and len(archived_refs) == 96 and
            [item.get('path') for item in archived_refs if isinstance(item, dict)] == paths and
            len([item for item in archived_refs if isinstance(item, dict)]) == 96 and
            all(set(item) == {'path', 'sha256'} and
                _lower_sha256(item.get('sha256'))
                for item in archived_refs),
            'archive-aware raw-member ref set is not the exact96 indexed roster')
    require(Path(root).resolve() == Path(ROOT).resolve(),
            'current source snapshot scope escaped the pinned checkout')
    source_by_path = {item['path']: item for item in refs
                      if isinstance(item, dict) and set(item) == {'path', 'sha256'}}
    require(len(source_by_path) == len(refs) and
            all(source_by_path.get(item['path']) == item for item in archived_refs),
            'archive-member refs are outside the exact source-ref closure')
    _validate_current_source_input_closure(
        root, current_core, normalized, source_input_closure, source_by_path)
    closure_sha256 = digest(packet_canonical(source_input_closure))
    if expected_closure_sha256 is not None:
        require(expected_closure_sha256 == closure_sha256,
                'opaque runtime current source-input closure changed')
    source_inputs = normalized.get('source_inputs')
    require(isinstance(source_inputs, list) and
            all(isinstance(item, dict) and isinstance(item.get('path'), str) and
                isinstance(item.get('sha256'), str) for item in source_inputs),
            'normalized current source-input closure is malformed')
    normalized_by_path = {item['path']: item for item in source_inputs}
    require(len(normalized_by_path) == len(source_inputs),
            'normalized current source inputs contain duplicate paths')
    archived_paths = set(paths)
    direct_inputs = [copy.deepcopy(item) for item in source_inputs
                     if item['path'] not in archived_paths]
    original = getattr(executor, '_assert_source_snapshot', None)
    original_source_file = getattr(executor, '_source_file', None)
    require(callable(original), 'frozen executor source snapshot guard is unavailable')
    require(callable(original_source_file), 'frozen executor source-file reader is unavailable')
    def scoped(candidate_root: Path, candidate_commit: str,
               candidate_runner_sha256: str | None = None,
               candidate_inputs: list[dict[str, Any]] = ()) -> Any:
        require(Path(candidate_root).resolve() == Path(root).resolve() and
                candidate_commit == source_commit and
                candidate_runner_sha256 == runner_source_sha256 and
                candidate_inputs == source_inputs,
                'frozen source guard invocation escaped its current graph context')
        for ref in archived_refs:
            read_ref(root, ref)
        return original(candidate_root, candidate_commit,
                        candidate_runner_sha256, direct_inputs)

    archived_by_path = {item['path']: item for item in archived_refs}

    def source_file(candidate_root: Path, candidate_commit: str,
                    relative: str, expected: str) -> bytes:
        path = relative.as_posix() if hasattr(relative, 'as_posix') else relative
        if candidate_commit == source_commit and path in archived_by_path:
            require(Path(candidate_root).resolve() == Path(root).resolve(),
                    'archived source-file read escaped the exact current checkout')
            ref = archived_by_path[path]
            require(expected == ref['sha256'],
                    'archived source-file digest differs from its current CAS ref')
            return read_ref(root, ref)
        return original_source_file(candidate_root, candidate_commit,
                                    relative, expected)

    executor._assert_source_snapshot = scoped
    executor._source_file = source_file
    installed_guard = scoped
    installed_source_file = source_file
    body_error: BaseException | None = None
    try:
        yield
    except BaseException as error:
        body_error = error
        raise
    finally:
        cleanup_errors = []
        if getattr(executor, '_assert_source_snapshot', None) is not installed_guard:
            cleanup_errors.append('frozen source snapshot callback identity changed')
        if getattr(executor, '_source_file', None) is not installed_source_file:
            cleanup_errors.append('frozen source-file callback identity changed')
        executor._assert_source_snapshot = original
        executor._source_file = original_source_file
        if cleanup_errors:
            cleanup_error = RuntimeError('; '.join(cleanup_errors))
            if body_error is not None:
                attach_cleanup_error(body_error, cleanup_error)
            else:
                raise cleanup_error

def _source_manifest(root: Path, core: dict[str, Any]) -> dict[str, Any]:
    from packet import document
    value = document(root, core['source_evidence'])
    for key in ('runner', 'runner_artifact', 'runner_environment', 'executor_environment', 'qualification', 'control_review', 'contract_delta', 'source_commit', 'plan_commit', 'replacement_groups'):
        if key == 'contract_delta' and key not in core:
            continue
        require(key in core, 'core omits source binding: ' + key)
        require(key not in value or value[key] == core[key], 'source evidence/core differs: ' + key)
        value[key] = copy.deepcopy(core[key])
    return value

@contextlib.contextmanager
def historical_context_scope(root: Path, graph: Any, *, current: dict[str, Any] | None=None, ledger_bytes: bytes | None=None) -> Iterator[dict[str, Any]]:
    """Reconstruct all nine origins through actual frozen helper bodies.

    This function is an execution-time replay API, never called by preparation
    against real evidence. It does not call the retained current-HEAD loader,
    relabel a source, transfer an old opaque stage, or accept normalized JSON.
    Its inherited scopes bind the exact old core24 and restore all callbacks.
    The private unit test stops at the first real-parser I/O boundary.
    """
    from packet import inherited_core, document, read_ref, digest as packet_digest, load_history_provider
    from history import validate, _parse_jsonl
    from bridge import inherited_view
    graph = inherited_view(graph)
    core = inherited_core(root)
    for (role, ref) in core['runtime_module_graph'].items():
        _pinned_member(root, graph, role, ref)
    stage = graph.module('stage_runtime11')
    protocol24 = graph.module('protocol24')
    executor = graph.module('executor')
    replacement = graph.module('replacement05')
    require(current is not None and type(ledger_bytes) is bytes,
            'current core and exact bounded ledger bytes are required')
    facts = validate(root, core=current, git=stage._git, live_ledger_bytes=ledger_bytes)
    live_path = core.get('ledger_path', 'reports/releases/v0.9.2/ledger-v1.jsonl')
    live_raw = read_ref(root, {'path': live_path, 'sha256': packet_digest(ledger_bytes)})
    require(live_raw == ledger_bytes, 'live ledger differs from exact caller-bound snapshot')
    lines, live_rows = _parse_jsonl(live_raw)
    require(len(live_rows) in (130, 131), 'actual current ledger must be exact130 or one physical row131')
    provider = load_history_provider(root)
    historical_raw = b''.join(lines[:109])
    require(len(lines) >= 130 and packet_digest(historical_raw) == provider.SEALED109_RAW_SHA256,
            'actual live ledger does not preserve the sealed109 byte prefix')
    rows = stage._canonical_rows(historical_raw, 'sealed109 ledger')
    require(len(rows) == 109 and rows == facts['historical109']['rows'],
            'actual historical109 row objects differ from provider03')
    current_rows = stage._canonical_rows(live_raw, 'actual current ledger')
    require(len(current_rows) == len(live_rows), 'frozen row parser changed current ledger count')
    from protocol import require_terminal_tail
    require_terminal_tail(current_rows, current)
    original_resume = protocol24.validate_resume_history
    original_stage_read = stage._read

    def retained_resume(repo, selected_core, *, live_raw=None):
        require(Path(repo).resolve() == root.resolve() and selected_core is core, 'retained resume projection escaped exact core/root')
        require(live_raw is None or live_raw == historical_raw, 'retained resume supplied another ledger')
        return original_resume(repo, selected_core, live_raw=historical_raw)

    def retained_read(repo, path):
        if Path(repo).resolve() == root.resolve() and path == live_path:
            return historical_raw
        return original_stage_read(repo, path)
    modules = stage._stage_modules(graph, require_legacy=True)
    manifest = _source_manifest(root, core)
    contract_raw = read_ref(root, core['contract'])
    require(stage._git_show(root, core['plan_commit'], core['contract']['path']) == contract_raw, 'historical BF24 contract differs from committed plan blob')

    @contextlib.contextmanager
    def retained_ledger_scope():
        protocol24.validate_resume_history = retained_resume
        stage._read = retained_read
        try:
            yield
        finally:
            protocol24.validate_resume_history = original_resume
            stage._read = original_stage_read
    with retained_ledger_scope(), stage.resume_runtime_scope(root, core, protocol24, graph=graph), stage._stage_full_graph_scope(root, core, graph, modules, mode='after', ledger_bytes=historical_raw, stdlib_importlib=graph.module('bridge19').HOST_STDLIB_IMPORTLIB):
        normalized = stage._stage_validate_replacement_with_scoped_resource_boundary(root, executor, replacement, root / core['contract']['path'], core['contract'], contract_raw, core, manifest, core['source_commit'], rows, historical_raw)
        require(normalized['plan'] == document(root, core['contract']) and normalized['bytes_sha256'] == core['contract']['sha256'], 'historical BF24 normalization changed identity')
        design = document(root, core['source_design'])
        stage._source_delta05(root, design, manifest, core['continuation']['source_commit'], core['source_commit'], incoming_plan=core['continuation']['plan_commit'])
        stage._validate_binary_identity(root, core, normalized)
        sources = stage._validate_normalized_source_inputs(executor, normalized, root, inherited=core['continuation']['source_inputs'])
        executor._assert_source_snapshot(root, core['source_commit'], normalized['plan']['runner_source_sha256'], sources)
        contexts = stage._load_contexts(root, executor, core, replacement, normalized, core['contract'], core['source_commit'], core['plan_commit'], manifest, rows=rows, raw=historical_raw, fixture_only=False)
        verify_runtime_context_bindings(root, contexts)
        yield {'contexts': contexts, 'historical_validated': normalized,
               'rows': current_rows, 'historical_rows': rows, 'raw': live_raw,
               'history_result': facts, 'graph': graph, 'stage': stage,
               'modules': modules, 'core': core, 'source_manifest': manifest}

@contextlib.contextmanager
def current_validation_scope(root: Path, core: dict[str, Any], graph: Any, refs: dict[str, Any], *, ledger_bytes: bytes | None=None) -> Iterator[dict[str, Any]]:
    """Full current parser plus exact history/CAS/native proof; missing gates deny.

    Native plan validation stays in the actual graph-owned runner's parser.
    No callback supplies an eligible plan or invented qualification result.
    """
    from packet import document, read_ref, missing_prerequisites, canonical
    from protocol import contract_delta_from_review, dispatch_groups
    missing = missing_prerequisites(root, refs, purpose='stage-qualification')
    require(not missing, 'missing actual artifacts: ' + ','.join(missing))
    require(core.get('core_identity', refs['current_core']) == refs['current_core'] and document(root, refs['current_core']) == {k: v for (k, v) in core.items() if k not in {'core_identity', 'prerequisite_refs'}}, 'current core differs from bound artifact')
    require(core['contract'] == refs['current_contract'] and core['source_evidence'] == refs['current_source_evidence'], 'current artifact refs differ')
    dispatch_groups(core)
    with historical_context_scope(root, graph, current=core, ledger_bytes=ledger_bytes) as inherited:
        old = inherited['core']
        stage = inherited['stage']
        executor = inherited['modules']['executor']
        replacement = inherited['modules']['replacement05']
        require_current_head(root, core, stage._git)
        raw = read_ref(root, core['contract'])
        plan = json.loads(raw)
        require(stage._git_show(root, core['plan_commit'], core['contract']['path']) == raw, 'current contract differs from committed plan blob')
        contract_delta_from_review(root, document(root, old['contract']), plan, refs['group_contract_review'])
        manifest = _source_manifest(root, core)
        # The frozen source-delta helper is part of the sealed109 historical
        # reconstruction above. Current S has a separate archive-aware CAS
        # proof from history.validate; applying the old exact-patch delta to S
        # would incorrectly require the predecessor's old ancestry/patch.
        qualification_ref = core['qualification']
        replacement._validate_qualification(root, qualification_ref, old['replacement_groups'])
        qualification_raw = read_ref(root, qualification_ref)
        qualification = json.loads(qualification_raw)
        parsed_qualification = copy.deepcopy(qualification)
        require(set(parsed_qualification['tool']) == {'path', 'sha256', 'version', 'build_identity', 'bytes', 'public_tag_commit'}, 'qualification identity fields changed')
        del parsed_qualification['tool']['bytes']
        del parsed_qualification['tool']['public_tag_commit']
        bf_groups = [g for g in plan['groups'] if g['tool'] == 'bifrost']
        require(len(bf_groups) == 20 and all((g['environment'] == bf_groups[0]['environment'] for g in bf_groups)), 'retained Bifrost environments differ')
        replacement._validate_runner_binding(root, manifest, plan['tools']['runner'], plan, core['source_commit'], bf_groups[0]['environment'])
        original = {name: getattr(executor, name) for name in ('_source_inputs', '_read_json', '_validate_resource_recovery', '_wall_budget')}
        resolved_source_inputs: list[list[dict[str, Any]]] = []
        base = [v for v in inherited['contexts'].values() if v['role'] == 'base']
        require(len(base) == 1 and isinstance(base[0]['validated'].get('resource_recovery'), dict), 'actual historical base resource recovery absent')

        def inputs(candidate, repo, qual):
            require(candidate == parser_plan and Path(repo).resolve() == root.resolve(), 'current source resolver escaped scoped plan')
            resolved = stage._resolve_replacement_source_inputs(
                original['_source_inputs'], candidate, repo, qual,
                document(root, old['contract'])['source_inputs'])
            resolved_source_inputs.append(copy.deepcopy(resolved))
            return resolved

        def reader(path, label):
            (value, raw_value) = original['_read_json'](path, label)
            if Path(path).resolve() == (root / qualification_ref['path']).resolve():
                require(value == qualification and raw_value == qualification_raw, 'qualification bytes changed')
                return (copy.deepcopy(parsed_qualification), raw_value)
            return (value, raw_value)

        def resource(value):
            require(value['bytes_sha256'] == core['contract']['sha256'] and value['plan'] == parser_plan, 'current resource scope escaped exact plan')
            return copy.deepcopy(base[0]['validated']['resource_recovery'])

        def wall(candidate):
            require(candidate == parser_plan and candidate['total_wall_budget_seconds'] is None, 'current no-expiry scope escaped exact plan')
            return float(stage.TOTAL_WALL_SECONDS)
        executor._read_json = reader
        executor._source_inputs = inputs
        executor._validate_resource_recovery = resource
        executor._wall_budget = wall
        try:
            from admission import eligible_plan_scope
            reviewed_group = next((g for g in plan['groups'] if g['id'] == GROUP))
            runner = _pinned_member(root, graph, core['joern_runner_role'], core['joern_runner_source'])
            from admission import DIAGNOSTIC_ADMISSION_ROLE
            with eligible_plan_scope(
                    executor, root, reviewed_group, refs['eligible_joern_plan'], runner,
                    graph=graph, runner_role=core['joern_runner_role'],
                    runner_ref=core['joern_runner_source'],
                    diagnostic_ref=core['runtime_module_graph'][DIAGNOSTIC_ADMISSION_ROLE]), \
                    parser_scope(executor, root, core['contract'], plan, raw) as parser_plan:
                parser_plan['resource_guards']['working_set_gib'] = 12
                normalized = executor.validate_plan(root / core['contract']['path'], repo_root=root)
                require(normalized['plan'] == parser_plan, 'current frozen parser changed plan')
                require(resolved_source_inputs and
                        all(value == resolved_source_inputs[0]
                            for value in resolved_source_inputs) and
                        normalized.get('source_inputs') == resolved_source_inputs[0],
                        'current parser output differs from the exact frozen resolver closure')
            normalized['plan'] = copy.deepcopy(plan)
            for group in normalized['groups']:
                group['maximum_attempts'] = next((g['maximum_attempts'] for g in plan['groups'] if g['id'] == group['id']))
            require(normalized['total_wall_budget_seconds'] == stage.TOTAL_WALL_SECONDS, 'finite parser normalization changed')
            normalized['total_wall_budget_seconds'] = None
            resolver_closure = current_source_input_closure(
                core, old, resolved_source_inputs[0])
            stage._validate_binary_identity(root, core, normalized)
            source_proof = inherited['history_result']['current_source_proof']
            with current_source_snapshot_scope(
                    executor, root, core['source_commit'], plan['runner_source_sha256'],
                    normalized, source_proof, current_core=core,
                    source_input_closure=resolver_closure,
                    expected_closure_sha256=digest(canonical(resolver_closure))):
                executor._assert_source_snapshot(
                    root, core['source_commit'], plan['runner_source_sha256'],
                    normalized['source_inputs'])
            current = {'contract': core['contract'], 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'source_evidence': core['source_evidence']}
            from admission import validate_native_execution_decision
            native_acceptance = validate_native_execution_decision(root, refs, core)
            contexts = dict(inherited['contexts'])
            contexts[core['contract']['sha256']] = {'validated': normalized, 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'role': 'joern05-current'}
            verify_runtime_context_bindings(root, contexts, current)
            yield {**inherited, 'validated': normalized, 'contexts': contexts,
                   'current_core': core, 'current_source_proof': inherited['history_result']['current_source_proof'],
                   'current_source_input_closure': resolver_closure,
                   'native_acceptance': native_acceptance}
        finally:
            for (name, value) in original.items():
                setattr(executor, name, value)

def load_runtime_context(root: Path, core: dict[str, Any], *, graph: Any, mode: str='before', ledger_bytes: bytes | None=None) -> Any:
    """Actual current130/131 reconstruction/checker; no serialized authority.

    Before mode requires exact130; after mode requires one exact physical131
    Joern tail. No subsequent ledger state is accepted by this adapter.
    """
    from packet import canonical
    from history import selected_rows
    require(mode in {'before', 'after'}, 'unknown Joern runtime mode')
    refs = core['prerequisite_refs']
    with current_validation_scope(root, core, graph, refs, ledger_bytes=ledger_bytes) as value:
        require(ledger_bytes is not None and ledger_bytes == value['raw'], 'actual stage must bind exact current ledger bytes')
        modules = value['modules']
        stage = value['stage']
        frozen = {name: modules[name] for name in ('replacement05', 'executor', 'checker', 'configuration')}
        mixed = {'root': root, 'validated': value['validated'], 'contexts': value['contexts'],
                 'checker': frozen['checker'], 'executor': frozen['executor'],
                 'prefix': value['rows'][:89], 'rows': value['rows'],
                 'history_result': value['history_result'], 'current_core': core,
                 'native_acceptance': value['native_acceptance']}
        selected = selected_rows(root, value['history_result'])
        expected_rows = 130 if mode == 'before' else 131
        require(len(value['rows']) == expected_rows,
                'mode/current ledger rows differ')
        tail = value['history_result'].get('tail_row131')
        if mode == 'before':
            require(tail is None and len(selected) == 83 and GROUP not in selected,
                    'exact130 before-state must remain the observed 83-group partial history')
        elif tail['row'].get('status') == 'completed':
            require(len(selected) == 84 and selected.get(GROUP) == tail['row'],
                    'successful physical131 must add only the current Joern group')
        else:
            require(len(selected) == 83 and
                    selected.get(GROUP, {}).get('attempt_id') != tail['row']['attempt_id'],
                    'noncompleted physical131 cannot replace or add a selected Joern group')
        summary = replay_current_history(root, value, mixed, selected)
        expected = (83, 87, 4144, 0) if len(selected) == 83 else (84, 92, 4252, 0)
        require((summary['selected_groups'], summary['partitions'], summary['rows'], summary['known_stale']) == expected, 'actual checker denominators differ')
        configuration = {'status': 'pending',
                         'reason': 'C5/0.14.4 Scala remains incomplete; Joern108 does not satisfy full84'}
        # The Joern108 operational result is a bounded group completion. The
        # separate C5/Scala annex remains incomplete, so configuration and
        # full-target gates stay closed even when the 108-case group passes.
        summary['full_release_gate_satisfied'] = False
        diagnostic = {'schema': 'v092-joern05-actual-runtime/v1', 'mode': mode, 'ledger_rows': len(value['rows']), 'ledger_sha256': digest(value['raw']), 'graph_sha256': graph.graph_sha256, 'contract': core['contract'], 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'checker_summary': summary, 'dispatch_groups': [GROUP]}
        source_proof = value['current_source_proof']
        diagnostic['current_source_proof'] = {
            key: source_proof[key] for key in (
                'schema', 'status', 'source_commit', 'source_tree',
                'execution_head', 'baseline_current_head', 'source_refs_sha256',
                'source_ref_count', 'current_direct_count', 'archived_member_count',
            )
        }
        diagnostic['current_source_proof_sha256'] = digest(canonical(source_proof))
        source_input_closure = value['current_source_input_closure']
        diagnostic['current_source_input_closure_sha256'] = digest(
            canonical(source_input_closure))
        diagnostic['archived_member_paths_sha256'] = digest(
            canonical(source_proof['archived_member_paths']))
        diagnostic['native_acceptance_refs'] = {
            'eligible_plan': value['native_acceptance']['eligible_plan_ref'],
            'qualification_receipt': value['native_acceptance']['eligible_plan']['fresh_qualification'],
            'diagnostic_review': value['native_acceptance']['diagnostic_review_ref'],
        }
        from bridge import graph_provenance
        diagnostic['graph_provenance'] = graph_provenance(graph)
        diagnostic['context_digest'] = digest(canonical(diagnostic))
        objects = {'modules': frozen, 'validated': value['validated'], 'mixed_context': mixed,
                   'checker_summary': summary, 'configuration_summary': configuration,
                   'current_source_proof': value['current_source_proof'],
                   'current_core': value['current_core'],
                   'current_source_input_closure': source_input_closure,
                   'joern108_operational_completion': summary.get('joern108_operational_completion'),
                   'bridge_context': diagnostic}
        inherited_bridge = graph.module('bridge19')
        graph_modules = {name: graph.module(name) for name in inherited_bridge.REQUIRED_GRAPH_NAMES}
        return inherited_bridge.ActualRuntimeContext(root, mode, graph, graph_modules, diagnostic, objects)

def replay_current_history(root: Path, value: dict[str, Any], context: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    """Replay sealed109 origins and one current Joern131 tail separately."""
    import collections
    from packet import read_ref
    stage = value['stage']
    rows = value['rows']
    raw = value['raw']
    current = value['current_core']
    from protocol import require_terminal_tail
    require_terminal_tail(rows, current)
    require(read_ref(root, {'path': 'reports/releases/v0.9.2/ledger-v1.jsonl', 'sha256': digest(raw)}) == raw, 'checker actual ledger changed')
    executor = context['executor']
    checker = context['checker']
    replacement = value['modules']['replacement05']
    facts = value['history_result']
    historical_rows = facts['historical109']['rows']
    annex_rows = facts['bifrost0144_c5_annex21']['rows']
    packet_rows = historical_rows + annex_rows + ([facts['tail_row131']['row']]
                    if facts.get('tail_row131') is not None else [])
    require(packet_rows == rows, 'archive partitions and current physical row do not reconstruct the ledger')
    line_hashes = {json.loads(line)['attempt_id']: digest(line) for line in raw.splitlines(keepends=True)}
    reports = []
    failures = []
    outcomes = collections.Counter()
    # The nine sealed109 contexts are the only contexts that may verify old
    # reports. C5 rows remain a separate sealed annex; they are included in
    # attempt-directory and wall-provenance checks below, never relabeled as
    # 0144 Scala or given invented normalized contexts.
    for row in historical_rows:
        origin = stage._origin_context(context, row)
        normalized = origin['validated']
        group = executor._historical_group_for_replay(normalized, row)
        number = replacement._attempt_number(row['attempt_id'])
        with stage._resume_checker_context(replacement, context, origin):
            if row['status'] == 'completed':
                (bindings, counts) = checker._verify_one_group(root, normalized, group, row, origin['plan_commit'], number)
            else:
                path = f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json"
                receipt = (root / path).read_bytes()
                read_ref(root, {'path': path, 'sha256': digest(receipt)})
                failures.append(checker._verify_failed_attempt(root, normalized, group, row, origin['plan_commit'], number, line_hashes[row['attempt_id']], digest(receipt)))
                continue
        if selected.get(row['group_id'], {}).get('attempt_id') != row['attempt_id']:
            continue
        outcomes.update(counts)
        for binding in bindings:
            binding.update(attempt_id=row['attempt_id'], attempt_number=number, evidence_contract_sha256=row['contract_sha256'])
        reports.extend(bindings)
    tail = facts.get('tail_row131')
    if tail is not None:
        row = tail['row']
        require(selected.get(row['group_id'], {}).get('attempt_id') == row['attempt_id']
                if row['status'] == 'completed' else
                selected.get(row['group_id'], {}).get('attempt_id') != row['attempt_id'],
                'selected Joern row differs from the successful/current terminal')
        origin = stage._origin_context(context, row)
        normalized = origin['validated']
        group = executor._historical_group_for_replay(normalized, row)
        number = replacement._attempt_number(row['attempt_id'])
        with stage._resume_checker_context(replacement, context, origin):
            if row['status'] == 'completed':
                bindings, counts = checker._verify_one_group(
                    root, normalized, group, row, origin['plan_commit'], number)
                outcomes.update(counts)
                joern_outcomes = collections.Counter(counts)
                for binding in bindings:
                    binding.update(attempt_id=row['attempt_id'], attempt_number=number,
                                   evidence_contract_sha256=row['contract_sha256'])
                reports.extend(bindings)
                from protocol import joern108_operational_completion
                completion = joern108_operational_completion(
                    origin, row, bindings, dict(joern_outcomes),
                    context['native_acceptance'], tail_proof=tail)
                context['joern108_operational_completion'] = completion
            else:
                path = f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json"
                receipt = (root / path).read_bytes()
                read_ref(root, {'path': path, 'sha256': digest(receipt)})
                failures.append(checker._verify_failed_attempt(
                    root, normalized, group, row, origin['plan_commit'], number,
                    line_hashes[row['attempt_id']], digest(receipt)))
    consumed = facts['sealed109_lineage']['consumed_events']
    ids = {row['attempt_id'] for row in rows}
    orphan = {event['attempt_id'] for event in consumed}
    require(not ids & orphan, 'consumed-unclosed event was fabricated as a terminal')
    checker._assert_attempt_directories(root, ids | orphan)
    stage._observed_wall(checker, rows)
    require(not any(('stale' in str(key).lower() and count for (key, count) in outcomes.items())), 'selected reports contain stale outcomes')
    partitions = 0
    expected_rows = 0
    for row in selected.values():
        origin = stage._origin_context(context, row)
        group = executor._historical_group_for_replay(origin['validated'], row)
        partitions += len(group['reports'])
        expected_rows += sum((len(report['case_ids']) for report in group['reports']))
    require(len(reports) == partitions and sum((int(report['rows']) for report in reports)) == expected_rows, 'actual selected report denominators differ')
    joern_complete = context.get('joern108_operational_completion')
    status = 'joern108-operationally-complete' if joern_complete else 'partial-evidence-verified'
    return {'status': status, 'ledger_rows': len(rows), 'selected_groups': len(selected),
            'partitions': partitions, 'rows': expected_rows, 'known_stale': 0,
            'fresh_reports': reports, 'failed_attempts': failures,
            'missing_groups': sorted({g['id'] for g in context['validated']['groups']} - set(selected)),
            'joern108_operational_completion': joern_complete,
            'full_release_gate_satisfied': False}
