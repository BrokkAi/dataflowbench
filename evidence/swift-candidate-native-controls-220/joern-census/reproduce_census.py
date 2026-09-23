#!/usr/bin/env python3
"""Reproducible, non-scored Joern candidate census for DataFlowBench #220.

This script reads only an already acquired/extracted candidate. It writes
incremental JSONL rows and summary JSON under the caller-selected output dir.
It never edits the repository and never executes Joern/JVM code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path


KEYWORDS = re.compile(
    r"(?i)(defaultsemantics|semantics|semantic|role|source|sink|summary|model|loader|"
    r"native|swift|taint|dataflow|atoi|processinfo|commandline|contents|endpoint)"
)


def sha256_stream(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_capture(argv: list[str]) -> dict:
    started = time.time()
    try:
        completed = subprocess.run(argv, text=True, capture_output=True, check=False)
        return {
            "argv": argv,
            "exit_status": completed.returncode,
            "elapsed_seconds": round(time.time() - started, 6),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except OSError as exc:
        return {
            "argv": argv,
            "exit_status": None,
            "elapsed_seconds": round(time.time() - started, 6),
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def first_party_classification(jar_name: str, member_name: str) -> str:
    """Conservative ecosystem provenance, recorded as a rule, not a role claim."""
    if not member_name.endswith(".class"):
        return "not-class"
    package = member_name[:-6].replace("/", ".")
    if member_name.startswith("io/joern/"):
        return "joern-first-party-package"
    if member_name.startswith("io/shiftleft/"):
        return "joern-ecosystem-package"
    if jar_name.startswith("io.joern."):
        return "joern-artifact-other-package"
    return "dependency-or-unclassified"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    archive = args.archive.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    files_path = out / "all-files.jsonl"
    jars_path = out / "jars.jsonl"
    unique_jars_path = out / "unique-jars.jsonl"
    members_path = out / "all-jar-members.jsonl"
    resources_path = out / "all-jar-resources.jsonl"
    classes_path = out / "first-party-classes.jsonl"
    keywords_path = out / "keyword-navigation-hits.jsonl"
    for path in (files_path, jars_path, unique_jars_path, members_path, resources_path, classes_path, keywords_path):
        path.write_text("", encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "started_epoch": time.time(),
        "candidate": str(candidate),
        "archive": str(archive),
        "python": run_capture([sys.executable, "--version"]),
        "platform": {"sys_platform": sys.platform, "os_name": os.name},
        "rules": {
            "first_party_classification": "io/joern packages are Joern first-party package provenance; io/shiftleft packages are Joern ecosystem provenance; all other classes remain dependency-or-unclassified",
            "keyword_use": "navigation only; no absence or role conclusion",
            "resource_scope": "every non-directory JAR member whose name does not end in .class or .tasty, including metadata and unselected resources",
        },
    }
    write_json(out / "run-start.json", manifest)

    archive_stat = archive.stat()
    archive_row = {
        "path": str(archive),
        "size_bytes": archive_stat.st_size,
        "sha256": sha256_stream(archive),
        "mode": stat.S_IMODE(archive_stat.st_mode),
    }
    write_json(out / "archive.json", archive_row)

    candidate_files = []
    for root, dirs, names in os.walk(candidate, followlinks=False):
        dirs.sort()
        names.sort()
        for name in names:
            path = Path(root) / name
            relative = path.relative_to(candidate).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                row = {"relative_path": relative, "kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISREG(info.st_mode):
                row = {
                    "relative_path": relative,
                    "kind": "file",
                    "size_bytes": info.st_size,
                    "sha256": sha256_stream(path),
                }
                candidate_files.append((relative, path, row))
            else:
                row = {"relative_path": relative, "kind": "other", "mode": stat.S_IMODE(info.st_mode)}
            write_jsonl(files_path, row)
            if KEYWORDS.search(relative):
                write_jsonl(keywords_path, {"surface": "filesystem-path", "relative_path": relative, "keywords": sorted(set(m.group(0).lower() for m in KEYWORDS.finditer(relative)))})

    jars = sorted((path for _, path, _ in candidate_files if path.suffix.lower() == ".jar"), key=lambda p: p.relative_to(candidate).as_posix())
    seen_jar_sha256: set[str] = set()
    duplicate_jar_count = 0
    total_members = 0
    total_resources = 0
    total_classes = 0
    keyword_member_count = 0
    for jar in jars:
        jar_rel = jar.relative_to(candidate).as_posix()
        jar_row = {
            "relative_path": jar_rel,
            "size_bytes": jar.stat().st_size,
            "sha256": sha256_stream(jar),
        }
        write_jsonl(jars_path, jar_row)
        jar_sha256 = jar_row["sha256"]
        if jar_sha256 in seen_jar_sha256:
            duplicate_jar_count += 1
            continue
        seen_jar_sha256.add(jar_sha256)
        write_jsonl(unique_jars_path, {
            "jar_sha256": jar_sha256,
            "representative_jar": jar_rel,
            "size_bytes": jar_row["size_bytes"],
        })
        try:
            with zipfile.ZipFile(jar) as handle:
                for member in sorted(handle.infolist(), key=lambda item: item.filename):
                    total_members += 1
                    is_dir = member.is_dir() or member.filename.endswith("/")
                    row = {
                        "jar_sha256": jar_sha256,
                        "representative_jar": jar_rel,
                        "member": member.filename,
                        "is_directory": is_dir,
                        "compressed_size_bytes": member.compress_size,
                        "size_bytes": member.file_size,
                        "crc32": f"{member.CRC:08x}",
                    }
                    data = b""
                    if not is_dir:
                        data = handle.read(member)
                        row["sha256"] = sha256_bytes(data)
                    write_jsonl(members_path, row)
                    if not is_dir and not member.filename.endswith((".class", ".tasty")):
                        total_resources += 1
                        write_jsonl(resources_path, row)
                    if not is_dir and member.filename.endswith(".class"):
                        total_classes += 1
                        classification = first_party_classification(jar.name, member.filename)
                        if classification in ("joern-first-party-package", "joern-ecosystem-package", "joern-artifact-other-package"):
                            write_jsonl(classes_path, {
                                "jar_sha256": jar_sha256,
                                "representative_jar": jar_rel,
                                "member": member.filename,
                                "binary_name": member.filename[:-6].replace("/", "."),
                                "classification": classification,
                                "size_bytes": member.file_size,
                                "sha256": row["sha256"],
                            })
                    haystack = (jar_rel + "!" + member.filename).lower()
                    text = data.decode("utf-8", errors="ignore") if data else ""
                    matches = sorted(set(m.group(0).lower() for m in KEYWORDS.finditer(haystack + "\n" + text)))
                    if matches:
                        keyword_member_count += 1
                        write_jsonl(keywords_path, {
                            "surface": "jar-member",
                            "jar_sha256": jar_sha256,
                            "representative_jar": jar_rel,
                            "member": member.filename,
                            "keywords": matches,
                            "member_sha256": row.get("sha256"),
                        })
        except (OSError, zipfile.BadZipFile) as exc:
            write_jsonl(out / "errors.jsonl", {"surface": "jar", "jar": jar_rel, "error": f"{type(exc).__name__}: {exc}"})

    summary = {
        "schema_version": 1,
        "candidate": str(candidate),
        "archive": archive_row,
        "filesystem_file_count": sum(1 for _, _, row in candidate_files if row.get("kind") == "file"),
        "jar_count": len(jars),
        "unique_jar_count": len(seen_jar_sha256),
        "duplicate_jar_count": duplicate_jar_count,
        "jar_member_count": total_members,
        "non_class_non_tasty_resource_count": total_resources,
        "class_member_count": total_classes,
        "first_party_class_row_count": sum(1 for _ in classes_path.open(encoding="utf-8")),
        "keyword_navigation_hit_row_count": sum(1 for _ in keywords_path.open(encoding="utf-8")),
        "candidate_file_hashes": str(files_path),
        "jar_hashes": str(jars_path),
        "unique_jar_content": str(unique_jars_path),
        "all_member_hashes": str(members_path),
        "all_resource_hashes": str(resources_path),
        "first_party_classes": str(classes_path),
        "keyword_navigation_hits": str(keywords_path),
        "completed_epoch": time.time(),
    }
    write_json(out / "summary.json", summary)
    manifest["completed_epoch"] = time.time()
    write_json(out / "run-complete.json", manifest)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
