"""Private pending-plan native-control qualifier; never a scored Joern attempt.

No eligible plan or completed native controls are inputs. Root integration and
an exact independent invocation review are required before any CLI mode.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import contextvars
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import time
import threading
import uuid
from typing import Any

ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
GIB = 1024 ** 3
LOCK = Path('/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock')
CORE = {'path': 'reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-24/manifest-identity.json', 'sha256': 'b1b405d1f28bae9b84632de4830352ae9a27f352f47bbb49a3a046e2567add6d'}
OBSERVER = {'path': 'reports/releases/v0.9.2/acquisition/joern-native-startup-observer-06.py', 'sha256': 'aec2c68dfb12d9204fb12f66764bca0a18ed68edba88a57ad14a6faf9f759551'}
PLAN = {'path': 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-04/pending-execution-plan-01.json', 'sha256': '08ef4108097f399732ed84b4d81fa46fbf869edafaebb79fb156785cc4888888'}
LEDGER = {'path': 'reports/releases/v0.9.2/ledger-v1.jsonl', 'sha256': '2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851'}
PYTHON = '/opt/homebrew/bin/python3.13'
ORIGIN = '2026-10-20T00:57:00.680937+00:00'
FIELDS = {'schema', 'expected_head', 'ledger', 'observer', 'pending_plan', 'control_plan', 'evidence', 'agent_jar', 'agent_source', 'design', 'source_review', 'decision_review', 'authority', 'source_refs', 'namespace', 'tool_refs'}
REF_FIELDS = ('observer', 'pending_plan', 'control_plan', 'evidence', 'agent_jar', 'agent_source', 'design', 'source_review', 'decision_review', 'authority')


def require(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable(root: Path, ref: dict[str, str]) -> bytes:
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'exact reference fields required')
    value = ref['path']
    require(type(value) is str and value and not Path(value).is_absolute() and Path(value).as_posix() == value and '..' not in Path(value).parts, 'canonical relative reference required')
    require(type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'SHA256 required')
    path = root / value
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink reference forbidden')
    a = path.stat()
    require(stat.S_ISREG(a.st_mode) and a.st_size <= 256 * 1024 ** 2, 'bounded regular file required')
    raw = path.read_bytes()
    b = path.stat()
    sig = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(sig(a) == sig(b) and sha(raw) == ref['sha256'], 'artifact changed or digest differs')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'path changed to symlink')
    return raw


def document(root: Path, ref: dict[str, str]) -> dict[str, Any]:
    value = json.loads(stable(root, ref))
    require(type(value) is dict, 'JSON object required')
    return value


_OWNED_LOADS = contextvars.ContextVar('native_qualifier_owned_loads', default=None)

def release_owned_modules(loaded: list, start: int = 0) -> None:
    foreign = []
    for name, module in reversed(loaded[start:]):
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            foreign.append((name, module))
    loaded[start:] = list(reversed(foreign))
    require(not foreign, 'wrapper-owned module registry identity changed: ' + ', '.join(name for name, _ in foreign))


def attach_cleanup_error(primary: BaseException, cleanup: BaseException) -> None:
    detail = {'type': type(cleanup).__name__, 'message': str(cleanup)}
    errors = getattr(primary, 'native_module_cleanup_errors', [])
    primary.native_module_cleanup_errors = [*errors, detail]
    primary.add_note('Additional native module cleanup failure: ' + repr(cleanup))


@contextlib.contextmanager
def owned_module_scope():
    loaded: list = []
    token = _OWNED_LOADS.set(loaded)
    primary = None
    try:
        yield loaded
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            release_owned_modules(loaded)
        except BaseException as cleanup:
            if primary is None:
                raise
            attach_cleanup_error(primary, cleanup)
        finally:
            _OWNED_LOADS.reset(token)


def load(root: Path, ref: dict[str, str], prefix: str) -> Any:
    raw = stable(root, ref)
    name = prefix + '_' + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(name, root / ref['path'])
    require(spec is not None, 'module spec missing')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(root / ref['path']), 'exec'), module.__dict__)
    except BaseException as error:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            attach_cleanup_error(error, ValueError(
                'failed module execution registry identity changed: ' + name))
        raise
    loaded = _OWNED_LOADS.get()
    if loaded is not None:
        loaded.append((name, module))
    return module


def immutable(path: Path, value: Any) -> dict[str, str]:
    """Exclusive atomic/fsynced write; existing bytes are never reused."""
    raw = canonical(value)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'unsafe receipt ancestry')
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'unsafe receipt path')
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
    return {'path': str(path), 'sha256': sha(raw)}


def expected_environment(root: Path, cfg: dict, plan: dict) -> dict[str, str]:
    base = root / cfg['namespace']
    runtime = plan['runtime']
    java = runtime['java_home']
    return {'PATH': java + '/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'JAVA_HOME': java, 'SWIFTASTGEN_BIN': runtime['astgen'],
            'JAVA_OPTS': '-Xmx512m -XX:ActiveProcessorCount=2',
            '_JAVA_OPTIONS': '', 'JDK_JAVA_OPTIONS': '', 'CLASSPATH': '',
            'LANG': 'C', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1',
            'HOME': str(base / 'parent-home'), 'TMPDIR': str(base / 'tmp'),
            'DFB_CACHE_ROOT': str(base / 'cache'), 'BIFROST_CACHE_ROOT': str(base / 'cache'),
            'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1',
            'DATAFLOWBENCH_V092_QUALIFICATION': '1',
            'DATAFLOWBENCH_V092_GROUP_ID': 'joern-swift-common108'}


def validate_environment(env: dict, expected: dict) -> None:
    require(env == expected, 'exact clean native-control environment differs')
    for key in ('DATAFLOWBENCH_V092_RELEASE_EXECUTION', 'DATAFLOWBENCH_V092_QUALIFICATION'):
        require(env[key] == '1', 'guarded marker missing')
    require(env['CLASSPATH'] == env['_JAVA_OPTIONS'] == env['JDK_JAVA_OPTIONS'] == '', 'ambient Java options forbidden')
    require(env['LANG'] == env['LC_ALL'] == 'C', 'C locale required')



def required_source_closure(root: Path, cfg: dict) -> list[dict[str, str]]:
    """Derive the minimum from immutable authorities, not caller counts.

    Inventory entries describing installed tools remain covered by their sealed
    manifest; binaries outside the source repository are not source commits.
    Decision evidence is the actual explicit evidence list, never an inferred
    recursive walk through historical reports or installation inventories.
    """
    refs: dict[str, dict[str, str]] = {}
    runtime: set[str] = set()

    def add(value: dict, *, code: bool = False) -> None:
        require(type(value) is dict and {'path', 'sha256'} <= set(value), 'typed source reference required')
        path = value['path']
        if Path(path).is_absolute():
            require(Path(path).is_relative_to(root), 'source reference outside repository')
            path = Path(path).relative_to(root).as_posix()
        ref = {'path': path, 'sha256': value['sha256']}
        stable(root, ref)
        require(path not in refs or refs[path] == ref, 'conflicting required source path/SHA')
        refs[path] = ref
        if code and path.endswith('.py'):
            runtime.add(path)

    for name in REF_FIELDS:
        add(cfg[name], code=name == 'observer')
    for value in cfg['tool_refs'].values():
        add(value, code=True)
    add(CORE)
    core = document(root, CORE)
    require(type(core.get('source_inputs')) is list, 'inherited source_inputs missing')
    for value in core['source_inputs']:
        require(value.get('role') == 'release-input', 'inherited source role changed')
        add(value)
    add(core['contract'])
    contract = document(root, core['contract'])
    require(type(contract.get('source_inputs')) is list, 'inherited contract source_inputs missing')
    for value in contract['source_inputs']:
        require(value.get('role') == 'release-input', 'inherited contract source role changed')
        add(value)
    graph = core.get('runtime_module_graph')
    require(type(graph) is dict and len(graph) == 88, 'actual inherited88 source graph required')
    for value in graph.values():
        add(value, code=True)
    plan = document(root, cfg['pending_plan'])
    for values in plan['configurations'].values():
        for value in values:
            add(value)
    selected_cases = set(plan['cases'])
    control = document(root, cfg['control_plan'])
    selected_cases.update(control['controls'].values())
    population_seen: set[str] = set()
    population_refs = [value for values in plan['configurations'].values() for value in values
                       if value['path'].startswith('populations/')]
    for value in population_refs:
        population = document(root, value)
        for case in population['cases']:
            if case['id'] in selected_cases:
                add(case)
                population_seen.add(case['id'])
                for fixture in case['fixture_digests']:
                    add(fixture)
    if population_refs:
        require(selected_cases <= population_seen, 'selected plan/control fixture omitted from sealed populations')
    decisions = [case['decision'] for case in plan['cases'].values() if 'decision' in case]
    require(len(decisions) == 12, 'all12 pending native decisions required')
    for value in decisions:
        add(value)
        decision = document(root, value)
        require(type(decision.get('evidence')) is list and decision['evidence'], 'pending decision evidence missing')
        for evidence in decision['evidence']:
            add(evidence)
        for fixture in decision.get('current_fixture_digests', []):
            add(fixture)
    # Static local import/path closure supplements graph/source-input bindings.
    # Runtime tool paths are sealed through manifests and retained bootstrap;
    # no tool binary or generated output is silently treated as source code.
    process = 'scripts/swift_v2_process.py'
    add({'path': process, 'sha256': sha((root / process).read_bytes())}, code=True)
    visited: set[str] = set()
    while runtime - visited:
        path = sorted(runtime - visited)[0]
        visited.add(path)
        tree = ast.parse(stable(root, refs[path]), filename=path)
        candidates: set[Path] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [x.name for x in node.names] if isinstance(node, ast.Import) else [node.module or '']
                for name in names:
                    if name:
                        relative = Path(*name.split('.')).with_suffix('.py')
                        candidates.update((Path(path).parent / relative, Path('scripts') / relative))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith('.py'):
                value = Path(node.value)
                if not value.is_absolute() and '..' not in value.parts:
                    if node.value.startswith(('scripts/', 'reports/releases/v0.9.2/acquisition/')):
                        candidates.add(value)
                    elif len(value.parts) == 1:
                        candidates.add(Path(path).parent / value)
        for candidate in sorted(candidates):
            target = root / candidate
            if target.is_file():
                add({'path': candidate.as_posix(), 'sha256': sha(target.read_bytes())}, code=True)
    return [refs[path] for path in sorted(refs)]


def validate_request(root: Path, cfg: dict, *, check_git: bool = True) -> dict:
    require(root == ROOT and root.resolve() == root, 'canonical production root required')
    require(type(cfg) is dict and set(cfg) == FIELDS and cfg['schema'] == 'v092-joern-native-control-request/v1', 'exact pending-control request schema required')
    require(cfg['observer'] == OBSERVER and cfg['pending_plan'] == PLAN and cfg['ledger'] == LEDGER, 'sealed observer/plan/history differs')
    require(type(cfg['expected_head']) is str and re.fullmatch('[0-9a-f]{40}', cfg['expected_head']), 'actual committed HEAD required')
    path = Path(cfg['namespace'])
    prefix = Path('reports/releases/v0.9.2/qualification/joern-post-bifrost-01')
    require(not path.is_absolute() and path.as_posix() == cfg['namespace'] and '..' not in path.parts and path.parent == prefix and re.fullmatch('native-controls-[0-9]{2}', path.name), 'fresh canonical native-control namespace required')
    require(not any(p.is_symlink() for p in (root / path, *(root / path).parents)), 'unsafe output namespace ancestry')
    refs = [cfg[name] for name in REF_FIELDS]
    require(type(cfg['source_refs']) is list and len(cfg['source_refs']) > 0, 'exact reviewed source closure required')
    require(type(cfg['tool_refs']) is dict and set(cfg['tool_refs']) == {'wrapper', 'resources'}, 'wrapper/dependency bindings required')
    for ref in refs + cfg['source_refs'] + list(cfg['tool_refs'].values()):
        stable(root, ref)
    source_map = {ref['path']: ref for ref in cfg['source_refs']}
    require(len(source_map) == len(cfg['source_refs']), 'duplicate source closure entry')
    for name in ('observer', 'pending_plan', 'control_plan', 'evidence', 'agent_jar', 'agent_source'):
        require(source_map.get(cfg[name]['path']) == cfg[name], 'required source input is outside exact reviewed closure')
    for ref in cfg['tool_refs'].values():
        require(source_map.get(ref['path']) == ref, 'wrapper/dependency outside committed source closure')
    for required in required_source_closure(root, cfg):
        require(source_map.get(required['path']) == required, 'required committed source closure omitted or rebound: ' + required['path'])
    ledger = stable(root, cfg['ledger'])
    rows = [json.loads(line) for line in ledger.splitlines()]
    require(len(rows) == 109 and sum(r['status'] == 'completed' for r in rows) == 103, 'exact109/103 history required')
    plan = document(root, cfg['pending_plan'])
    require(plan['qualification_control_plan'] == cfg['control_plan'] and plan['status'] == 'qualification-pending' and plan['execution_eligible'] is False and plan['fresh_qualification'] is None, 'pending plan required, never fabricated eligible plan')
    require(plan['qualification_control_projection_sha256'] == '326487c047812a20f6c4f22f184a7faa4fc276e7c78ae1af317d5a750c0e8844', 'control projection changed')
    control = document(root, cfg['control_plan'])
    require(control['arms'] == ['off', 'on'] and len(control['controls']) == 6 and control['case_arm_count'] == 12 and control['maximum_phase_invocations'] == 36 and control['case_arm_budget_seconds'] == 75 and control['total_budget_seconds'] == 900 and control['scratch_allowance_bytes'] == 4 * GIB, 'six/12/36/75/900/4GiB policy differs')
    authority = document(root, cfg['authority'])
    require(authority.get('status') in {'approved', 'human-approved'} and authority.get('automatic_retry') is False and authority.get('publication_hold') is True, 'reviewed derived native-control authority required; publication held')
    if check_git:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        require(head == cfg['expected_head'], 'actual HEAD differs')
        for ref in cfg['source_refs']:
            raw = subprocess.check_output(['git', 'show', head + ':' + ref['path']], cwd=root)
            require(sha(raw) == ref['sha256'], 'source input does not match committed blob')
        dirty = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=root, text=True).splitlines()
        require(set(dirty) <= {LEDGER['path']}, 'tracked source dirty outside retained ledger')
    env = expected_environment(root, cfg, plan)
    validate_environment(env, expected_environment(root, cfg, plan))
    return {'plan': plan, 'control': control, 'environment': env, 'ledger_bytes': len(ledger), 'ledger_rows':109}


def validate_review(root: Path, ref: dict, request_ref: dict, cfg: dict) -> dict:
    review = document(root, ref)
    require(review.get('status') == 'approved-for-native-control-qualification-only' and review.get('automatic_retry') is False, 'independent exact native-control invocation approval required')
    b = review.get('bindings', {})
    expected = {'request_sha256': request_ref['sha256'], 'wrapper_sha256': cfg['tool_refs']['wrapper']['sha256'], 'resources_sha256': cfg['tool_refs']['resources']['sha256'], 'observer_sha256': cfg['observer']['sha256'], 'pending_plan_sha256': cfg['pending_plan']['sha256'], 'ledger_sha256': cfg['ledger']['sha256'], 'source_head': cfg['expected_head']}
    require(all(b.get(k) == v for k,v in expected.items()), 'exact invocation review binding differs')
    return review


@contextlib.contextmanager
def modules(root: Path, *, cleanup_receipt: Path | None = None):
    """Actual inherited88 graph; release only wrapper-owned later imports.

    Hosts exist before the graph snapshot and remain until frozen close. Loads
    after snapshot (resource/process helpers) are checked and removed FIRST.
    Foreign/replaced entries remain subject to the unchanged frozen boundary.
    """
    core = document(root, CORE)
    with owned_module_scope() as loaded:
        hosts = {}
        graph = None
        boundary = 0
        primary = None
        try:
            for role in ('bridge19', 'protocol24', 'admission24', 'supervisor24'):
                hosts[role] = load(root, core['runtime_module_graph'][role], '_native_host_' + role)
            graph = hosts['bridge19'].prepare_graph(root, core, host_modules=hosts)
            boundary = len(loaded)
            yield core, graph
        except BaseException as error:
            primary = error
            raise
        finally:
            failures = []
            if graph is not None:
                try:
                    release_owned_modules(loaded, boundary)
                except BaseException as cleanup:
                    failures.append(cleanup)
                try:
                    graph.import_context.close_on_error()
                except BaseException as cleanup:
                    failures.append(cleanup)
            if failures:
                if cleanup_receipt is not None and cleanup_receipt.parent.exists():
                    try:
                        immutable(cleanup_receipt, {'schema':'v092-native-module-cleanup-error/v1',
                            'original_error':None if primary is None else {'type':type(primary).__name__,'message':str(primary)},
                            'cleanup_errors':[{'type':type(e).__name__,'message':str(e)} for e in failures],
                            'automatic_retry':False,'qualification_inferred':False})
                    except BaseException as receipt_error:
                        failures.append(receipt_error)
                if primary is not None:
                    for cleanup in failures:
                        attach_cleanup_error(primary, cleanup)
                else:
                    for cleanup in failures[1:]:
                        attach_cleanup_error(failures[0], cleanup)
                    raise failures[0]


class Resources:
    """Same real policy authorities and complete retained source/scratch paths."""
    def __init__(self, root: Path, cfg: dict, core: dict, graph: Any):
        self.root, self.cfg, self.core, self.graph = root, cfg, core, graph
        self.helper = load(root, cfg['tool_refs']['resources'], '_native_resources')
        require(sha(Path(__file__).with_name('retained_resources.py').read_bytes()) == cfg['tool_refs']['resources']['sha256'], 'local resource dependency differs')
        self.contract = document(root, core['contract'])
        self.executor, self.disk = graph.module('executor'), graph.module('disk_guard')
        self.admission, self.protocol, self.bridge = (graph.module(n) for n in ('admission24', 'protocol24', 'bridge19'))
        self.paths = self.helper.accounting_paths(root, self.contract, self.executor, self.protocol)
        base = root / cfg['namespace']
        self.paths['scratch'].extend([base / 'capture', base / 'parent-home', base / 'tmp', base / 'cache'])
        supervision = root / (cfg['namespace'] + '-supervision')
        self.paths['scratch'].append(supervision)
        self.paths['retention'].extend((base, supervision))
        self.guard = self.disk.DiskGuard(launch_floor_bytes=127*GIB, protected_reserve_bytes=40*GIB, stop_margin_bytes=8*GIB, stop_floor_bytes=48*GIB, scratch_ceiling_bytes=24*GIB, retention_ceiling_bytes=24*GIB, working_ceiling_bytes=30*GIB)

    def sample(self, *, launch: bool = False) -> dict:
        live = self.admission._live_resources(self.root, self.core)
        cap = self.protocol.validate_working_cap(self.root, self.core)
        require(cap['authorized_change']['after_bytes'] == 30*GIB, 'aggregate30 authority changed')
        require(live['resource_policy']['minimum_free_gib'] == 127, 'schedule127 policy changed')
        measured = {k:self.guard.check(projected_bytes=0, category=k, paths=v, capacity_path=self.root, phase='launch' if launch else 'active') for k,v in self.paths.items()}
        free = min(v['free_bytes'] for v in measured.values())
        require(free >= 110*GIB and free >= (127 if launch else 125)*GIB, 'outer110 or schedule127/inner125 floor reached')
        require(self.guard.logical_size([self.root / self.cfg['namespace'] / 'capture']) <= 4*GIB, 'native control4GiB allowance reached')
        # Every retained source snapshot remains under the separate12GiB cap.
        groups = self.root / Path(*self.executor.EXECUTION_ROOT.parts)
        for series in groups.iterdir() if groups.exists() else ():
            for group in series.iterdir():
                for attempt in group.iterdir():
                    members = [attempt / Path(*self.protocol._relative(x, 'snapshot member').parts) for x in (*self.executor.SNAPSHOT_DIRECTORIES, *self.executor.SNAPSHOT_FILES, *(r['path'] for r in self.contract['source_inputs']), '.git')]
                    require(self.guard.logical_size(members) <= 12*GIB, 'retained per-source12GiB ceiling reached')
        return {'free_bytes':free, 'measurements':measured, 'working_cap_bytes':30*GIB, 'per_source_cap_bytes':12*GIB, 'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat()}

    def quick_sample(self) -> dict:
        free = self.guard._free_bytes(self.root)
        require(free >= 125 * GIB and free >= 110 * GIB, 'continuous inner125/outer110 floor reached')
        capture = self.root / self.cfg['namespace']
        require(self.guard.logical_size([capture / 'capture']) <= 4 * GIB, 'native control4GiB allowance reached')
        # New writes are restricted to this reviewed fresh namespace. Complete
        # historical source/scratch/retention scans continue in GuardMonitor.
        self.guard.check(projected_bytes=0, category='scratch', paths=[capture, self.root / (self.cfg['namespace'] + '-supervision')],
                         capacity_path=self.root, phase='active')
        self.guard.check(projected_bytes=0, category='retention', paths=[capture, self.root / (self.cfg['namespace'] + '-supervision')],
                         capacity_path=self.root, phase='active')
        return {'free_bytes': free}


class GuardMonitor:
    """Full historical scans never block the parent's finite phase clock.

    No category/path is excluded or cached. Each full scan runs unchanged,
    followed immediately by the next scan. Cheap active capacity checks run in
    the parent loop. Completion requires another full scan under the240s tail.
    """
    def __init__(self, resources: Any):
        self.resources = resources
        self.stop = threading.Event()
        self.error = None
        self.latest = None
        self.scans = 0
        self.final_thread = None
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _scan(self):
        started = time.monotonic()
        try:
            value = self.resources.sample(launch=False)
            self.latest = {'duration_seconds': time.monotonic() - started,
                           'completed_monotonic': time.monotonic(), 'sample': value}
            self.scans += 1
        except BaseException as error:
            self.error = error
            self.stop.set()

    def _loop(self):
        while not self.stop.is_set():
            self._scan()

    def check(self):
        if self.error is not None:
            raise RuntimeError('continuous full resource guard failed') from self.error
        self.resources.quick_sample()

    def finish(self, deadline: float):
        self.stop.set()
        self.thread.join(timeout=max(0, deadline - time.monotonic()))
        require(not self.thread.is_alive(), 'full resource guard did not stop within recording tail')
        self.check()
        # A final complete scan starts after the child returned. Its thread is
        # bounded by the same anchored recording tail, never a fresh timeout.
        self.final_thread = threading.Thread(target=self._scan, daemon=True)
        self.final_thread.start()
        self.final_thread.join(timeout=max(0, deadline - time.monotonic()))
        require(not self.final_thread.is_alive(), 'final resource scan exceeded recording tail')
        self.check()
        return {'full_scans': self.scans, 'last_full_scan': self.latest,
                'full_historical_coverage_unchanged': True}

    def cancel(self, deadline: float) -> bool:
        self.stop.set()
        self.thread.join(timeout=max(0, deadline - time.monotonic()))
        if self.final_thread is not None:
            self.final_thread.join(timeout=max(0, deadline - time.monotonic()))
        return not self.thread.is_alive() and (self.final_thread is None or not self.final_thread.is_alive())



def command(root: Path, request_ref: dict, review_ref: dict, lock_fd: int, witness_fd: int, token: str, parent: dict) -> list[str]:
    return [PYTHON, '-B', '-E', str(Path(__file__).resolve()), 'worker', '--request', request_ref['path'], '--request-sha256', request_ref['sha256'], '--review', review_ref['path'], '--review-sha256', review_ref['sha256'], '--lock-fd', str(lock_fd), '--witness-fd', str(witness_fd), '--token', token, '--parent-pid', str(parent['pid']), '--parent-birth', parent['birth_identity']]


def phase(fd: int, token: str, value: dict) -> None:
    raw = canonical({'token':token, **value})
    require(len(raw) < 4096, 'bounded atomic phase frame required')
    os.write(fd, raw)


def consume_frames(fd: int, pending: bytes, expected: dict, *, observed: float) -> tuple[bytes,list[dict]]:
    while select.select([fd], [], [], 0)[0]:
        raw = os.read(fd, 4096)
        if not raw:
            break
        pending += raw
        require(len(pending) <= 16384, 'phase channel exceeded bound')
    frames=[]
    while b'\n' in pending:
        line,pending=pending.split(b'\n',1)
        value=json.loads(line)
        require(type(value) is dict and set(value) == {'token','pid','birth_identity','phase','observed_monotonic'}, 'exact child phase fields required')
        require(all(value[k] == v for k,v in expected.items()), 'phase token/owned birth differs')
        stamp=value['observed_monotonic']
        require(type(stamp) in (int,float) and math.isfinite(stamp) and stamp <= observed, 'phase clock invalid')
        frames.append(value)
    return pending,frames


def contenders(executor: Any, controller: Any, proc: Any, tracked: dict) -> list[str]:
    native = proc.process_table()
    table = executor._process_table()
    filtered=[]
    for line in table.splitlines():
        fields=line.split(None,1)
        if fields and fields[0].isdigit():
            pid=int(fields[0])
            if pid in tracked and pid in native and native[pid][1] == tracked[pid]:
                continue
        filtered.append(line)
    text='\n'.join(filtered)
    return list(dict.fromkeys(executor._contenders(text) + controller._hashed_bifrost_contenders(text)))


def supervise(argv: list[str], *, root: Path, env: dict, stdout: Any, stderr: Any, lock_fd: int, request_sha: str, controller: Any, proc: Any, resources: Any, executor: Any, namespace: Path, token: str, read_fd: int, write_fd: int, popen: Any = subprocess.Popen, clock: Any = time.monotonic) -> dict:
    """Finite parent monitoring. Only this Popen tree is cleanup-authorized."""
    child=None; identity=None; tracked={}; cleanup=None; failure=None; code=None
    monitor = None
    guard_result = None
    anchor=clock(); state='handshake'; deadline=anchor+120; last_stamp=anchor; pending=b''; phases=[]
    def transition(frames):
        nonlocal state, deadline, last_stamp
        for frame in frames:
            name = frame['phase']
            stamp = frame['observed_monotonic']
            require(anchor <= stamp and last_stamp <= stamp <= deadline, 'late or reversed child phase')
            if state == 'handshake':
                require(name == 'ready', 'first phase must be ready')
                state, deadline = 'startup', anchor + 600
            elif state == 'startup':
                require(name == 'controls-started', 'control start phase required')
                state, deadline = 'controls', anchor + 600 + 900
            elif state == 'controls':
                require(name == 'controls-returned', 'control return phase required')
                state, deadline = 'recording', stamp + 240
            else:
                raise ValueError('unexpected extra phase')
            last_stamp = stamp
            phases.append(frame)
    try:
        child=popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,pass_fds=(lock_fd,write_fd))
        os.close(write_fd); write_fd=-1
        identity=controller._process(child.pid)
        birth=proc.start_identity(child.pid,None)
        require(birth is not None,'high-resolution owned root birth unavailable')
        tracked[child.pid]=birth
        immutable(namespace/'child-started.json',{'pid':child.pid,'birth_identity':identity['birth_identity'],'native_start_identity':birth,'popen_monotonic':anchor,'request_sha256':request_sha,'argv':argv,'environment':env,'automatic_retry':False})
        expected={'token':token,'pid':child.pid,'birth_identity':identity['birth_identity']}
        if hasattr(resources, 'quick_sample'):
            monitor = GuardMonitor(resources)
        while True:
            now=clock()
            pending,frames=consume_frames(read_fd,pending,expected,observed=now)
            transition(frames)
            table=proc.process_table();tracked=proc.descendants(table,tracked)
            require(not contenders(executor,controller,proc,tracked),'foreign analyzer/heavy contender')
            if monitor is not None:
                monitor.check()
            else:
                resources.sample(launch=False)
            code=child.poll()
            if code is not None:
                # Re-drain after exit closes exists/poll race. A valid finish
                # must have been consumed before completion can be accepted.
                pending,extra=consume_frames(read_fd,pending,expected,observed=clock())
                transition(extra)
                require(code==0 and state=='recording' and clock() <= deadline and not pending,'child failed/incomplete/late native control capture')
                if monitor is not None:
                    guard_result = monitor.finish(deadline)
                    require(clock() <= deadline, 'resource finalization exceeded anchored recording tail')
                break
            require(now <= deadline, 'native qualification '+state+' deadline expired')
            time.sleep(0.2)
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error)}
    finally:
        if write_fd>=0:os.close(write_fd)
        os.close(read_fd)
        if child is not None:
            try:
                # Retained exact-birth cleanup; no group signal without owned
                # Popen identity. Direct-child fallback when birth capture fails.
                group_witness = None
                if child.poll() is None:
                    try:
                        group_witness = os.getpgid(child.pid)
                    except OSError:
                        pass
                cleanup = (controller._bounded_reap_owned_group(child, identity)
                           if identity is not None and group_witness == child.pid
                           else controller._bounded_reap_unidentified_child(child))
                table=proc.process_table();tracked=proc.descendants(table,tracked)
                survivors=proc.active(table,tracked)
                for sig in (signal.SIGTERM,signal.SIGKILL):
                    for pid in reversed(survivors):
                        current=proc.process_table()
                        if pid in proc.active(current,tracked):os.kill(pid,sig)
                    until=clock()+1
                    while survivors and clock()<until:
                        time.sleep(.05);survivors=proc.active(proc.process_table(),tracked)
                require(not survivors,'tracked owned descendants survive cleanup')
                require(cleanup.get('coordinator_reaped') is True,'owned direct child not reaped')
            except BaseException as error:
                failure=failure or {'type':'CleanupError','message':str(error)}
                cleanup={'status':'containment-unknown','error':repr(error)}
        if monitor is not None:
            cleanup_deadline = deadline if state == 'recording' else min(deadline + 240, anchor + 1740)
            stopped = monitor.cancel(cleanup_deadline)
            if not stopped and failure is None:
                failure = {'type': 'GuardCleanupError', 'message': 'full scan did not finish within anchored cleanup bound'}
    return {'status':'process-returned' if failure is None else 'failed','exit_code':code,'failure':failure,'cleanup':cleanup,'phases':phases,'tracked_processes':[{'pid':p,'start_identity':b} for p,b in tracked.items()],'descendant_containment':'polling-unknown-even-if-no-tracked-survivors','automatic_retry':False,'qualification_inferred':False, 'resource_monitor':guard_result}



def validate_worker_argv(recorded: list[str], actual: list[str]) -> dict:
    """Retain raw argv and every argument; accept only proven interpreter IDs."""
    require(type(recorded) is list and type(actual) is list and recorded and actual,
            'worker argv records missing')
    require(recorded[0] == PYTHON and recorded[1:] == actual[1:],
            'worker command arguments differ')
    configured = Path(PYTHON).resolve(strict=True)
    executable = Path(sys.executable).resolve(strict=True)
    require(configured == executable and os.path.samefile(PYTHON, sys.executable) and sys.version_info[:2] == (3, 13),
            'worker interpreter differs from configured Python3.13')
    framework_app = configured.parent.parent / 'Resources/Python.app/Contents/MacOS/Python'
    allowed = {str(configured), PYTHON}
    if framework_app.is_file():
        allowed.add(str(framework_app))
    require(actual[0] in allowed, 'worker raw argv interpreter is not the configured launcher or exact framework app')
    native = configured.stat()
    return {'configured_path': PYTHON, 'configured_resolved': str(configured),
            'configured_native_identity':{'device':native.st_dev,'inode':native.st_ino},
            'configured_sha256': sha(configured.read_bytes()),
            'sys_executable': sys.executable, 'raw_executable': actual[0],
            'raw_executable_sha256': sha(Path(actual[0]).read_bytes()),
            'all_arguments_after_argv0_exact': True}



def run_worker(root: Path, cfg: dict, request_ref: dict, *, lock_fd: int, witness_fd: int, token: str, parent_pid: int, parent_birth: str) -> dict:
    with owned_module_scope():
        return _run_worker_body(root, cfg, request_ref, lock_fd=lock_fd, witness_fd=witness_fd,
                                token=token, parent_pid=parent_pid, parent_birth=parent_birth)


def _run_worker_body(root: Path, cfg: dict, request_ref: dict, *, lock_fd: int, witness_fd: int, token: str, parent_pid: int, parent_birth: str) -> dict:
    require(stable(root, cfg['tool_refs']['wrapper']) == Path(__file__).read_bytes(), 'worker source differs from invocation review')
    observer=load(root,cfg['observer'],'_native_observer06')

    controller=load(root,document(root,CORE)['runtime_module_graph']['supervisor24'],'_native_controller')
    require(os.getppid()==parent_pid and controller._birth(parent_pid)==parent_birth,'direct owned parent birth differs')
    started_ref = {'path':cfg['namespace'] + '/parent-started.json',
        'sha256':sha((root/cfg['namespace']/'parent-started.json').read_bytes())}
    started = document(root, started_ref)
    require(started['request'] == request_ref and started['source_head'] == cfg['expected_head']
        and started['ledger'] == cfg['ledger'] and started['process']['pid'] == parent_pid
        and started['process']['birth_identity'] == parent_birth, 'worker parent ownership/receipt differs')
    interpreter_identity = validate_worker_argv(started['argv'], sys.orig_argv)
    require(started.get('interpreter_identity') == interpreter_identity, 'worker interpreter differs from exact parent-observed native identity')
    held=os.fstat(lock_fd); current=LOCK.stat()
    require((held.st_dev,held.st_ino)==(current.st_dev,current.st_ino) and stat.S_ISREG(held.st_mode),'held common lock inode differs')
    # A separate descriptor must conflict with the parent's held flock.
    import fcntl
    other=os.open(LOCK,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        try:fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise ValueError('parent analyzer flock is not held')
    finally:os.close(other)
    identity=controller._process(os.getpid())
    pending = document(root, cfg['pending_plan'])
    require(dict(os.environ) == expected_environment(root, cfg, pending), 'worker environment differs')
    immutable(root/cfg['namespace']/'worker-invocation.json', {'schema':'v092-native-control-worker-invocation/v1',
        'request':request_ref, 'review':started['review'], 'parent_started_ref':started_ref,
        'process':identity, 'parent_process':started['process'],
        'recorded_popen_argv':started['argv'], 'actual_raw_argv':list(sys.orig_argv),
        'interpreter_identity':interpreter_identity, 'parent_interpreter_identity':started['interpreter_identity'], 'environment':dict(os.environ),
        'environment_sha256':sha(canonical(dict(os.environ))), 'automatic_retry':False})
    phase(witness_fd,token,{'phase':'ready','pid':os.getpid(),'birth_identity':identity['birth_identity'],'observed_monotonic':time.monotonic()})
    # The real observer.controls API performs its retained bootstrap validation
    # once. Do not repeat a separate13-second preflight or fabricate eligibility.
    phase(witness_fd,token,{'phase':'controls-started','pid':os.getpid(),'birth_identity':identity['birth_identity'],'observed_monotonic':time.monotonic()})
    result=observer.controls(root,str(root/cfg['namespace']/'capture'),new_plan_path=cfg['pending_plan']['path'],evidence_path=cfg['evidence']['path'],expected_new_plan_sha256=cfg['pending_plan']['sha256'],expected_evidence_sha256=cfg['evidence']['sha256'])
    phase(witness_fd,token,{'phase':'controls-returned','pid':os.getpid(),'birth_identity':identity['birth_identity'],'observed_monotonic':time.monotonic()})
    run=result['run']; summary=result['startup_observation']
    require(len(run['records'])==12 and run['phase_invocation_count']==36 and summary['qualification_safe'] is True,'actual12/36 startup capture incomplete')
    immutable(root/cfg['namespace']/'control-result.json',{'schema':'v092-native-control-qualification-result/v1','request':request_ref,'observer':cfg['observer'],'pending_plan':cfg['pending_plan'],'run':run,'startup_observation':summary,'scored_activation':False,'creates_unsupported_decisions':False,'automatic_retry':False})
    return result


@contextlib.contextmanager
def held_lock(helper: Any, inherited_fd: int | None):
    if inherited_fd is None:
        with helper.observe_existing_lock(LOCK) as value:
            yield value
        return
    import fcntl
    require(type(inherited_fd) is int and inherited_fd >= 0, 'inherited lock descriptor invalid')
    require(not any(p.is_symlink() for p in (LOCK, *LOCK.parents)), 'lock symlink forbidden')
    held, current = os.fstat(inherited_fd), LOCK.stat()
    require(stat.S_ISREG(held.st_mode) and (held.st_dev, held.st_ino) == (current.st_dev, current.st_ino), 'inherited lock inode differs')
    other = os.open(LOCK, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        try:
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ValueError('inherited analyzer lock is not held')
    finally:
        os.close(other)
    yield {'path': str(LOCK), 'dev': held.st_dev, 'ino': held.st_ino,
           'existing_only': True, 'fd': inherited_fd, 'bounded_handoff': 'same-open-file-description'}


def bootstrap(root: Path, cfg: dict, request_ref: dict, review_ref: dict) -> dict:
    """Detached parent owns inherited flock; explicit pipe releases startup."""
    checked = validate_request(root, cfg)
    validate_review(root, review_ref, request_ref, cfg)
    require(stable(root, cfg['tool_refs']['wrapper']) == Path(__file__).read_bytes(), 'wrapper source differs')
    directory = root / (cfg['namespace'] + '-supervision')
    require(not directory.exists() and not directory.is_symlink(), 'exclusive bootstrap namespace already exists')
    with modules(root, cleanup_receipt=directory/'module-cleanup-error.json') as (core, graph):
        helper = load(root, cfg['tool_refs']['resources'], '_bootstrap_resources')
        controller = graph.module('supervisor24')
        with helper.observe_existing_lock(LOCK) as lock:
            resources = Resources(root, cfg, core, graph)
            initial = resources.sample(launch=True)
            require(not contenders(graph.module('executor'), controller,
                load(root, next(r for r in cfg['source_refs'] if r['path'] == 'scripts/swift_v2_process.py'), '_bootstrap_process'), {}), 'foreign contender before bootstrap')
            directory.mkdir()
            immutable(directory / 'started.json', {'request': request_ref, 'review': review_ref, 'resources': initial, 'automatic_retry': False})
            read_fd, write_fd = os.pipe()
            token = uuid.uuid4().hex
            argv = [PYTHON, '-B', '-E', str(Path(__file__).resolve()), 'parent',
                    '--request', request_ref['path'], '--request-sha256', request_ref['sha256'],
                    '--review', review_ref['path'], '--review-sha256', review_ref['sha256'],
                    '--lock-fd', str(lock['fd']), '--bootstrap-read-fd', str(read_fd), '--token', token]
            child = awake = None
            identity = awake_identity = None
            try:
                with (directory / 'parent.stdout').open('xb') as out, (directory / 'parent.stderr').open('xb') as err:
                    child = subprocess.Popen(argv, cwd=root, env=checked['environment'], stdin=subprocess.DEVNULL,
                        stdout=out, stderr=err, start_new_session=True, pass_fds=(lock['fd'], read_fd))
                    os.close(read_fd)
                    read_fd = -1
                    identity = controller._process(child.pid)
                    awake = subprocess.Popen(['/usr/bin/caffeinate', '-w', str(child.pid)], cwd=root,
                        env=checked['environment'], stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
                    awake_identity = controller._process(awake.pid)
                    result = {'schema': 'v092-native-control-bootstrap/v1', 'status': 'owned-parent-started',
                        'parent': identity, 'keepawake': awake_identity, 'request': request_ref, 'review': review_ref,
                        'argv': argv, 'lock_inode': [lock['dev'], lock['ino']], 'automatic_retry': False,
                        'execution_terminal_observed': False, 'qualification_inferred': False}
                    immutable(directory / 'result.json', result)
                    os.write(write_fd, canonical({'token': token, 'request_sha256': request_ref['sha256']}))
                    for stream in (out, err):
                        stream.flush()
                        os.fsync(stream.fileno())
                    return result
            except BaseException as error:
                cleanup = {}
                for label, process, birth in (('parent', child, identity), ('keepawake', awake, awake_identity)):
                    if process is not None:
                        cleanup[label] = controller._bounded_reap_owned_group(process, birth) if birth else controller._bounded_reap_unidentified_child(process)
                immutable(directory / 'failed.json', {'status': 'bootstrap-failed', 'error': repr(error), 'cleanup': cleanup,
                    'request': request_ref, 'automatic_retry': False, 'qualification_inferred': False})
                raise
            finally:
                for fd in (read_fd, write_fd):
                    if fd >= 0:
                        os.close(fd)


def bootstrap_gate(fd: int, token: str, request_sha256: str) -> None:
    """Bounded anonymous-pipe handoff; parent never races a fresh LOCK_NB."""
    deadline = time.monotonic() + 120
    raw = b''
    try:
        while b'\n' not in raw:
            left = deadline - time.monotonic()
            require(left > 0 and select.select([fd], [], [], left)[0], 'bootstrap release handshake expired')
            block = os.read(fd, 4096)
            require(block and len(raw) + len(block) <= 4096, 'bootstrap release missing/oversized')
            raw += block
        require(json.loads(raw) == {'token': token, 'request_sha256': request_sha256}, 'bootstrap release token/request differs')
    finally:
        os.close(fd)


def run_parent(root: Path, cfg: dict, request_ref: dict, review_ref: dict, *, inherited_lock_fd: int | None = None) -> dict:
    checked=validate_request(root,cfg)
    validate_review(root,review_ref,request_ref,cfg)
    require(stable(root,cfg['tool_refs']['wrapper'])==Path(__file__).read_bytes(),'wrapper source differs')
    with modules(root, cleanup_receipt=root/cfg['namespace']/'module-cleanup-error.json') as (core,graph):
        helper=load(root,cfg['tool_refs']['resources'],'_native_resource_lock')
        with held_lock(helper, inherited_lock_fd) as lock:
            resources=Resources(root,cfg,core,graph)
            initial=resources.sample(launch=True)
            executor=graph.module('executor');controller=graph.module('supervisor24')
            proc_ref={'path':'scripts/swift_v2_process.py','sha256':sha((root/'scripts/swift_v2_process.py').read_bytes())}
            require(proc_ref in cfg['source_refs'],'retained process source not in reviewed committed closure')
            proc=load(root,proc_ref,'_native_process')
            require(not contenders(executor,controller,proc,{}),'foreign analyzer/heavy contender before startup')
            namespace=root/cfg['namespace'];require(not namespace.exists() and not namespace.is_symlink(),'native qualification namespace already exists')
            namespace.mkdir()
            for part in ('parent-home','tmp','cache'):(namespace/part).mkdir()
            read_fd,write_fd=os.pipe();token=uuid.uuid4().hex
            parent=controller._process(os.getpid())
            argv=command(root,request_ref,review_ref,lock['fd'],write_fd,token,parent)
            immutable(namespace/'parent-started.json',{'schema':'v092-native-control-parent/v1','request':request_ref,'review':review_ref,'process':parent,'argv':argv,'interpreter_identity':validate_worker_argv([PYTHON,*sys.orig_argv[1:]],list(sys.orig_argv)),'source_head':cfg['expected_head'],'ledger':cfg['ledger'],'resources':initial,'origin_utc':ORIGIN,'execution_window_seconds':None,'publication_hold':True,'automatic_retry':False})
            result=None
            with (namespace/'stdout.txt').open('xb') as out,(namespace/'stderr.txt').open('xb') as err:
                try:
                    result=supervise(argv,root=root,env=checked['environment'],stdout=out,stderr=err,lock_fd=lock['fd'],request_sha=request_ref['sha256'],controller=controller,proc=proc,resources=resources,executor=executor,namespace=namespace,token=token,read_fd=read_fd,write_fd=write_fd)
                    require(stable(root,cfg['ledger'])==stable(root,LEDGER),'ledger changed during native qualification')
                    if result['failure'] is None:
                        artifact=document(root,{'path':cfg['namespace']+'/control-result.json','sha256':sha((namespace/'control-result.json').read_bytes())})
                        require(artifact['request']==request_ref,'control result request differs')
                    immutable(namespace/'exit.json',{'schema':'v092-native-control-parent-exit/v1','request':request_ref,'result':result,'ended_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'qualification_inferred':False,'ledger_unchanged':True,'automatic_retry':False})
                except BaseException as error:
                    immutable(namespace/'exception.json',{'schema':'v092-native-control-parent-exception/v1','request':request_ref,'error_type':type(error).__name__,'error':str(error),'result':result,'automatic_retry':False,'qualification_inferred':False})
                    raise
                finally:
                    for stream in (out,err):stream.flush();os.fsync(stream.fileno())
            require(result['failure'] is None,'native control parent failed; inspect preserved receipts')
            return result


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('bootstrap','parent','worker'))
    for flag in ('request','request-sha256','review','review-sha256'):parser.add_argument('--'+flag,required=True)
    for flag in ('lock-fd','witness-fd','parent-pid','bootstrap-read-fd'):parser.add_argument('--'+flag,type=int)
    for flag in ('token','parent-birth'):parser.add_argument('--'+flag)
    args=parser.parse_args(argv)
    require(__debug__ and sys.version_info[:2]==(3,13),'unoptimized Python3.13 required')
    request={'path':args.request,'sha256':args.request_sha256};review={'path':args.review,'sha256':args.review_sha256}
    cfg=document(ROOT,request)
    if args.mode == 'bootstrap':
        print(canonical(bootstrap(ROOT, cfg, request, review)).decode(), end='', flush=True)
    elif args.mode == 'parent':
        if args.bootstrap_read_fd is not None:
            require(args.token is not None and args.lock_fd is not None, 'bootstrap lock/token missing')
            bootstrap_gate(args.bootstrap_read_fd, args.token, request['sha256'])
        try:
            print(canonical(run_parent(ROOT, cfg, request, review, inherited_lock_fd=args.lock_fd)).decode(), end='', flush=True)
        finally:
            if args.lock_fd is not None:
                os.close(args.lock_fd)
    else:
        try:
            validate_request(ROOT,cfg);validate_review(ROOT,review,request,cfg)
            require(all(getattr(args,n) is not None for n in ('lock_fd','witness_fd','parent_pid','token','parent_birth')),'worker handshake fields missing')
            run_worker(ROOT,cfg,request,lock_fd=args.lock_fd,witness_fd=args.witness_fd,token=args.token,parent_pid=args.parent_pid,parent_birth=args.parent_birth)
        finally:
            if args.witness_fd is not None:os.close(args.witness_fd)
    return 0


if __name__=='__main__' and __spec__ is None:
    raise SystemExit(main())
