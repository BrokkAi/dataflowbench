"""Private singleton controller; actual dispatch requires sealed execution authority."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from packet import require
from protocol import GROUP, ATTEMPT, dispatch_groups

STARTUP_HANDOFF_SCHEMA = 'v092-joern05-startup-handoff/v1'
STARTUP_TIMEOUT_SECONDS = 600.0
STARTUP_FRAME_MAX_BYTES = 16 * 1024

def dispatch_plan(core: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    dispatch_groups(core)
    groups = [g for g in normalized['plan']['groups'] if g['id'] == GROUP]
    require(len(groups) == 1 and groups[0]['maximum_attempts'] == 5, 'Joern cap/slot differs')
    return {'group_id': GROUP, 'attempt_id': ATTEMPT, 'group': groups[0], 'automatic_retry': False, 'execution_authorized': False}


def _startup_receipt_path(core: dict[str, Any]) -> str:
    """Return the one immutable receipt path for the bootstrap handoff."""
    from pathlib import PurePosixPath
    namespace = PurePosixPath(core['sidecar_namespace'])
    require(not namespace.is_absolute() and '..' not in namespace.parts,
            'startup namespace is unsafe')
    return str(namespace / 'supervision' / 'startup-ready.json')


def _startup_lock_identity(fd: int) -> dict[str, int]:
    import os
    require(type(fd) is int and fd > 2, 'startup lock fd is invalid')
    stat = os.fstat(fd)
    return {'dev': stat.st_dev, 'ino': stat.st_ino}


def startup_child_ready(root: Path, core: dict[str, Any], manifest_ref: dict[str, str], *,
                        graph: Any, lock_fd: int, startup_fd: int, token: str,
                        receipt_path: str) -> dict[str, str]:
    """Verify and durably publish readiness while retaining the inherited lock.

    The lock descriptor is inherited from bootstrap.  A nonblocking flock on
    that descriptor is intentionally a proof of descriptor ownership, not a
    second pathname acquisition.  The immutable receipt is published before
    its one-record pipe frame, so bootstrap can validate both bytes and the
    exact PID/birth identities before it releases its references.
    """
    import fcntl
    import os
    import re
    from pathlib import Path
    from packet import canonical
    controller = graph.module('supervisor24')
    require(type(startup_fd) is int and startup_fd > 2, 'startup readiness fd is invalid')
    require(isinstance(token, str) and re.fullmatch(r'[0-9a-f]{32}', token),
            'startup token is malformed')
    expected_receipt = _startup_receipt_path(core)
    require(receipt_path == expected_receipt, 'startup receipt path is not source-bound')
    target = Path(core['lock_path'])
    require(target.is_absolute() and not target.is_symlink(), 'canonical startup lock is unsafe')
    before = target.stat()
    held = _startup_lock_identity(lock_fd)
    require(held == {'dev': before.st_dev, 'ino': before.st_ino},
            'inherited startup lock identity differs from canonical path')
    try:
        # This succeeds only for the inherited open-file description.  An
        # independently opened descriptor remains blocked by bootstrap's lock.
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise ValueError('startup lock was not transferred') from exc
    require(not target.is_symlink(), 'canonical startup lock changed to symlink')
    after = target.stat()
    require(held == {'dev': after.st_dev, 'ino': after.st_ino},
            'canonical startup lock changed during handoff')
    process = controller._process(os.getpid())
    parent_process = controller._process(os.getppid())
    identity = {'dev': held['dev'], 'ino': held['ino']}
    receipt = {
        'schema': STARTUP_HANDOFF_SCHEMA, 'status': 'lock-ready',
        'automatic_retry': False, 'token': token,
        'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
        'process': process, 'parent_process': parent_process,
        'lock': identity, 'lock_ownership': 'inherited-open-file-description',
        'graph_sha256': graph.graph_sha256, 'source_commit': core['source_commit'],
        'plan_commit': core['plan_commit'], 'contract_sha256': core['contract']['sha256'],
        'semantic_completion_inferred': False,
    }
    receipt_ref = _write(root, graph, receipt_path, receipt)
    frame = {'schema': STARTUP_HANDOFF_SCHEMA, 'status': 'lock-ready',
             'automatic_retry': False, 'token': token, 'receipt_ref': receipt_ref,
             'process': process, 'parent_process': parent_process, 'lock': identity,
             'graph_sha256': graph.graph_sha256,
             'semantic_completion_inferred': False}
    raw = canonical(frame)
    require(len(raw) <= STARTUP_FRAME_MAX_BYTES, 'startup readiness frame is oversized')
    try:
        written = os.write(startup_fd, raw)
        require(written == len(raw), 'startup readiness frame was partial')
    finally:
        try:
            os.close(startup_fd)
        except OSError:
            pass
    return receipt_ref


def await_startup_ready(root: Path, core: dict[str, Any], manifest_ref: dict[str, str], *,
                        child: Any, read_fd: int, expected_process: dict[str, Any],
                        expected_parent_process: dict[str, Any], expected_lock: dict[str, int],
                        token: str, receipt_path: str, expected_graph_sha256: str,
                        timeout_seconds: float = STARTUP_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Read one bounded, durable startup frame; never retry lock acquisition."""
    import json
    import os
    import select
    import time
    require(type(read_fd) is int and read_fd > 2, 'startup readiness read fd is invalid')
    require(timeout_seconds > 0, 'startup timeout must be positive')
    deadline = time.monotonic() + timeout_seconds
    buffer = bytearray()
    while True:
        if child.poll() is not None:
            raise ValueError('startup peer exited before lock handoff')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('startup lock handoff timed out')
        readable, _, _ = select.select([read_fd], [], [], min(remaining, 0.05))
        if not readable:
            continue
        chunk = os.read(read_fd, STARTUP_FRAME_MAX_BYTES - len(buffer))
        if not chunk:
            raise ValueError('startup peer closed before lock handoff')
        buffer.extend(chunk)
        require(len(buffer) <= STARTUP_FRAME_MAX_BYTES, 'startup readiness frame is oversized')
        if b'\n' not in buffer:
            continue
        require(buffer.count(b'\n') == 1 and buffer.endswith(b'\n'),
                'startup readiness channel contains more than one record')
        # The child closes its write end immediately after this frame.  Read
        # EOF before accepting it so trailing bytes cannot be ignored.
        while True:
            if child.poll() is not None and not readable:
                raise ValueError('startup peer exited during lock handoff')
            remaining = deadline - time.monotonic()
            require(remaining > 0, 'startup lock handoff timed out')
            readable, _, _ = select.select([read_fd], [], [], min(remaining, 0.05))
            if not readable:
                continue
            tail = os.read(read_fd, STARTUP_FRAME_MAX_BYTES - len(buffer))
            if not tail:
                break
            buffer.extend(tail)
            require(buffer.count(b'\n') == 1 and buffer.endswith(b'\n'),
                    'startup readiness channel contains more than one record')
        break
    try:
        frame = json.loads(bytes(buffer))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError('startup readiness frame is not canonical JSON') from exc
    require(isinstance(frame, dict) and set(frame) == {
        'schema', 'status', 'automatic_retry', 'token', 'receipt_ref', 'process',
        'parent_process', 'lock', 'graph_sha256', 'semantic_completion_inferred'},
        'startup readiness frame schema differs')
    require(frame['schema'] == STARTUP_HANDOFF_SCHEMA and frame['status'] == 'lock-ready'
            and frame['automatic_retry'] is False
            and frame['semantic_completion_inferred'] is False,
            'startup readiness status differs')
    require(isinstance(frame['receipt_ref'], dict) and
            set(frame['receipt_ref']) == {'path', 'sha256'} and
            frame['token'] == token and frame['receipt_ref']['path'] == receipt_path,
            'startup readiness token/path differs')
    require(frame['graph_sha256'] == expected_graph_sha256,
            'startup readiness graph differs')
    require(frame['process'] == expected_process and
            frame['parent_process'] == expected_parent_process,
            'startup readiness PID/birth differs')
    require(frame['lock'] == expected_lock, 'startup readiness lock identity differs')
    receipt_ref, receipt = _read_file_ref(root, receipt_path)
    require(frame['receipt_ref'] == receipt_ref, 'startup receipt reference differs')
    require(isinstance(receipt, dict) and set(receipt) == {
        'schema', 'status', 'automatic_retry', 'token', 'manifest_ref', 'core_identity',
        'process', 'parent_process', 'lock', 'lock_ownership', 'graph_sha256',
        'source_commit', 'plan_commit', 'contract_sha256',
        'semantic_completion_inferred'}, 'startup receipt schema differs')
    require(receipt['schema'] == STARTUP_HANDOFF_SCHEMA and receipt['status'] == 'lock-ready'
            and receipt['automatic_retry'] is False
            and receipt['semantic_completion_inferred'] is False
            and receipt['token'] == token and receipt['manifest_ref'] == manifest_ref
            and receipt['core_identity'] == core['core_identity']
            and receipt['process'] == expected_process
            and receipt['parent_process'] == expected_parent_process
            and receipt['lock'] == expected_lock
            and receipt['lock_ownership'] == 'inherited-open-file-description'
            and receipt['graph_sha256'] == expected_graph_sha256
            and receipt['source_commit'] == core['source_commit']
            and receipt['plan_commit'] == core['plan_commit']
            and receipt['contract_sha256'] == core['contract']['sha256'],
            'startup receipt binding differs')
    return {'frame': frame, 'receipt_ref': receipt_ref, 'receipt': receipt}

