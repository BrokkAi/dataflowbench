#!/usr/bin/env python3
"""Inert source-only selection builder; never imports qualifier or mutates Git.

Revision02 adds an explicit sealed private-stream copy map; no seal is omitted.
Root supplies exact reviewed inputs. Running this builder reads a finite explicit
closure and writes three fresh private drafts, not a request/commit/admission.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any

ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
HEAD = '76e6121651e94be113fd0d5f027419f7d0f0859b'
BRANCH = 'dave/v0.9.2-full-refresh'
PREFIX = 'reports/releases/v0.9.2/'
ACQ = PREFIX + 'acquisition/'
QUAL = PREFIX + 'qualification/joern-capability-repair-01/'
JQ = PREFIX + 'qualification/joern-post-bifrost-01/'
LEDGER = {'path': PREFIX + 'ledger-v1.jsonl', 'sha256': '2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851'}
BASE = {'path': JQ + 'native-control-request-04.json', 'sha256': 'e5fef8bf3a9d3b234c88f0b36731f5231ddde9dac044aa4029555780908459ea'}
STOP = {'path': PREFIX + 'validation/joern-post-bifrost-01/native-controls04-root-stop-check-01.json', 'sha256': '6d8958898aacaa53e6affb6708f1e3bcf2c008c0d33c7f2f4ffcc4390acd3e32'}
OBSERVER = {'path': ACQ + 'joern-native-startup-observer-07.py', 'sha256': '4e3998dfb3f32b5d377c8697ea644d247f147220679eb784cc64fc501f7bc199'}
JAR = {'path': ACQ + 'joern-startup-witness-agent-05.jar', 'sha256': '1e30a6a5c88abb0216c5f205bd337f18fc30dd91345a8aeae244398cc0803261'}
PLAN = {'path': QUAL + 'plan-v092-06/pending-execution-plan-01.json', 'sha256': '09d6748e23b670dbd8998a9f5f80075a25f4b388788004f36fd8b279bec5533e'}
CONTROL_SHA = '05d8b63d78df07ad4a66b4609573ffd051f5b44cf0416f316aab7b2dc9755a2f'
PROJECTION = 'a4c8f13af295d174f3aedff5665ab03e16457aace9859b36a0b3436e4f8b557f'
CAP = 100 * 1024 * 1024


def require(ok: Any, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def relative(value: str) -> str:
    require(type(value) is str and bool(value) and not any(x in value for x in ('\0', '\n', '\r')), 'invalid path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and p.as_posix() == value, 'noncanonical repository path: ' + value)
    return value


def no_symlinks(path: Path) -> None:
    require(path.is_absolute(), 'absolute path required')
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink forbidden: ' + str(part))


def stable(path: Path) -> bytes:
    no_symlinks(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode), 'regular file required: ' + str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            raw = handle.read()
        after = os.fstat(fd)
    finally:
        os.close(fd)
    final = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(opened) == identity(after) == identity(final) and len(raw) == final.st_size, 'file changed while reading: ' + str(path))
    return raw


def reference(item: Any) -> dict[str, str]:
    require(type(item) is dict and set(item) == {'path', 'sha256'}, 'exact path/SHA ref required')
    relative(item['path'])
    require(type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}', item['sha256']), 'invalid SHA256')
    require(item['path'] != LEDGER['path'], 'ledger forbidden in source closure')
    return dict(item)


def bound(item: dict[str, str], *, ledger: bool = False) -> bytes:
    if not ledger:
        reference(item)
    raw = stable(ROOT / relative(item['path']))
    require(digest(raw) == item['sha256'], 'bound SHA differs: ' + item['path'])
    return raw


def document(item: dict[str, str]) -> dict:
    value = json.loads(bound(item))
    require(type(value) is dict, 'JSON object required: ' + item['path'])
    return value


def git(*args: str, data: bytes | None = None) -> bytes:
    # Read-only Git commands only, explicitly disable optional stat-cache writes.
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    return subprocess.run(['git', *args], cwd=ROOT, env=env, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def git_state() -> set[str]:
    require(git('rev-parse', 'HEAD').decode().strip() == HEAD, 'HEAD differs')
    require(git('symbolic-ref', '--quiet', '--short', 'HEAD').decode().strip() == BRANCH, 'branch differs/detached')
    require(not git('diff', '--cached', '--name-only', '-z'), 'index contains staged changes')
    dirty = git('diff', 'HEAD', '--name-only', '-z').decode().split('\0')
    require([x for x in dirty if x] == [LEDGER['path']], 'tracked dirt is not exact ledger-only')
    bound(LEDGER, ledger=True)
    return set(x for x in git('ls-files', '-z').decode().split('\0') if x)


def committed_same(refs: list[dict[str, str]]) -> None:
    """Verify finite tracked closure against actual HEAD blobs, bounded batches."""
    for offset in range(0, len(refs), 16):
        batch = refs[offset:offset + 16]
        raw = git('cat-file', '--batch', data=b''.join((HEAD + ':' + x['path'] + '\n').encode() for x in batch))
        position = 0
        for item in batch:
            end = raw.index(b'\n', position)
            fields = raw[position:end].split()
            require(len(fields) == 3 and fields[1] == b'blob', 'committed regular blob missing: ' + item['path'])
            size = int(fields[2]); position = end + 1
            blob = raw[position:position + size]; position += size
            require(raw[position:position + 1] == b'\n', 'malformed cat-file boundary')
            position += 1
            require(digest(blob) == item['sha256'], 'HEAD blob differs: ' + item['path'])
        require(position == len(raw), 'unexpected cat-file output')


def directory_files(name: str) -> list[str]:
    path = ROOT / relative(name)
    no_symlinks(path)
    require(path.is_dir(), 'explicit source directory missing: ' + name)
    found = []
    for parent, dirs, files in os.walk(path, followlinks=False):
        for child in [*dirs, *files]:
            no_symlinks(Path(parent) / child)
        # Bytecode is not a reviewed source input; no other path is silently omitted.
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for child in sorted(files):
            if child.endswith(('.pyc', '.pyo')):
                continue
            f = Path(parent) / child
            require(f.is_file(), 'non-file source entry: ' + str(f))
            found.append(f.relative_to(ROOT).as_posix())
    require(found, 'empty source directory: ' + name)
    return found



def private_seal_copies(map_path: str, expected_sha: str,
                        seals: list[dict]) -> tuple[dict, dict[str, dict]]:
    """Map every sealed private original to a verified repository copy.

    Map schema: {schema, entries}; each entry has exact {original, copy,
    copy_receipt}. original/copy are {path, sha256, bytes}; copy_receipt is
    an exact repository-relative {path, sha256} reference. The receipt bytes
    are hash-bound and selected alongside copies; no receipt status is guessed.
    """
    manifest = Path(map_path)
    require(manifest.is_absolute(), 'private seal map must be an explicit absolute path')
    raw = stable(manifest)
    require(digest(raw) == expected_sha, 'private seal map SHA differs')
    value = json.loads(raw)
    require(type(value) is dict and set(value) == {'schema', 'entries'} and
            value['schema'] == 'v092-native04-private-seal-copy-map/v1',
            'exact private seal copy map schema required')
    entries = value['entries']
    private = {x['path']: x for x in seals if Path(x['path']).is_absolute()}
    require(len(private) == 3 and len(seals) - len(private) == 258,
            'actual sealed original split must be258relative/3private')
    require(type(entries) is list and len(entries) == len(private),
            'map must account for all3 private originals exactly')
    result = {}
    destinations = set()
    prefix = JQ + 'native-controls04-private-stream-copies-01/'
    for item in entries:
        require(type(item) is dict and set(item) == {'original', 'copy', 'copy_receipt'},
                'exact original/copy/copy_receipt entry required')
        original, copied, receipt = item['original'], item['copy'], item['copy_receipt']
        require(type(original) is dict and set(original) == {'path', 'sha256', 'bytes'} and
                original.get('path') in private and original == private[original['path']],
                'original metadata differs from immutable root stop seal')
        name = original['path']
        require(name not in result, 'duplicate private original mapping')
        require(type(original['bytes']) is int and original['bytes'] >= 0,
                'invalid original byte count')
        original_raw = stable(Path(name))
        require(len(original_raw) == original['bytes'] and digest(original_raw) == original['sha256'],
                'private original bytes differ from immutable seal')
        require(type(copied) is dict and set(copied) == {'path', 'sha256', 'bytes'},
                'exact copied-file metadata required')
        copy_ref = reference({'path': copied['path'], 'sha256': copied['sha256']})
        require(copy_ref['path'].startswith(prefix) and
                copy_ref['path'] not in destinations,
                'copy must have unique path under exact reviewed copy namespace')
        require(type(copied['bytes']) is int and copied['bytes'] == original['bytes'] and
                copied['sha256'] == original['sha256'], 'copy metadata differs from original')
        copied_raw = bound(copy_ref)
        require(copied_raw == original_raw and len(copied_raw) == copied['bytes'],
                'copy is not byte-identical to original')
        receipt = reference(receipt)
        require(receipt['path'] != copy_ref['path'], 'copy receipt cannot be the copied stream')
        document(receipt)
        destinations.add(copy_ref['path'])
        result[name] = {'copy': copy_ref, 'copy_receipt': receipt}
    require(set(result) == set(private), 'private seal map contains omission/unknown original')
    require(not any(x['copy_receipt']['path'] in destinations for x in result.values()),
            'receipt aliases a copied stream')
    return {'path': str(manifest), 'sha256': digest(raw)}, result


def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def private_output(value: str) -> Path:
    p = Path(value)
    require(p.is_absolute() and str(p) == p.as_posix() and '..' not in p.parts and p.parent == Path('/private/tmp'), 'output must be directly under /private/tmp')
    no_symlinks(p)
    require(not p.exists(), 'occupied output: ' + str(p))
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canonical-wrapper-dir', required=True)
    for role in ('integration-review', 'copy-receipt', 'authority'):
        parser.add_argument('--' + role, required=True)
        parser.add_argument('--' + role + '-sha256', required=True)
    parser.add_argument('--private-seal-copy-map', required=True)
    parser.add_argument('--private-seal-copy-map-sha256', required=True)
    parser.add_argument('--extra-refs-json')
    parser.add_argument('--extra-refs-sha256')
    parser.add_argument('--out-selection', required=True)
    parser.add_argument('--out-pathspec', required=True)
    parser.add_argument('--out-request-draft', required=True)
    args = parser.parse_args()
    require(args.canonical_wrapper_dir == ACQ + 'joern-native-controls-05', 'only exact canonical wrapper05 allowed')
    outputs = [private_output(v) for v in (args.out_selection, args.out_pathspec, args.out_request_draft)]
    require(len(set(outputs)) == 3, 'output paths must be distinct')
    tracked = git_state()
    base = document(BASE)
    inherited = base['source_refs']
    require(base['expected_head'] == HEAD and base['ledger'] == LEDGER and base['namespace'] == JQ + 'native-controls-04', 'actual request04 identity differs')
    require(type(inherited) is list and len(inherited) == 2335, 'exact2335 inherited refs required')
    merged: dict[str, dict[str, str]] = {}
    sizes: dict[str, int] = {}

    def add(item: dict[str, str]) -> None:
        item = reference(item)
        raw = bound(item)
        require(item['path'] not in merged or merged[item['path']] == item, 'path/SHA conflict: ' + item['path'])
        merged[item['path']] = item
        sizes[item['path']] = len(raw)

    for item in inherited:
        require(item['path'] not in merged and item['path'] in tracked, 'inherited duplicate or untracked path')
        add(item)
    committed_same(inherited)
    explicit = {}
    for role in ('integration_review', 'copy_receipt', 'authority'):
        item = {'path': relative(getattr(args, role)), 'sha256': getattr(args, role + '_sha256')}
        value = document(item)  # Exact caller-reviewed artifact, no guessed approval.
        explicit[role] = item
        add(item)
        if role == 'authority':
            require(value.get('automatic_retry') is False and value.get('publication_hold') is True, 'derived authority must preserve hold/no retry')
    plan = document(PLAN)
    require(plan['qualification_control_plan']['sha256'] == CONTROL_SHA and plan['qualification_control_projection_sha256'] == PROJECTION, 'plan/control projection differs')
    require(plan['status'] == 'qualification-pending' and plan['fresh_qualification'] is None and plan['execution_eligible'] is False and plan['diagnostic_execution_eligible'] is False, 'pending plan only')
    decisions = [case['decision'] for case in plan['cases'].values() if 'decision' in case]
    require(len(decisions) == 12 and len({x['path'] for x in decisions}) == 12, 'exact12 decision03 refs required')
    for item in decisions:
        require(PurePosixPath(item['path']).parent.as_posix() == QUAL + 'unsupported-decisions-03', 'foreign decision directory')
        add(item)
    for item in (OBSERVER, JAR, PLAN, plan['qualification_control_plan'], STOP):
        add(item)
    for folder in (ACQ + 'joern-native-startup-observer-07-source', QUAL + 'plan-v092-06', QUAL + 'unsupported-decisions-03', args.canonical_wrapper_dir):
        for name in directory_files(folder):
            add({'path': name, 'sha256': digest(stable(ROOT / name))})
    for name in (ACQ + 'StartupWitnessAgent-05.java', ACQ + 'StartupWitnessAgentTraversalTest-05.java'):
        add({'path': name, 'sha256': digest(stable(ROOT / name))})
    stop = document(STOP)
    seals = stop['sealed_evidence']
    require(type(seals) is list and len(seals) == 261 and len({x['path'] for x in seals}) == 261, 'exact261 native04 evidence seals required')
    map_ref, mapped = private_seal_copies(args.private_seal_copy_map,
                                               args.private_seal_copy_map_sha256, seals)
    for seal in seals:
        require(set(seal) == {'path', 'sha256', 'bytes'}, 'unexpected stop seal metadata')
        if Path(seal['path']).is_absolute():
            entry = mapped[seal['path']]
            add(entry['copy'])
            add(entry['copy_receipt'])
            require(sizes[entry['copy']['path']] == seal['bytes'], 'private copy size differs')
        else:
            add({'path': seal['path'], 'sha256': seal['sha256']})
            require(sizes[seal['path']] == seal['bytes'], 'stop seal size differs')
    require(bool(args.extra_refs_json) == bool(args.extra_refs_sha256), 'extras require exact path and SHA')
    extra_manifest = None
    if args.extra_refs_json:
        extras_path = Path(args.extra_refs_json)
        require(extras_path.is_absolute(), 'extra-ref manifest must be explicit absolute path')
        raw = stable(extras_path)
        require(digest(raw) == args.extra_refs_sha256, 'extra-ref manifest SHA differs')
        extra_manifest = {'path': str(extras_path), 'sha256': digest(raw)}
        extras = json.loads(raw)
        require(type(extras) is list, 'extra refs must be exact list of path/SHA refs')
        for item in extras:
            require(item['path'] not in {BASE['path'], JQ + 'native-control-request-05.json'}, 'request self-cycle forbidden')
            add(item)
    # Any tracked union entry must be the exact HEAD blob; new files alone enter pathspec.
    committed_same([v for k, v in merged.items() if k in tracked and k not in {x['path'] for x in inherited}])
    selected = [{**merged[k], 'bytes': sizes[k]} for k in sorted(merged) if k not in tracked]
    require(selected, 'empty new source selection')
    require(all(x['bytes'] < CAP for x in selected), 'selected file must be strictly below100MiB')
    require(not any(x in merged for x in (BASE['path'], JQ + 'native-control-request-05.json')), 'request cannot bind itself')
    all_refs = copy.deepcopy(inherited) + [merged[k] for k in sorted(merged) if k not in {x['path'] for x in inherited}]
    draft = copy.deepcopy(base)
    draft.update(expected_head=HEAD, namespace=JQ + 'native-controls-05', observer=OBSERVER,
                 pending_plan=PLAN, control_plan=plan['qualification_control_plan'], agent_jar=JAR,
                 agent_source=merged[ACQ + 'StartupWitnessAgent-05.java'], source_refs=all_refs,
                 authority=explicit['authority'], source_review=explicit['integration_review'],
                 decision_review=None, design=None,
                 tool_refs={name: merged[args.canonical_wrapper_dir + '/' + file]
                            for name, file in [('wrapper', 'native_qualifier.py'), ('resources', 'retained_resources.py')]})
    selection = {'schema': 'v092-native05-source-selection/v1', 'status': 'draft-source-selection-only-not-approved',
                 'base_head': HEAD, 'branch': BRANCH, 'files': selected, 'bytes': sum(x['bytes'] for x in selected),
                 'source_refs': all_refs, 'required_source_refs': len(all_refs), 'inherit2335': copy.deepcopy(inherited),
                 'inherited_source_count': 2335, 'sealed_originals': 261, 'relative_seals_preserved': 258, 'private_originals_verified_and_copied': 3, 'inputs': {'base_request': BASE, 'root_stop': STOP, 'private_seal_copy_map': map_ref, 'extra_manifest': extra_manifest, **explicit},
                 'scope': 'Finite explicit source-only union; no whole-repo sweep. Tracked identical blobs omitted from selected files. Future HEAD/design/decision/invocation review remain pending.',
                 'no_runtime': True, 'native_controls_launched': False, 'publication_hold': True,
                 'automatic_retry': False, 'request_draft_authoritative': False,
                 'pending_request_requirements': ['replace expected_head with reviewed actual new source commit', 'bind actual design and decision review', 'exact independent request/invocation review', 'fresh actual resource/process admission']}
    # Recheck every finite binding and Git gates immediately before exclusive private writes.
    for item in all_refs:
        bound(item)
    require(git_state() == tracked, 'tracked roster changed during preparation')
    for path in outputs:
        private_output(str(path))
    payloads = [canonical(selection), b''.join((x['path'] + '\0').encode() for x in selected), canonical(draft)]
    for path, raw in zip(outputs, payloads):
        with path.open('xb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps({'status': 'private-drafts-written-no-runtime', 'selected_count': len(selected),
                      'selected_bytes': selection['bytes'], 'source_count': len(all_refs),
                      'outputs': [{'path': str(f), 'sha256': digest(raw)} for f, raw in zip(outputs, payloads)]}, sort_keys=True))


if __name__ == '__main__':
    main()
