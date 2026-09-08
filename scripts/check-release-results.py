#!/usr/bin/env python3
"""Check the v0.7.1 release manifest and generated result artifacts.

The release check deliberately runs in a disposable, full-history clone.  The
checkout containing this script must be clean; the clone is the only place in
which the missing release tag may be created or result artifacts may be
generated.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


EXPECTED_REVISION = "2007f15d687e0081c948e55bba39c952d248ee0f"
RELEASE = "v0.7.1"
REQUIRED_REMOTE = "https://github.com/BrokkAi/dataflowbench.git"
REMOTE_NAME = "release-github"


class GateError(RuntimeError):
    """A release gate assertion failed."""


def _describe_command(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise GateError(f"could not run {_describe_command(command)}: {exc}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if len(detail) > 2_000:
            detail = detail[-2_000:]
        suffix = f": {detail}" if detail else ""
        raise GateError(
            f"command failed ({result.returncode}): {_describe_command(command)}{suffix}"
        )
    return result


def _git(
    checkout: Path,
    args: Sequence[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", str(checkout), *args], check=check)


def _git_output(checkout: Path, args: Sequence[str]) -> str:
    return _git(checkout, args).stdout.strip()


def _is_ancestor(checkout: Path, ancestor: str, descendant: str) -> bool:
    result = _git(
        checkout,
        ["merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.strip() or result.stdout.strip()
    raise GateError(
        f"could not prove {ancestor} is an ancestor of {descendant}: {detail}"
    )


def _assert_clean_source(source: Path) -> str:
    top = Path(_git_output(source, ["rev-parse", "--show-toplevel"])).resolve()
    if top != source.resolve():
        raise GateError(f"source checkout is not the repository root: {top}")
    head = _git_output(source, ["rev-parse", "HEAD^{commit}"])
    status = _git_output(source, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status:
        raise GateError("cannot run release gate from a dirty checkout:\n" + status)
    return head


def _load_manifest(source: Path) -> None:
    manifest_path = source / "reports" / "freeze.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read release freeze manifest {manifest_path}: {exc}") from exc
    try:
        claim_scope = manifest["claim"]["scope"]
        release = manifest["benchmark"]["release"]
        revision = manifest["benchmark"]["revision"]
    except (KeyError, TypeError) as exc:
        raise GateError(f"freeze manifest is missing its release identity: {exc}") from exc
    if claim_scope != "release":
        raise GateError(f"freeze claim scope is {claim_scope!r}, expected 'release'")
    if release != RELEASE:
        raise GateError(f"freeze release is {release!r}, expected {RELEASE!r}")
    if revision != EXPECTED_REVISION:
        raise GateError(
            f"freeze benchmark.revision is {revision!r}, expected {EXPECTED_REVISION!r}"
        )


def _clone_without_shared_objects(source: Path, destination: Path) -> None:
    # --no-local is needed in addition to --no-hardlinks: a local clone can
    # otherwise use the source repository's object store even when hardlinks
    # are disabled by a caller's Git configuration.
    _run(
        [
            "git",
            "clone",
            "--no-local",
            "--no-hardlinks",
            "--no-tags",
            "--no-single-branch",
            str(source),
            str(destination),
        ]
    )
    shallow = _git_output(destination, ["rev-parse", "--is-shallow-repository"])
    if shallow != "false":
        raise GateError("disposable release clone is shallow; full history is required")
    source_git_dir = Path(_git_output(source, ["rev-parse", "--absolute-git-dir"])).resolve()
    clone_git_dir = Path(_git_output(destination, ["rev-parse", "--absolute-git-dir"])).resolve()
    if source_git_dir == clone_git_dir:
        raise GateError("disposable release clone shares the source Git directory")
    alternates = clone_git_dir / "objects" / "info" / "alternates"
    if alternates.exists() and alternates.read_text(encoding="utf-8").strip():
        raise GateError("disposable release clone uses a shared Git object store")


def _fetch_github_main_and_tags(clone: Path, git_remote: str) -> str:
    # The production default is intentionally a constant.  Tests inject a
    # local bare remote through run_gate(), while the CLI has no remote flag.
    _git(clone, ["remote", "remove", "origin"], check=False)
    _git(clone, ["remote", "add", REMOTE_NAME, git_remote])
    # Fetching main and tags are separate successful operations.  In
    # particular, a failed tag fetch must not be treated as an absent tag.
    _git(clone, ["-c", "fetch.prune=false", "-c", "fetch.pruneTags=false", "fetch", "--no-prune", "--no-prune-tags", "--no-tags", REMOTE_NAME, "main"])
    _git(clone, ["-c", "fetch.prune=false", "-c", "fetch.pruneTags=false", "fetch", "--no-prune", "--no-prune-tags", "--tags", REMOTE_NAME])
    fetched_main = _git_output(
        clone, ["rev-parse", f"refs/remotes/{REMOTE_NAME}/main^{{commit}}"]
    )
    if not _is_ancestor(clone, EXPECTED_REVISION, fetched_main):
        raise GateError(
            f"required evidence revision {EXPECTED_REVISION} is not an ancestor of "
            f"fetched main {fetched_main}"
        )
    return fetched_main


def _tag_commit(clone: Path) -> str | None:
    remote = _git(clone, ['ls-remote', '--exit-code', REMOTE_NAME, f'refs/tags/{RELEASE}'], check=False)
    local = _git(clone, ['show-ref', '--verify', '--quiet', f'refs/tags/{RELEASE}'], check=False)
    if remote.returncode == 2:
        if local.returncode != 1:
            raise GateError('remote tag absent but inherited local tag exists or is unreadable')
        return None
    if remote.returncode != 0:
        raise GateError('cannot determine remote tag state: ' + remote.stderr)
    if local.returncode != 0:
        raise GateError('remote release tag was not fetched')
    remote_oid = remote.stdout.split()[0]
    local_oid = _git_output(clone, ['rev-parse', f'refs/tags/{RELEASE}'])
    if remote_oid != local_oid:
        raise GateError('remote and fetched release tag identities differ')
    return _git_output(clone, ['rev-parse', f'refs/tags/{RELEASE}^{{commit}}'])


def _assert_release_tree_matches_current(clone: Path, current_head: str, tag: str) -> None:
    result = _git(
        clone,
        ["diff", "--quiet", current_head, tag, "--", "reports/freeze.json", "results"],
        check=False,
    )
    if result.returncode == 0:
        return
    if result.returncode == 1:
        raise GateError(
            f"existing {RELEASE} tag does not byte-match the current committed "
            "reports/freeze.json and results tree"
        )
    detail = result.stderr.strip() or result.stdout.strip()
    raise GateError(f"could not compare current release tree with {RELEASE}: {detail}")


def _run_binary(binary: Path, args: Sequence[str], clone: Path) -> None:
    result = _run([str(binary), *args], cwd=clone, check=False)
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip()
    if len(detail) > 2_000:
        detail = detail[-2_000:]
    raise GateError(
        f"release binary failed ({result.returncode}): {binary} {' '.join(args)}"
        + (f": {detail}" if detail else "")
    )


def _copy_generated_results(clone: Path, output: Path) -> None:
    generated = (clone / "results").resolve()
    if not generated.is_dir():
        raise GateError(f"release binary did not generate a results directory: {generated}")
    destination = output.expanduser().resolve()
    if destination == generated or generated in destination.parents:
        raise GateError("--generate-output must be outside the disposable clone")
    if destination.exists():
        if not destination.is_dir():
            raise GateError(f"--generate-output is not a directory: {destination}")
        if any(destination.iterdir()):
            raise GateError(f"--generate-output must be empty: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
    shutil.copytree(generated, destination, dirs_exist_ok=True)


def run_gate(
    source: Path | None = None,
    *,
    binary: Path,
    generate_output: Path | None = None,
    git_remote: str = REQUIRED_REMOTE,
) -> None:
    """Run the release gate.

    ``git_remote`` is an in-process dependency injection point for the
    lightweight tests.  It is deliberately absent from the production CLI so
    a release check cannot be redirected to a local or user-selected remote.
    """

    source = (source or Path(__file__).resolve().parents[1]).resolve()
    if not binary.is_absolute():
        raise GateError("--binary must be an absolute path to the reviewed binary")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise GateError(f"--binary is not an executable file: {binary}")
    _assert_clean_source(source)
    _load_manifest(source)
    current_head = _git_output(source, ["rev-parse", "HEAD^{commit}"])

    with tempfile.TemporaryDirectory(prefix="dataflowbench-release-") as temp:
        clone = Path(temp) / "repo"
        _clone_without_shared_objects(source, clone)
        # A clone made from a detached source or a feature branch must still
        # validate and generate from exactly the clean source commit.
        _git(clone, ["checkout", "--detach", current_head])
        _fetch_github_main_and_tags(clone, git_remote)
        if not _is_ancestor(clone, EXPECTED_REVISION, current_head):
            raise GateError('current committed tree does not contain required evidence revision')
        tag = _tag_commit(clone)
        if tag is None:
            source_tag = _git(source, ['show-ref', '--verify', '--quiet', f'refs/tags/{RELEASE}'], check=False)
            if source_tag.returncode != 1:
                raise GateError('remote tag absent but inherited local tag exists or is unreadable')
            # This is intentionally a lightweight local tag.  No push command
            # exists in this program and the disposable clone is deleted on
            # return.
            _git(clone, ["-c", "tag.gpgsign=false", "tag", RELEASE, "HEAD"])
            # The normal gate checks committed results.  --generate-output is
            # the explicit bootstrap mode that generates and copies results.
            check_results = generate_output is None
        else:
            if not _is_ancestor(clone, EXPECTED_REVISION, tag):
                raise GateError(f"existing {RELEASE} tag does not contain {EXPECTED_REVISION}")
            _assert_release_tree_matches_current(clone, current_head, tag)
            if generate_output is not None:
                raise GateError(
                    f"--generate-output is only valid when {RELEASE} is absent; "
                    "existing release artifacts must be checked"
                )
            check_results = True

        _run_binary(binary, ["validate-freeze", "reports/freeze.json"], clone)
        result_args = [
            "generate-results",
            "--manifest",
            "reports/freeze.json",
            "--output-directory",
            "results",
        ]
        if check_results:
            result_args.append("--check")
        _run_binary(binary, result_args, clone)
        if not check_results and generate_output is not None:
            _copy_generated_results(clone, generate_output)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        required=True,
        type=Path,
        help="absolute path to the reviewed, unmodified dataflowbench binary",
    )
    parser.add_argument(
        "--generate-output",
        type=Path,
        help="copy generated results here when the v0.7.1 tag is absent",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        run_gate(binary=args.binary, generate_output=args.generate_output)
    except GateError as exc:
        print(f"release gate failed: {exc}", file=sys.stderr)
        return 1
    print(f"release gate passed for {RELEASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