def frozen_freshness(executor: Any, root: Path, group: dict[str, Any], reports: list[dict]) -> Any:
    require(group['id'] == GROUP and type(group.get('maximum_attempts')) is int and (group['maximum_attempts'] == 5), 'only actual Joern05 cap may reach freshness')
    rows = executor._ledger_rows(root / executor.LEDGER_PATH)
    prior = [row for row in rows if row['group_id'] == GROUP]
    require(len(prior) == 4, 'Joern consumed history must be exactly four')
    numbers = [int(row['attempt_id'].split('-attempt-')[1].split('-')[0]) for row in prior]
    require(sorted(numbers) == [1, 2, 3, 4], 'global Joern counters reused or missing')
    result = executor._assert_fresh(root, group, reports, 2)
    require(result[-1] == ATTEMPT, 'real frozen freshness did not select global five')
    return result

def require_full_summary(summary: dict[str, Any], configuration: dict[str, Any]) -> None:
    require(summary.get('status') == 'fresh-evidence-verified' and (summary.get('selected_groups'), summary.get('partitions'), summary.get('rows'), summary.get('known_stale')) == (84, 92, 4252, 0) and (not summary.get('missing_groups')), 'full actual checker gate not satisfied')
    require(configuration.get('status') == 'ready-to-execute' and configuration.get('execution_requested') is False, 'actual configuration execute=False gate not satisfied')

def run_child_group(root: Path, core: dict[str, Any], manifest_ref: dict[str, str], *, graph: Any, child: Any, parent_ref: dict[str, str], dispatch_sidecars: dict[str, Any], lock_fd: int, popen_monotonic: float, phase_bindings: dict[str, Any]) -> dict[str, Any]:
    """One actual frozen run_group, gated by an actual opaque child.

    This is the child execution adapter, not a Popen parent or execution permit.
    The outer durable parent/anonymous-pipe supervisor must be integrated and
    reviewed separately. Missing current prerequisites deny before freshness.
    No preparation test calls this function with real evidence or processes.
    """
    import contextlib
    import datetime as dt
    import fcntl
    import os
    import time
    from packet import document
    from admission import require_markers, validate_prerequisites
    from stage_runtime import _pinned_member
    require_markers(dict(os.environ))
    dispatch_groups(core)
    manifest = document(root, manifest_ref)
    require(manifest['core_identity'] == core['core_identity'], 'child manifest/core differs')
    require(core.get('prerequisite_refs', {}).get('current_manifest') == manifest_ref, 'child prerequisite manifest differs')
    refs = core['prerequisite_refs']
    runner = _pinned_member(root, graph, core['joern_runner_role'], core['joern_runner_source'])
    validate_prerequisites(root, refs, runner, refs['eligible_joern_plan']['path'])
    original_core = document(root, core['core_identity'])
    require(original_core == {k: v for (k, v) in core.items() if k not in {'core_identity', 'prerequisite_refs'}}, 'child bound core differs')
    from packet import inherited_core
    historical = inherited_core(root)
    for (role, ref) in historical['runtime_module_graph'].items():
        _pinned_member(root, graph, role, ref)
    inherited = graph.module('bridge19')
    controller = graph.module('supervisor24')
    require(type(child) is inherited.ChildStage, 'child execution requires actual opaque child')
    slot = manifest['execution_admission_slots'][GROUP]
    require(slot['attempt_id'] == ATTEMPT, 'manifest dispatch slot is not globalJoern05')
    require(set(phase_bindings) == {'phase_receipt_path', 'process', 'child_stage_witness', 'child_stage_witness_ref'}, 'phase bindings fields differ')
    require(phase_bindings['process'] == {'pid': os.getpid(), 'birth_identity': controller._birth(os.getpid())}, 'phase child exact birth differs')
    require(phase_bindings['phase_receipt_path'] == slot['analyzer_phase_path'], 'analyzer phase path differs from bound slot')
    require(core['dispatch_groups'] == [GROUP], 'no independent group may be redispatched')

    def ready():
        return inherited.assert_child_ready_from_receipt(root, child, parent_receipt_ref=parent_ref, graph=graph, manifest_ref=manifest_ref, core_identity=core['core_identity'], core=core, dispatch_sidecars=dispatch_sidecars, now_monotonic=time.monotonic(), stage_bridge=inherited)
    ready()
    parent = inherited._read_compact_parent(root, parent_ref, core=core)
    witness = controller._validate_child_stage_witness(phase_bindings['child_stage_witness'], stage=child, process=phase_bindings['process'], expected_child_stage_identity_sha256=child.identity_sha256, parent_stage_identity_sha256=parent['stage_identity_sha256'], parent_stage_ref=parent_ref)
    controller._validate_child_stage_witness_ref(root, phase_bindings['child_stage_witness_ref'], expected_path=controller._child_stage_witness_path(phase_bindings['phase_receipt_path']), expected_witness=witness)
    held = os.fstat(lock_fd)
    require((held.st_dev, held.st_ino) == (parent['lock']['dev'], parent['lock']['ino']), 'inherited descriptor is not canonical parent lock')
    require(parent['lock']['parent_pid'] == os.getppid() and controller._birth(os.getppid()) == parent['lock']['parent_birth'], 'child exact parent birth differs')
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    actual = inherited.runtime_objects(child)
    require(isinstance(actual, inherited.ActualRuntimeContext) and actual.graph is graph, 'child runtime is not exact actual graph context')
    objects = actual.objects
    validated = objects['validated']
    executor = objects['modules']['executor']
    require(executor is graph.module('executor') and validated['bytes_sha256'] == core['contract']['sha256'] and (validated['plan']['source_commit'] == core['source_commit']), 'child normalized source/contract differs')
    group = dispatch_plan(core, validated)['group']
    runtime = controller._dispatch_lease(validated, GROUP, popen_monotonic=popen_monotonic)
    original = {name: getattr(executor, name) for name in ('_exclusive_lock', '_matrix_elapsed_wall', '_contenders')}

    @contextlib.contextmanager
    def inherited_lock():
        os.fstat(lock_fd)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield

    def clock(candidate, *, now_seconds=None):
        require(candidate is runtime, 'clock received another runtime')
        now = time.time() if now_seconds is None else now_seconds
        elapsed = now - dt.datetime.fromisoformat(controller.ORIGIN).timestamp()
        require(elapsed >= 0, 'clock precedes original immutable origin')
        return elapsed
    executor._exclusive_lock = inherited_lock
    executor._matrix_elapsed_wall = clock
    executor._contenders = lambda table: list(dict.fromkeys(original['_contenders'](table) + controller._hashed_bifrost_contenders(table)))
    try:
        executor._check_resources(root, 127 * 1024 ** 3)
        reports = next((g['reports'] for g in validated['groups'] if g['id'] == GROUP))
        frozen_freshness(executor, root, group, reports)
        loaders = graph.module('runtime_loaders24')
        required_phase = {'root': root, 'protocol': graph.module('protocol24'), 'group_id': GROUP, 'attempt_id': ATTEMPT, 'stage': child, 'graph_sha256': graph.graph_sha256, 'parent_stage_identity_sha256': parent['stage_identity_sha256'], 'parent_graph_sha256': parent['graph_sha256'], 'parent_stage_ref': parent_ref, 'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'], 'contract_sha256': core['contract']['sha256'], 'registered': group['deadline_seconds']}
        require(not set(phase_bindings) & set(required_phase), 'phase binding overrides protected identity')
        with loaders.scoped_runtime_loaders(root, executor=executor, graph=graph, module_names=loaders.PRODUCTION_MODULE_NAMES), controller._scoped_contract_snapshot(executor, runtime, core['plan_commit']), controller._per_source_projection_guard(executor, runtime), controller._scoped_analyzer_phase_hook(executor, **required_phase, **phase_bindings):
            ready()
            result = executor.run_group(runtime, GROUP)
    finally:
        for (name, value) in original.items():
            setattr(executor, name, value)
    require(result.get('attempt_id') == ATTEMPT and result.get('group_id') == GROUP and (result.get('source_commit') == core['source_commit']) and (result.get('plan_commit') == core['plan_commit']) and (result.get('contract_sha256') == core['contract']['sha256']), 'actual terminal result identity differs')
    return result


