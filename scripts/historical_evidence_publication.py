#!/usr/bin/env python3
"""Verify or hydrate archived history after a later release freeze is published.

The frozen historical_evidence helper remains authoritative for archive bytes,
rewritten-base identity, and preserved tags. This wrapper changes only which
commit is checked for the historical filtered-tree invariant once the current
release advances beyond v0.9.0. It does not validate or qualify a later release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PINNED_HELPER_SHA256 = "fae3e4e0086700dca4b061d95e1c3c00fc617ca3c7049be8afd6a91514cb5a18"
import historical_evidence as historical

OLD_FREEZE = "reports/freeze.json"
OLD_RESULTS = "results/results.json"
RETAINED_V090_FREEZE = "reports/releases/v0.9.0/freeze.json"
RETAINED_V090_RESULTS = "docs/src/data/archive/v0-9-0-results.json"
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


# Compile the reviewed source bytes into the imported module so a timestamp-
# based stale .pyc cannot silently change the helper implementation in use.
_helper_path = Path(historical.__file__)
_helper_source = _helper_path.read_bytes()
if hashlib.sha256(_helper_source).hexdigest() != PINNED_HELPER_SHA256:
    raise RuntimeError("frozen historical_evidence.py differs from the reviewed helper identity")
exec(compile(_helper_source, str(_helper_path), "exec", dont_inherit=True), historical.__dict__)


class PublicationEvidenceError(historical.EvidenceError):
    """The successor publication's historical evidence boundary is invalid."""


def _assert_frozen_helper() -> None:
    helper_path = Path(historical.__file__)
    digest = hashlib.sha256(helper_path.read_bytes()).hexdigest()
    if digest != PINNED_HELPER_SHA256:
        raise PublicationEvidenceError(
            "frozen historical_evidence.py differs from the reviewed helper identity"
        )


def _read_regular(root: Path, relative: str, *, limit: int = 8 * 1024 * 1024) -> bytes:
    fd = historical._open_nofollow(root, Path(relative))
    try:
        with os.fdopen(fd, "rb") as stream:
            data = stream.read(limit + 1)
    except OSError as exc:
        raise PublicationEvidenceError(f"cannot read {relative}: {exc}") from exc
    if len(data) > limit:
        raise PublicationEvidenceError(f"{relative} exceeds the {limit}-byte safety limit")
    return data


