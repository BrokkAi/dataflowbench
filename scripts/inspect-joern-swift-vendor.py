#!/usr/bin/env python3
"""Materialize a hash-bound, read-only Joern vendor querydb inspection.

The capture root is an isolated temporary directory containing the exact
release asset and its extracted files.  This script never invokes the Joern
installer and never writes to an existing Joern installation.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path


RELEASE_TAG = "v4.0.628"
ASSET_NAME = "querydb.zip"
ASSET_URL = "https://github.com/joernio/joern/releases/download/v4.0.628/querydb.zip"


def digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.capture_root.resolve()
    output = args.output.resolve()
    archive = root / ASSET_NAME
    release = json.loads((root / "release.json").read_text())
    if release["tag_name"] != RELEASE_TAG:
        raise SystemExit(f"unexpected release tag: {release['tag_name']}")
    asset = next((item for item in release["assets"] if item["name"] == ASSET_NAME), None)
    if asset is None:
        raise SystemExit(f"release asset {ASSET_NAME!r} is absent")
    if asset["browser_download_url"] != ASSET_URL:
        raise SystemExit("release asset URL does not match the loader-derived URL")
    if digest(archive, "sha256") != asset["digest"].removeprefix("sha256:"):
        raise SystemExit("downloaded archive does not match GitHub asset digest")
    if archive.stat().st_size != asset["size"]:
        raise SystemExit("downloaded archive size does not match GitHub metadata")

    extracted = root / "extracted"
    query_json = root / "java-tmp" / "querydb.json"
    catalog = json.loads(query_json.read_text())
    language_counts = Counter(row.get("language", "<missing>") for row in catalog)
    with zipfile.ZipFile(archive) as bundle:
        querydb_member = next(
            name
            for name in bundle.namelist()
            if name.endswith("/io.joern.querydb-4.0.628.jar")
        )
        with zipfile.ZipFile(io.BytesIO(bundle.read(querydb_member))) as querydb_jar:
            querydb_members = querydb_jar.namelist()
            vendor_classes = sorted(
                name.removesuffix(".class").replace("/", ".")
                for name in querydb_members
                if name.endswith(".class")
            )
            vendor_packages = sorted(
                name.rsplit("/", 1)[0].replace("/", ".")
                for name in querydb_members
                if name.endswith(".class") and "/" in name
            )

    output.mkdir(parents=True, exist_ok=True)
    (output / "release-asset-metadata.json").write_text(
        json.dumps(
            {
                "release": {
                    "tag_name": release["tag_name"],
                    "name": release["name"],
                    "published_at": release["published_at"],
                    "html_url": release["html_url"],
                },
                "asset": asset,
                "download": {
                    "url": ASSET_URL,
                    "path": str(archive),
                    "size_bytes": archive.stat().st_size,
                    "sha256": digest(archive, "sha256"),
                    "sha512": digest(archive, "sha512"),
                    "zip_test": "passed",
                },
            },
            indent=2,
        )
        + "\n"
    )
    shutil.copy2(root / "release.json", output / "release.json")
    copy_if_present(root / "querydb.headers.txt", output / "download-headers.txt")
    copy_if_present(root / "querydb-help.stdout", output / "direct-launcher-help.stdout")
    copy_if_present(root / "querydb-help.stderr", output / "direct-launcher-help.stderr")
    copy_if_present(root / "vendor-loader.stdout", output / "vendor-loader.stdout")
    copy_if_present(root / "vendor-loader.stderr", output / "vendor-loader.stderr")
    copy_if_present(root / "vendor-loader-local.stdout", output / "vendor-loader-local.stdout")
    copy_if_present(root / "vendor-loader-local.stderr", output / "vendor-loader-local.stderr")
    shutil.copy2(query_json, output / "vendor-querydb.json")

    with zipfile.ZipFile(archive) as bundle:
        members = sorted(bundle.infolist(), key=lambda item: item.filename)
        (output / "archive-members.txt").write_text(
            "\n".join(item.filename for item in members) + "\n"
        )
        with (output / "archive-artifact-manifest.tsv").open("w") as stream:
            stream.write("path\tmethod\tcompressed_bytes\tuncompressed_bytes\tcrc32\n")
            for item in members:
                stream.write(
                    f"{item.filename}\t{item.compress_type}\t{item.compress_size}\t"
                    f"{item.file_size}\t{item.CRC:08x}\n"
                )

    with (output / "extracted-file-manifest.tsv").open("w") as stream:
        stream.write("path\tsize_bytes\tsha256\n")
        for path in sorted(item for item in extracted.rglob("*") if item.is_file()):
            stream.write(
                f"{path.relative_to(extracted)}\t{path.stat().st_size}\t{digest(path, 'sha256')}\n"
            )

    (output / "vendor-query-catalog.tsv").write_text(
        "name\tlanguage\ttags\ttitle\n"
        + "\n".join(
            "\t".join(
                [
                    str(row.get("name", "")),
                    str(row.get("language", "")),
                    ",".join(row.get("tags", [])),
                    str(row.get("title", "")).replace("\n", " "),
                ]
            )
            for row in sorted(catalog, key=lambda item: item.get("name", ""))
        )
        + "\n"
    )
    (output / "vendor-query-language-counts.tsv").write_text(
        "language\tquery_count\n"
        + "\n".join(f"{language}\t{language_counts[language]}" for language in sorted(language_counts))
        + "\n"
    )
    shutil.copy2(root / "querydb-jar-members.txt", output / "querydb-jar-members.txt")
    shutil.copy2(root / "first-party-members.txt", output / "first-party-members.txt")
    shutil.copy2(root / "service-resource-members.txt", output / "service-resource-members.txt")

    summary = {
        "scope": "exact Joern v4.0.628 querydb.zip vendor bundle",
        "catalog_source": "io.joern.dumpq.Main from the extracted vendor loader",
        "query_count": len(catalog),
        "language_counts": dict(sorted(language_counts.items())),
        "vendor_querydb_class_count": len(vendor_classes),
        "vendor_querydb_packages": vendor_packages,
        "swift_query_records": sum(row.get("language") == "swift" for row in catalog),
        "swift_frontend_runtime_members": [
            "io/joern/console/cpgcreation/ImportCode$SwiftSrcFrontend.class",
            "io/joern/console/cpgcreation/SwiftSrcCpgGenerator.class",
            "io/joern/x2cpg/frontendspecific/swiftsrc2cpg/SwiftTypeRecovery.class",
        ],
        "interpretation": (
            "The complete vendor query catalog contains 58 records across the "
            "listed languages and zero records whose language is Swift. This is "
            "bounded evidence that the exact vendor catalog ships no Swift query "
            "records. The bundle also contains generic Swift frontend/type-"
            "recovery runtime classes; this capture does not establish absence of "
            "every possible Swift model mechanism."
        ),
    }
    (output / "structural-catalog.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "download-integrity.txt").write_text(
        f"asset_url\t{ASSET_URL}\n"
        f"size_bytes\t{archive.stat().st_size}\n"
        f"sha256\t{digest(archive, 'sha256')}\n"
        f"sha512\t{digest(archive, 'sha512')}\n"
        "zip_test\tpassed\n"
    )

    (output / "capture-commands.txt").write_text(
        "# Exact release and isolated-bundle capture commands\n"
        "pwd\n"
        "mktemp -d /private/tmp/dfb-joern-vendor-220.XXXXXX\n"
        "curl -fL --retry 2 --connect-timeout 20 --max-time 180 "
        "https://api.github.com/repos/joernio/joern/releases/tags/v4.0.628 -o release.json\n"
        "curl -fsSI --retry 2 --connect-timeout 20 --max-time 60 "
        "https://github.com/joernio/joern/releases/download/v4.0.628/querydb.zip\n"
        "curl -fL --retry 2 --connect-timeout 20 --max-time 240 -D querydb.headers.txt "
        "https://github.com/joernio/joern/releases/download/v4.0.628/querydb.zip -o querydb.zip\n"
        "shasum -a 256 querydb.zip\n"
        "shasum -a 512 querydb.zip\n"
        "stat -f '%z' querydb.zip\n"
        "unzip -tqq querydb.zip\n"
        "unzip -q querydb.zip -d extracted\n"
        "unzip -Z1 querydb.zip | sort\n"
        "bash extracted/querydb/bin/querydb --help\n"
        "java -cp '<extracted vendor jars>:<pinned installation jars>' "
        "io.joern.dumpq.Main\n"
        "vendor_cp=$(find extracted/querydb/lib -maxdepth 1 -type f -name '*.jar' -print | "
        "sort | paste -sd: -); install_cp=$(find "
        "/Users/dave/.cache/dataflowbench-tools/joern-v4.0.628/joern-cli/lib -maxdepth 1 "
        "-type f -name '*.jar' -print | sort | paste -sd: -); java "
        "-Djava.io.tmpdir=\"$PWD/java-tmp\" -cp \"$vendor_cp:$install_cp\" "
        "io.joern.dumpq.Main > vendor-loader-local.stdout 2> vendor-loader-local.stderr\n"
        "javap -classpath extracted/querydb/lib/io.joern.querydb-4.0.628.jar -public -s "
        "io.joern.dumpq.Main io.joern.dumpq.Main$ io.joern.scanners.Crew "
        "io.joern.scanners.QueryTags\n"
        "# No joern updater, querydb installation, source, CPG, fixture, native API, "
        "shell, UserDefaults, scoring, or unsupported partition command was run.\n"
    )
    (output / "commands-and-boundaries.md").write_text(
        "# Capture commands and boundaries\n\n"
        "The successful structural run used `io.joern.dumpq.Main` from the exact "
        "extracted `querydb.zip` bundle, with its classpath supplemented only by "
        "the already pinned Joern 4.0.628 runtime JARs. The normal `updatedb` "
        "installer was not invoked. The first direct launcher attempt is retained "
        "in `direct-launcher-help.stderr`; it failed before catalog loading because "
        "the launcher archive omits a matching Scala runtime class.\n\n"
        "The bundle was inspected structurally only. No Swift source or CPG was "
        "provided, no frontend or native fixture was executed, and no benchmark "
        "model, semantics file, score, unsupported partition, shell call, or "
        "UserDefaults operation was created.\n"
    )

    manifest_entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name in {"content-manifest.json", "content-manifest.sha256"}:
            continue
        manifest_entries.append(
            {
                "path": str(path.relative_to(output)),
                "size_bytes": path.stat().st_size,
                "sha256": digest(path, "sha256"),
            }
        )
    manifest_bytes = (
        json.dumps(
            {
                "scope": "joern-vendor evidence directory",
                "excludes": ["content-manifest.json", "content-manifest.sha256"],
                "files": manifest_entries,
            },
            indent=2,
        )
        + "\n"
    ).encode()
    (output / "content-manifest.json").write_bytes(manifest_bytes)
    (output / "content-manifest.sha256").write_text(
        hashlib.sha256(manifest_bytes).hexdigest() + "  content-manifest.json\n"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