def _slot(root: Path, core: dict[str, Any], manifest: dict[str, Any]) -> dict[str, str]:
    """One canonical fresh slot; no predecessor namespace can be reused."""
    from pathlib import PurePosixPath
    require(set(manifest['execution_admission_slots']) == {GROUP}, 'manifest dispatch is not singleton')
    value = manifest['execution_admission_slots'][GROUP]
    require(value['attempt_id'] == ATTEMPT, 'slot does not consume global five')
    namespace = PurePosixPath(core['sidecar_namespace'])
    require(not namespace.is_absolute() and '..' not in namespace.parts, 'unsafe dispatch namespace')
    for key in ('admission_path', 'phase_gate_path', 'completion_path', 'analyzer_phase_path'):
        path = PurePosixPath(value[key])
        require(not path.is_absolute() and '..' not in path.parts and
                path.is_relative_to(namespace), 'slot escapes current namespace')
    return value


def _write(root: Path, graph: Any, path: str, value: dict[str, Any]) -> dict[str, str]:
    return graph.module('protocol24').write_immutable(root, path, value)


def _stage_receipt(root: Path, core: dict, manifest_ref: dict, stage: Any,
                   graph: Any, *, predecessor_ref: dict | None=None) -> dict:
    path = core['sidecar_namespace'] + '/stages/stage-%02d.json' % stage.identity.index
    return graph.module('bridge19').write_compact_stage_receipt(root, path, stage,
        status='parent-stage-verified' if stage.identity.index == 0 else 'successor-stage-verified',
        sidecar_names=tuple(sorted(stage.sidecars)), manifest_ref=manifest_ref,
        core_identity=core['core_identity'], predecessor_receipt_ref=predecessor_ref, core=core)


def _snapshot(root: Path, core: dict, graph: Any, index: int) -> dict:
    from packet import digest
    from history import validate
    from protocol import require_terminal_tail
    require(index in (0, 1), 'singleton has only before/after snapshots')
    validate(root, historical_only=index == 1)
    raw = (root / 'reports/releases/v0.9.2/ledger-v1.jsonl').read_bytes()
    import json
    rows = [json.loads(line) for line in raw.splitlines()]
    require_terminal_tail(rows, core)
    require(len(rows) == 109 + index, 'singleton snapshot transition count differs')
    path = core['sidecar_namespace'] + '/stages/stage-%02d-ledger.jsonl' % index
    graph.module('protocol24').write_immutable_bytes(root, path, raw)
    return {'path': path, 'sha256': digest(raw), 'rows': len(rows)}


def _held_proxy(root: Path, core: dict, graph: Any, stream: Any):
    """Descriptor wrappers may have integer .name; bind the canonical path explicitly."""
    import types
    proxy = graph.module('supervisor24')._HeldLockProxy(root,
        types.SimpleNamespace(name=core['lock_path'], fileno=stream.fileno))
    proxy.assert_live(core['lock_path'])
    return proxy


def _fresh_gate(root: Path, core: dict, graph: Any, stage: Any, held_lock: Any) -> dict:
    frozen = graph.module('bridge19')
    controller = graph.module('supervisor24')
    frozen.assert_stage_current(root, stage, graph)
    actual = frozen.runtime_objects(stage)
    executor = actual.objects['modules']['executor']
    admission24 = graph.module('admission24')
    proxy = _held_proxy(root, core, graph, held_lock)
    value = controller._configuration_live_gate(admission24, executor, root, core, proxy,
                actual.objects['validated'], core['source_commit'], 'joern05-before-dispatch')
    executor._check_resources(root, 127 * 1024 ** 3)
    table = executor._process_table()
    require(not controller._hashed_bifrost_contenders(table), 'foreign hashed Bifrost contender')
    return value


