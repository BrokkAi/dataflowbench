#!/usr/bin/env python3
"""Inventory exact task-owned runtime bytes, modes and symlink targets."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inventory(root):
    root = root.absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("runtime root must be a real directory")
    files, links, external = [], [], {}
    for current, directories, names in os.walk(root, followlinks=False):
        for name in sorted(directories + names):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            mode = stat.S_IMODE(path.lstat().st_mode)
            if path.is_symlink():
                target = path.resolve(strict=True)
                links.append({"path": relative, "target": os.readlink(path), "mode": mode})
                if not target.is_relative_to(root):
                    if not target.is_file():
                        raise ValueError("external directory symlink requires a separately reviewed runtime: " + str(path))
                    external[str(target)] = {"path": str(target), "sha256": digest(target),
                                             "mode": stat.S_IMODE(target.stat().st_mode)}
            elif path.is_file():
                files.append({"path": relative, "sha256": digest(path), "mode": mode})
            elif not path.is_dir():
                raise ValueError("unsupported runtime entry: " + str(path))
    if not files:
        raise ValueError("runtime inventory is empty")
    return {"schema_version": 1, "root": str(root),
            "files": sorted(files, key=lambda row: row["path"]),
            "symlinks": sorted(links, key=lambda row: row["path"]),
            "external_files": [external[key] for key in sorted(external)]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.root)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(str(args.root) + ": " + str(len(result["files"])) + " files")
