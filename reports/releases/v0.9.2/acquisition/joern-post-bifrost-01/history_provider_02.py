"""Verify sealed 109-row history bindings without replay or execution authority.

The immutable original-89 recovery provider remains a separate API. This reader
returns evidence references and counters, never normalized runtime objects,
permits, or an inferred terminal for the interrupted Smoke02 attempt.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

JsonObject = dict[str, Any]
DESCRIPTOR_PATH = (
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
    "history-provider-descriptor-01.json"
)
DESCRIPTOR_SHA = "dc771f3bf7de580d826bff62150fb64e28fdf7a3b7aeb180dab876ea19c35eca"
LIVE_LEDGER = "reports/releases/v0.9.2/ledger-v1.jsonl"
MAX_BYTES = 256 * 1024 * 1024
ENGINE_SHA = "fc9a2a4cff4e73b91a1b4e15f403bf572052bc796a362440e347336be46385e6"
CODEQL_TERMINAL_SHA = "24795ec582742b39ba8e5851ce39fa4249aa66bd79d1a0cdcd9823d5f6fc9d0d"
DESCRIPTOR_FIELDS = {
    "schema", "status", "execution_authorized", "automatic_retry", "core",
    "manifest", "stage02", "batch", "resume_history", "ledger_prefix",
    "prefixes", "original89_provider", "source_contexts", "replacements",
    "consumed_events", "stop_evidence", "publication_hold",
}


class HistoryError(ValueError):
    """A bound historical input does not satisfy this reader's contract."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise HistoryError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def relative(value: str) -> str:
    need(
        isinstance(value, str) and bool(value) and "\\" not in value and "\x00" not in value,
        "invalid path",
    )
    path = PurePosixPath(value)
    need(
        not path.is_absolute()
        and path.as_posix() == value
        and not any(part in {".", ".."} for part in path.parts),
        "noncanonical path",
    )
    return value


def _stat_identity(metadata: Any) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns,
    )


def stable(root: Path, value: str) -> bytes:
    """Read a bounded regular file with symlink and stat-change rejection."""
    path = Path(root) / relative(value)
    for component in [path, *path.parents]:
        need(not component.is_symlink(), "symlink path")
    before = path.stat()
    need(
        stat.S_ISREG(before.st_mode) and before.st_size <= MAX_BYTES,
        "file kind or bounded size differs",
    )
    raw = path.read_bytes()
    after = path.stat()
    need(_stat_identity(before) == _stat_identity(after), "file changed during read")
    for component in [path, *path.parents]:
        need(not component.is_symlink(), "path changed to symlink")
    return raw


