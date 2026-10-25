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
    entries = context_bindings(root, current)
    require(set(contexts) == set(entries), 'normalized context roster differs')
    for (key, entry) in entries.items():
        value = contexts[key]
        normalized = value.get('validated')
        require(isinstance(normalized, dict) and normalized.get('bytes_sha256') == key, 'actual normalized contract identity missing')
        require(normalized.get('plan', {}).get('source_commit') == entry['source_commit'] and value.get('source_commit') == entry['source_commit'] and (value.get('plan_commit') == entry['plan_commit']), 'normalized historical source/plan relabeled')

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
    from packet import inherited_core, document, read_ref
    from history import validate
    from bridge import inherited_view
    graph = inherited_view(graph)
    core = inherited_core(root)
    facts = validate(root, historical_only=current is not None)
    require(facts['ledger_prefix']['rows'] == 109, 'history reader did not seal109')
    for (role, ref) in core['runtime_module_graph'].items():
        _pinned_member(root, graph, role, ref)
    stage = graph.module('stage_runtime11')
    protocol24 = graph.module('protocol24')
    executor = graph.module('executor')
    replacement = graph.module('replacement05')
    raw = read_ref(root, {k: facts['ledger_prefix'][k] for k in ('path', 'sha256')})
    rows = stage._canonical_rows(raw, 'sealed109 ledger')
    require(len(rows) == 109, 'actual history row count changed')
    live_path = core.get('ledger_path', 'reports/releases/v0.9.2/ledger-v1.jsonl')
    if ledger_bytes is None:
        require(current is None, 'new before/after runtime requires explicit bound ledger bytes')
        ledger_bytes = raw
    live_raw = read_ref(root, {'path': live_path, 'sha256': digest(ledger_bytes)})
    require(live_raw == ledger_bytes and live_raw.startswith(raw), 'live ledger/snapshot109 changed')
    live_rows = stage._canonical_rows(live_raw, 'actual current ledger')
    if current is None:
        require(live_raw == raw, 'unregistered live tail is forbidden')
    else:
        from protocol import require_terminal_tail
        require_terminal_tail(live_rows, current)
    original_resume = protocol24.validate_resume_history
    original_stage_read = stage._read

    def retained_resume(repo, selected_core, *, live_raw=None):
        require(Path(repo).resolve() == root.resolve() and selected_core is core, 'retained resume projection escaped exact core/root')
        require(live_raw is None or live_raw == raw, 'retained resume supplied another ledger')
        return original_resume(repo, selected_core, live_raw=raw)

    def retained_read(repo, path):
        if Path(repo).resolve() == root.resolve() and path == live_path:
            return raw
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
    with retained_ledger_scope(), stage.resume_runtime_scope(root, core, protocol24, graph=graph), stage._stage_full_graph_scope(root, core, graph, modules, mode='after', ledger_bytes=raw, stdlib_importlib=graph.module('bridge19').HOST_STDLIB_IMPORTLIB):
        normalized = stage._stage_validate_replacement_with_scoped_resource_boundary(root, executor, replacement, root / core['contract']['path'], core['contract'], contract_raw, core, manifest, core['source_commit'], rows, raw)
        require(normalized['plan'] == document(root, core['contract']) and normalized['bytes_sha256'] == core['contract']['sha256'], 'historical BF24 normalization changed identity')
        design = document(root, core['source_design'])
        stage._source_delta05(root, design, manifest, core['continuation']['source_commit'], core['source_commit'], incoming_plan=core['continuation']['plan_commit'])
        stage._validate_binary_identity(root, core, normalized)
        sources = stage._validate_normalized_source_inputs(executor, normalized, root, inherited=core['continuation']['source_inputs'])
        executor._assert_source_snapshot(root, core['source_commit'], normalized['plan']['runner_source_sha256'], sources)
        contexts = stage._load_contexts(root, executor, core, replacement, normalized, core['contract'], core['source_commit'], core['plan_commit'], manifest, rows=rows, raw=raw, fixture_only=False)
        verify_runtime_context_bindings(root, contexts)
        yield {'contexts': contexts, 'historical_validated': normalized, 'rows': live_rows, 'historical_rows': rows, 'raw': live_raw, 'graph': graph, 'stage': stage, 'modules': modules, 'core': core, 'source_manifest': manifest}

