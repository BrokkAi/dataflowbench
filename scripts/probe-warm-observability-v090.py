#!/usr/bin/env python3
"""Capture advertised CLI help surfaces for the v0.9.0 pinned tool set.

This is observational evidence only. It does not run an analyzer, interpret a
missing help option as a capability decline, or make any warm-performance
claim. The OpenTaint product wrapper is observed only when its exact identity
is registered in the reviewed v0.9.0 contract.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reports/releases/v0.9.0/execution-v1/contract.json"
OUTPUT_ROOT = ROOT / "reports/raw/warm-observability-v090"
TIMEOUT_SECONDS = 75


def _group_environment(contract: Mapping[str, object], command_id: str) -> dict[str, str]:
    groups = contract.get("groups")
    if not isinstance(groups, list):
        raise ValueError("v0.9 contract groups must be a list")
    wanted_tool = {
        "bifrost": "bifrost", "codeql-create": "codeql", "codeql-analyze": "codeql",
        "joern": "joern", "semgrep": "semgrep", "infer": "infer",
        "flowdroid": "flowdroid", "pysa": "pysa", "opentaint-jar": "opentaint",
        "opentaint-product": "opentaint",
    }[command_id]
    for group in groups:
        if group.get('tool') == wanted_tool and isinstance(group.get('environment'), dict):
            environment = dict(group['environment'])
            if command_id == 'opentaint-product':
                runtime = str(Path(contract['tools']['opentaint-wrapper']['path']).parent / 'jre')
                environment['JAVA_HOME'] = runtime
                environment['PATH'] = runtime + '/bin:' + environment['PATH']
            reference = contract.get('control_inventory')
            if reference:
                raw = (ROOT / reference['path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != reference['sha256']:
                    raise ValueError('control inventory digest mismatch')
                matches = [item for item in json.loads(raw)['controls'] if item['id'] == 'probe-warm-observability']
                if len(matches) != 1:
                    raise ValueError('warm observability control must be registered exactly once')
                environment['TMPDIR'] = matches[0]['environment']['TMPDIR']
            return environment
    raise ValueError('missing explicit tool environment: ' + wanted_tool)


def _run_bounded(argv: Sequence[str], *, cwd: Path, stdout: object, stderr: object,
                 env: Mapping[str, str], timeout: int = TIMEOUT_SECONDS) -> int:
    def interrupted(signum, frame):
        raise KeyboardInterrupt('probe interrupted by signal ' + str(signum))
    old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    for sig in old_handlers:
        signal.signal(sig, interrupted)
    process = None
    def stop():
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    try:
        process = subprocess.Popen(
            list(argv), cwd=cwd, stdout=stdout, stderr=stderr, env=dict(env),
            start_new_session=True,
        )
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop()
        return 124
    except BaseException:
        stop()
        raise
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


def _tool(tools: Mapping[str, object], key: str) -> tuple[str, str]:
    entry = tools.get(key)
    if not isinstance(entry, dict):
        raise ValueError(f"v0.9 contract has no pinned tool record for {key}")
    path = entry.get("path")
    digest = entry.get("sha256")
    if not isinstance(path, str) or not path:
        raise ValueError(f"v0.9 contract has no path for {key}")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"v0.9 contract has no SHA-256 for {key}")
    return path, digest


def _check_pinned_file(path: str, expected_sha256: str) -> None:
    candidate = Path(path)
    if not candidate.is_file():
        raise ValueError(f"pinned CLI file is missing or not a regular file: {path}")
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"pinned CLI file digest differs from v0.9 contract: {path}")


def command_inventory(contract: Mapping[str, object]) -> list[dict[str, object]]:
    tools = contract.get("tools")
    if not isinstance(tools, dict):
        raise ValueError("v0.9 contract tools must be an object")

    pinned = {key: _tool(tools, key) for key in (
        "bifrost", "codeql", "joern", "semgrep", "infer", "java",
        "flowdroid", "pyre", "opentaint-analyzer",
    )}
    commands: list[dict[str, object]] = [
        {"id": "bifrost", "argv": [pinned["bifrost"][0], "--help"], "identity": ["bifrost"]},
        {"id": "codeql-create", "argv": [pinned["codeql"][0], "database", "create", "--help"], "identity": ["codeql"]},
        {"id": "codeql-analyze", "argv": [pinned["codeql"][0], "database", "analyze", "--help"], "identity": ["codeql"]},
        {"id": "joern", "argv": [pinned["joern"][0], "--help"], "identity": ["joern"]},
        {"id": "semgrep", "argv": [pinned["semgrep"][0], "scan", "--help"], "identity": ["semgrep"]},
        {"id": "infer", "argv": [pinned["infer"][0], "analyze", "--help"], "identity": ["infer"]},
        {"id": "flowdroid", "argv": [pinned["java"][0], "-jar", pinned["flowdroid"][0], "--help"], "identity": ["java", "flowdroid"]},
        {"id": "pysa", "argv": [pinned["pyre"][0], "analyze", "--help"], "identity": ["pyre"]},
        {"id": "opentaint-jar", "argv": [pinned["java"][0], "-jar", pinned["opentaint-analyzer"][0], "--help"], "identity": ["java", "opentaint-analyzer"]},
        {"id": "opentaint-product", "argv": None, "identity": ["opentaint-wrapper"],
         "status": "not-run-no-pinned-v090-identity"},
    ]
    if 'opentaint-wrapper' in tools:
        pinned['opentaint-wrapper'] = _tool(tools, 'opentaint-wrapper')
        commands[-1] = {'id': 'opentaint-product',
                        'argv': [pinned['opentaint-wrapper'][0], 'scan', '--help'],
                        'identity': ['opentaint-wrapper']}
    for item in commands:
        item["tool_identities"] = {
            key: {"path": pinned[key][0], "sha256": pinned[key][1]}
            for key in item["identity"] if key in pinned
        }
    return commands


def capture(
    contract_path: Path = CONTRACT,
    output_root: Path = OUTPUT_ROOT,
    runner: Callable[..., int] | None = None,
) -> int:
    raw_contract = contract_path.read_bytes()
    contract = json.loads(raw_contract)
    if contract.get("schema") != "release-execution-contract/v1" or contract.get("release") != "v0.9.0":
        raise ValueError("contract is not the v0.9.0 execution-v1 contract")
    if not isinstance(contract.get("execution_authorized"), bool):
        raise ValueError("contract must preserve its explicit execution_authorized boolean")

    records = command_inventory(contract)
    tools = contract["tools"]
    assert isinstance(tools, dict)
    for key in ("bifrost", "codeql", "joern", "semgrep", "infer", "java", "flowdroid", "pyre", "opentaint-analyzer"):
        path, digest = _tool(tools, key)
        _check_pinned_file(path, digest)
    if 'opentaint-wrapper' in tools:
        _check_pinned_file(*_tool(tools, 'opentaint-wrapper'))
        from release_runtime_inventory_v090 import verify
        bundle = str(Path(tools['opentaint-wrapper']['path']).parent)
        matched = False
        for reference in contract.get('runtime_trees', []):
            raw = (ROOT / reference['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != reference['sha256']:
                raise ValueError('runtime inventory digest mismatch')
            manifest = json.loads(raw)
            if manifest.get('root') == bundle:
                verify(manifest)
                matched = True
        if not matched:
            raise ValueError('full product runtime tree is not bound')
    output_root.mkdir(parents=True, exist_ok=False)
    command_log = output_root / "commands.jsonl"
    failures = 0
    with command_log.open("x", encoding="utf-8") as log:
        for record in records:
            if record.get("argv") is None:
                record.update({"exit_code": None, "status": record["status"]})
                log.write(json.dumps(record, sort_keys=True) + "\n")
                continue

            name = str(record["id"])
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                load_before = os.getloadavg()
            except (AttributeError, OSError):
                load_before = None
            try:
                env = _group_environment(contract, name)
                execute = runner or _run_bounded
                with (output_root / f"{name}-stdout.txt").open("xb") as stdout, \
                     (output_root / f"{name}-stderr.txt").open("xb") as stderr:
                    if runner is None:
                        code = execute(record["argv"], cwd=ROOT, stdout=stdout, stderr=stderr,
                                       env=env, timeout=TIMEOUT_SECONDS)
                    else:
                        code = execute(record["argv"], cwd=ROOT, stdout=stdout, stderr=stderr,
                                       env=env, timeout=TIMEOUT_SECONDS)
                code = int(code)
                record.update({"status": "captured" if code != 124 else "timeout", "exit_code": code,
                               "timeout_seconds": TIMEOUT_SECONDS,
                               "environment": env})
                failures += code != 0
            except OSError as exc:
                record.update({"status": "launch-error", "exit_code": None, "error": str(exc)})
                failures += 1
            record.update({
                "started_utc": started,
                "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "load_before": load_before,
            })
            log.write(json.dumps(record, sort_keys=True) + "\n")

    scope = {
        "kind": "released-cli-surface-audit",
        "release": "v0.9.0",
        "contract_sha256": __import__("hashlib").sha256(raw_contract).hexdigest(),
        "scope": "Advertised CLI help only. Help absence does not establish declined capability; pair with the registered same-work controls.",
        "flowdroid": "Batch support does not establish whole-population per-case-config equivalence; preserve as unsupported/unresolved unless independently qualified.",
        "warm_measurements": ["Joern Java", "Semgrep Java largest identical-rule group"],
        "opentaint_product": ("Pinned shipped wrapper help captured; no equivalence inferred."
                              if 'opentaint-wrapper' in tools else
                              "not run: v0.9 contract does not pin the full product wrapper identity/runtime tree"),
    }
    (output_root / "scope.json").write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    try:
        return capture(args.contract, args.output_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
