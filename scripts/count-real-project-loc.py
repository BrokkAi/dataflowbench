#!/usr/bin/env python3
"""Count preregistered physical source lines for one pinned source tree.

This is measurement plumbing, not an analyzer runner.  It deliberately has a
small, stdlib-only surface so a freeze can bind this file's SHA-256 and replay
the same count without depending on a moving third-party line-count package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


SCHEMA_VERSION = 1
EXTENSIONS = {
    "java": {".java"},
    "javascript": {".cjs", ".js", ".mjs"},
    "python": {".py"},
}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "deps",
    "dist",
    "external",
    "node_modules",
    "out",
    "target",
    "third-party",
    "third_party",
    "vendor",
    "vendors",
    "venv",
}
GENERATED_NAME_FRAGMENTS = (".generated.", "_generated.", ".min.js")
GENERATED_MARKERS = (b"@generated", b"generated code", b"do not edit")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_tree(root: Path, language: str) -> tuple[list[dict[str, object]], dict[str, int]]:
    included: list[dict[str, object]] = []
    excluded = {"directory": 0, "generated_name": 0, "generated_marker": 0, "symlink": 0}
    extensions = EXTENSIONS[language]

    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for name in sorted(directories):
            candidate = current_path / name
            if candidate.is_symlink():
                excluded["symlink"] += 1
            elif name.lower() in EXCLUDED_DIRECTORIES:
                excluded["directory"] += 1
            else:
                kept_directories.append(name)
        directories[:] = kept_directories

        for name in sorted(filenames):
            path = current_path / name
            if path.suffix.lower() not in extensions:
                continue
            relative = path.relative_to(root).as_posix()
            lowered_name = name.lower()
            if path.is_symlink():
                excluded["symlink"] += 1
                continue
            if any(fragment in lowered_name for fragment in GENERATED_NAME_FRAGMENTS):
                excluded["generated_name"] += 1
                continue
            with path.open("rb") as handle:
                prefix = handle.read(8192).lower()
                if any(marker in prefix for marker in GENERATED_MARKERS):
                    excluded["generated_marker"] += 1
                    continue
                handle.seek(0)
                lines = sum(1 for _ in handle)
            included.append({"path": relative, "physical_lines": lines, "sha256": file_sha256(path)})

    included.sort(key=lambda row: str(row["path"]))
    return included, excluded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="materialized root of one verified source archive")
    parser.add_argument("--language", required=True, choices=sorted(EXTENSIONS))
    parser.add_argument("--pin-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--source-archive-sha256", required=True)
    args = parser.parse_args()

    root = args.root.resolve(strict=True)
    if not root.is_dir():
        parser.error("root must be a directory")
    if len(args.revision) != 40 or any(character not in "0123456789abcdef" for character in args.revision):
        parser.error("revision must be 40 lowercase hexadecimal characters")
    if len(args.source_archive_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in args.source_archive_sha256
    ):
        parser.error("source archive SHA-256 must be 64 lowercase hexadecimal characters")

    files, excluded = count_tree(root, args.language)
    result = {
        "schema_version": SCHEMA_VERSION,
        "pin_id": args.pin_id,
        "revision": args.revision,
        "source_archive_sha256": args.source_archive_sha256,
        "language": args.language,
        "definition": "physical newline-delimited lines, including blank and comment lines",
        "extensions": sorted(EXTENSIONS[args.language]),
        "excluded_directories": sorted(EXCLUDED_DIRECTORIES),
        "generated_name_fragments": list(GENERATED_NAME_FRAGMENTS),
        "generated_markers_first_8192_bytes_ascii_case_insensitive": [
            marker.decode("ascii") for marker in GENERATED_MARKERS
        ],
        "symlinks_followed": False,
        "files": files,
        "file_count": len(files),
        "physical_source_lines": sum(int(row["physical_lines"]) for row in files),
        "excluded_entry_counts": excluded,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