def command_spec(root: Path, core: dict, manifest_ref: dict, request_ref: dict,
                 parent_stage_ref: dict, *, graph: Any, lock_fd: int,
                 witness_fd: int, token: str, popen_monotonic: float) -> dict:
    """Exact source-bound singleton child command; this does not spawn it."""
    import sys
    from packet import canonical, digest, document, read_ref
    from admission import child_environment
    from bridge import assert_graph95_core
    assert_graph95_core(root, graph, core)
    source = core['adapter_module_refs']['joern05_supervisor']
    read_ref(root, source)
    group = next(g for g in document(root, core['contract'])['groups'] if g['id'] == GROUP)
    require(group['maximum_attempts'] == 5, 'command cap differs')
    require(type(lock_fd) is int and lock_fd > 2 and type(witness_fd) is int and witness_fd > 2,
            'command descriptors missing')
    argv = [sys.executable, '-B', '-E', str(root / source['path']), 'child',
            '--root', str(root), '--manifest', manifest_ref['path'], '--manifest-sha256', manifest_ref['sha256'],
            '--request', request_ref['path'], '--request-sha256', request_ref['sha256'],
            '--parent-stage', parent_stage_ref['path'], '--parent-stage-sha256', parent_stage_ref['sha256'],
            '--lock-fd', str(lock_fd), '--witness-fd', str(witness_fd),
            '--witness-token', token, '--popen-monotonic', repr(popen_monotonic)]
    value = {'argv': argv, 'environment': child_environment(group),
             'group_id': GROUP, 'attempt_id': ATTEMPT, 'manifest_ref': manifest_ref,
             'core_identity': core['core_identity'], 'parent_stage_ref': parent_stage_ref,
             'graph_sha256': graph.graph_sha256}
    return {**value, 'command_spec_sha256': digest(canonical(value))}


def qualify_stage(root: Path, core: dict, manifest_ref: dict, *, graph: Any, held_lock: Any) -> dict:
    """One actual before replay and command construction; zero Popen/dispatch.

    A separate reviewed qualification wrapper must own finite total runtime and
    exact invocation refs. This API never accepts an execution permit.
    """
    import os
    from packet import missing_prerequisites
    from bridge import create_parent, inherited_view
    from history import validate
    import time
    import secrets
    missing = missing_prerequisites(root, core['prerequisite_refs'], purpose='stage-qualification')
    require(not missing, 'qualification source/control bindings absent: ' + ','.join(missing))
    controller = graph.module('supervisor24')
    frozen = graph.module('bridge19')
    _held_proxy(root, core, graph, held_lock)
    lock = frozen.capture_lock(root, core['lock_path'], os.getpid(), controller._birth(os.getpid()))
    facts = validate(root)
    ledger = facts['ledger_prefix']
    stage = create_parent(root, core, manifest_ref, ledger, graph=graph, lock_identity=lock,
                          sidecars={}, runtime_role='joern05_stage_runtime',
                          runtime_ref=core['adapter_module_refs']['joern05_stage_runtime'])
    actual = frozen.runtime_objects(stage)
    require(actual.diagnostic['ledger_rows'] == 109 and
            actual.objects['checker_summary']['full_release_gate_satisfied'] is False,
            'qualification before-state must remain honest partial history')
    namespace = core['qualification_namespace']
    require(namespace != core['sidecar_namespace'] and
            not namespace.startswith(core['sidecar_namespace'] + '/'),
            'qualification must preserve fresh execution namespace')
    from pathlib import PurePosixPath
    path = PurePosixPath(namespace)
    require(not path.is_absolute() and '..' not in path.parts,
            'qualification namespace is not canonical')
    stage_ref = frozen.write_compact_stage_receipt(root, namespace + '/stage-00.json', stage,
        status='parent-stage-verified', sidecar_names=[], manifest_ref=manifest_ref,
        core_identity=core['core_identity'])
    request_ref = _write(root, graph, namespace + '/request.json', {
        'core_identity': core['core_identity'], 'manifest_ref': manifest_ref,
        'prerequisite_refs': core['prerequisite_refs']})
    # Anonymous pipe is construction-only here; no Popen or pipe witness is
    # emitted. Both descriptors close before the qualification result returns.
    read_fd, write_fd = controller._open_child_stage_identity_pipe()
    try:
        command = command_spec(root, core, manifest_ref, request_ref, stage_ref,
            graph=graph, lock_fd=held_lock.fileno(), witness_fd=write_fd,
            token=secrets.token_hex(16), popen_monotonic=time.monotonic())
    finally:
        os.close(read_fd)
        os.close(write_fd)
    return {'schema': 'v092-joern05-qualification/v1', 'status': 'actual-before-runtime-verified',
            'purpose': 'stage-qualification', 'execution_authorized': False,
            'analyzer_dispatches': 0, 'dispatch_groups': [GROUP],
            'fixed_commands': [command], 'stage_receipt': stage_ref,
            'runtime_authority_reusable_across_processes': False,
            'graph_sha256': graph.graph_sha256,
            'inherited_graph88_sha256': inherited_view(graph).graph_sha256,
            'stage_identity_sha256': stage.identity_sha256,
            'checker_summary': actual.objects['checker_summary']}


