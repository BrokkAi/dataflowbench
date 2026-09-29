#!/usr/bin/env python3
"""Mocked authorization, capture, retention, and isolation tests for the v0.9 probe."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import signal
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("probe-python-modeling-load-bearing-v090.py")
SPEC = importlib.util.spec_from_file_location("python_modeling_v090", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return sha256(path)


def prepared_root(root: Path) -> tuple[Path, Path, Path]:
    """Create a tiny hash-bound contract and fixture tree; no analyzer is run."""
    execution = root / "reports/releases/v0.9.0/execution-v1"
    scratch = root / "isolated/reports/raw/control-scratch/probe-python-modeling-load-bearing"
    scratch.mkdir(parents=True)
    script_copy = root / "scripts/probe-python-modeling-load-bearing-v090.py"
    script_copy.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, script_copy)

    tool_root = root / "tools"
    tools: dict[str, dict[str, str]] = {}
    artifacts = []
    for key in ("bifrost", "codeql", "joern", "semgrep", "semgrep-core"):
        path = tool_root / key / "bin" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((key + " pinned bytes\n").encode())
        path.chmod(0o755)
        digest = sha256(path)
        tools[key] = {"path": str(path), "sha256": digest}
        if key != "codeql":
            artifacts.append({"id": key, "path": str(path), "sha256": digest})

    packs = tool_root / "codeql-packs"
    pack_file = packs / "codeql/python/1.0.0/qlpack.yml"
    pack_file.parent.mkdir(parents=True)
    pack_file.write_text("name: codeql/python\n", encoding="utf-8")
    pack_manifest_rel = "reports/releases/v0.9.0/execution-v1/non-swift-codeql-packs.json"
    pack_manifest_sha = write_json(execution / "non-swift-codeql-packs.json", {
        "claim": "exact local pack file inventory",
        "root": str(packs),
        "files": [{"path": pack_file.relative_to(packs).as_posix(), "sha256": sha256(pack_file), "bytes": pack_file.stat().st_size}],
    })
    tools["codeql-packs"] = {"path": str(packs), "tree_sha256": "a" * 64}

    cli_tree_rel = "adapters/codeql/swift-normal-v1/plan-test/cli-tree.json"
    cli_tree_sha = write_json(root / cli_tree_rel, {
        "codeql": {"sha256": sha256(Path(tools["codeql"]["path"])), "mode": 0o755},
    })
    swift_plan_rel = "adapters/codeql/swift-normal-v1/plan-test/plan.json"
    swift_plan_sha = write_json(root / swift_plan_rel, {
        "runtime": {
            "codeql": tools["codeql"]["path"],
            "manifests": {"cli_tree": {"path": cli_tree_rel, "sha256": cli_tree_sha}},
        },
    })

    held_sha = write_json(execution / "held-tool-digests.json", {"artifacts": artifacts})
    inventory_rel = "reports/releases/v0.9.0/execution-v1/control-inventory.json"
    inventory = {
        "schema": "release-control-inventory/v1",
        "release": "v0.9.0",
        "supplemental_control_ids": ["probe-python-modeling-load-bearing"],
        "controls": [{
            "id": "probe-python-modeling-load-bearing",
            "argv": ["/usr/bin/python3", "scripts/probe-python-modeling-load-bearing-v090.py"],
            "output_roots": [
                "reports/raw/load-bearing-python-modeling-v090",
                "reports/raw/control-scratch/probe-python-modeling-load-bearing",
            ],
            "environment": {"HOME": str(root), "PATH": "/pinned/bin", "TMPDIR": str(scratch)},
            "script_identity": [{"path": "scripts/probe-python-modeling-load-bearing-v090.py", "sha256": sha256(script_copy)}],
        }],
    }
    inventory_sha = write_json(root / inventory_rel, inventory)
    contract = {
        "schema": "release-execution-contract/v1",
        "release": "v0.9.0",
        "execution_authorized": True,
        "tools": tools,
        "groups": [
            {"id": f"{tool}-python-modeling", "environment": {"HOME": str(root), "PATH": "/pinned/{tool}", "TMPDIR": "/private/tmp"}}
            for tool in ("bifrost", "codeql", "joern", "semgrep")
        ],
        "control_inventory": {"path": inventory_rel, "sha256": inventory_sha},
        "identity_evidence": [
            {"path": "reports/releases/v0.9.0/execution-v1/held-tool-digests.json", "sha256": held_sha},
            {"path": pack_manifest_rel, "sha256": pack_manifest_sha},
        ],
        "input_identities": {
            inventory_rel: inventory_sha,
            "reports/releases/v0.9.0/execution-v1/held-tool-digests.json": held_sha,
            pack_manifest_rel: pack_manifest_sha,
            swift_plan_rel: swift_plan_sha,
            "scripts/probe-python-modeling-load-bearing-v090.py": sha256(script_copy),
        },
        "swift_plans": {"codeql": {"path": swift_plan_rel, "sha256": swift_plan_sha}},
    }
    contract_path = execution / "contract.json"
    write_json(contract_path, contract)

    case_names = (
        "model-declared-source-positive", "model-declared-source-negative",
        "model-declared-sink-positive", "model-declared-sink-negative",
        "model-opaque-propagator-positive", "model-sanitizer-kill-negative",
        "model-summary-through-positive", "model-sanitizer-selectivity-positive",
    )
    for name in case_names:
        fixture = root / "cases/taint/python" / name
        fixture.mkdir(parents=True)
        (fixture / "fixture.py").write_text("value = 1\n", encoding="utf-8")
    bifrost = root / "adapters/bifrost/policies/model-python.rqlp"
    bifrost.parent.mkdir(parents=True)
    bifrost.write_text(
        '(source :id declared-source :selector (rql :schema-version 1))])\n'
        '(sink :id declared-sink :selector (rql :schema-version 1))])\n', encoding="utf-8"
    )
    codeql_queries = root / "adapters/codeql/python/queries"
    codeql_queries.mkdir(parents=True)
    for name in ("PythonModeling.ql", "PythonModelingProbe.ql"):
        (codeql_queries / name).write_text("// mock query\n", encoding="utf-8")
    joern_semantics = root / "adapters/joern/semantics/model-python.semantics"
    joern_semantics.parent.mkdir(parents=True)
    joern_semantics.write_text('"clean.py:<module>.scrub"\n', encoding="utf-8")
    joern_query = root / "adapters/joern/queries/modeling.sc"
    joern_query.parent.mkdir(parents=True)
    joern_query.write_text("// mock query\n", encoding="utf-8")
    semgrep_rule = root / "adapters/semgrep/rules/model-python.yaml"
    semgrep_rule.parent.mkdir(parents=True)
    semgrep_rule.write_text(
        "- pattern: fetch_remote(...)\n"
        "- pattern: record(...)\n"
        "taint_assume_safe_functions: true\n", encoding="utf-8"
    )
    return contract_path, root, scratch


class PythonModelingV090Tests(unittest.TestCase):
    def test_explicit_ready_contract_preserves_disabled_canonical_and_rejects_wrong_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            canonical, root, scratch = prepared_root(Path(temporary))
            contract = json.loads(canonical.read_text())
            write_json(canonical, {**contract, 'execution_authorized': False})
            original = canonical.read_bytes()
            inventory = json.loads((root/contract['control_inventory']['path']).read_text())
            ready_rel = 'reports/releases/v0.9.0/execution-v1/final-01/contract.json'
            inventory_rel = 'reports/releases/v0.9.0/execution-v1/final-01/control-inventory.json'
            inventory['controls'][0]['argv'] += ['--contract', ready_rel]
            digest = write_json(root/inventory_rel, inventory)
            contract['control_inventory'] = {'path': inventory_rel, 'sha256': digest}
            contract['input_identities'][inventory_rel] = digest
            ready = root/ready_rel
            write_json(ready, contract)
            self.assertEqual(MODULE.capture(ready, root/'output', root=root, runner=lambda *a, **k: 0), 0)
            self.assertEqual(canonical.read_bytes(), original)
            inventory['controls'][0]['argv'][-1] = 'reports/releases/v0.9.0/execution-v1/other.json'
            digest = write_json(root/inventory_rel, inventory)
            contract['control_inventory']['sha256'] = digest
            contract['input_identities'][inventory_rel] = digest
            write_json(ready, contract)
            with self.assertRaisesRegex(ValueError, 'exact contract path'):
                MODULE.capture(ready, root/'rejected', root=root, runner=lambda *a, **k: 0)
            self.assertFalse((root/'rejected').exists())

    def test_denied_execution_creates_no_output_and_never_calls_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path = root / "contract.json"
            write_json(contract_path, {
                "schema": "release-execution-contract/v1",
                "release": "v0.9.0",
                "execution_authorized": False,
            })
            output = root / "must-not-exist"
            calls: list[object] = []

            with self.assertRaisesRegex(ValueError, "execution authorization"):
                MODULE.capture(contract_path, output, root=root, runner=lambda *a, **k: calls.append(a) or 0)

            self.assertFalse(output.exists())
            self.assertEqual(calls, [])

    def test_failed_mocked_commands_retain_outputs_and_use_isolated_joern_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path, root, scratch = prepared_root(root)
            output = root / "reports/raw/load-bearing-python-modeling-v090"
            calls: list[dict[str, object]] = []

            def fail_mock(argv, *, cwd, stdout, stderr, env, timeout):
                calls.append({"argv": argv, "cwd": cwd, "env": dict(env), "timeout": timeout})
                stdout.write(b"mock failure stdout\n")
                stderr.write(b"mock failure stderr\n")
                return 17

            self.assertEqual(MODULE.capture(contract_path, output, root=root, runner=fail_mock), 1)
            self.assertEqual(len(calls), 23)  # Extraction fails; the exact historical controls continue.
            self.assertTrue((output / "workspace/bifrost-declared-source-positive-with/fixture.py").is_file())
            first_name = "bifrost-declared-source-positive-with"
            self.assertTrue((output / f"{first_name}-stdout.txt").is_file())
            self.assertTrue((output / f"{first_name}-stderr.txt").is_file())
            self.assertIn("mock failure stdout", (output / f"{first_name}-stdout.txt").read_text())
            records = [json.loads(line) for line in (output / "commands.jsonl").read_text().splitlines()]
            self.assertEqual(records[0]["exit_code"], 17)
            self.assertEqual(records[0]["status"], "failed")
            self.assertEqual(records[0]["environment"]["TMPDIR"], str(scratch))
            self.assertTrue(all(call["env"]["TMPDIR"] == str(scratch) for call in calls))
            joern_cwds = [record["cwd"] for record in records if record["tool"] == "joern"]
            self.assertEqual(len(joern_cwds), 4)
            self.assertEqual(len(set(joern_cwds)), 4)
            self.assertTrue(all(Path(cwd).is_dir() for cwd in joern_cwds))

    def test_codeql_pack_manifest_rejects_extra_tree_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path, root, _scratch = prepared_root(root)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            extra = Path(contract["tools"]["codeql-packs"]["path"]) / "unlisted.txt"
            extra.write_text("unlisted\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unlisted CodeQL pack file"):
                MODULE._check_held_tool_digests(contract, contract_path, root)

    def test_current_codeql_pin_uses_swift_tree_when_absent_from_held_file_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path, root, _scratch = prepared_root(root)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            held_path = root / "reports/releases/v0.9.0/execution-v1/held-tool-digests.json"
            held = json.loads(held_path.read_text(encoding="utf-8"))
            self.assertNotIn("codeql", {item["id"] for item in held["artifacts"]})
            pinned = MODULE._check_held_tool_digests(contract, contract_path, root)
            self.assertEqual(pinned["codeql"]["path"], contract["tools"]["codeql"]["path"])

    def test_outer_term_runs_bounded_nested_process_group_cleanup(self) -> None:
        calls: list[tuple[int, int]] = []

        class MockProcess:
            pid = 12345

            def __init__(self):
                self.wait_calls = 0

            def wait(self, timeout=None):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise MODULE.ProbeInterrupted("recorder TERM")
                return 0

        process = MockProcess()
        with patch.object(MODULE.subprocess, "Popen", return_value=process) as popen, \
             patch.object(MODULE.os, "killpg", side_effect=lambda pid, sig: calls.append((pid, sig))):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with self.assertRaisesRegex(MODULE.ProbeInterrupted, "recorder TERM"):
                    MODULE._run_bounded(
                        ["mock-tool"], cwd=root, stdout=None, stderr=None,
                        env={"PATH": "/mock"}, timeout=5,
                    )
            self.assertEqual(popen.call_args.kwargs["start_new_session"], True)
        self.assertEqual(calls, [(process.pid, signal.SIGTERM), (process.pid, signal.SIGKILL)])
        self.assertEqual(process.wait_calls, 3)


if __name__ == "__main__":
    unittest.main()