@contextlib.contextmanager
def current_validation_scope(root: Path, core: dict[str, Any], graph: Any, refs: dict[str, Any], *, ledger_bytes: bytes | None=None) -> Iterator[dict[str, Any]]:
    """Full current parser plus exact history/source delta; missing gates deny.

    Native plan validation stays in the actual graph-owned runner's parser.
    No callback supplies an eligible plan or invented qualification result.
    """
    from packet import document, read_ref, missing_prerequisites
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
        design = document(root, core['source_design'])
        stage._source_delta05(root, design, manifest, old['source_commit'], core['source_commit'], incoming_plan=old['plan_commit'])
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
        base = [v for v in inherited['contexts'].values() if v['role'] == 'base']
        require(len(base) == 1 and isinstance(base[0]['validated'].get('resource_recovery'), dict), 'actual historical base resource recovery absent')

        def inputs(candidate, repo, qual):
            require(candidate == parser_plan and Path(repo).resolve() == root.resolve(), 'current source resolver escaped scoped plan')
            return stage._resolve_replacement_source_inputs(original['_source_inputs'], candidate, repo, qual, document(root, old['contract'])['source_inputs'])

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
            with eligible_plan_scope(executor, root, reviewed_group, refs['eligible_joern_plan'], runner, graph=graph, runner_role=core['joern_runner_role'], runner_ref=core['joern_runner_source']), parser_scope(executor, root, core['contract'], plan, raw) as parser_plan:
                parser_plan['resource_guards']['working_set_gib'] = 12
                normalized = executor.validate_plan(root / core['contract']['path'], repo_root=root)
                require(normalized['plan'] == parser_plan, 'current frozen parser changed plan')
            normalized['plan'] = copy.deepcopy(plan)
            for group in normalized['groups']:
                group['maximum_attempts'] = next((g['maximum_attempts'] for g in plan['groups'] if g['id'] == group['id']))
            require(normalized['total_wall_budget_seconds'] == stage.TOTAL_WALL_SECONDS, 'finite parser normalization changed')
            normalized['total_wall_budget_seconds'] = None
            stage._validate_binary_identity(root, core, normalized)
            executor._assert_source_snapshot(root, core['source_commit'], plan['runner_source_sha256'], normalized['source_inputs'])
            current = {'contract': core['contract'], 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'source_evidence': core['source_evidence']}
            contexts = dict(inherited['contexts'])
            contexts[core['contract']['sha256']] = {'validated': normalized, 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'role': 'joern05-current'}
            verify_runtime_context_bindings(root, contexts, current)
            yield {**inherited, 'validated': normalized, 'contexts': contexts, 'current_core': core}
        finally:
            for (name, value) in original.items():
                setattr(executor, name, value)

def load_runtime_context(root: Path, core: dict[str, Any], *, graph: Any, mode: str='before', ledger_bytes: bytes | None=None) -> Any:
    """Actual before-stage109 reconstruction/checker; no serialized authority.

    The after110 successor remains deliberately unavailable until its exact
    terminal/source/context closure is implemented and independently reviewed.
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
        mixed = {'root': root, 'validated': value['validated'], 'contexts': value['contexts'], 'checker': frozen['checker'], 'executor': frozen['executor'], 'prefix': value['rows'][:89], 'rows': value['rows']}
        selected = selected_rows(root, value['rows'])
        require(mode == 'before' and len(value['rows']) == 109 or (mode == 'after' and len(value['rows']) == 110), 'mode/current ledger rows differ')
        summary = replay_current_history(root, value, mixed, selected)
        expected = (83, 87, 4144, 0) if len(selected) == 83 else (84, 92, 4252, 0)
        require((summary['selected_groups'], summary['partitions'], summary['rows'], summary['known_stale']) == expected, 'actual checker denominators differ')
        configuration = {'status': 'pending', 'reason': 'Joern05 missing or unsuccessful; no full84 claim'}
        if summary['full_release_gate_satisfied']:
            config_checker = stage._configuration_checker_summary(root, summary, selected, value['validated'], fixture_only=False)
            configuration = stage._call_configuration(frozen['configuration'], frozen['checker'], frozen['executor'], root, root / core['contract']['path'], core['configuration_output'], value['validated'], config_checker)
            from supervisor import require_full_summary
            require_full_summary(summary, configuration)
        diagnostic = {'schema': 'v092-joern05-actual-runtime/v1', 'mode': mode, 'ledger_rows': len(value['rows']), 'ledger_sha256': digest(value['raw']), 'graph_sha256': graph.graph_sha256, 'contract': core['contract'], 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'checker_summary': summary, 'dispatch_groups': [GROUP]}
        from bridge import graph_provenance
        diagnostic['graph_provenance'] = graph_provenance(graph)
        diagnostic['context_digest'] = digest(canonical(diagnostic))
        objects = {'modules': frozen, 'validated': value['validated'], 'mixed_context': mixed, 'checker_summary': summary, 'configuration_summary': configuration, 'bridge_context': diagnostic}
        inherited_bridge = graph.module('bridge19')
        graph_modules = {name: graph.module(name) for name in inherited_bridge.REQUIRED_GRAPH_NAMES}
        return inherited_bridge.ActualRuntimeContext(root, mode, graph, graph_modules, diagnostic, objects)

def replay_current_history(root: Path, value: dict[str, Any], context: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    """Actual per-row verifiers, exact directory UNION consumed orphan event."""
    import collections
    from packet import read_ref
    from history import validate
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
    line_hashes = {json.loads(line)['attempt_id']: digest(line) for line in raw.splitlines(keepends=True)}
    reports = []
    failures = []
    outcomes = collections.Counter()
    for row in rows:
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
    facts = validate(root, historical_only=True)
    ids = {row['attempt_id'] for row in rows}
    orphan = {event['attempt_id'] for event in facts['consumed_events']}
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
    full = (len(selected), partitions, expected_rows) == (84, 92, 4252)
    return {'status': 'fresh-evidence-verified' if full else 'partial-evidence-verified', 'ledger_rows': len(rows), 'selected_groups': len(selected), 'partitions': partitions, 'rows': expected_rows, 'known_stale': 0, 'fresh_reports': reports, 'failed_attempts': failures, 'missing_groups': sorted({g['id'] for g in context['validated']['groups']} - set(selected)), 'full_release_gate_satisfied': full}