def run_parent(root: Path, core: dict, manifest_ref: dict, *, graph: Any,
               held_lock: Any) -> dict:
    """Durable singleton dispatch using inherited authenticated finite lifecycle.

    This API is never exercised against real evidence in preparation. It
    requires actual sealed review/authority/control artifacts, then creates
    fresh immutable runtime receipts and exactly one owned child. No retry.
    """
    import os
    import secrets
    import sys
    import subprocess
    import time
    from pathlib import PurePosixPath
    from packet import canonical, digest, document
    from admission import validate_execution_authority
    from bridge import create_parent, assert_graph95_core
    dispatch_groups(core)
    assert_graph95_core(root, graph, core)
    validate_execution_authority(root, core, manifest_ref, graph=graph)
    frozen = graph.module('bridge19')
    controller = graph.module('supervisor24')
    manifest = document(root, manifest_ref)
    slot = _slot(root, core, manifest)
    protocol24 = graph.module('protocol24')
    process = controller._process(os.getpid())
    lock = frozen.capture_lock(root, core['lock_path'], os.getpid(), process['birth_identity'])
    ledger = _snapshot(root, core, graph, 0)
    stage = create_parent(root, core, manifest_ref, ledger, graph=graph, lock_identity=lock,
                          sidecars={}, runtime_role='joern05_stage_runtime',
                          runtime_ref=core['adapter_module_refs']['joern05_stage_runtime'])
    stage_ref = _stage_receipt(root, core, manifest_ref, stage, graph)
    _fresh_gate(root, core, graph, stage, held_lock)
    request_ref = _write(root, graph, core['sidecar_namespace'] + '/request.json', {
        'core_identity': core['core_identity'], 'manifest_ref': manifest_ref,
        'prerequisite_refs': core['prerequisite_refs']})
    parent_permit = controller.raw_permit(os.getpid(), {'argv': list(sys.orig_argv),
                            'command_spec_sha256': None}, scope='parent', stage=stage)
    parent_ref = _write(root, graph, core['sidecar_namespace'] + '/parent-admission.json', {
        'schema': 'v092-joern05-parent-admission/v1', 'status': 'admitted',
        'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
        'stage_ref': stage_ref, 'permit': parent_permit,
        'external_review': core['prerequisite_refs']['external_launch_review'],
        'authorization_bundle': core['prerequisite_refs']['authorization_bundle']})
    started = time.monotonic()
    read_fd, write_fd = controller._open_child_stage_identity_pipe()
    token = secrets.token_hex(16)
    child = None
    child_process = None
    channel = None
    stdout = stderr = None
    try:
        spec = command_spec(root, core, manifest_ref, request_ref, stage_ref, graph=graph,
            lock_fd=held_lock.fileno(), witness_fd=write_fd, token=token, popen_monotonic=started)
        # Fresh exclusive streams; failure before Popen consumes no attempt.
        out = root / core['sidecar_namespace']
        stdout = (out / 'child-stdout.txt').open('xb')
        stderr = (out / 'child-stderr.txt').open('xb')
        child = subprocess.Popen(spec['argv'], cwd=root, env=spec['environment'],
                    start_new_session=True, close_fds=True,
                    pass_fds=(held_lock.fileno(), write_fd), stdout=stdout, stderr=stderr)
        os.close(write_fd)
        write_fd = -1
        channel = controller._ChildStageIdentityChannel(read_fd)
        read_fd = -1
        # Protect every fallible operation after Popen with owned cleanup.
        child_process = controller._process(child.pid)
        permit = controller.raw_permit(child.pid, spec, group_id=GROUP, attempt_id=ATTEMPT, stage=stage)
        permit_path = str(PurePosixPath(slot['admission_path']).parent / 'supervisor-permit.json')
        permit_ref = _write(root, graph, permit_path, permit)
        _fresh_gate(root, core, graph, stage, held_lock)
        group_ref = _write(root, graph, slot['admission_path'], {
            'schema': 'v092-joern05-group-admission/v1', 'status': 'admitted',
            'group_id': GROUP, 'attempt_id': ATTEMPT, 'parent_admission': parent_ref,
            'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
            'parent_stage_ref': stage_ref, 'process': child_process,
            'supervisor_permit_ref': permit_ref, 'command': spec})
        phase_ref = _write(root, graph, slot['phase_gate_path'], {
            'schema': 'v092-joern05-phase-gate/v1', 'group_id': GROUP, 'attempt_id': ATTEMPT,
            'admission_ref': group_ref, 'supervisor_permit_ref': permit_ref,
            'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
            'parent_stage_ref': stage_ref, 'process': child_process,
            'command_spec_sha256': spec['command_spec_sha256'], 'popen_monotonic': started})
        validated = frozen.runtime_objects(stage).objects['validated']
        terminal_path = f'reports/releases/v0.9.2/attempts/{ATTEMPT}/completed.json'
        timeout_path = str(PurePosixPath(slot['admission_path']).parent / 'coordinator-timeout.json')
        code = controller._wait_group_child(child, validated, GROUP, popen_monotonic=started,
            root=root, attempt_id=ATTEMPT, phase_receipt_path=slot['analyzer_phase_path'],
            timeout_evidence_path=timeout_path, terminal_receipt_path=terminal_path,
            parent_stage_ref=stage_ref, process=child_process, stage=stage, protocol=protocol24,
            child_stage_identity_channel=channel, child_stage_identity_token=token,
            parent_process=process)
        channel.close()
        cleanup = controller._bounded_reap_owned_group(child, child_process)
        require(cleanup.get('status') == 'reaped', 'owned child/descendants not contained')
        terminal_raw = (root / terminal_path).read_bytes()
        import json
        terminal = json.loads(terminal_raw)
        graph.module('joern05_protocol')._terminal_identity(terminal, group_id=GROUP, attempt_id=ATTEMPT,
            source_commit=core['source_commit'], plan_commit=core['plan_commit'],
            contract_sha256=core['contract']['sha256'], execution_series=2,
            label='Joern05 actual terminal')
        next_ledger = _snapshot(root, core, graph, 1)
        loader = graph.module('joern05_stage_runtime').load_runtime_context
        runtime, _ = frozen.load_runtime_stage(root, graph=graph, runtime_loader=loader,
            mode='after', core_identity=core, ledger_bytes=(root / next_ledger['path']).read_bytes())
        transition = [stage_ref, parent_ref, permit_ref, group_ref, phase_ref,
                      {'path': terminal_path, 'sha256': digest(terminal_raw)}]
        successor = frozen.build_successor_stage(root, predecessor=stage, index=1,
            ledger_after=next_ledger, runtime=runtime, graph=graph,
            source_commit=core['source_commit'], plan_commit=core['plan_commit'],
            contract_sha256=core['contract']['sha256'],
            sidecars={r['path']: r for r in transition},
            source_refs=[{'path': r.path, 'sha256': r.sha256} for r in stage.inventory[1:]],
            analyzer_deadline_seconds=stage.identity.analyzer_deadline_seconds,
            live_ledger={'path': 'reports/releases/v0.9.2/ledger-v1.jsonl',
                         'sha256': next_ledger['sha256']})
        actual = frozen.runtime_objects(successor).objects
        loaders = graph.module('runtime_loaders24')
        with loaders.scoped_runtime_loaders(root, executor=actual['modules']['executor'],
                graph=graph, module_names=loaders.PRODUCTION_MODULE_NAMES):
            safety = controller._terminal_continuation_safety(root, core, terminal,
                digest(terminal_raw), actual['modules']['executor'], graph.module('admission24'),
                actual['validated'], _held_proxy(root, core, graph, held_lock),
                protocol=graph.module('joern05_protocol'), disk=graph.module('disk_guard'))
        result = {'schema': 'v092-joern05-completion/v1', 'group_id': GROUP,
                  'attempt_id': ATTEMPT, 'terminal': transition[-1], 'child_exit_code': code,
                  'cleanup': cleanup, 'continuation_safety': safety,
                  'checker_summary': actual['checker_summary'],
                  'configuration_summary': actual['configuration_summary'], 'automatic_retry': False}
        finalized = frozen.write_completion(root, predecessor=stage, successor=successor,
            completion_path=slot['completion_path'], completion=result,
            expected_group_id=GROUP, expected_attempt_id=ATTEMPT, graph=graph)
        result['stage_after'] = _stage_receipt(root, core, manifest_ref, finalized, graph,
                                             predecessor_ref=stage_ref)
        _write(root, graph, core['sidecar_namespace'] + '/outcome.json', result)
        require(code == 0 and terminal['status'] == 'completed' and terminal['exit_code'] == 0
                and terminal['timed_out'] is False, 'Joern05 retained non-success; no retry')
        require_full_summary(actual['checker_summary'], actual['configuration_summary'])
        return result
    except BaseException as error:
        cleanup = None
        if child is not None:
            cleanup = controller._bounded_reap_owned_group(child, child_process) if child_process else controller._bounded_reap_unidentified_child(child)
        _write(root, graph, core['sidecar_namespace'] + '/stop.json', {
            'schema': 'v092-joern05-stop/v1', 'status': 'stopped', 'automatic_retry': False,
            'group_id': GROUP, 'attempt_id': ATTEMPT, 'error_type': type(error).__name__,
            'error': str(error), 'cleanup': cleanup, 'semantic_completion_inferred': False})
        raise
    finally:
        if channel is not None:
            channel.close()
        for fd in (read_fd, write_fd):
            if fd >= 0:
                os.close(fd)
        for stream in (stdout, stderr):
            if stream is not None:
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()