def _decode_json(data: bytes, where: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=historical._reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, historical.EvidenceError) as exc:
        raise PublicationEvidenceError(f"{where} is not unambiguous UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicationEvidenceError(f"{where} must be a JSON object")
    return value


def _current_release(root: Path) -> tuple[Path, dict[str, Any], str]:
    root_path, _, head = historical._repo_root(root)
    entries = historical._tree_entries(root_path, head)
    entry = entries.get(os.fsencode(OLD_FREEZE))
    if entry is None or entry[0] not in (b"100644", b"100755") or entry[1] != b"blob":
        raise PublicationEvidenceError("current HEAD lacks a regular reports/freeze.json blob")
    freeze_bytes = historical._git(root_path, ["cat-file", "blob", entry[2].decode("ascii")]).stdout
    freeze = _decode_json(freeze_bytes, OLD_FREEZE)
    benchmark = freeze.get("benchmark")
    if not isinstance(benchmark, dict) or not isinstance(benchmark.get("release"), str):
        raise PublicationEvidenceError("current freeze lacks benchmark.release")
    if benchmark["release"] == "v0.9.2" and _read_regular(root_path, OLD_FREEZE) != freeze_bytes:
        raise PublicationEvidenceError("working reports/freeze.json differs from current HEAD")
    return root_path, freeze, benchmark["release"]


def _verify_v092_freeze(freeze: dict[str, Any]) -> None:
    if type(freeze.get("schema_version")) is not int or freeze["schema_version"] != 1:
        raise PublicationEvidenceError("current v0.9.2 freeze has an unsupported schema_version")
    benchmark = freeze.get("benchmark")
    claim = freeze.get("claim")
    if not isinstance(benchmark, dict) or benchmark.get("release") != "v0.9.2":
        raise PublicationEvidenceError("current freeze is not v0.9.2")
    if benchmark.get("dirty") is not False:
        raise PublicationEvidenceError("current v0.9.2 freeze must declare benchmark.dirty=false")
    if not isinstance(benchmark.get("revision"), str) or not REVISION_RE.fullmatch(benchmark["revision"]):
        raise PublicationEvidenceError("current v0.9.2 freeze revision must be a full lowercase SHA-1")
    if not isinstance(claim, dict) or claim.get("scope") != "release":
        raise PublicationEvidenceError("current v0.9.2 freeze claim.scope must be release")


def _verify_retained_v090_files(
    root: Path, archive_repo: Path, manifest: dict[str, Any], head: str
) -> None:
    original_entries = historical._tree_entries(archive_repo, manifest["original_main"])
    current_entries = historical._tree_entries(root, head)
    pairs = (
        (RETAINED_V090_FREEZE, OLD_FREEZE),
        (RETAINED_V090_RESULTS, OLD_RESULTS),
    )
    for retained_path, original_path in pairs:
        retained_key = os.fsencode(retained_path)
        original_key = os.fsencode(original_path)
        retained = current_entries.get(retained_key)
        original = original_entries.get(original_key)
        if retained is None or original is None:
            raise PublicationEvidenceError(f"retained v0.9.0 archive path is missing: {retained_path}")
        if retained[0] not in (b"100644", b"100755") or original[0] not in (b"100644", b"100755"):
            raise PublicationEvidenceError(f"retained v0.9.0 archive path is not a regular file: {retained_path}")
        if retained != original:
            raise PublicationEvidenceError(f"retained v0.9.0 Git blob differs from original_main: {retained_path}")
        expected = historical._git(
            archive_repo,
            ["cat-file", "blob", original[2].decode("ascii")],
        ).stdout
        actual = _read_regular(root, retained_path)
        if actual != expected:
            raise PublicationEvidenceError(f"retained v0.9.0 working file differs from original_main: {retained_path}")


def _successor_state(root: Path) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    _assert_frozen_helper()
    root_path, _, manifest, archive_repo, head = historical._load_archive(Path(root))
    historical._verify_current_tags(root_path, manifest)
    ancestor = historical._git(
        root_path,
        ["merge-base", "--is-ancestor", manifest["rewritten_base"], head],
        check=False,
    )
    if ancestor.returncode != 0:
        raise PublicationEvidenceError("rewritten_base is not an ancestor of current HEAD")
    # The filtered-history proof is anchored at the migration commit. Later
    # release commits may legitimately replace the current freeze/results.
    historical._check_filtered_tree(root_path, archive_repo, manifest, manifest["rewritten_base"])
    _verify_retained_v090_files(root_path, archive_repo, manifest, head)
    freeze = _decode_json(_read_regular(root_path, OLD_FREEZE), OLD_FREEZE)
    _verify_v092_freeze(freeze)
    return (
        {
            "verified": True,
            "scope": "historical-only",
            "original_main": manifest["original_main"],
            "rewritten_base": manifest["rewritten_base"],
            "head": head,
            "preserved_tags": len(manifest["preserved_tags"]),
            "removed_prefixes": len(manifest["removed_paths"]["prefixes"]),
            "removed_files": len(manifest["removed_paths"]["files"]),
            "bundle_sha256": manifest["bundle"]["sha256"],
            "retained_v090_files": 2,
            "current_release_validation": "pending-v0.9.2-release-gate",
            "publication_qualification": "not-evaluated",
        },
        root_path,
        manifest,
        archive_repo,
    )


def verify(root: Path) -> dict[str, Any]:
    """Delegate v0.9.0 unchanged; prove only historical boundaries for v0.9.2."""
    _assert_frozen_helper()
    _, _, release = _current_release(Path(root))
    if release == "v0.9.0":
        return historical.verify(Path(root))
    if release != "v0.9.2":
        raise PublicationEvidenceError(f"unsupported current release for historical wrapper: {release!r}")
    result, _, _, _ = _successor_state(Path(root))
    return result


def hydrate(root: Path) -> dict[str, Any]:
    """Restore only archive-manifest-selected regular files after verifying scope."""
    _assert_frozen_helper()
    _, _, release = _current_release(Path(root))
    if release == "v0.9.0":
        return historical.hydrate(Path(root))
    if release != "v0.9.2":
        raise PublicationEvidenceError(f"unsupported current release for historical wrapper: {release!r}")
    _, root_path, manifest, archive_repo = _successor_state(Path(root))
    selected = historical._selected_original_entries(archive_repo, manifest)
    restored = already_present = restored_bytes = already_present_bytes = 0
    with historical._ArchiveBlobReader(archive_repo) as reader:
        for path, mode, object_id in selected:
            relative = os.fsdecode(path)
            try:
                created, size = historical._hydrate_one(root_path, relative, mode, object_id, reader)
            except historical.EvidenceError as exc:
                if str(exc) == "refusing to overwrite different bytes":
                    raise PublicationEvidenceError(f"refusing to overwrite different bytes at {relative!r}") from exc
                raise
            if created:
                restored += 1
                restored_bytes += size
            else:
                already_present += 1
                already_present_bytes += size
    return {
        "verified": True,
        "scope": "historical-only",
        "restored_files": restored,
        "already_present_files": already_present,
        "restored_bytes": restored_bytes,
        "already_present_bytes": already_present_bytes,
        "bundle_sha256": manifest["bundle"]["sha256"],
        "current_release_validation": "pending-v0.9.2-release-gate",
        "publication_qualification": "not-evaluated",
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("verify", "verify archived history and the current release boundary"),
        ("hydrate", "restore only manifest-selected archived paths"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(args.root) if args.command == "verify" else hydrate(args.root)
    except (historical.EvidenceError, OSError, subprocess.SubprocessError) as exc:
        print(f"historical-evidence-publication: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
