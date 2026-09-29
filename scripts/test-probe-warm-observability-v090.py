#!/usr/bin/env python3
"""Mocked contract/output tests for probe-warm-observability-v090.py."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("probe-warm-observability-v090.py")
SPEC = importlib.util.spec_from_file_location("warm_observability_v090", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture_contract() -> dict:
    keys = (
        "bifrost", "codeql", "joern", "semgrep", "infer", "java",
        "flowdroid", "pyre", "opentaint-analyzer",
    )
    return {
        "schema": "release-execution-contract/v1",
        "release": "v0.9.0",
        "execution_authorized": False,
        "groups": [{"tool": key, "environment": {"PATH": "/pinned/bin", "JAVA_HOME": "/pinned/jdk"}} for key in ["bifrost","codeql","joern","semgrep","infer","flowdroid","pysa","opentaint"]],
        "tools": {key: {"path": f"/pinned/{key}", "sha256": "0" * 64} for key in keys},
    }


class WarmObservabilityV090Tests(unittest.TestCase):
    def test_uses_only_v090_pins_and_skips_unpinned_wrapper(self) -> None:
        inventory = MODULE.command_inventory(fixture_contract())
        self.assertEqual(len(inventory), 10)
        self.assertEqual(inventory[0]["argv"], ["/pinned/bifrost", "--help"])
        self.assertEqual(inventory[-1]["argv"], None)
        self.assertEqual(inventory[-1]["status"], "not-run-no-pinned-v090-identity")
        self.assertEqual(inventory[-1]["tool_identities"], {})
        self.assertIn("sha256", inventory[6]["tool_identities"]["flowdroid"])

    def test_capture_records_help_calls_and_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            contract_path = base / "contract.json"
            contract = fixture_contract()
            for entry in contract["tools"].values():
                path = base / Path(entry["path"]).name
                path.write_bytes((path.name + " tool bytes\n").encode())
                entry["path"] = str(path)
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            output = base / "fresh-root"
            called: list[list[str]] = []

            def fake_run(argv, *, cwd, stdout, stderr, env, timeout):
                called.append(list(argv))
                stdout.write(b"mock stdout\n")
                stderr.write(b"mock stderr\n")
                return 0

            self.assertEqual(MODULE.capture(contract_path, output, fake_run), 0)
            self.assertEqual(len(called), 9)
            self.assertTrue((output / "bifrost-stdout.txt").exists())
            records = [json.loads(line) for line in (output / "commands.jsonl").read_text().splitlines()]
            self.assertEqual(records[-1]["status"], "not-run-no-pinned-v090-identity")
            self.assertEqual(json.loads((output / "scope.json").read_text())["release"], "v0.9.0")
            with self.assertRaises(FileExistsError):
                MODULE.capture(contract_path, output, fake_run)

    def test_observability_does_not_gate_on_execution_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            contract_path = base / "contract.json"
            contract = fixture_contract()
            contract["execution_authorized"] = True
            for entry in contract["tools"].values():
                path = base / Path(entry["path"]).name
                path.write_bytes((path.name + " tool bytes\n").encode())
                entry["path"] = str(path)
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            self.assertEqual(
                MODULE.capture(contract_path, base / "out", lambda *args, **kwargs: 0), 0
            )


if __name__ == "__main__":
    unittest.main()