def _read_current_request(root: Path, request_ref: dict, manifest_ref: dict) -> dict:
    """An envelope carries references only; its core must equal the sealed file."""
    from packet import document, bound_current_core
    request = document(root, request_ref)
    require(set(request) == {'core_identity', 'manifest_ref', 'prerequisite_refs'},
            'request fields differ')
    require(request['manifest_ref'] == manifest_ref, 'request manifest differs')
    value = document(root, request['core_identity'])
    core = {**value, 'core_identity': request['core_identity'],
            'prerequisite_refs': request['prerequisite_refs']}
    bound_current_core(root, core)
    require(core['prerequisite_refs']['current_manifest'] == manifest_ref,
            'request prerequisite manifest differs')
    require(document(root, manifest_ref)['core_identity'] == core['core_identity'],
            'manifest refers to another core')
    return core


def _read_file_ref(root: Path, path: str) -> tuple[dict, dict]:
    """Use the inherited stable stat/hash/stat reader, then our strict ref reader."""
    from packet import document
    # This is a source bootstrap, before any inherited module is available.
    # Ref creation rejects symlinks and is followed by strict stat/hash/stat read.
    import os
    from packet import digest, require, read_ref
    from pathlib import PurePosixPath
    relative = PurePosixPath(path)
    require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe sidecar path')
    current = root
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), 'sidecar symlink denied')
    before = current.stat()
    require(current.is_file(), 'sidecar is not a file')
    raw = current.read_bytes()
    after = current.stat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    require(all(getattr(before, k) == getattr(after, k) for k in fields), 'sidecar changed during read')
    ref = {'path': path, 'sha256': digest(raw)}
    read_ref(root, ref)
    return ref, document(root, ref)


def consume_dispatch(root: Path, core: dict, manifest_ref: dict, *, graph: Any,
                     request_ref: dict, parent_ref: dict, lock_fd: int,
                     witness_fd: int, token: str, popen_monotonic: float) -> dict:
    """Child-only handshake, real opaque rebuild, then one guarded run_group.

    Each child constructs its own graph and runtime. Compact receipts are
    metadata witnesses, never serialized opaque contexts. The 120-second
    handshake precedes historical evidence work and charges original Popen time.
    """
    import fcntl
    import os
    import sys
    import time
    from pathlib import PurePosixPath
    from packet import document, canonical, digest
    from admission import require_markers, validate_execution_authority
    from bridge import create_child, child_ledger_selector, assert_graph95_core
    require_markers(dict(os.environ))
    assert_graph95_core(root, graph, core)
    controller = graph.module('supervisor24')
    frozen = graph.module('bridge19')
    manifest = document(root, manifest_ref)
    slot = _slot(root, core, manifest)
    require(type(popen_monotonic) is float and popen_monotonic > 0,
            'original Popen clock missing')
    deadline = popen_monotonic + 120.0
    # Never acquire/replay native evidence while waiting for the same parent.
    while not all((root / slot[k]).is_file() for k in ('admission_path', 'phase_gate_path')):
        require(time.monotonic() < deadline, 'child admission handshake expired')
        time.sleep(0.05)
    require(time.monotonic() <= deadline, 'child admission handshake arrived late')
    group_ref, group = _read_file_ref(root, slot['admission_path'])
    phase_ref, phase = _read_file_ref(root, slot['phase_gate_path'])
    permit_path = str(PurePosixPath(slot['admission_path']).parent / 'supervisor-permit.json')
    permit_ref, permit = _read_file_ref(root, permit_path)
    parent = frozen._read_compact_parent(root, parent_ref, core=core)
    for value, schema in ((group, 'v092-joern05-group-admission/v1'),
                          (phase, 'v092-joern05-phase-gate/v1')):
        require(value.get('schema') == schema and value.get('group_id') == GROUP
                and value.get('attempt_id') == ATTEMPT, 'dispatch receipt identity differs')
        require(value.get('manifest_ref') == manifest_ref and
                value.get('core_identity') == core['core_identity'] and
                value.get('parent_stage_ref') == parent_ref and
                value.get('supervisor_permit_ref') == permit_ref,
                'dispatch receipt context differs')
    require(phase['admission_ref'] == group_ref and phase['popen_monotonic'] == popen_monotonic,
            'phase admission/original clock differs')
    process = controller._process(os.getpid())
    require(group['process'] == phase['process'] == process, 'child exact birth differs')
    require(permit.get('schema') == controller.RAW_PERMIT_SCHEMA and permit.get('scope') == 'group'
            and permit.get('automatic_retry') is False and permit.get('pid') == os.getpid()
            and permit.get('birth') == process['birth_identity'] and permit.get('group_id') == GROUP
            and permit.get('attempt_id') == ATTEMPT, 'raw live process permit differs')
    unsigned = dict(permit)
    unsigned['permit_id'] = None
    require(permit.get('permit_id') == digest(canonical(unsigned)), 'raw permit digest differs')
    require(permit.get('argv_sha256') == digest(canonical(list(sys.orig_argv))),
            'child full interpreter invocation differs')
    expected = command_spec(root, core, manifest_ref, request_ref, parent_ref,
        graph=graph, lock_fd=lock_fd, witness_fd=witness_fd, token=token,
        popen_monotonic=popen_monotonic)
    require(group['command'] == expected and
            expected['argv'] == sys.orig_argv and
            permit.get('command_spec_sha256') == phase['command_spec_sha256'] ==
            expected['command_spec_sha256'], 'child command/environment spec differs')
    # Environment is exact, not ambient. The parent used the reviewed group env.
    require(all(os.environ.get(key) == value for key, value in expected['environment'].items()),
            'child reviewed environment differs')
    require(parent['manifest_ref'] == manifest_ref and parent['core_identity'] == core['core_identity']
            and parent['graph_sha256'] == graph.graph_sha256 == permit.get('graph_sha256')
            and parent['stage_identity_sha256'] == permit.get('stage_identity_sha256') ==
            permit.get('parent_stage_identity_sha256'), 'child parent graph/stage escaped')
    admitted_parent = document(root, group['parent_admission'])
    require(admitted_parent.get('schema') == 'v092-joern05-parent-admission/v1' and
            admitted_parent.get('status') == 'admitted' and
            admitted_parent.get('manifest_ref') == manifest_ref and
            admitted_parent.get('core_identity') == core['core_identity'] and
            admitted_parent.get('stage_ref') == parent_ref and
            admitted_parent.get('external_review') == core['prerequisite_refs']['external_launch_review'] and
            admitted_parent.get('authorization_bundle') == core['prerequisite_refs']['authorization_bundle'],
            'child parent admission differs')
    parent_permit = admitted_parent['permit']
    parent_unsigned = dict(parent_permit)
    parent_unsigned['permit_id'] = None
    require(parent_permit.get('schema') == controller.RAW_PERMIT_SCHEMA and
            parent_permit.get('scope') == 'parent' and parent_permit.get('automatic_retry') is False and
            parent_permit.get('pid') == parent['lock']['parent_pid'] and
            parent_permit.get('birth') == parent['lock']['parent_birth'] and
            parent_permit.get('stage_identity_sha256') == parent['stage_identity_sha256'] and
            parent_permit.get('graph_sha256') == graph.graph_sha256 and
            parent_permit.get('permit_id') == digest(canonical(parent_unsigned)),
            'child parent process permit differs')
    owner = parent['lock']
    require(owner['parent_pid'] == os.getppid() and
            controller._birth(os.getppid()) == owner['parent_birth'], 'child creator birth differs')
    held = os.fstat(lock_fd)
    target = Path(core['lock_path'])
    require(target.is_absolute() and not target.is_symlink(), 'canonical lock is unsafe')
    actual = target.stat()
    require((held.st_dev, held.st_ino) == (owner['dev'], owner['ino']) ==
            (actual.st_dev, actual.st_ino), 'inherited lock identity differs')
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    validate_execution_authority(root, core, manifest_ref, graph=graph)
    registered = controller._registered_group_timeout({'plan': document(root, core['contract'])}, GROUP)
    lease = frozen.Lease(popen_monotonic, registered, 600)
    frozen.validate_lease_progress(lease, now_monotonic=time.monotonic(),
                                   registered_deadline_seconds=registered)
    sidecars = {r['path']: r for r in (group_ref, phase_ref, permit_ref)}
    child = create_child(root, core, manifest_ref, parent_ref, child_ledger_selector(parent),
        graph=graph, lock_identity=frozen.LockIdentity(**owner), lease=lease,
        child_identity={'creator_pid': os.getppid(), 'creator_birth': owner['parent_birth'],
                        'pid': os.getpid(), 'birth': process['birth_identity']},
        sidecars=sidecars, runtime_role='joern05_stage_runtime',
        runtime_ref=core['adapter_module_refs']['joern05_stage_runtime'])
    witness = graph.module('admission24').validate_child_stage_from_receipt(
        root, child, parent_receipt_ref=parent_ref, graph=graph, manifest_ref=manifest_ref,
        core_identity=core['core_identity'], core=core, dispatch_sidecars=sidecars,
        now_monotonic=time.monotonic(), stage_bridge=frozen)
    controller._write_child_stage_identity(witness_fd, group_id=GROUP, attempt_id=ATTEMPT,
        token=token, child_stage=child, child_process=process,
        parent_process={'pid': owner['parent_pid'], 'birth_identity': owner['parent_birth']},
        parent_stage=parent, parent_stage_ref=parent_ref, graph_sha256=graph.graph_sha256,
        source_commit=core['source_commit'], plan_commit=core['plan_commit'],
        contract_sha256=core['contract']['sha256'])
    ready_ref = controller._write_child_stage_witness(root,
        controller._child_stage_witness_path(slot['analyzer_phase_path']), witness,
        graph.module('protocol24'))
    return run_child_group(root, core, manifest_ref, graph=graph, child=child,
        parent_ref=parent_ref, dispatch_sidecars=sidecars, lock_fd=lock_fd,
        popen_monotonic=popen_monotonic, phase_bindings={
            'phase_receipt_path': slot['analyzer_phase_path'], 'process': process,
            'child_stage_witness': witness, 'child_stage_witness_ref': ready_ref})




