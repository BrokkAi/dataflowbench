#!/usr/bin/env python3
"""Build or audit the immutable analyzer-free R2 independent-review packet.

The builder never consults analyzer output, runs an analyzer, or makes network
requests.  It reads committed repository bytes only, binds their SHA-256
identities, and writes a packet plus a pending two-reviewer skeleton.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(".")
PROTOCOL = pathlib.Path("corpus/real-project/r2/protocol.json")
PREREGISTRATION = pathlib.Path("docs/real-project-r2-preregistration.md")
SNAPSHOT_MANIFEST = pathlib.Path("corpus/real-project/r2/snapshot/manifest.json")
FRAME = pathlib.Path("corpus/real-project/r2/frame.json")
ELIGIBILITY = pathlib.Path("corpus/real-project/r2/eligibility.json")
DRAW = pathlib.Path("corpus/real-project/r2/draw.json")
PINS_DIR = pathlib.Path("corpus/real-project/r2/pins")
EVIDENCE_DIR = pathlib.Path("corpus/real-project/r2/evidence")
PIN_EVIDENCE_DIR = pathlib.Path("corpus/real-project/r2/pin-evidence")
R1_FRAME = pathlib.Path("corpus/real-project/frame.json")
R1_DRAW = pathlib.Path("corpus/real-project/draw.json")
R1_REVIEW = pathlib.Path("corpus/real-project/review.json")
R1_PREREGISTRATION = pathlib.Path("docs/real-project-preregistration.md")
SUBJECTS = (
    "snapshot_completeness",
    "frame_derivation",
    "eligibility_e1_e8",
    "draw_and_replacement",
    "pins_and_archives",
    "licenses",
    "vulnerable_fixed_semantics",
    "claim_bounds",
    "descriptive_latency_scope",
)
SCHEMA_DOMAINS = {
    "real-project-r2-protocol.schema.json": "protocol",
    "real-project-r2-snapshot.schema.json": "snapshot",
    "real-project-r2-frame.schema.json": "frame",
    "real-project-r2-eligibility.schema.json": "eligibility",
    "real-project-r2-draw.schema.json": "draw",
    "real-project-r2-pin.schema.json": "pin",
    "real-project-r2-pin-evidence.schema.json": "pin-evidence",
    "real-project-r2-review.schema.json": "review",
}
FORBIDDEN_PATH = re.compile(
    r"(^|/)(reports|results|freeze|freezes|analyzer-output|analyzer-outputs|coverage)(/|$)"
    r"|\.(log|sarif)$",
    re.IGNORECASE,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*arguments: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, check=check
    )
    return completed.stdout


def artifact(path: pathlib.Path, expected_sha256: str | None = None) -> dict:
    if path.is_absolute() or not path.is_file():
        raise RuntimeError(f"packet input is not a repository file: {path}")
    if path.is_symlink():
        raise RuntimeError(f"packet input must not be a symlink: {path}")
    relative = path.as_posix()
    if relative.startswith("/") or ".." in path.parts:
        raise RuntimeError(f"unsafe packet input path: {relative}")
    if FORBIDDEN_PATH.search(relative):
        raise RuntimeError(f"possible mutable or analyzer artifact refused: {relative}")
    data = path.read_bytes()
    observed = digest(data)
    if expected_sha256 is not None and observed != expected_sha256:
        raise RuntimeError(f"digest mismatch for {relative}: {observed} != {expected_sha256}")
    if path.suffix == ".json":
        try:
            json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"invalid JSON packet input {relative}: {error}") from error
    tracked = git("ls-files", "--", relative).strip()
    if not tracked:
        raise RuntimeError(f"packet input is not tracked by Git: {relative}")
    return {"path": relative, "sha256": observed}


def distinct(artifacts: list[dict]) -> list[dict]:
    by_path: dict[str, dict] = {}
    for item in artifacts:
        previous = by_path.get(item["path"])
        if previous is not None and previous != item:
            raise RuntimeError(f"conflicting digest bindings for {item['path']}")
        by_path[item["path"]] = item
    return [by_path[path] for path in sorted(by_path)]


def require_clean_merged_source() -> tuple[str, str, str]:
    status = git("status", "--porcelain", "--untracked-files=all")
    if status:
        lines = status.decode("utf-8", errors="replace").strip().splitlines()
        detail = "; ".join(lines[:10])
        raise RuntimeError(f"packet construction requires a clean worktree: {detail}")
    source_revision = git("rev-parse", "HEAD").decode().strip()
    main_revision = git("rev-parse", "refs/remotes/origin/main").decode().strip()
    if source_revision != main_revision:
        raise RuntimeError(
            f"packet source HEAD {source_revision} is not merged origin/main {main_revision}"
        )
    introduced = git(
        "log",
        "--diff-filter=A",
        "--format=%H",
        "-1",
        "--",
        PROTOCOL.as_posix(),
    ).decode().strip()
    if len(introduced) != 40:
        raise RuntimeError("cannot resolve the commit introducing the R2 protocol")
    git("merge-base", "--is-ancestor", introduced, source_revision)
    introduced_bytes = subprocess.run(
        ["git", "show", f"{introduced}:{PROTOCOL.as_posix()}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    if introduced_bytes != PROTOCOL.read_bytes():
        raise RuntimeError("the R2 protocol differs from its merged preregistration bytes")
    return source_revision, introduced, digest(PROTOCOL.read_bytes())


def snapshot_pages() -> tuple[dict, list[dict]]:
    manifest_bytes = SNAPSHOT_MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("wave") != "R2":
        raise RuntimeError("R2 packet requires the R2 snapshot manifest")
    pages: list[dict] = []
    for query in manifest.get("queries", []):
        for page in query.get("pages", []):
            path = pathlib.Path(page["response_path"])
            pages.append(
                {
                    "path": path.as_posix(),
                    "sha256": digest(path.read_bytes()),
                    "ecosystem": query["ecosystem"],
                    "page": page["page"],
                }
            )
            artifact(path, page.get("sha256"))
    if not pages:
        raise RuntimeError("R2 snapshot manifest has no response pages")
    return manifest, pages


def pins() -> list[dict]:
    if not PINS_DIR.is_dir():
        raise RuntimeError(f"missing R2 pin directory: {PINS_DIR}")
    paths = sorted(path for path in PINS_DIR.glob("*.json") if path.is_file())
    if len(paths) != 6:
        raise RuntimeError(f"R2 review requires exactly six selected pins; found {len(paths)}")
    records = []
    repositories = set()
    for path in paths:
        value = json.loads(path.read_bytes())
        identity = value.get("advisory", {}).get("ghsa_id")
        repository = value.get("bindings", {}).get("selected_repository")
        stratum = value.get("stratum")
        if not identity or not repository or stratum not in {"java", "javascript", "python"}:
            raise RuntimeError(f"cannot identify R2 pin {path}")
        if repository.casefold() in repositories:
            raise RuntimeError(f"R2 pins contain duplicate repository {repository}")
        repositories.add(repository.casefold())
        records.append(
            {
                "artifact": artifact(path),
                "ghsa_id": identity,
                "repository": repository,
                "stratum": stratum,
            }
        )
    return records


def pin_evidence(pin_records: list[dict]) -> list[dict]:
    if not EVIDENCE_DIR.is_dir():
        raise RuntimeError(f"missing R2 evidence directory: {EVIDENCE_DIR}")
    paths = sorted(
        path
        for directory in (EVIDENCE_DIR, PIN_EVIDENCE_DIR)
        for path in directory.rglob("*")
        if path.is_file()
    )
    if not paths:
        raise RuntimeError("R2 evidence directory is empty")
    records = [artifact(path) for path in paths]
    for record in pin_records:
        path = pathlib.Path(record["artifact"]["path"])
        value = json.loads(path.read_bytes())
        manifest = value.get("bindings", {}).get("evidence_manifest", {})
        manifest_path = manifest.get("path")
        if not manifest_path:
            raise RuntimeError(f"pin does not bind an evidence manifest: {path}")
        artifact(pathlib.Path(manifest_path), manifest.get("sha256"))
        if not any(item["path"] == manifest_path for item in records):
            raise RuntimeError(f"unbound evidence manifest excluded from packet: {manifest_path}")
        pin_manifest = value.get("bindings", {}).get("pin_evidence_manifest", {})
        pin_manifest_path = pin_manifest.get("path")
        if not pin_manifest_path:
            raise RuntimeError(f"pin does not bind a pin-evidence manifest: {path}")
        artifact(pathlib.Path(pin_manifest_path), pin_manifest.get("sha256"))
        if not any(item["path"] == pin_manifest_path for item in records):
            raise RuntimeError(f"unbound pin-evidence manifest excluded from packet: {pin_manifest_path}")
    return records


def schemas() -> list[dict]:
    records = []
    for path in sorted(pathlib.Path("schemas").glob("real-project-r2-*.schema.json")):
        domain = SCHEMA_DOMAINS.get(path.name)
        if domain is None:
            raise RuntimeError(f"unclassified R2 schema refused: {path}")
        records.append({"artifact": artifact(path), "path": path.as_posix(), "sha256": digest(path.read_bytes()), "domain": domain})
    if len({record["domain"] for record in records}) != len(SCHEMA_DOMAINS):
        raise RuntimeError("R2 packet is missing at least one required schema domain")
    return records


def tools() -> list[dict]:
    purposes = {
        "capture-real-project-r2.py": "capture",
        "derive-real-project-r2-frame.py": "frame-derivation",
    }
    records = []
    for path in sorted(pathlib.Path("scripts").glob("*real-project-r2*.py")):
        if "pin" in path.name:
            purpose = "pin-artifact-capture"
        elif "review-packet" in path.name:
            purpose = "review-packet-construction"
        elif path.name in purposes:
            purpose = purposes[path.name]
        else:
            raise RuntimeError(f"unclassified R2 tool refused: {path}")
        records.append({"artifact": artifact(path), "purpose": purpose})
    names = {record["artifact"]["path"] for record in records}
    if "scripts/build-real-project-r2-review-packet.py" not in names:
        raise RuntimeError("packet builder must bind its own bytes")
    return records


def generic_artifacts(paths: list[pathlib.Path]) -> list[dict]:
    return [artifact(path) for path in paths if path.is_file()]


def collect_bindings(source_revision: str) -> tuple[dict, list[dict], dict]:
    _, pages = snapshot_pages()
    pin_records = pins()
    evidence_records = pin_evidence(pin_records)
    bindings = {
        "preregistration": artifact(PREREGISTRATION),
        "protocol": artifact(PROTOCOL),
        "snapshot_manifest": artifact(SNAPSHOT_MANIFEST),
        "snapshot_pages": pages,
        "frame": artifact(FRAME),
        "eligibility": artifact(ELIGIBILITY),
        "draw": artifact(DRAW),
        "pins": pin_records,
        "pin_evidence": evidence_records,
        "schemas": schemas(),
        "tools": tools(),
        "independence_inputs": generic_artifacts(
            [R1_FRAME, R1_DRAW, R1_REVIEW, R1_PREREGISTRATION]
            + sorted(pathlib.Path("corpus/real-project/pins").glob("*.json"))
        ),
        "e5_reference_lists": generic_artifacts(
            [
                pathlib.Path("docs/benchmark-sources.md"),
                pathlib.Path("docs/challenge-tier.md"),
            ]
            + sorted(pathlib.Path("adapters").glob("*/README.md"))
            + sorted(pathlib.Path("adapters").rglob("provenance.json"))
        ),
    }
    for name in ("independence_inputs", "e5_reference_lists"):
        if len(bindings[name]) < 2:
            raise RuntimeError(f"R2 packet has insufficient {name}")
    all_artifacts = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                all_artifacts.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(bindings)
    unique_artifacts = distinct(all_artifacts)
    if not unique_artifacts:
        raise RuntimeError("R2 packet did not derive an artifact digest set")
    identity = {
        "source_revision": source_revision,
        "artifacts": unique_artifacts,
    }
    packet_id = "dfb-rp-r2-packet-" + digest(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )[:24]
    return bindings, unique_artifacts, {"packet_id": packet_id}


def planned_reviewer(role: str, provider: str, model: str, effort: str, packet: dict) -> dict:
    return {
        "role": role,
        "provider": provider,
        "model": model,
        "reasoning_effort": effort,
        "run_id": None,
        "started_at": None,
        "completed_at": None,
        "status": "planned",
        "checkout": None,
        "evidence_path": f"<created separately for {role}>",
        "packet": packet,
        "packet_digest_set_identical": False,
        "report": None,
        "subject_verdicts": {subject: "not-reviewed" for subject in SUBJECTS},
        "analyzer_evidence_consulted": False,
        "notes": "Planned before either reviewer started; this record makes no review claim.",
    }


def verify_packet(path: pathlib.Path) -> dict:
    packet_bytes = path.read_bytes()
    packet = json.loads(packet_bytes)
    if packet.get("wave") != "R2" or packet.get("analyzer_evidence_consulted") is not False:
        raise RuntimeError("refusing a packet that is not analyzer-free R2 evidence")
    expected_id = packet.get("packet_id")
    if not isinstance(expected_id, str):
        raise RuntimeError("packet_id is missing")
    bindings = packet.get("artifact_bindings")
    artifacts = packet.get("artifacts")
    if not isinstance(bindings, dict) or not isinstance(artifacts, list):
        raise RuntimeError("packet bindings or artifact digest set is missing")
    flattened: list[dict] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                flattened.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(bindings)
    if distinct(flattened) != sorted(artifacts, key=lambda item: item["path"]):
        raise RuntimeError("packet artifact digest set does not match its bindings")
    for item in artifacts:
        artifact(pathlib.Path(item["path"]), item["sha256"])
    if packet["source_revision"] != git("rev-parse", "HEAD").decode().strip():
        raise RuntimeError("packet source revision differs from the current checkout")
    return packet


def check(output_directory: pathlib.Path) -> None:
    require_clean_merged_source()
    packet_path = output_directory / "packet.json"
    review_path = output_directory / "review.json"
    packet = verify_packet(packet_path)
    packet_artifact = {
        "path": packet_path.as_posix(),
        "sha256": digest(packet_path.read_bytes()),
    }
    review = json.loads(review_path.read_bytes())
    if review.get("status") != "pending":
        raise RuntimeError("builder check is only for the pending review skeleton")
    if review.get("packet") != packet_artifact:
        raise RuntimeError("review skeleton does not bind the packet bytes")
    if review.get("artifact_bindings") != packet.get("artifact_bindings"):
        raise RuntimeError("review skeleton bindings differ from packet bindings")
    if review.get("readiness", {}).get("execution_ready") is not False:
        raise RuntimeError("pending review skeleton must not be execution-ready")
    for role in ("reviewer_a", "reviewer_b"):
        reviewer = review.get("reviewers", {}).get(role, {})
        if reviewer.get("status") != "planned" or reviewer.get("packet") != packet_artifact:
            raise RuntimeError(f"{role} is not a valid planned packet consumer")
    print(f"verified {packet['packet_id']} and its pending review skeleton")


def write_atomic(output_directory: pathlib.Path, files: dict[pathlib.Path, bytes]) -> None:
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = pathlib.Path(tempfile.mkdtemp(prefix=f".{output_directory.name}.tmp-", dir=output_directory.parent))
    try:
        for path, data in files.items():
            target = temporary / path
            target.write_bytes(data)
            with target.open("rb") as handle:
                os.fsync(handle.fileno())
        temporary.chmod(0o755)
        temporary.rename(output_directory)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def build(output_directory: pathlib.Path) -> None:
    if output_directory.exists():
        raise RuntimeError(f"refusing to overwrite packet directory {output_directory}")
    if output_directory == ROOT:
        raise RuntimeError("packet output must be a dedicated subdirectory")
    source_revision, _, _ = require_clean_merged_source()
    bindings, artifacts, identity = collect_bindings(source_revision)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    packet = {
        "schema_version": 1,
        "packet_id": identity["packet_id"],
        "wave": "R2",
        "created_at": timestamp,
        "source_revision": source_revision,
        "analyzer_evidence_consulted": False,
        "artifact_bindings": bindings,
        "artifacts": artifacts,
        "review_rule": {
            "separate_clean_checkouts": True,
            "separate_evidence_paths": True,
            "same_packet_digest_set": True,
            "no_analyzer_outputs": True,
            "no_cross_reviewer_discussion_before_submission": True,
        },
    }
    packet_bytes = (json.dumps(packet, indent=2, sort_keys=True) + "\n").encode("utf-8")
    packet_path = output_directory / "packet.json"
    packet_artifact = {
        "path": packet_path.as_posix(),
        "sha256": hashlib.sha256(packet_bytes).hexdigest(),
    }
    per_pin = [
        {
            "ghsa_id": record["ghsa_id"],
            "reviewer_a": "not-reviewed",
            "reviewer_b": "not-reviewed",
            "remediation_location": "not-reviewed",
            "vulnerable_fixed_semantics": "not-reviewed",
            "archive_digests": "not-reviewed",
            "license": "not-reviewed",
        }
        for record in bindings["pins"]
    ]
    review = {
        "schema_version": 1,
        "wave": "R2",
        "review_id": "dfb-rp-r2-review-v1",
        "status": "pending",
        "created_at": timestamp,
        "updated_at": timestamp,
        "source_revision": source_revision,
        "packet": packet_artifact,
        "artifact_bindings": bindings,
        "analyzer_evidence_consulted": False,
        "reviewers": {
            "reviewer_a": planned_reviewer(
                "reviewer-a", "openai", "gpt-5.6-sol", "medium", packet_artifact
            ),
            "reviewer_b": planned_reviewer(
                "reviewer-b", "z.ai", "glm-5.3", "max", packet_artifact
            ),
        },
        "per_pin_reviews": per_pin,
        "disagreement": {
            "packet_digest_sets_identical": False,
            "subject_disagreements": [],
            "pin_disagreements": [],
            "adjudication": {
                "status": "not-required",
                "allowed_inputs": [
                    "immutable-packet",
                    "reviewer-a-report",
                    "reviewer-b-report",
                ],
                "decision_record": None,
            },
        },
        "readiness": {
            "outcome": "pending",
            "execution_ready": False,
            "freeze_ready": False,
            "blocking_reasons": [
                "reviewer-a has not submitted",
                "reviewer-b has not submitted",
            ],
        },
    }
    write_atomic(
        output_directory,
        {
            pathlib.Path("packet.json"): packet_bytes,
            pathlib.Path("review.json"): (
                json.dumps(review, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8"),
        },
    )
    print(f"built {identity['packet_id']} with {len(artifacts)} digest-bound files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="DIRECTORY", type=pathlib.Path)
    group.add_argument("--build", metavar="DIRECTORY", type=pathlib.Path)
    arguments = parser.parse_args()
    directory: pathlib.Path = arguments.check or arguments.build
    if arguments.check:
        check(directory)
    else:
        build(directory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, RuntimeError, json.JSONDecodeError) as error:
        print(f"R2 review packet failed: {error}", file=sys.stderr)
        raise SystemExit(1)
