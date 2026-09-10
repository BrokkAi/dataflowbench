#!/usr/bin/env python3
"""Pin R2's selected source pairs without retaining or consulting analyzer output."""

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
import urllib.request

ROOT = pathlib.Path("corpus/real-project/r2")
SNAPSHOT = ROOT / "snapshot/manifest.json"
FRAME = ROOT / "frame.json"
ELIGIBILITY = ROOT / "eligibility.json"
DRAW = ROOT / "draw.json"
EVIDENCE = ROOT / "evidence"
PINS = ROOT / "pins"
PIN_EVIDENCE = ROOT / "pin-evidence"
STAGING = ROOT / ".pin-capture.partial"
STRATA = ("java", "javascript", "python")

# These are proposed review subjects, not accepted ground truth. Each entry is
# transcribed from the selected advisory's immutable fix diff.
REMEDIATION = {
    "GHSA-jcrp-x7w3-ffmg": (
        "api/src/main/java/ai/djl/util/ZipUtils.java",
        "ZipEntry.getName() supplies an attacker-controlled archive entry name.",
        "dest.resolve(entryName) selects the filesystem path written during extraction.",
        "The fix routes every entry name through validateArchiveEntry before resolving or writing it.",
    ),
    "GHSA-6fhj-vr9j-g45r": (
        "src/main/java/org/cyclonedx/parsers/XmlParser.java",
        "The parser accepts XML through an InputSource.",
        "DocumentBuilder.parse(in) expands content under the factory's parser policy.",
        "The fix enables FEATURE_SECURE_PROCESSING in addition to the existing external-access restrictions.",
    ),
    "GHSA-g4cf-pp4x-hqgw": (
        "src/routes/gitImportSite.js",
        "req.body.site.git.url supplies a user-controlled repository URL.",
        "GitPlus configures and pulls that URL through the git command boundary.",
        "The fix removes the vulnerable gitImportSite route and its advertised API entry.",
    ),
    "GHSA-wphj-fx3q-84ch": (
        "lib/filesystem.js",
        "The drive argument is caller-controlled input used to construct a PowerShell command.",
        "util.powerShell(cmd) executes the interpolated command string.",
        "The fix applies strict sanitizeShellString handling before interpolating drive.",
    ),
    "GHSA-fhw8-8v9p-7jp7": (
        "bbot/modules/internal/unarchive.py",
        "An archive event supplies the path used to derive the extraction directory.",
        "The unarchive helper extracts files into that destination directory.",
        "The fix atomically creates a deterministic destination and aborts if it already exists.",
    ),
    "GHSA-6556-fwc2-fg2p": (
        "src/picklescan/scanner.py",
        "Pickle GLOBAL references provide module and callable names.",
        "The scanner's safety classification determines whether executable globals are reported dangerous.",
        "The fix expands unsafe globals and propagates wildcard danger through every parent module.",
    ),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: pathlib.Path) -> dict:
    return {"path": path.as_posix(), "sha256": digest(path.read_bytes())}


def write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def selected_rows(draw: dict) -> list[dict]:
    return [
        {"stratum": stratum, **row}
        for stratum in STRATA
        for row in draw["walk"][stratum]
        if row["disposition"] == "selected"
    ]


def response(manifest: dict, purpose: str) -> tuple[dict, dict]:
    record = next(item for item in manifest["responses"] if item["purpose"] == purpose)
    path = pathlib.Path(record["path"])
    data = path.read_bytes()
    if digest(data) != record["sha256"] or len(data) != record["bytes"]:
        raise RuntimeError(f"captured evidence drift: {path}")
    return record, json.loads(data)