def execute_recorded(root: Path, core: dict, manifest_ref: dict, *, graph: Any,
                     held_lock: Any) -> dict:
    """Record this exact parent's return code; never infer a missing terminal."""
    import os
    import datetime as dt
    controller = graph.module('supervisor24')
    process = controller._process(os.getpid())
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = None
    error = None
    try:
        result = run_parent(root, core, manifest_ref, graph=graph, held_lock=held_lock)
        return result
    except BaseException as caught:
        error = {'type': type(caught).__name__, 'message': str(caught)}
        raise
    finally:
        _write(root, graph, core['sidecar_namespace'] + '/supervision/parent-exit.json', {
            'schema': 'v092-joern05-parent-exit/v1', 'status': 'controller-returned' if error is None else 'controller-raised',
            'automatic_retry': False, 'process': process, 'started_utc': started,
            'ended_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'exit_code': 0 if error is None else 1, 'error': error,
            'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
            'graph_sha256': graph.graph_sha256, 'source_commit': core['source_commit'],
            'plan_commit': core['plan_commit'], 'contract': core['contract'],
            'actual_outcome_returned': result is not None,
            'semantic_completion_inferred': False})

def bootstrap_parent(root: Path, core: dict, manifest_ref: dict, request_ref: dict,
                     *, graph: Any, held_lock: Any) -> dict:
    """Detach exactly one owned durable parent; return startup evidence only.

    The bootstrap holds the existing canonical lock through child birth and
    immutable startup receipt. The new parent acquires its own lock after this
    function returns, reconstructs its own graph, and owns the complete finite
    analyzer lifecycle. No opaque runtime is passed between these processes.
    """
    import os
    import secrets
    import sys
    import subprocess
    from packet import document, read_ref, canonical, digest
    from admission import validate_execution_authority, child_environment
    from bridge import assert_graph95_core
    assert_graph95_core(root, graph, core)
    validate_execution_authority(root, core, manifest_ref, graph=graph)
    _held_proxy(root, core, graph, held_lock)
    source = core['adapter_module_refs']['joern05_supervisor']
    read_ref(root, source)
    group = next(g for g in document(root, core['contract'])['groups'] if g['id'] == GROUP)
    argv = [sys.executable, '-B', '-E', str(root / source['path']), 'execution',
            '--root', str(root), '--manifest', manifest_ref['path'],
            '--manifest-sha256', manifest_ref['sha256'], '--request', request_ref['path'],
            '--request-sha256', request_ref['sha256']]
    controller = graph.module('supervisor24')
    directory = core['sidecar_namespace'] + '/supervision'
    startup_receipt_path = _startup_receipt_path(core)
    startup_token = secrets.token_hex(16)
    for filename in ('bootstrap-started.json', 'bootstrap-result.json', 'bootstrap-failed.json',
                     'parent-stdout.txt', 'parent-stderr.txt', 'startup-ready.json'):
        target = root / directory / filename
        require(not target.exists() and not target.is_symlink(), 'bootstrap outputs must be fresh')
    startup_read_fd, startup_write_fd = os.pipe()
    os.set_inheritable(startup_read_fd, False)
    os.set_inheritable(startup_write_fd, True)
    startup_lock_fd = held_lock.fileno()
    argv.extend(['--lock-fd', str(startup_lock_fd), '--startup-fd', str(startup_write_fd),
                 '--startup-token', startup_token, '--startup-receipt', startup_receipt_path])
    # Once-only marker is exclusive even if Popen itself fails. Recovery needs
    # a new reviewed namespace; this function never retries a consumed launch.
    started = _write(root, graph, directory + '/bootstrap-started.json', {
        'schema': 'v092-joern05-bootstrap/v1', 'status': 'starting-owned-parent',
        'automatic_retry': False, 'manifest_ref': manifest_ref,
        'core_identity': core['core_identity'], 'request_ref': request_ref,
        'source': source, 'argv_sha256': digest(canonical(argv)),
        'graph_sha256': graph.graph_sha256, 'startup_receipt_path': startup_receipt_path,
        'startup_token': startup_token, 'lock_ownership': 'inherited-open-file-description',
        'semantic_completion_inferred': False})
    parent = keepawake = None
    parent_identity = awake_identity = None
    ready = None
    out = err = None
    try:
        out = (root / directory / 'parent-stdout.txt').open('xb')
        err = (root / directory / 'parent-stderr.txt').open('xb')
        parent = subprocess.Popen(argv, cwd=root, env=child_environment(group),
            start_new_session=True, close_fds=True, stdin=subprocess.DEVNULL,
            stdout=out, stderr=err,
            pass_fds=(startup_lock_fd, startup_write_fd))
        os.close(startup_write_fd)
        startup_write_fd = -1
        parent_identity = controller._process(parent.pid)
        require(parent.poll() is None, 'durable parent exited before bootstrap witness')
        bootstrap_process = controller._process(os.getpid())
        ready = await_startup_ready(root, core, manifest_ref, child=parent,
            read_fd=startup_read_fd, expected_process=parent_identity,
            expected_parent_process=bootstrap_process,
            expected_lock=_startup_lock_identity(startup_lock_fd), token=startup_token,
            receipt_path=startup_receipt_path, expected_graph_sha256=graph.graph_sha256)
        os.close(startup_read_fd)
        startup_read_fd = -1
        keepawake = subprocess.Popen(['/usr/bin/caffeinate', '-w', str(parent.pid)],
            start_new_session=True, close_fds=True, stdin=subprocess.DEVNULL,
            stdout=out, stderr=err)
        awake_identity = controller._process(keepawake.pid)
        require(keepawake.poll() is None, 'keepawake exited before bootstrap witness')
        value = {'schema': 'v092-joern05-bootstrap/v1', 'status': 'owned-parent-started',
            'automatic_retry': False, 'manifest_ref': manifest_ref, 'core_identity': core['core_identity'],
            'started_ref': started, 'parent': parent_identity, 'keepawake': awake_identity,
            'argv_sha256': digest(canonical(argv)), 'graph_sha256': graph.graph_sha256,
            'startup_ready': ready['receipt_ref'], 'startup_frame': ready['frame'],
            'lock_ownership': 'inherited-open-file-description',
            'execution_terminal_observed': False, 'semantic_completion_inferred': False}
        value['receipt_ref'] = _write(root, graph, directory + '/bootstrap-result.json', value)
        return value
    except BaseException as error:
        cleanup = {}
        for label, child, identity in (('keepawake', keepawake, awake_identity),
                                        ('parent', parent, parent_identity)):
            if child is not None:
                cleanup[label] = controller._bounded_reap_owned_group(child, identity) if identity else controller._bounded_reap_unidentified_child(child)
        _write(root, graph, directory + '/bootstrap-failed.json', {
            'schema': 'v092-joern05-bootstrap/v1', 'status': 'bootstrap-failed',
            'automatic_retry': False, 'started_ref': started, 'error_type': type(error).__name__,
            'error': str(error), 'cleanup': cleanup,
            'startup_receipt_path': startup_receipt_path, 'startup_token': startup_token,
            'startup_ready': None if ready is None else ready['receipt_ref'],
            'lock_ownership': 'inherited-open-file-description',
            'semantic_completion_inferred': False})
        raise
    finally:
        for fd in (startup_read_fd, startup_write_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        for stream in (out, err):
            if stream is not None:
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()

def main(argv: list[str] | None=None) -> int:
    """Explicit qualification and execution purposes; never automatic retry."""
    import argparse
    import fcntl
    import json
    import os
    from packet import prepare_current_graph, canonical, require
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('stage-qualification', 'bootstrap', 'execution', 'child'))
    for name in ('root', 'manifest', 'manifest-sha256', 'request', 'request-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('parent-stage', 'parent-stage-sha256', 'witness-token'):
        parser.add_argument('--' + name)
    for name in ('lock-fd', 'witness-fd'):
        parser.add_argument('--' + name, type=int)
    parser.add_argument('--startup-fd', type=int)
    parser.add_argument('--startup-token')
    parser.add_argument('--startup-receipt')
    parser.add_argument('--popen-monotonic', type=float)
    args = parser.parse_args(argv)
    root = Path(args.root)
    require(root.is_absolute() and root.resolve() == root, 'root is not canonical')
    manifest = {'path': args.manifest, 'sha256': args.manifest_sha256}
    request = {'path': args.request, 'sha256': args.request_sha256}
    core = _read_current_request(root, request, manifest)
    with prepare_current_graph(root, core) as graph:
        current = graph.module('joern05_supervisor')
        if args.mode == 'child':
            require(all(value is not None for value in (args.parent_stage,
                args.parent_stage_sha256, args.witness_token, args.lock_fd,
                args.witness_fd, args.popen_monotonic)), 'child handshake arguments missing')
            try:
                current.consume_dispatch(root, core, manifest, graph=graph, request_ref=request,
                    parent_ref={'path': args.parent_stage, 'sha256': args.parent_stage_sha256},
                    lock_fd=args.lock_fd, witness_fd=args.witness_fd, token=args.witness_token,
                    popen_monotonic=args.popen_monotonic)
            finally:
                try:
                    os.close(args.witness_fd)
                except OSError:
                    pass
        else:
            if args.mode == 'execution':
                require(all(value is not None for value in
                            (args.lock_fd, args.startup_fd, args.startup_token,
                             args.startup_receipt)), 'execution startup handoff arguments missing')
                try:
                    current.startup_child_ready(root, core, manifest, graph=graph,
                        lock_fd=args.lock_fd, startup_fd=args.startup_fd,
                        token=args.startup_token, receipt_path=args.startup_receipt)
                    with os.fdopen(os.dup(args.lock_fd), 'rb') as lock:
                        value = current.execute_recorded(root, core, manifest,
                            graph=graph, held_lock=lock)
                    print(canonical(value).decode(), end='', flush=True)
                finally:
                    for fd in (args.startup_fd, args.lock_fd):
                        try:
                            os.close(fd)
                        except OSError:
                            pass
            else:
                path = Path(core['lock_path'])
                require(path.is_absolute() and not path.is_symlink(), 'canonical lock unsafe')
                flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                fd = os.open(path, flags)  # Existing lock only; no creation or truncation.
                try:
                    before = path.stat()
                    held = os.fstat(fd)
                    require((before.st_dev, before.st_ino) == (held.st_dev, held.st_ino), 'lock changed')
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    with os.fdopen(os.dup(fd), 'rb') as lock:
                        operation = current.bootstrap_parent if args.mode == 'bootstrap' else current.qualify_stage
                        value = operation(root, core, manifest, request, graph=graph, held_lock=lock) \
                            if args.mode == 'bootstrap' else operation(root, core, manifest, graph=graph, held_lock=lock)
                        print(canonical(value).decode(), end='', flush=True)
                finally:
                    os.close(fd)
    return 0


if __name__ == '__main__' and __spec__ is None:
    raise SystemExit(main())