def bound(root: Path, ref: JsonObject) -> bytes:
    need(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact ref required")
    need(
        isinstance(ref["sha256"], str)
        and re.fullmatch("[0-9a-f]{64}", ref["sha256"]) is not None,
        "invalid digest",
    )
    raw = stable(root, ref["path"])
    need(sha(raw) == ref["sha256"], "reference digest differs: " + ref["path"])
    return raw


def document(root: Path, ref: JsonObject) -> JsonObject:
    return json.loads(bound(root, ref))


def ledger_rows(raw: bytes) -> tuple[list[bytes], list[JsonObject]]:
    need(raw.endswith(b"\n"), "ledger missing final newline")
    lines = raw.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    need(all(isinstance(row, dict) for row in rows), "ledger row shape differs")
    return lines, rows


def consumed_attempts(
    rows: list[JsonObject], event: JsonObject, replacement_groups: list[str]
) -> JsonObject:
    """Count ledger events plus the separately retained interrupted event.

    Global attempt numbers cannot be reused under a different series. The next
    Joern number is descriptive only and never grants a retry or admission.
    """
    counters: dict[str, int] = {}
    consumed: list[JsonObject] = []
    global_attempts: set[tuple[str, int]] = set()
    for row in [*rows, event]:
        attempt_id = row["attempt_id"]
        group_id = row["group_id"]
        pattern = re.escape(group_id) + r"-attempt-(\d+)-series-(\d+)"
        match = re.fullmatch(pattern, attempt_id)
        need(match is not None, "attempt counter syntax differs")
        number = int(match.group(1))
        need(number > 0, "invalid attempt number")
        key = (group_id, number)
        need(key not in global_attempts, "reused global group/attempt number across series")
        global_attempts.add(key)
        counters[group_id] = max(counters.get(group_id, 0), number)
        consumed.append({
            "group_id": group_id,
            "attempt_id": attempt_id,
            "attempt_number": number,
            "classification": row.get("status", row.get("classification")),
        })
    need(
        counters["bifrost-smoke"] == 3
        and counters["bifrost-c-kernel"] == 3
        and all(
            counters[group] == 2
            for group in replacement_groups
            if group not in {"bifrost-smoke", "bifrost-c-kernel"}
        ),
        "global Bifrost consumed counters differ",
    )
    need(counters.get("joern-swift-common108") == 4, "Joern consumed counter must be four")
    return {
        "counters": counters,
        "consumed": consumed,
        "joern_next_attempt": {
            "group_id": "joern-swift-common108",
            "consumed_global_attempt": 4,
            "next_global_attempt": 5,
            "execution_authorized": False,
            "permit": False,
        },
    }


def validate_documents(
    descriptor: JsonObject,
    core: JsonObject,
    stage: JsonObject,
    batch: JsonObject,
    history: JsonObject,
    lines: list[bytes],
    rows: list[JsonObject],
) -> JsonObject:
    """Validate bound document relationships; this is not runtime replay."""
    need(set(descriptor) == DESCRIPTOR_FIELDS, "descriptor fields differ")
    need(
        descriptor["schema"] == "v092-joern05-sealed109-history-descriptor/v1"
        and descriptor["execution_authorized"] is False
        and descriptor["automatic_retry"] is False,
        "descriptor authority differs",
    )
    need(
        len(rows) == 109
        and collections.Counter(row["status"] for row in rows)
        == {"completed": 103, "failed": 3, "recorder-error": 3},
        "sealed109 counts differ",
    )
    need(
        descriptor["ledger_prefix"]["rows"] == 109
        and sha(b"".join(lines)) == descriptor["ledger_prefix"]["sha256"],
        "sealed109 identity differs",
    )
    need(
        set(descriptor["prefixes"]) == {"89", "107", "108"}
        and all(
            sha(b"".join(lines[:int(number)])) == digest
            for number, digest in descriptor["prefixes"].items()
        ),
        "89/107/108 prefix closure differs",
    )
    need(
        descriptor["source_contexts"] == core["source_contexts"]
        and len(core["source_contexts"]) == 9,
        "exact nine source contexts differ",
    )
    need(
        stage["core_identity"] == descriptor["core"]
        and stage["ledger_rows"] == 109
        and stage["ledger_sha256"] == descriptor["ledger_prefix"]["sha256"]
        and stage["stage_index"] == 2
        and stage["status"] == "successor-stage-verified",
        "stage02 identity differs",
    )
    need(
        stage["source_commit"] == core["source_commit"]
        and stage["plan_commit"] == core["plan_commit"]
        and stage["contract_sha256"] == core["contract"]["sha256"],
        "current source/plan/contract differs",
    )
    need(
        sha(canonical(stage["stage_identity"])) == stage["stage_identity_sha256"],
        "stage identity digest differs",
    )
    need(
        batch["status"] == "batch-covered"
        and batch["full_release_gate_satisfied"] is False
        and len(batch["retained_outcomes"]) == 18
        and len(batch["outcomes"]) == 2,
        "batch scope differs",
    )
    selected = batch["selected_matrix"]
    need(
        tuple(selected[key] for key in ("selected_groups", "partitions", "rows", "known_stale"))
        == (83, 87, 4144, 0)
        and selected["missing_groups"] == ["joern-swift-common108"]
        and not selected["full_release_gate_satisfied"],
        "partial selection differs",
    )
    need(
        len(descriptor["replacements"]) == 20
        and [item["group_id"] for item in descriptor["replacements"]]
        == core["replacement_groups"],
        "full20 selection differs",
    )
    need(
        descriptor["consumed_events"] == history["consumed_events"]
        and len(descriptor["consumed_events"]) == 1,
        "consumed event registry differs",
    )
    event = descriptor["consumed_events"][0]
    need(
        event["attempt_id"] == "bifrost-smoke-attempt-02-series-02"
        and event["group_id"] == "bifrost-smoke"
        and event["classification"] == "started-unclosed-unknown-interrupted",
        "consumed Smoke02 identity differs",
    )
    need(
        not any(row["attempt_id"] == event["attempt_id"] for row in rows),
        "unclosed Smoke02 fabricated into ledger",
    )
    ids = [row["attempt_id"] for row in rows]
    need(len(ids) == len(set(ids)), "duplicate ledger attempt ID")
    facts = consumed_attempts(rows, event, core["replacement_groups"])
    facts["selected_partial"] = {
        key: selected[key]
        for key in (
            "status", "selected_groups", "partitions", "rows", "known_stale",
            "missing_groups", "full_release_gate_satisfied",
        )
    }
    return facts


def _verify_replacements(
    root: Path,
    descriptor: JsonObject,
    batch: JsonObject,
    lines: list[bytes],
    rows: list[JsonObject],
) -> list[JsonObject]:
    outcomes = batch["retained_outcomes"] + batch["outcomes"]
    retained = []
    for index, item in enumerate(descriptor["replacements"]):
        row = rows[89 + index]
        outcome = outcomes[index]
        need(
            item["group_id"] == row["group_id"] == outcome["group_id"]
            and item["attempt_id"] == row["attempt_id"] == outcome["attempt_id"],
            "replacement terminal ledger ordering differs",
        )
        terminal = document(root, item["terminal"])
        completion = document(root, item["completion"])
        after = document(root, item["stage_after"])
        need(terminal == row, "terminal differs from actual ledger row")
        need(
            terminal["status"] == "completed" and terminal["exit_code"] == 0
            and terminal["timed_out"] is False and terminal["capacity_loss"] is None,
            "replacement not complete",
        )
        need(
            terminal["tool_binding"]["version"] == "0.14.0"
            and terminal["tool_binding"]["sha256"] == ENGINE_SHA,
            "replacement engine differs",
        )
        need(
            all(item[key] == terminal[key] for key in (
                "source_commit", "plan_commit", "contract_sha256"
            )),
            "historical context binding differs",
        )
        context = descriptor["source_contexts"][item["contract_sha256"]]
        need(
            context["source_commit"] == item["source_commit"]
            and context["plan_commit"] == item["plan_commit"],
            "terminal source context mapping differs",
        )
        need(
            completion["completed_receipt_sha256"] == item["terminal"]["sha256"]
            and completion["status"] == "completed",
            "completion terminal differs",
        )
        need(
            outcome["completion"] == item["completion"]
            and outcome["stage_after"] == item["stage_after"],
            "batch terminal proof differs",
        )
        need(
            after["ledger_rows"] == 90 + index
            and after["ledger_sha256"] == sha(b"".join(lines[:90 + index])),
            "successor prefix differs",
        )
        bound(root, {key: after["ledger_ref"][key] for key in ("path", "sha256")})
        retained.append(item)
    return retained


def _verify_codeql(root: Path, rows: list[JsonObject]) -> JsonObject:
    codeql = rows[88]
    need(
        codeql["group_id"] == "codeql-swift-common108"
        and codeql["status"] == "completed"
        and sum(row["group_id"] == codeql["group_id"] for row in rows) == 1,
        "retained CodeQL completion differs",
    )
    ref = {
        "path": "reports/releases/v0.9.2/attempts/" + codeql["attempt_id"] + "/completed.json",
        "sha256": CODEQL_TERMINAL_SHA,
    }
    need(document(root, ref) == codeql, "CodeQL terminal differs")
    return ref


def _verify_unclosed_event(root: Path, descriptor: JsonObject) -> None:
    event = descriptor["consumed_events"][0]
    for key in ("started", "admission", "phase_gate", "supervisor_permit"):
        document(root, event[key])
    started = document(root, event["started"])
    need(started["attempt_id"] == event["attempt_id"], "consumed started identity differs")
    terminal = root / Path(event["started"]["path"]).with_name("completed.json")
    need(not terminal.exists() and not terminal.is_symlink(), "unclosed Smoke02 now has terminal")
    for ref in descriptor["stop_evidence"].values():
        document(root, ref)


def validate_tail(
    root: Path, descriptor_ref: JsonObject, *, live_mode: str = "exact"
) -> JsonObject:
    """Return sealed historical bindings; never authorize a subsequent attempt.

    ``exact`` rejects every unknown live tail. ``prefix-history-only`` permits
    historical recovery after appends, but does not validate or authorize them.
    """
    root = Path(root)
    need(root.is_absolute(), "absolute root required")
    need(
        descriptor_ref == {"path": DESCRIPTOR_PATH, "sha256": DESCRIPTOR_SHA},
        "exact immutable descriptor required",
    )
    need(live_mode in {"exact", "prefix-history-only"}, "unknown live ledger mode")
    descriptor = document(root, descriptor_ref)
    core = document(root, descriptor["core"])
    manifest = document(root, descriptor["manifest"])
    stage = document(root, descriptor["stage02"])
    batch = document(root, descriptor["batch"])
    history = document(root, descriptor["resume_history"])
    need(manifest["core_identity"] == descriptor["core"], "manifest core differs")
    prefix = bound(root, {
        key: descriptor["ledger_prefix"][key] for key in ("path", "sha256")
    })
    lines, rows = ledger_rows(prefix)
    facts = validate_documents(descriptor, core, stage, batch, history, lines, rows)
    live = stable(root, LIVE_LEDGER)
    live_lines, live_rows = ledger_rows(live)
    need(
        len(live_rows) >= 109 and b"".join(live_lines[:109]) == prefix,
        "live ledger does not preserve sealed109 prefix",
    )
    need(live_mode != "exact" or live == prefix, "unregistered live tail forbidden in exact mode")
    bound(root, descriptor["original89_provider"])
    bound(root, descriptor["publication_hold"])
    for context in descriptor["source_contexts"].values():
        document(root, context["contract"])
    retained = _verify_replacements(root, descriptor, batch, lines, rows)
    codeql_ref = _verify_codeql(root, rows)
    _verify_unclosed_event(root, descriptor)
    return {
        "schema": "v092-joern05-sealed109-history-context/v1",
        "status": "sealed109-history-bindings-verified-not-runtime-replay",
        "execution_authorized": False,
        "automatic_retry": False,
        "descriptor_ref": copy.deepcopy(descriptor_ref),
        "ledger_prefix": copy.deepcopy(descriptor["ledger_prefix"]),
        "live_ledger_mode": live_mode,
        "live_rows_observed": len(live_rows),
        "later_rows_authorized": False,
        "original89_provider": copy.deepcopy(descriptor["original89_provider"]),
        "source_contexts": copy.deepcopy(descriptor["source_contexts"]),
        "retained20": copy.deepcopy(retained),
        "retained_codeql": codeql_ref,
        "consumed_events": copy.deepcopy(descriptor["consumed_events"]),
        **facts,
    }