def api_json(slug: str, purpose: str, suffix: str, directory: pathlib.Path) -> tuple[dict, dict]:
    endpoint = f"/repos/{slug}{suffix}"
    completed = subprocess.run(
        ["gh", "api", "--include", endpoint], capture_output=True, check=True
    )
    headers, separator, body = completed.stdout.partition(b"\r\n\r\n")
    if not separator:
        headers, separator, body = completed.stdout.partition(b"\n\n")
    fields = headers.decode("utf-8", errors="strict").splitlines()[0].split()
    if not separator or len(fields) < 2 or fields[1] != "200":
        raise RuntimeError(f"GitHub did not return HTTP 200 for {endpoint}")
    path = directory / f"{purpose}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    relative = pathlib.Path("corpus/real-project/r2/pin-evidence") / directory.name / path.name
    record = {
        "purpose": purpose,
        "path": relative.as_posix(),
        "sha256": digest(body),
        "bytes": len(body),
        "request_url": f"https://api.github.com{endpoint}",
        "http_status": 200,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return record, json.loads(body)


def archive_record(slug: str, revision: str, role: str, directory: pathlib.Path) -> tuple[dict, dict]:
    url = f"https://codeload.github.com/{slug}/tar.gz/{revision}"
    with urllib.request.urlopen(url, timeout=120) as stream:
        data = stream.read()
    if not data:
        raise RuntimeError(f"empty source archive: {url}")
    record_path = directory / f"archive-{role}.json"
    relative_record_path = pathlib.Path("corpus/real-project/r2/pin-evidence") / directory.name / record_path.name
    record = {
        "schema_version": 1,
        "wave": "R2",
        "repository": slug,
        "revision": revision,
        "role": role,
        "archive_url": url,
        "archive_sha256": digest(data),
        "archive_bytes": len(data),
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "analyzer_evidence_consulted": False,
    }
    write_json(record_path, record)
    pin_value = {
        "revision": revision,
        "role": (
            "the first parent of the selected remediation commit; the proposed last vulnerable revision"
            if role == "vulnerable"
            else "the selected advisory remediation commit; the proposed first fixed revision"
        ),
        "archive_url": url,
        "archive_sha256": record["archive_sha256"],
        "archive_bytes": record["archive_bytes"],
        "retrieved_on": record["retrieved_at"][:10],
        "capture_record": {
            "path": relative_record_path.as_posix(),
            "sha256": digest(record_path.read_bytes()),
        },
    }
    return record, pin_value


def main() -> int:
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=True).stdout:
        raise RuntimeError("R2 pin capture requires a clean worktree")
    introduction = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "-1", "--", __file__],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    if len(introduction) != 40 or subprocess.run(
        ["git", "merge-base", "--is-ancestor", introduction, "refs/remotes/origin/main"]
    ).returncode != 0:
        raise RuntimeError("R2 pin capture tool must be merged into origin/main before use")
    if PINS.exists() or PIN_EVIDENCE.exists() or STAGING.exists():
        raise RuntimeError("refusing to overwrite R2 pin artifacts")

    frame = json.loads(FRAME.read_bytes())
    eligibility = json.loads(ELIGIBILITY.read_bytes())
    draw = json.loads(DRAW.read_bytes())
    snapshot_ref, frame_ref, eligibility_ref, draw_ref = map(
        artifact, (SNAPSHOT, FRAME, ELIGIBILITY, DRAW)
    )
    frame_by_ghsa = {row["ghsa_id"]: row for row in frame["candidates"]}
    eligibility_by_ghsa = {row["ghsa_id"]: (index, row) for index, row in enumerate(eligibility["candidates"])}

    for row in selected_rows(draw):
        ghsa, slug = row["ghsa_id"], row["repository"]
        frame_row = frame_by_ghsa[ghsa]
        eligibility_index, eligibility_row = eligibility_by_ghsa[ghsa]
        if eligibility_index != row["eligibility_index"] or eligibility_row["repository"] != slug:
            raise RuntimeError(f"selected identity drift: {ghsa}")
        source_manifest_path = EVIDENCE / ghsa / "manifest.json"
        source_manifest = json.loads(source_manifest_path.read_bytes())
        commits = []
        for purpose in sorted(
            item["purpose"] for item in source_manifest["responses"] if item["purpose"].startswith("commit-")
        ):
            record, body = response(source_manifest, purpose)
            commits.append((body["commit"]["committer"]["date"], record, body))
        commits.sort(key=lambda item: (item[0], item[2]["sha"]))
        _, fix_record, fix_body = commits[-1]
        if len(fix_body["parents"]) != 1:
            raise RuntimeError(f"selected fix is not single-parent: {ghsa}")
        fixed, vulnerable = fix_body["sha"], fix_body["parents"][0]["sha"]

        evidence_dir = STAGING / "pin-evidence" / ghsa
        _, vulnerable_pin = archive_record(slug, vulnerable, "vulnerable", evidence_dir)
        _, fixed_pin = archive_record(slug, fixed, "fixed", evidence_dir)
        compare_record, compare_body = api_json(
            slug, "compare-vulnerable-fixed", f"/compare/{vulnerable}...{fixed}", evidence_dir
        )
        if compare_body.get("status") != "ahead":
            raise RuntimeError(f"fixed revision is not ahead of vulnerable revision: {ghsa}")
        vulnerable_license_record, vulnerable_license = api_json(
            slug,
            "license-vulnerable",
            "/license?" + urllib.parse.urlencode({"ref": vulnerable}),
            evidence_dir,
        )
        fixed_license_record, fixed_license = api_json(
            slug,
            "license-fixed",
            "/license?" + urllib.parse.urlencode({"ref": fixed}),
            evidence_dir,
        )
        pin_manifest_path = evidence_dir / "manifest.json"
        archive_artifacts = []
        for role in ("vulnerable", "fixed"):
            archive_path = evidence_dir / f"archive-{role}.json"
            archive_artifacts.append(
                {
                    "path": f"corpus/real-project/r2/pin-evidence/{ghsa}/archive-{role}.json",
                    "sha256": digest(archive_path.read_bytes()),
                }
            )
        write_json(
            pin_manifest_path,
            {
                "schema_version": 1,
                "wave": "R2",
                "ghsa_id": ghsa,
                "repository": slug,
                "responses": [compare_record, vulnerable_license_record, fixed_license_record],
                "artifacts": archive_artifacts,
                "analyzer_evidence_consulted": False,
            },
        )

        vulnerable_license_bytes = base64.b64decode(vulnerable_license["content"])
        fixed_license_bytes = base64.b64decode(fixed_license["content"])
        owner, name = slug.split("/", 1)
        advisory_page = pathlib.Path(frame_row["advisory_evidence"]["path"])
        advisory = json.loads(advisory_page.read_bytes())[frame_row["advisory_evidence"]["array_index"]]
        fix_commits = [{"revision": fixed, "evidence": {"path": fix_record["path"], "sha256": fix_record["sha256"]}}]
        related_commits = [
            {
                "revision": body["sha"],
                "role": "introduction-reference",
                "evidence": {"path": record["path"], "sha256": record["sha256"]},
            }
            for _, record, body in commits[:-1]
        ]
        file_path, source_hint, sink_hint, candidate_basis = REMEDIATION[ghsa]
        staged_manifest_ref = artifact(pin_manifest_path)
        staged_manifest_ref["path"] = f"corpus/real-project/r2/pin-evidence/{ghsa}/manifest.json"
        pin = {
            "schema_version": 2,
            "wave": "R2",
            "pin_id": f"dfb-rp-r2-{name.lower().replace('_', '-').replace('.', '-')}",
            "lifecycle": "pending-review",
            "stratum": row["stratum"],
            "language": row["stratum"],
            "ecosystem": frame_row["ecosystem"],
            "repository": {"owner": owner, "name": name, "url": f"https://github.com/{slug}"},
            "advisory": {
                "ghsa_id": ghsa,
                "url": f"https://github.com/advisories/{ghsa}",
                "cve_id": frame_row["cve_id"],
                "cwes": frame_row["cwes"],
                "summary": advisory["summary"],
                "severity": frame_row["severity"],
                "published_at": frame_row["published_at"],
                "affected_packages": frame_row["packages"],
            },
            "bindings": {
                "snapshot_manifest": snapshot_ref,
                "frame": frame_ref,
                "eligibility": eligibility_ref,
                "draw": draw_ref,
                "evidence_manifest": artifact(source_manifest_path),
                "draw_position": row["draw_position"],
                "draw_key": row["draw_key"],
                "selected_repository": slug,
                "eligibility_candidate_index": eligibility_index,
                "pin_evidence_manifest": staged_manifest_ref,
            },
            "fix_commits": fix_commits,
            "related_commits": related_commits,
            "revisions": {"vulnerable": vulnerable_pin, "fixed": fixed_pin},
            "license": {
                "spdx_id": vulnerable_license["license"]["spdx_id"],
                "file_path": vulnerable_license["path"],
                "vulnerable_content_sha256": digest(vulnerable_license_bytes),
                "fixed_content_sha256": digest(fixed_license_bytes),
                "identical_at_both_revisions": vulnerable_license_bytes == fixed_license_bytes,
                "vulnerable_bytes": len(vulnerable_license_bytes),
                "fixed_bytes": len(fixed_license_bytes),
                "evidence": {
                    "vulnerable": {"path": vulnerable_license_record["path"], "sha256": vulnerable_license_record["sha256"]},
                    "fixed": {"path": fixed_license_record["path"], "sha256": fixed_license_record["sha256"]},
                },
            },
            "proposed_remediation": {
                "status": "proposed",
                "file_path": file_path,
                "source_hint": source_hint,
                "sink_hint": sink_hint,
                "candidate_basis": candidate_basis,
            },
            "ground_truth": {
                "status": "proposed",
                "adjudication": "pending",
                "review_independence": "pending",
                "reviewers": [],
                "basis": "Analyzer-free proposal from the immutable advisory fix diff; acceptance requires both independent R2 reports.",
            },
            "analyzer_evidence_consulted": False,
        }
        write_json(STAGING / "pins" / f"{name.lower().replace('_', '-').replace('.', '-')}.json", pin)

    os.replace(STAGING / "pins", PINS)
    os.replace(STAGING / "pin-evidence", PIN_EVIDENCE)
    shutil.rmtree(STAGING)
    print("captured six analyzer-free R2 revision pairs and source-archive digests")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        if STAGING.exists():
            shutil.rmtree(STAGING)
        print(f"R2 pin capture failed: {error}", file=sys.stderr)
        raise SystemExit(1)
