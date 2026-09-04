#!/usr/bin/env python3
"""Rebuild the real-project sampling frame from the GitHub Advisory Database.

This is the script that produced `corpus/real-project/frame.json` for wave R1,
kept so the frame's provenance is executable rather than described. It reads
advisory metadata only: it never invokes an analyzer, never reads a
DataFlowBench report, and has no way to know what any engine does with any
candidate. See docs/real-project-preregistration.md.

The frame is *retained*, not re-queried. The advisory database grows, so a later
run of this script will not reproduce the committed bytes; comparing its output
against the committed frame shows how the population has moved, which is input
to a future wave and never a correction to a wave already drawn.

Usage:
    gh auth login                       # the GitHub CLI supplies the credential
    python3 scripts/build-real-project-frame.py > /tmp/frame-candidates.json
"""

import json
import re
import subprocess
import sys

# One stratum per language, keyed by the ecosystem the advisory database indexes.
ECOSYSTEMS = {"maven": "java", "npm": "javascript", "pip": "python"}

# Weakness classes whose definition *is* a source-to-sink flow with an
# unambiguous sink: path traversal, OS command injection, SQL injection, code
# injection, XML external entity, and server-side request forgery. Cross-site
# scripting is deliberately absent — its sink is a framework-dependent rendering
# boundary, so a disagreement about an XSS case is usually a disagreement about
# the sink rather than about the flow.
CWES = "22,78,89,94,611,918"

# A closed historical window. An open-ended one would drift with every new
# disclosure and the frame would stop being a stable object.
WINDOW = "2025-01-01..2025-12-31"

COMMIT_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/commit/([0-9a-f]{7,40})")
REPOSITORY_URL = re.compile(r"^https://github\.com/([^/]+)/([^/#?]+)/?$")


def query(ecosystem: str) -> str:
    return (
        f"/advisories?ecosystem={ecosystem}&type=reviewed&published={WINDOW}"
        f"&cwes={CWES}&per_page=100&sort=published&direction=asc"
    )


def fetch(ecosystem: str) -> list[dict]:
    result = subprocess.run(
        ["gh", "api", query(ecosystem), "--paginate", "--slurp"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [advisory for page in json.loads(result.stdout) for advisory in page]


def admit(advisory: dict, stratum: str, ecosystem: str) -> dict | None:
    """Apply the frame admission rule.

    An advisory enters the frame when it is not withdrawn, its
    `source_code_location` is a GitHub repository, and at least one of its
    references is a commit URL under that same repository. The last condition is
    what makes a revision pin possible at all: without it there is no upstream
    commit to pin the vulnerable and fixed revisions against.
    """
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
        if commit.group(1).lower() != owner.lower():
            continue
        if commit.group(2).lower() != repository.lower():
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
        "packages": sorted(
            {item["package"]["name"] for item in advisory.get("vulnerabilities", [])}
        ),
        "fix_commit_references": fixes,
    }


def main() -> int:
    candidates = []
    for ecosystem, stratum in ECOSYSTEMS.items():
        for advisory in fetch(ecosystem):
            entry = admit(advisory, stratum, ecosystem)
            if entry is not None:
                candidates.append(entry)
    candidates.sort(key=lambda entry: (entry["stratum"], entry["ghsa_id"]))
    json.dump(candidates, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    counts = {
        stratum: sum(1 for entry in candidates if entry["stratum"] == stratum)
        for stratum in ECOSYSTEMS.values()
    }
    print(f"{len(candidates)} candidates {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
