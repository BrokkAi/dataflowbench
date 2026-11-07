"""Focused Git-object proof for historical S/P replay against a rewritten HEAD."""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath

import packet
import stage_runtime


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


class HistoricalGit:
    @staticmethod
    def _ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
        try:
            subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                           cwd=root, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise packet.AdapterError(f"{label} is not an ancestor") from exc

    @staticmethod
    def _relative(value: object, label: str = "path") -> PurePosixPath:
        packet.require(isinstance(value, str) and value and "\x00" not in value and
                       "\\" not in value, f"{label} is malformed")
        path = PurePosixPath(value)
        packet.require(not path.is_absolute() and path.as_posix() == value and
                       all(part not in {"", ".", ".."} for part in path.parts),
                       f"{label} is unsafe")
        return path

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        return git(root, *args)


class HistoricalSourceReplayTests(unittest.TestCase):
    def _repo(self, *, changed_source_between_s_and_p: bool = False,
              wrong_runner_at_s: bool = False):
        temporary = tempfile.TemporaryDirectory(prefix="joern08-historical-source-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        git(root, "init", "-q")
        git(root, "config", "user.name", "Source Replay Test")
        git(root, "config", "user.email", "source-replay-test@example.invalid")
        git(root, "config", "commit.gpgsign", "false")

        runner = b"frozen historical executor source\n"
        case = b"{\"case\":\"sealed\"}\n"
        library = b"pub fn retained() {}\n"
        runner_at_s = b"incorrect runner source\n" if wrong_runner_at_s else runner
        for path, raw in (("scripts/execute-release-v092.py", runner_at_s),
                          ("cases/sample.json", case), ("src/lib.rs", library)):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        git(root, "add", "scripts/execute-release-v092.py", "cases/sample.json", "src/lib.rs")
        git(root, "commit", "-qm", "historical source S")
        source_commit = git(root, "rev-parse", "HEAD")

        if changed_source_between_s_and_p:
            (root / "cases/sample.json").write_bytes(b"{\"case\":\"drifted\"}\n")
            git(root, "add", "cases/sample.json")
        else:
            (root / "reports").mkdir()
            (root / "reports/plan-note.json").write_bytes(b"unprotected plan note\n")
            git(root, "add", "reports/plan-note.json")
        git(root, "commit", "-qm", "sealed historical plan P")
        plan_commit = git(root, "rev-parse", "HEAD")

        expected = [
            {"path": "cases/sample.json", "sha256": hashlib.sha256(case).hexdigest(),
             "role": "release-input"},
            {"path": "src/lib.rs", "sha256": hashlib.sha256(library).hexdigest(),
             "role": "release-input"},
        ]
        runner_sha = hashlib.sha256(runner).hexdigest()

        # Simulate a rewritten current HEAD whose tree is independent of the
        # sealed historical lineage. The old source and plan commits remain
        # readable objects and S remains an ancestor of P.
        git(root, "checkout", "--orphan", "rewritten-current-head")
        git(root, "rm", "-rf", ".")
        (root / "README.md").write_bytes(b"rewritten current source tree\n")
        git(root, "add", "README.md")
        git(root, "commit", "-qm", "rewritten current HEAD")
        head = git(root, "rev-parse", "HEAD")
        return root, source_commit, plan_commit, head, runner_sha, expected

    def _assert_snapshot(self, root, source, plan, runner_sha, sources):
        stage_runtime._assert_historical_source_snapshot(
            root, HistoricalGit(), source, plan, runner_sha,
            {"path": "scripts/execute-release-v092.py", "sha256": runner_sha},
            sources)

    def test_old_source_and_plan_pass_even_when_current_head_is_rewritten(self):
        root, source, plan, head, runner_sha, inputs = self._repo()
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.run(["git", "merge-base", "--is-ancestor", source, head],
                           cwd=root, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        self._assert_snapshot(root, source, plan, runner_sha, inputs)

    def test_protected_source_path_drift_from_old_source_to_plan_is_rejected(self):
        root, source, plan, _head, runner_sha, inputs = self._repo(
            changed_source_between_s_and_p=True)
        with self.assertRaisesRegex(packet.AdapterError,
                                    "protected source paths drift"):
            self._assert_snapshot(root, source, plan, runner_sha, inputs)

    def test_historical_runner_blob_must_match_frozen_digest(self):
        root, source, plan, _head, runner_sha, inputs = self._repo(wrong_runner_at_s=True)
        with self.assertRaisesRegex(packet.AdapterError,
                                    "runner digest|runner source digest|source blob differs"):
            self._assert_snapshot(root, source, plan, runner_sha, inputs)

    def test_historical_input_blob_must_match_normalized_ref(self):
        root, source, plan, _head, runner_sha, inputs = self._repo()
        inputs[0] = dict(inputs[0], sha256="0" * 64)
        with self.assertRaisesRegex(packet.AdapterError,
                                    "source blob differs"):
            self._assert_snapshot(root, source, plan, runner_sha, inputs)


if __name__ == "__main__":
    unittest.main()
