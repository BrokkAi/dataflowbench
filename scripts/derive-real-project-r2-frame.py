#!/usr/bin/env python3
"""Derive R2's candidate frame from its committed advisory snapshot only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path("corpus/real-project/r2")
MANIFEST = ROOT / "snapshot/manifest.json"
OUTPUT = ROOT / "frame.json"
COMMIT_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/commit/([0-9a-f]{7,40})")
REPOSITORY_URL = re.compile(r"^https://github\.com/([^/]+)/([^/#?]+)/?$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def admit(advisory: dict, stratum: str, ecosystem: str, evidence: dict) -> dict | None:
    if advisory.get("withdrawn_at"):
        return None
    location = advisory.get("source_code_location") or ""
    matched = REPOSITORY_URL.match(location)
    if not matched:
        return None
    owner, repository = matched.group(1), matched.group(2)
    fixes: list[str] = []
    for reference in advisory.get("references", []):
        commit = COMMIT_URL.match(reference)
        if not commit:
            continue
        if commit.group(1).lower() != owner.lower() or commit.group(2).lower() != repository.lower():
            continue
        if commit.group(3) not in fixes:
            fixes.append(commit.group(3))
    if not fixes:
        return None
    return {
        "stratum": stratum,
        "ecosystem": ecosystem,
        "ghsa_id": advisory["ghsa_id"],
        "cve_id": advisory.get("cve_id"),
        "cwes": [cwe["cwe_id"] for cwe in advisory.get("cwes", [])],
        "severity": advisory.get("severity"),
        "published_at": advisory.get("published_at"),
        "repository": f"{owner}/{repository}",
        "source_code_location": location,
        "packages": sorted({item["package"]["name"] for item in advisory.get("vulnerabilities", [])}),
        "fix_commit_references": fixes,
        "advisory_evidence": evidence,
    }


def main() -> int:
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    candidates = []
    raw_counts = {}
    for query in manifest["queries"]:
        raw_counts[query["stratum"]] = 0
        for page in query["pages"]:
            path = pathlib.Path(page["response_path"])
            body = path.read_bytes()
            if digest(body) != page["sha256"]:
                raise RuntimeError(f"snapshot digest mismatch: {path}")
            advisories = json.loads(body)
            raw_counts[query["stratum"]] += len(advisories)
            for index, advisory in enumerate(advisories):
                candidate = admit(
                    advisory,
                    query["stratum"],
                    query["ecosystem"],
                    {"path": path.as_posix(), "sha256": page["sha256"], "array_index": index},
                )
                if candidate is not None:
                    candidates.append(candidate)
    candidates.sort(key=lambda row: (row["stratum"], row["ghsa_id"]))
    admitted_counts = {
        stratum: sum(candidate["stratum"] == stratum for candidate in candidates)
        for stratum in ("java", "javascript", "python")
    }
    frame = {
        "schema_version": 2,
        "wave": "R2",
        "derived_from": {"path": MANIFEST.as_posix(), "sha256": digest(manifest_bytes)},
        "admission_rule": "A non-withdrawn advisory is admitted only when source_code_location is a github.com owner/repository and at least one reference is a commit URL under that same repository.",
        "counts": {
            "raw": raw_counts,
            "admitted": admitted_counts,
            "rejected": {key: raw_counts[key] - admitted_counts[key] for key in raw_counts},
        },
        "candidates": candidates,
        "analyzer_evidence_consulted": False,
    }
    OUTPUT.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n")
    print(f"derived {len(candidates)} candidates: {admitted_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
