#!/usr/bin/env python3
"""Check the v0.8.0 release manifest and generated result artifacts.

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


EXPECTED_REVISION = "80d4f01bb189d530849f9ceb5d775680fcedfb52"
RELEASE = "v0.8.0"
REQUIRED_REMOTE = "https://github.com/BrokkAi/dataflowbench.git"
REMOTE_NAME = "release-github"
HISTORY_MIGRATION_DIRECTORY = "evidence-archives/main-before-20261026"
HISTORY_MIGRATION_MANIFEST = f"{HISTORY_MIGRATION_DIRECTORY}/manifest.json"
HISTORY_EVIDENCE_HELPER = "scripts/historical_evidence.py"


class GateError(RuntimeError):
    """A release gate assertion failed."""


def _describe_command(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
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
    enable_lfs_smudge: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if enable_lfs_smudge:
        env.pop("GIT_LFS_SKIP_SMUDGE", None)
    else:
        env["GIT_LFS_SKIP_SMUDGE"] = "1"
    return _run(["git", "-C", str(checkout), *args], check=check, env=env)


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


def _has_committed_history_migration_manifest(checkout: Path) -> bool:
    manifest = checkout / HISTORY_MIGRATION_MANIFEST
    if not manifest.is_file():
        return False
    tracked = _git(
        checkout,
        ["ls-files", "--error-unmatch", HISTORY_MIGRATION_MANIFEST],
        check=False,
    )
    if tracked.returncode == 0:
        return True
    if tracked.returncode == 1:
        return False
    detail = tracked.stderr.strip() or tracked.stdout.strip()
    raise GateError(f"could not establish whether the history migration manifest is committed: {detail}")


def _prove_archival_lineage(checkout: Path, revision: str, release: str) -> bool:
    if not _has_committed_history_migration_manifest(checkout):
        return False
    helper = checkout / HISTORY_EVIDENCE_HELPER
    result = _run(
        [
            "python3",
            str(helper),
            "prove",
            "--root",
            str(checkout),
            "--revision",
            revision,
            "--release",
            release,
        ],
        cwd=checkout,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GateError(
            f"historical evidence verifier rejected {revision} for {release}"
            + (f": {detail}" if detail else "")
        )
    try:
        proof = json.loads(result.stdout)
        manifest = json.loads((checkout / HISTORY_MIGRATION_MANIFEST).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise GateError(f"historical evidence verifier returned invalid proof data: {exc}") from exc
    if (
        not isinstance(proof, dict)
        or proof.get("verified") is not True
        or proof.get("revision") != revision
        or proof.get("release") != release
        or proof.get("original_main") != manifest.get("original_main")
        or proof.get("rewritten_base") != manifest.get("rewritten_base")
        or not _is_git_revision(proof.get("original_main"))
        or not _is_git_revision(proof.get("rewritten_base"))
    ):
        raise GateError(
            f"historical evidence verifier returned an invalid proof for {revision} and {release}"
        )
    return True


def _is_git_revision(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(
        character in "0123456789abcdefABCDEF" for character in value
    )


def _install_local_lfs_filters(checkout: Path) -> None:
    env = os.environ.copy()
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    _run(
        ["git", "-C", str(checkout), "lfs", "install", "--local", "--skip-repo"],
        env=env,
    )


def _pull_archival_bundle(checkout: Path) -> bool:
    if not _has_committed_history_migration_manifest(checkout):
        return False
    # A caller may have cloned an original tag before fetching rewritten main.
    # That source checkout has no migration manifest, so clone setup could not
    # install local filters; install them now after the migrated commit arrives.
    _install_local_lfs_filters(checkout)
    try:
        manifest = json.loads(
            (checkout / HISTORY_MIGRATION_MANIFEST).read_text(encoding="utf-8")
        )
        parts = manifest["bundle"]["parts"]
        paths = [part["path"] for part in parts]
    except (KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        raise GateError(f"cannot read historical bundle part paths: {exc}") from exc
    if (
        not isinstance(parts, list)
        or not paths
        or any(
            not isinstance(path, str)
            or Path(path).is_absolute()
            or path in {".", ".."}
            or "/" in path
            or "\\" in path
            or "," in path
            or ".git" in Path(path).parts
            or not Path(path).name.startswith("original-history.bundle.part")
            or not Path(path).name.removeprefix("original-history.bundle.part").isdigit()
            for path in paths
        )
    ):
        raise GateError("migration manifest contains invalid historical bundle part paths")
    repo_paths = [f"{HISTORY_MIGRATION_DIRECTORY}/{path}" for path in paths]
    include = ",".join(repo_paths)
    # The disposable clone skips smudging before its remote is configured.
    # Fetch only the LFS parts listed by the committed migration manifest now
    # that the real release remote has been installed.
    _git(
        checkout,
        ["lfs", "pull", "--include", include, REMOTE_NAME],
        enable_lfs_smudge=True,
    )
    _git(
        checkout,
        ["lfs", "checkout", *repo_paths],
        enable_lfs_smudge=True,
    )
    return True


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
    clone_env = os.environ.copy()
    clone_env["GIT_LFS_SKIP_SMUDGE"] = "1"
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
        ],
        env=clone_env,
    )
    if _has_committed_history_migration_manifest(destination):
        # LFS filters are commonly installed in the source checkout's local
        # Git config, which is not copied by clone. Install them only for
        # migrated checkouts; --skip-repo avoids a disposable pre-push hook.
        _install_local_lfs_filters(destination)
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
    if _has_committed_history_migration_manifest(clone):
        _pull_archival_bundle(clone)
    if not _is_ancestor(clone, EXPECTED_REVISION, fetched_main):
        previous_head = _git_output(clone, ["rev-parse", "HEAD^{commit}"])
        _git(clone, ["checkout", "--detach", fetched_main])
        try:
            if _has_committed_history_migration_manifest(clone):
                # A checkout can leave LFS pointers in place after switching
                # commits; explicitly materialize the already-fetched parts
                # before the helper opens the archived bundle.
                _pull_archival_bundle(clone)
            proved = _prove_archival_lineage(clone, EXPECTED_REVISION, RELEASE)
        finally:
            _git(clone, ["checkout", "--detach", previous_head])
        if not proved:
            raise GateError(
                f"required evidence revision {EXPECTED_REVISION} is not an ancestor of "
                f"fetched main {fetched_main} and no committed archival proof is available"
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
        if not _is_ancestor(clone, EXPECTED_REVISION, current_head) and not _prove_archival_lineage(
            clone, EXPECTED_REVISION, RELEASE
        ):
            raise GateError('current committed tree does not contain required evidence revision or archival proof')
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

        # The current branch may already contain evidence for the next
        # release. Validate this release from its immutable tag after proving
        # that the frozen manifest and generated results match the branch.
        if tag is not None:
            _git(clone, ["checkout", "--detach", tag])

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
        help="copy generated results here when the v0.8.0 tag is absent",
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
