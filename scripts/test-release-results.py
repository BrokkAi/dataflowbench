#!/usr/bin/env python3
"""Lightweight tests for scripts/check-release-results.py.

These tests use only tiny local Git repositories and a stub executable.  They
exercise the release gate's safety boundaries without building the benchmark
binary or contacting GitHub.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Iterable
from unittest import mock


sys.dont_write_bytecode = True

SCRIPT = Path(__file__).with_name("check-release-results.py")
SPEC = importlib.util.spec_from_file_location("check_release_results", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check:
        result.check_returncode()
    return result


def git_output(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="dfb-release-gate-test-")
        self.root = Path(self.temp.name)
        self.old_revision = GATE.EXPECTED_REVISION

    def tearDown(self) -> None:
        GATE.EXPECTED_REVISION = self.old_revision
        self.temp.cleanup()

    def git_init(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        run_git(path, "init", "--initial-branch=main")
        run_git(path, "config", "user.email", "release-gate@example.invalid")
        run_git(path, "config", "user.name", "Release Gate Tests")
        run_git(path, "config", "commit.gpgsign", "false")
        run_git(path, "config", "tag.gpgsign", "false")

    def commit(self, path: Path, message: str) -> str:
        run_git(path, "add", ".")
        run_git(path, "commit", "-m", message)
        return git_output(path, "rev-parse", "HEAD")

    def make_source(self, *, results_text: str = "stable\n") -> tuple[Path, Path, str, str]:
        source = self.root / "source"
        self.git_init(source)
        (source / "README").write_text("tiny repository\n", encoding="utf-8")
        evidence = self.commit(source, "evidence")
        manifest = {
            "benchmark": {"release": "v0.7.1", "revision": evidence},
            "claim": {"scope": "release"},
        }
        (source / "reports").mkdir()
        (source / "reports" / "freeze.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
        (source / "results").mkdir()
        (source / "results" / "index.md").write_text(results_text, encoding="utf-8")
        current = self.commit(source, "release tree")
        GATE.EXPECTED_REVISION = evidence
        return source, self.make_remote(source), evidence, current

    def make_remote(self, source: Path) -> Path:
        remote = self.root / f"remote-{len(list(self.root.iterdir()))}"
        run_git(self.root, "init", "--bare", str(remote))
        run_git(source, "remote", "add", "test-push", str(remote))
        run_git(source, "push", "test-push", "main")
        return remote

    def stub_binary(self) -> Path:
        binary = self.root / "dataflowbench-stub"
        binary.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            "if [ \"$1\" = validate-freeze ]; then test -f reports/freeze.json; exit $?; fi\n"
            "if [ \"$1\" = generate-results ]; then\n"
            "  case \" $* \" in *\" --check \"*) test -f results/index.md; exit $?;; esac\n"
            "  mkdir -p results; printf 'generated\\n' > results/index.md; exit 0\n"
            "fi\n"
            "exit 64\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        return binary

    def test_absent_tag_creates_local_tag_and_copies_generated_results(self) -> None:
        source, remote, _evidence, _current = self.make_source()
        output = self.root / "generated"
        GATE.run_gate(source, binary=self.stub_binary(), generate_output=output, git_remote=str(remote))
        self.assertEqual(output.joinpath("index.md").read_text(), "generated\n")

    def test_matching_tag_checks_existing_results(self) -> None:
        source, remote, _evidence, current = self.make_source()
        run_git(source, "tag", GATE.RELEASE, current)
        run_git(source, "push", "test-push", GATE.RELEASE)
        GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_existing_tag_requires_byte_equivalent_release_tree(self) -> None:
        source, remote, evidence, _current = self.make_source(results_text="changed\n")
        # Tag the evidence commit, which contains neither the release manifest
        # nor results.  The required evidence revision is still contained.
        run_git(source, "tag", GATE.RELEASE, evidence)
        run_git(source, "push", "test-push", GATE.RELEASE)
        with self.assertRaisesRegex(GATE.GateError, "byte-match"):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_fetch_failure_fails_closed(self) -> None:
        source, _remote, _evidence, _current = self.make_source()
        with self.assertRaises(GATE.GateError):
            GATE.run_gate(
                source,
                binary=self.stub_binary(),
                git_remote=str(self.root / "does-not-exist.git"),
            )

    def test_wrong_revision_is_rejected_before_clone(self) -> None:
        source, _remote, _evidence, _current = self.make_source()
        manifest_path = source / "reports" / "freeze.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["benchmark"]["revision"] = "0" * 40
        manifest_path.write_text(json.dumps(manifest) + "\n")
        self.commit(source, "wrong revision")
        with self.assertRaisesRegex(GATE.GateError, "benchmark.revision"):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote="unused")

    def test_fetched_main_must_contain_evidence_revision(self) -> None:
        source, _remote, evidence, _current = self.make_source()
        unrelated = self.root / "unrelated"
        self.git_init(unrelated)
        (unrelated / "README").write_text("unrelated\n")
        self.commit(unrelated, "unrelated")
        remote = self.make_remote(unrelated)
        self.assertNotEqual(git_output(unrelated, "rev-parse", "HEAD"), evidence)
        with self.assertRaisesRegex(GATE.GateError, "not an ancestor"):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_dirty_source_checkout_is_rejected(self) -> None:
        source, remote, _evidence, _current = self.make_source()
        (source / "untracked").write_text("dirty\n")
        with self.assertRaisesRegex(GATE.GateError, "dirty checkout"):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_absent_remote_with_inherited_local_tag_rejected(self) -> None:
        source, remote, _evidence, current = self.make_source()
        run_git(source, 'tag', GATE.RELEASE, current)
        with self.assertRaisesRegex(GATE.GateError, 'inherited local tag'):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_absent_tag_default_checks_without_regenerating(self) -> None:
        source, remote, _evidence, _current = self.make_source()
        calls = []
        with mock.patch.object(GATE, '_run_binary', side_effect=lambda binary, args, clone: calls.append(args)):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))
        self.assertIn('--check', calls[-1])
        self.assertNotEqual(run_git(source, 'show-ref', '--verify', '--quiet', 'refs/tags/v0.7.1', check=False).returncode, 0)

    def test_unknown_tag_state_refuses_bootstrap(self) -> None:
        with mock.patch.object(GATE, '_git', return_value=subprocess.CompletedProcess([], 128, '', 'network failed')):
            with self.assertRaisesRegex(GATE.GateError, 'remote tag state'):
                GATE._tag_commit(self.root)

    def test_current_tree_must_contain_evidence(self) -> None:
        source, remote, evidence, current = self.make_source()
        run_git(source, 'checkout', '--orphan', 'unrelated-release')
        self.commit(source, 'release tree without evidence ancestry')
        with self.assertRaisesRegex(GATE.GateError, 'current committed tree'):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))

    def test_cli_does_not_expose_remote_override(self) -> None:
        with self.assertRaises(SystemExit):
            GATE._parse_args(["--binary", "/tmp/binary", "--git-remote", "/tmp/remote"])
        self.assertEqual(GATE.REQUIRED_REMOTE, "https://github.com/BrokkAi/dataflowbench.git")


if __name__ == "__main__":
    unittest.main()
