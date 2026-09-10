#!/usr/bin/env python3
"""Capture source-only eligibility evidence and execute R2's fixed seeded walk."""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path("corpus/real-project/r2")
FRAME = ROOT / "frame.json"
INVENTORY = ROOT / "e5-inventory.json"
ELIGIBILITY = ROOT / "eligibility.json"
DRAW = ROOT / "draw.json"
EVIDENCE = ROOT / "evidence"
STAGING = ROOT / ".eligibility-capture.partial"
SEED = "dataflowbench-real-project-wave-r2"
ORDERING = 'draw_key = SHA-256(seed + "\\n" + ghsa_id), ascending lowercase hex, ties by ascending GHSA identifier'
STRATA = ("java", "javascript", "python")
LANGUAGE_NAMES = {"java": "Java", "javascript": "JavaScript", "python": "Python"}
OSI_LICENSES = {
    "0BSD", "AGPL-3.0", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "BSL-1.0",
    "EPL-2.0", "GPL-2.0", "GPL-3.0", "ISC", "LGPL-2.1", "LGPL-3.0", "MIT",
    "MPL-2.0", "Unlicense", "Zlib",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def artifact(path: pathlib.Path) -> dict:
    return {"path": path.as_posix(), "sha256": digest(path.read_bytes())}


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def api(endpoint: str) -> tuple[bytes, int, str]:
    result = subprocess.run(["gh", "api", "--include", endpoint], capture_output=True)
    headers, separator, body = result.stdout.partition(b"\r\n\r\n")
    if not separator:
        headers, separator, body = result.stdout.partition(b"\n\n")
    if not separator:
        raise RuntimeError(f"no HTTP headers for {endpoint}")
    fields = headers.decode("utf-8", errors="strict").splitlines()[0].split()
    if len(fields) < 2 or not fields[1].isdigit():
        raise RuntimeError(f"invalid HTTP status for {endpoint}")
    return body, int(fields[1]), "https://api.github.com" + endpoint


def capture(ghsa: str, kind: str, endpoint: str, allowed_statuses: tuple[int, ...] = (200,)) -> tuple[dict, dict]:
    body, status, request_url = api(endpoint)
    if status not in allowed_statuses:
        raise RuntimeError(f"GitHub returned {status} for {request_url}")
    directory = STAGING / ghsa
    directory.mkdir(parents=True, exist_ok=True)
    raw = directory / f"{kind}.json"
    meta = directory / f"{kind}.meta.json"
    if raw.exists() or meta.exists():
        raise RuntimeError(f"refusing to overwrite {raw}")
    raw.write_bytes(body)
    metadata = {
        "bytes": len(body), "http_status": status, "path": (EVIDENCE / ghsa / raw.name).as_posix(),
        "request_url": request_url, "retrieved_at": now(), "sha256": digest(body),
    }
    meta.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return json.loads(body), {"path": metadata["path"], "sha256": metadata["sha256"]}


def decision(ok: bool, observed: str, evidence: list[dict], **extra: object) -> dict:
    answer = {"outcome": "pass" if ok else "fail", "observed": observed, "evidence": evidence}
    answer.update(extra)
    return answer


def main() -> int:
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=True).stdout:
        raise RuntimeError("eligibility capture requires a clean worktree")
    introduction = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "-1", "--", __file__],
        capture_output=True, check=True, text=True,
    ).stdout.strip()
    if len(introduction) != 40 or subprocess.run(
        ["git", "merge-base", "--is-ancestor", introduction, "refs/remotes/origin/main"]
    ).returncode != 0:
        raise RuntimeError("eligibility capture tool must be merged into origin/main before use")
    if ELIGIBILITY.exists() or DRAW.exists() or EVIDENCE.exists() or STAGING.exists():
        raise RuntimeError("refusing to overwrite existing R2 eligibility evidence")
    frame = json.loads(FRAME.read_bytes())
    inventory = json.loads(INVENTORY.read_bytes())
    inventory_refs = [inventory["r1_frame"], inventory["r1_draw"], *inventory["source_lists"]]
    for reference in inventory_refs:
        if digest(pathlib.Path(reference["path"]).read_bytes()) != reference["sha256"]:
            raise RuntimeError(f"E5 source digest drift: {reference['path']}")
    excluded_e5 = {
        value.casefold()
        for field in ("r1_selected_repositories", "named_donor_or_corpus_repositories", "evaluated_analyzer_or_dependency_repositories")
        for value in inventory[field]
    }
    candidates = frame["candidates"]
    records, walk, selected_global = [], {}, []
    for stratum in STRATA:
        ordered = sorted(
            (row for row in candidates if row["stratum"] == stratum),
            key=lambda row: (digest(f"{SEED}\n{row['ghsa_id']}".encode()), row["ghsa_id"]),
        )
        walk[stratum], selected_count = [], 0
        for position, candidate in enumerate(ordered, 1):
            ghsa, slug = candidate["ghsa_id"], candidate["repository"]
            owner, name = slug.split("/", 1)
            repo, repo_ref = capture(ghsa, "repository", f"/repos/{owner}/{name}")
            languages, languages_ref = capture(ghsa, "languages", f"/repos/{owner}/{name}/languages")
            commits = []
            for index, reference in enumerate(candidate["fix_commit_references"]):
                commit, commit_ref = capture(ghsa, f"commit-{index:02d}", f"/repos/{owner}/{name}/commits/{reference}")
                commits.append((commit, commit_ref))
            commits.sort(key=lambda item: (item[0]["commit"]["committer"]["date"], item[0]["sha"]))
            earliest, earliest_ref = commits[0]
            latest, _ = commits[-1]
            comparisons = []
            for index, ((older, _), (newer, _)) in enumerate(zip(commits, commits[1:])):
                comparison, comparison_ref = capture(
                    ghsa,
                    f"compare-{index:02d}",
                    f"/repos/{owner}/{name}/compare/{older['sha']}...{newer['sha']}",
                )
                comparisons.append((comparison, comparison_ref))
            parents = earliest.get("parents", [])
            vulnerable = parents[0]["sha"] if parents else earliest["sha"]
            vulnerable_license_endpoint = f"/repos/{owner}/{name}/license?" + urllib.parse.urlencode({"ref": vulnerable})
            fixed_license_endpoint = f"/repos/{owner}/{name}/license?" + urllib.parse.urlencode({"ref": latest["sha"]})
            license_record, license_ref = capture(ghsa, "license-vulnerable", vulnerable_license_endpoint, (200, 404))
            fixed_license, fixed_license_ref = capture(ghsa, "license-fixed", fixed_license_endpoint, (200, 404))
            readme, readme_ref = capture(
                ghsa,
                "readme-vulnerable",
                f"/repos/{owner}/{name}/readme?" + urllib.parse.urlencode({"ref": vulnerable}),
                (200, 404),
            )
            primary = repo.get("language")
            repository_spdx = (repo.get("license") or {}).get("spdx_id")
            spdx = (license_record.get("license") or {}).get("spdx_id")
            license_bytes = base64.b64decode(license_record.get("content", ""), validate=False)
            e1 = primary == LANGUAGE_NAMES[stratum]
            e2 = spdx in OSI_LICENSES and bool(license_bytes)
            e3 = repo.get("archived") is False and repo.get("fork") is False
            e4 = isinstance(repo.get("size"), int) and repo["size"] <= 256000
            e5 = slug.casefold() not in excluded_e5
            e6 = len(parents) == 1 and all(item[0].get("status") == "ahead" for item in comparisons)
            language_bytes = languages.get(LANGUAGE_NAMES[stratum], 0)
            e7 = isinstance(language_bytes, int) and language_bytes >= 20000
            e8 = slug.casefold() not in {value.casefold() for value in selected_global}
            rationale = (
                f"{slug} {'is not' if e5 else 'is'} named by the digest-bound R1 selection, donor/corpus, "
                f"or evaluated-analyzer inventories; the repository-owned README at {vulnerable} and "
                f"GitHub description {repo.get('description')!r} are retained for independent review."
            )
            decisions = {
                "E1": decision(e1, f"primary language={primary!r}; required={LANGUAGE_NAMES[stratum]!r}", [repo_ref]),
                "E2": decision(e2, f"repository SPDX={repository_spdx!r}; vulnerable-revision SPDX={spdx!r}; decoded license bytes={len(license_bytes)}", [repo_ref, license_ref]),
                "E3": decision(e3, f"archived={repo.get('archived')}; fork={repo.get('fork')}", [repo_ref]),
                "E4": decision(e4, f"repository size={repo.get('size')} KiB; maximum=256000 KiB", [repo_ref]),
                "E5": decision(e5, rationale, [repo_ref, readme_ref, artifact(INVENTORY)], rationale=rationale),
                "E6": decision(e6, f"earliest fix={earliest['sha']}; vulnerable parent={vulnerable}; parent count={len(parents)}; fix lines={len(commits)}; ancestry statuses={[item[0].get('status') for item in comparisons]}", [*[ref for _, ref in commits], *[ref for _, ref in comparisons]]),
                "E7": decision(e7, f"{LANGUAGE_NAMES[stratum]} bytes={language_bytes}; minimum=20000", [languages_ref]),
                "E8": decision(e8, "repository absent from earlier R2 selections" if e8 else "repository already selected in R2", [artifact(FRAME)], selected_repositories_before=list(selected_global)),
            }
            passed = all(value["outcome"] == "pass" for value in decisions.values())
            index = len(records)
            records.append({"ghsa_id": ghsa, "repository": slug, "stratum": stratum, "draw_position": position, "decisions": decisions})
            walk[stratum].append({
                "draw_position": position, "draw_key": digest(f"{SEED}\n{ghsa}".encode()),
                "ghsa_id": ghsa, "repository": slug, "disposition": "selected" if passed else "excluded",
                "eligibility_index": index,
            })
            manifest = {
                "schema_version": 1, "wave": "R2", "ghsa_id": ghsa, "repository": slug,
                "responses": sorted(
                    (
                        {"purpose": path.name[:-10], **json.loads(path.read_text())}
                        for path in (STAGING / ghsa).glob("*.meta.json")
                    ),
                    key=lambda value: value["purpose"],
                ),
                "analyzer_evidence_consulted": False,
            }
            atomic_write(STAGING / ghsa / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n")
            if passed:
                selected_global.append(slug)
                selected_count += 1
                if selected_count == 2:
                    break
        if selected_count != 2:
            raise RuntimeError(f"{stratum} exhausted before two selections")
    eligibility = {"schema_version": 2, "wave": "R2", "frame": artifact(FRAME), "analyzer_evidence_consulted": False, "candidates": records}
    eligibility_bytes = json.dumps(eligibility, indent=2, sort_keys=True).encode() + b"\n"
    draw = {
        "schema_version": 2, "wave": "R2", "drawn_at": now(), "seed": SEED,
        "target_per_stratum": 2, "ordering_rule": ORDERING, "frame": artifact(FRAME),
        "eligibility": {"path": ELIGIBILITY.as_posix(), "sha256": digest(eligibility_bytes)},
        "analyzer_evidence_consulted": False, "walk": walk,
    }
    os.replace(STAGING, EVIDENCE)
    atomic_write(ELIGIBILITY, eligibility_bytes)
    atomic_write(DRAW, json.dumps(draw, indent=2, sort_keys=True).encode() + b"\n")
    print(f"captured {len(records)} walked candidates; selected {selected_global}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        if STAGING.exists():
            shutil.rmtree(STAGING)
        print(f"R2 eligibility capture failed: {error}", file=sys.stderr)
        raise SystemExit(1)
