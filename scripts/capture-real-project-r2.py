#!/usr/bin/env python3
"""Capture the prospective R2 advisory population without deriving a draw.

Run only after the R2 protocol commit has merged. The command records complete
GitHub Advisory response bodies and request/pagination provenance. It never
invokes an analyzer, evaluates eligibility, or selects a repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.parse

API_ROOT = "https://api.github.com/advisories"
OUTPUT_ROOT = pathlib.Path("corpus/real-project/r2/snapshot")
PROTOCOL = pathlib.Path("corpus/real-project/r2/protocol.json")
QUERIES = (
    ("java", "maven"),
    ("javascript", "npm"),
    ("python", "pip"),
)
PARAMETERS = {
    "type": "reviewed",
    "published": "2025-01-01..2025-12-31",
    "cwes": "22,78,89,94,611,918",
    "per_page": "100",
    "sort": "published",
    "direction": "asc",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], capture_output=True, check=True
    ).stdout.strip()


def verify_merged_protocol() -> tuple[str, str, str]:
    if git("status", "--porcelain"):
        raise RuntimeError("capture requires a clean worktree")
    revision = git(
        "log", "--diff-filter=A", "--format=%H", "-1", "--", str(PROTOCOL)
    ).decode()
    if len(revision) != 40:
        raise RuntimeError("cannot resolve the commit that introduced the R2 protocol")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "refs/remotes/origin/main"],
        capture_output=True,
        check=True,
    )
    committed = subprocess.run(
        ["git", "show", f"{revision}:{PROTOCOL.as_posix()}"],
        capture_output=True,
        check=True,
    ).stdout
    current = PROTOCOL.read_bytes()
    if current != committed:
        raise RuntimeError("the R2 protocol differs from its merged preregistration bytes")
    head = git("rev-parse", "HEAD").decode()
    return revision, sha256(current), head


def gh_api(url: str) -> tuple[bytes, dict[str, str], int]:
    parsed_url = urllib.parse.urlsplit(url)
    endpoint = urllib.parse.urlunsplit(("", "", parsed_url.path, parsed_url.query, ""))
    completed = subprocess.run(
        ["gh", "api", "--include", endpoint], capture_output=True, check=True
    )
    header, separator, body = completed.stdout.partition(b"\r\n\r\n")
    if not separator:
        header, separator, body = completed.stdout.partition(b"\n\n")
    if not separator:
        raise RuntimeError("GitHub response did not contain an HTTP header block")
    header_lines = header.decode("utf-8", errors="strict").splitlines()
    status_fields = header_lines[0].split()
    if len(status_fields) < 2 or not status_fields[1].isdigit():
        raise RuntimeError("GitHub response contained an invalid HTTP status line")
    status = int(status_fields[1])
    headers: dict[str, str] = {}
    for line in header_lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower().strip()] = value.strip()
    return body, headers, status


def next_url(link: str | None) -> str | None:
    if not link:
        return None
    for part in link.split(","):
        fields = [field.strip() for field in part.split(";")]
        if len(fields) > 1 and 'rel="next"' in fields[1:]:
            return fields[0].removeprefix("<").removesuffix(">")
    return None


def capture() -> None:
    if OUTPUT_ROOT.exists():
        raise RuntimeError(f"refusing to overwrite existing snapshot directory {OUTPUT_ROOT}")
    protocol_revision, protocol_sha256, source_head = verify_merged_protocol()
    manifest = {
        "schema_version": 2,
        "wave": "R2",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "capture_tool": "scripts/capture-real-project-r2.py",
        "protocol": {
            "path": PROTOCOL.as_posix(),
            "revision": protocol_revision,
            "sha256": protocol_sha256,
        },
        "source_head": source_head,
        "analyzer_evidence_consulted": False,
        "queries": [],
    }
    for stratum, ecosystem in QUERIES:
        parameters = {"ecosystem": ecosystem, **PARAMETERS}
        url = API_ROOT + "?" + urllib.parse.urlencode(parameters)
        pages = []
        page_number = 1
        while url:
            body, headers, status = gh_api(url)
            if status != 200:
                raise RuntimeError(f"GitHub returned HTTP {status} for {url}")
            parsed = json.loads(body)
            if not isinstance(parsed, list):
                raise RuntimeError(f"page {page_number} for {ecosystem} was not a JSON array")
            relative = pathlib.Path("advisories") / ecosystem / f"page-{page_number:04d}.json"
            path = OUTPUT_ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            following = next_url(headers.get("link"))
            pages.append(
                {
                    "page": page_number,
                    "request_url": url,
                    "retrieved_at": dt.datetime.now(dt.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "http_status": status,
                    "item_count": len(parsed),
                    "next_url": following,
                    "response_path": str((OUTPUT_ROOT / relative).as_posix()),
                    "sha256": sha256(body),
                }
            )
            url = following
            page_number += 1
        manifest["queries"].append(
            {"stratum": stratum, "ecosystem": ecosystem, "parameters": parameters, "pages": pages}
        )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (OUTPUT_ROOT / "manifest.json").write_bytes(encoded)


def main() -> int:
    argparse.ArgumentParser().parse_args()
    capture()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, RuntimeError, json.JSONDecodeError) as error:
        print(f"capture failed: {error}", file=sys.stderr)
        raise SystemExit(1)
