#!/usr/bin/env python3
"""Lightweight tests for scripts/check-release-results.py.

These tests use only tiny local Git repositories and a stub executable.  They
exercise the release gate's safety boundaries without building the benchmark
binary or contacting GitHub.
"""

from __future__ import annotations

import hashlib
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
            "benchmark": {"release": GATE.RELEASE, "revision": evidence},
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

    def make_migrated_source(self, *, helper_verified: bool = True) -> tuple[Path, Path, str]:
        source, remote, evidence, current = self.make_source()
        run_git(source, "tag", GATE.RELEASE, current)
        run_git(source, "push", "test-push", GATE.RELEASE)

        # Preserve the complete tagged release tree while replacing main with
        # a root commit, as in the supported history migration.
        run_git(source, "checkout", "--orphan", "migrated-main")
        archive = source / "evidence-archives" / "main-before-20261026"
        archive.mkdir(parents=True)
        (archive / "manifest.json").write_text(
            json.dumps(
                {
                    "original_main": "1" * 40,
                    "rewritten_base": "2" * 40,
                    "bundle": {
                        "parts": [{"path": "original-history.bundle.part0000"}]
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        helper = source / "scripts" / "historical_evidence.py"
        helper.parent.mkdir(parents=True)
        helper.write_text(
            "import argparse, json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('command')\n"
            "parser.add_argument('--root', required=True)\n"
            "parser.add_argument('--revision', required=True)\n"
            "parser.add_argument('--release', required=True)\n"
            "args = parser.parse_args()\n"
            "manifest = json.loads((Path(args.root) / 'evidence-archives/main-before-20261026/manifest.json').read_text())\n"
            f"print(json.dumps({{'verified': {helper_verified!r}, 'revision': args.revision, 'release': args.release, 'original_main': manifest['original_main'], 'rewritten_base': manifest['rewritten_base']}}))\n",
            encoding="utf-8",
        )
        self.commit(source, "rewrite main with archival evidence")
        run_git(source, "push", "--force", "test-push", "migrated-main:main")
        return source, remote, evidence

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

    def test_matching_tag_is_validated_from_the_tag_checkout(self) -> None:
        source, remote, _evidence, current = self.make_source()
        run_git(source, "tag", GATE.RELEASE, current)
        run_git(source, "push", "test-push", GATE.RELEASE)
        (source / "next-release-evidence").write_text("future\n", encoding="utf-8")
        self.commit(source, "prepare next release")
        binary = self.stub_binary()
        binary.write_text(
            binary.read_text(encoding="utf-8").replace(
                "set -eu\n", "set -eu\ntest ! -e next-release-evidence\n"
            ),
            encoding="utf-8",
        )
        GATE.run_gate(source, binary=binary, git_remote=str(remote))

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

    @mock.patch.object(GATE, "_pull_archival_bundle")
    def test_main_only_history_migration_uses_archival_proof_and_still_checks_tag(
        self, pull_archival_bundle: mock.MagicMock
    ) -> None:
        source, remote, _evidence = self.make_migrated_source()
        GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))
        pull_archival_bundle.assert_called()

    @mock.patch.object(GATE, "_pull_archival_bundle")
    def test_main_only_history_migration_rejects_invalid_archival_proof(
        self, pull_archival_bundle: mock.MagicMock
    ) -> None:
        source, remote, _evidence = self.make_migrated_source(helper_verified=False)
        with self.assertRaisesRegex(GATE.GateError, "invalid proof"):
            GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))
        pull_archival_bundle.assert_called()

    def test_historical_tag_clone_installs_lfs_filters_after_fetching_migrated_main(self) -> None:
        source, remote, _evidence = self.make_migrated_source()
        historical_tag = git_output(source, "rev-parse", f"refs/tags/{GATE.RELEASE}^{{commit}}")
        run_git(source, "checkout", "--detach", historical_tag)
        clone = self.root / "historical-tag-clone"
        GATE._clone_without_shared_objects(source, clone)
        self.assertFalse(
            (clone / GATE.HISTORY_MIGRATION_MANIFEST).exists()
        )
        self.assertEqual(
            run_git(
                clone,
                "config",
                "--local",
                "--get",
                "filter.lfs.process",
                check=False,
            ).returncode,
            1,
        )

        original_git = GATE._git
        lfs_commands: list[tuple[list[str], bool]] = []

        def record_lfs(
            checkout: Path,
            args: list[str],
            *,
            check: bool = True,
            enable_lfs_smudge: bool = False,
        ):
            if args and args[0] == "lfs":
                lfs_commands.append((args, enable_lfs_smudge))
                return subprocess.CompletedProcess(["git", *args], 0, "", "")
            return original_git(
                checkout,
                args,
                check=check,
                enable_lfs_smudge=enable_lfs_smudge,
            )

        with mock.patch.object(GATE, "_git", side_effect=record_lfs):
            fetched_main = GATE._fetch_github_main_and_tags(clone, str(remote))

        self.assertEqual(
            git_output(clone, "rev-parse", "HEAD^{commit}"),
            historical_tag,
        )
        self.assertEqual(
            run_git(clone, "config", "--local", "--get", "filter.lfs.process").stdout.strip(),
            "git-lfs filter-process",
        )
        self.assertEqual(
            lfs_commands,
            [
                (
                    [
                        "lfs",
                        "pull",
                        "--include",
                        f"{GATE.HISTORY_MIGRATION_DIRECTORY}/original-history.bundle.part0000",
                        GATE.REMOTE_NAME,
                    ],
                    True,
                ),
                (
                    [
                        "lfs",
                        "checkout",
                        f"{GATE.HISTORY_MIGRATION_DIRECTORY}/original-history.bundle.part0000",
                    ],
                    True,
                ),
            ],
        )
        self.assertEqual(
            fetched_main,
            git_output(remote, "rev-parse", "refs/heads/main^{commit}"),
        )

    @mock.patch.object(GATE, "_pull_archival_bundle")
    def test_legacy_release_checkout_does_not_use_lfs_archive(
        self, pull_archival_bundle: mock.MagicMock
    ) -> None:
        source, remote, _evidence, _current = self.make_source()
        GATE.run_gate(source, binary=self.stub_binary(), git_remote=str(remote))
        pull_archival_bundle.assert_not_called()

    def test_lfs_pull_uses_all_exact_manifest_bundle_part_paths(self) -> None:
        checkout = self.root / "archive-fixture"
        self.git_init(checkout)
        manifest_source = (
            Path(__file__).resolve().parents[1] / GATE.HISTORY_MIGRATION_MANIFEST
        )
        manifest_path = checkout / GATE.HISTORY_MIGRATION_MANIFEST
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_bytes(manifest_source.read_bytes())
        self.commit(checkout, "migration manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        parts = manifest["bundle"]["parts"]
        self.assertEqual(len(parts), 17)
        self.assertTrue(all("/" not in part["path"] for part in parts))

        original_git = GATE._git
        lfs_commands: list[list[str]] = []

        def record_lfs(
            checkout: Path,
            args: list[str],
            *,
            check: bool = True,
            enable_lfs_smudge: bool = False,
        ):
            if args and args[0] == "lfs":
                lfs_commands.append(args)
                return subprocess.CompletedProcess(["git", *args], 0, "", "")
            return original_git(
                checkout,
                args,
                check=check,
                enable_lfs_smudge=enable_lfs_smudge,
            )

        with mock.patch.object(GATE, "_git", side_effect=record_lfs):
            self.assertTrue(GATE._pull_archival_bundle(checkout))

        repo_paths = [
            f"{GATE.HISTORY_MIGRATION_DIRECTORY}/{part['path']}" for part in parts
        ]
        self.assertEqual(
            lfs_commands,
            [
                ["lfs", "pull", "--include", ",".join(repo_paths), GATE.REMOTE_NAME],
                ["lfs", "checkout", *repo_paths],
            ],
        )

    def test_git_checkout_skips_implicit_lfs_smudge_but_explicit_checkout_enables_it(self) -> None:
        calls: list[tuple[list[str], dict[str, str] | None]] = []

        def capture_run(
            command: list[str],
            *,
            cwd: str | None = None,
            check: bool = True,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            calls.append((command, env))
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.object(GATE, "_run", side_effect=capture_run):
            GATE._git(self.root, ["checkout", "--detach", "revision"])
            GATE._git(
                self.root,
                ["lfs", "checkout", "evidence-archives/main-before-20261026/part"],
                enable_lfs_smudge=True,
            )

        self.assertEqual(calls[0][1]["GIT_LFS_SKIP_SMUDGE"], "1")
        self.assertNotIn("GIT_LFS_SKIP_SMUDGE", calls[1][1])

    def test_migrated_clone_installs_local_lfs_filters_and_checks_out_exact_bytes(self) -> None:
        source = self.root / "lfs-source"
        self.git_init(source)
        installed = subprocess.run(
            ["git", "-C", str(source), "lfs", "install", "--local", "--skip-repo"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(installed.returncode, 0, installed.stderr)

        archive_dir = source / GATE.HISTORY_MIGRATION_DIRECTORY
        archive_dir.mkdir(parents=True)
        part_name = "original-history.bundle.part0000"
        part_path = archive_dir / part_name
        payload = b"synthetic archival bundle bytes\n" * 1024
        part_path.write_bytes(payload)
        (source / ".gitattributes").write_text(
            f"{GATE.HISTORY_MIGRATION_DIRECTORY}/{part_name} "
            "filter=lfs diff=lfs merge=lfs -text\n",
            encoding="utf-8",
        )
        (archive_dir / "manifest.json").write_text(
            json.dumps({"bundle": {"parts": [{"path": part_name}]}}) + "\n",
            encoding="utf-8",
        )
        self.commit(source, "migration LFS fixture")

        clone = self.root / "lfs-clone"
        GATE._clone_without_shared_objects(source, clone)
        self.assertEqual(
            run_git(clone, "config", "--local", "--get", "filter.lfs.process").stdout.strip(),
            "git-lfs filter-process",
        )
        pointer = (clone / GATE.HISTORY_MIGRATION_DIRECTORY / part_name).read_bytes()
        self.assertIn(b"version https://git-lfs.github.com/spec/v1", pointer)

        oid = hashlib.sha256(payload).hexdigest()
        source_object = source / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
        clone_object = clone / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
        self.assertTrue(source_object.is_file())
        clone_object.parent.mkdir(parents=True, exist_ok=True)
        clone_object.write_bytes(source_object.read_bytes())
        GATE._git(
            clone,
            [
                "lfs",
                "checkout",
                f"{GATE.HISTORY_MIGRATION_DIRECTORY}/{part_name}",
            ],
            enable_lfs_smudge=True,
        )
        restored = (clone / GATE.HISTORY_MIGRATION_DIRECTORY / part_name).read_bytes()
        self.assertEqual(hashlib.sha256(restored).hexdigest(), oid)
        self.assertEqual(restored, payload)

    def test_non_migrated_clone_does_not_install_local_lfs_filters(self) -> None:
        source = self.root / "legacy-source"
        self.git_init(source)
        (source / "README").write_text("legacy fixture\n", encoding="utf-8")
        self.commit(source, "legacy fixture")

        clone = self.root / "legacy-clone"
        GATE._clone_without_shared_objects(source, clone)
        configured = run_git(
            clone,
            "config",
            "--local",
            "--get",
            "filter.lfs.process",
            check=False,
        )
        self.assertEqual(configured.returncode, 1)

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
        self.assertNotEqual(
            run_git(
                source,
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/tags/{GATE.RELEASE}",
                check=False,
            ).returncode,
            0,
        )

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
