#!/usr/bin/env python3
"""Verify the one recorded command-environment PATH delta in native08.

This is a post-capture comparator only. It never launches a process or reads
the live process table. It checks the exact retained run and native08 capture,
then accepts only the already-reviewed old PATH digest to the exact native08
sanitized PATH. Its result is explicitly not input equivalence or a timing
comparison.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any


ROOT = Path(__file__).resolve().parents[6]
SCHEMA = "v092-joern-native08-command-input-delta/v1"
EXPECTED_STATUS = "semantic-only-PATH-delta-verified"

REQUEST_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json",
    "sha256": "a444c55cf107d64089ed1470d56b3db7dd64e00d683c2278b0b62937a1bb75df",
}
CONTROL_RESULT_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08/control-result.json",
    "sha256": "7701390bd9860147f0d3c654183d5220cf742824f83261251ff5cda13c1f2ba9",
}
CAPTURE_RUN_PATH = (
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
    "native-controls-08/capture/run.json"
)
HELPER_SOURCE_PATH = (
    "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/"
    "command-path-amendment-01/command_path_amendment_01.py"
)
NAMESPACE = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08"
WORKER_INVOCATION_REF = {
    "path": NAMESPACE + "/worker-invocation.json",
    "sha256": "9438ed1365c5fea1737f7da22e9f30516f65565232e7b69e8835ecd70e27c81e",
}
CAPTURE_ROOT = NAMESPACE + "/capture"
EXPECTED_HEAD = "ab5c8ade58b789957e48de29ca54f432457611c1"
EXPECTED_OBSERVER = {
    "path": "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-07.py",
    "sha256": "4e3998dfb3f32b5d377c8697ea644d247f147220679eb784cc64fc501f7bc199",
}
EXPECTED_PENDING_PLAN = {
    "path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/pending-execution-plan-01.json",
    "sha256": "09d6748e23b670dbd8998a9f5f80075a25f4b388788004f36fd8b279bec5533e",
}
EXPECTED_CONTROL_PLAN = {
    "path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/control-plan-01.json",
    "sha256": "05d8b63d78df07ad4a66b4609573ffd051f5b44cf0416f316aab7b2dc9755a2f",
}
EXPECTED_LEDGER = {
    "path": "reports/releases/v0.9.2/ledger-v1.jsonl",
    "sha256": "79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84",
}
OLD_PLAN_REF = {
    "path": "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
    "sha256": "e5cfd9d5473fd47f54de25d74a6f945c667c086ce471d5f6cdcead797bf9e3ab",
}
OLD_RECEIPT_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-04/qualification-receipt-02.json",
    "sha256": "c38aae7b1d4179bcd505ef32d3220f218efd25a16d5ce4eee0bf5d8eb4afc1bb",
}
OLD_RUN_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-04/run.json",
    "sha256": "a4f68131bce1b79151ad361a2e05b861f37a1c43f74d1fcb660d4082f9bf4ada",
}
RETAINED_SOURCE_REFS = {
    "scripts/joern_capability_repair_v092_03.py": "8e3d986f20c2262045d8473837d1bf5a56b61da1bc23fee6e778bd0ac47d2b51",
    "scripts/joern_normal_runner_v092.py": "683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4",
    "scripts/joern_normal_reports_v092.py": "75531186a9091e9e907a2c42388efea0e33d4872787a28fa9fc20b3643131db1",
    "scripts/swift_common_population_v2.py": "3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6",
    "scripts/joern_diagnostic_admission_v092.py": "c2faeeb5ef99f539ad8a4bee6fbc85656c0cc142f92196c02f5f26a446140a9e",
}
EXPECTED_TOOL_REFS = {
    "wrapper": {
        "path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py",
        "sha256": "5f513fe20ff23e3f2fed6f32adb311e3cfa77ab43b56b50b13a0251969777f42",
    },
    "resources": {
        "path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py",
        "sha256": "ea8fa4268477a4411c55d44c1704f132d8b0b8b4b9bf0f722b4afd404f9bbe08",
    },
}
EXPECTED_OLD_PATH_SHA256 = "7c96ef759a4f8c588dde51712ab0690953d7add50968baa594a42ca9925e1f07"
EXPECTED_NEW_PATH = (
    "/Users/dave/.sdkman/candidates/java/21.0.8-tem/bin:/opt/homebrew/bin:"
    "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
)
EXPECTED_NEW_PATH_SHA256 = "f199a21ab656a5d5f6191757fc6982fbb94334a163f17143ccadef8d6e2763c2"
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_COMMANDS = 36
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
PHASES = ("typecheck", "frontend", "query")


class CommandPathError(ValueError):
    """A retained/native08 command-input binding failed closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CommandPathError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _open_directory(path: Path, description: str) -> int:
    absolute = Path(os.path.abspath(path))
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    require(getattr(os, "O_DIRECTORY", 0) and getattr(os, "O_NOFOLLOW", 0),
            "platform lacks no-follow directory opens")
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise CommandPathError(f"{description} has an unsafe or missing directory") from exc
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_parent(path: Path, description: str) -> tuple[int, str]:
    absolute = Path(os.path.abspath(path))
    require(absolute.is_absolute() and len(absolute.parts) >= 2,
            f"{description} path is malformed")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    require(getattr(os, "O_DIRECTORY", 0) and getattr(os, "O_NOFOLLOW", 0),
            "platform lacks no-follow directory opens")
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:-1]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise CommandPathError(f"{description} has an unsafe or missing parent") from exc
            os.close(descriptor)
            descriptor = child
        return descriptor, absolute.name
    except BaseException:
        os.close(descriptor)
        raise


def _read_stable(path: Path, maximum: int, description: str,
                 expected_sha256: str | None = None) -> bytes:
    require(type(maximum) is int and 0 < maximum <= 64 * 1024 * 1024,
            f"{description} size bound is invalid")
    parent_fd, name = _open_parent(path, description)
    descriptor = None
    try:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum,
                f"{description} is not a bounded regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(1024 * 1024, maximum + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            require(total <= maximum, f"{description} exceeds its size bound")
        after = os.fstat(descriptor)
        signature = lambda item: (item.st_dev, item.st_ino, item.st_mode, item.st_size,
                                  item.st_mtime_ns, item.st_ctime_ns)
        require(signature(before) == signature(after) and total == before.st_size,
                f"{description} changed while read")
        raw = b"".join(chunks)
        if expected_sha256 is not None:
            require(SHA256_RE.fullmatch(expected_sha256) is not None and
                    sha_bytes(raw) == expected_sha256,
                    f"{description} SHA-256 differs")
        return raw
    except OSError as exc:
        raise CommandPathError(f"{description} could not be read safely") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)


def _relative_path(root: Path, value: object, description: str) -> Path:
    require(type(value) is str and value and "\\" not in value,
            f"{description} path is malformed")
    path = Path(value)
    require(not path.is_absolute() and path.as_posix() == value and
            ".." not in path.parts and "" not in path.parts,
            f"{description} path is not canonical relative form")
    result = root / path
    require(result.resolve(strict=False).is_relative_to(root),
            f"{description} path escapes the repository")
    return result


def _read_ref(root: Path, ref: object, description: str,
              maximum: int = MAX_JSON_BYTES) -> tuple[bytes, dict[str, str]]:
    require(type(ref) is dict and set(ref) == {"path", "sha256"},
            f"{description} reference fields differ")
    require(type(ref.get("sha256")) is str and SHA256_RE.fullmatch(ref["sha256"]) is not None,
            f"{description} SHA-256 is malformed")
    path = _relative_path(root, ref.get("path"), description)
    raw = _read_stable(path, maximum, description, ref["sha256"])
    return raw, {"path": ref["path"], "sha256": ref["sha256"]}


def _object(raw: bytes, description: str) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{description} contains a duplicate JSON key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CommandPathError(f"{description} is not valid JSON") from exc
    require(type(value) is dict, f"{description} is not a JSON object")
    return value


def _read_json_ref(root: Path, ref: object, description: str,
                   maximum: int = MAX_JSON_BYTES) -> tuple[dict[str, Any], dict[str, str]]:
    raw, normalized_ref = _read_ref(root, ref, description, maximum)
    return _object(raw, description), normalized_ref


def _normalise_capture_path(value: object, old_capture: str,
                            new_capture: str) -> object:
    if not isinstance(value, str):
        return value
    return value.replace(old_capture, "<control-capture>").replace(
        new_capture, "<control-capture>")


def command_input_signature(command: dict[str, Any], old_capture: str,
                            new_capture: str) -> dict[str, Any]:
    """Match the frozen shim's selected recorded command-input fields."""
    required_fields = {"argv", "cwd", "environment", "measurement_wrapper",
                       "phase_id", "role", "deadline_scope"}
    require(required_fields <= set(command), "recorded command input fields are incomplete")
    argv = command["argv"]
    environment = command["environment"]
    require(type(argv) is list,
            "recorded argv is malformed")
    require(type(environment) is dict and
            all(type(key) is str for key in environment),
            "recorded command environment is malformed")
    return {
        "argv": [_normalise_capture_path(value, old_capture, new_capture) for value in argv],
        "cwd": _normalise_capture_path(command["cwd"], old_capture, new_capture),
        "environment": environment,
        "measurement_wrapper": command["measurement_wrapper"],
        "phase_id": command["phase_id"],
        "role": command["role"],
        "deadline_scope": command["deadline_scope"],
    }


def _record_key(record: object) -> tuple[str, str, str]:
    require(type(record) is dict and {"control", "case_id", "arm", "raw"} <= set(record),
            "control run record is malformed")
    control, case_id, arm = record.get("control"), record.get("case_id"), record.get("arm")
    require(type(control) is str and control and type(case_id) is str and case_id and
            arm in {"on", "off"}, "control run record identity is malformed")
    return control, case_id, arm


def _matches_path_delta(old_command: dict[str, Any], new_command: dict[str, Any],
                        old_capture: str, new_capture: str) -> str:
    old_signature = command_input_signature(old_command, old_capture, new_capture)
    new_signature = command_input_signature(new_command, old_capture, new_capture)
    for field in ("argv", "cwd", "measurement_wrapper", "phase_id", "role", "deadline_scope"):
        require(old_signature[field] == new_signature[field],
                f"recorded command input changed outside the approved PATH field: {field}")
    old_env = old_signature["environment"]
    new_env = new_signature["environment"]
    require(set(old_env) == set(new_env) and "PATH" in old_env,
            "recorded command environment fields differ or omit PATH")
    for key in old_env:
        if key == "PATH":
            continue
        require(old_env[key] == new_env[key],
                f"recorded command environment changed outside PATH: {key}")
    old_path = old_env["PATH"]
    new_path = new_env["PATH"]
    require(type(old_path) is str and type(new_path) is str,
            "recorded PATH fields are not strings")
    require(sha_bytes(old_path.encode("utf-8")) == EXPECTED_OLD_PATH_SHA256,
            "recorded historical PATH does not match the exact retained digest")
    require(new_path == EXPECTED_NEW_PATH and
            sha_bytes(new_path.encode("utf-8")) == EXPECTED_NEW_PATH_SHA256,
            "recorded native08 PATH differs from the exact reviewed sanitized value")
    return old_path


def _check_run_identity(run: dict[str, Any], description: str) -> None:
    require(run.get("schema") == "analyzer-qualification-control-run/v092" and
            run.get("group_id") == "joern-swift-common108" and
            type(run.get("phase_invocation_count")) is int and
            run["phase_invocation_count"] == 36 and
            type(run.get("records")) is list and len(run["records"]) == 12,
            f"{description} is not the exact 12-arm/36-phase retained run")
    identity = run.get("identity")
    require(type(identity) is dict and identity.get("tool") == "joern" and
            identity.get("tool_version") == "4.0.660" and
            identity.get("adapter_version") == "joern-normal-v092" and
            type(run.get("identity_components")) is list and
            type(run.get("identity_witness")) is dict,
            f"{description} runtime identity is incomplete or differs")


def _load_native08_context(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any],
                                                  dict[str, Any], dict[str, Any], str,
                                                  dict[str, str], dict[str, str], str]:
    request, request_ref = _read_json_ref(root, REQUEST_REF, "native08 request")
    require(request.get("schema") == "v092-joern-native-control-request/v2" and
            request.get("expected_head") == EXPECTED_HEAD and
            request.get("namespace") == NAMESPACE and
            request.get("ledger") == EXPECTED_LEDGER and
            request.get("observer") == EXPECTED_OBSERVER and
            request.get("pending_plan") == EXPECTED_PENDING_PLAN and
            request.get("control_plan") == EXPECTED_CONTROL_PLAN and
            request.get("tool_refs") == EXPECTED_TOOL_REFS,
            "native08 request differs from the exact captured source/runtime identity")
    source_refs = request.get("source_refs")
    require(type(source_refs) is list and source_refs and
            all(type(ref) is dict and set(ref) == {"path", "sha256"} for ref in source_refs),
            "native08 source-ref closure is malformed")
    source_map = {ref["path"]: ref for ref in source_refs}
    require(len(source_map) == len(source_refs) and
            all(source_map.get(path) == {"path": path, "sha256": digest}
                for path, digest in RETAINED_SOURCE_REFS.items()),
            "native08 source closure omits or changes a pinned retained runtime module")
    closure_sha256 = sha_bytes(canonical(source_refs))

    pending_plan, _pending_ref = _read_json_ref(root, EXPECTED_PENDING_PLAN,
                                                "native08 pending plan")
    control_plan, _control_ref = _read_json_ref(root, EXPECTED_CONTROL_PLAN,
                                                "native08 control plan")
    require(pending_plan.get("status") == "qualification-pending" and
            pending_plan.get("execution_eligible") is False and
            pending_plan.get("identity", {}).get("tool_version") == "4.0.660" and
            pending_plan.get("qualification_control_plan") == EXPECTED_CONTROL_PLAN and
            control_plan.get("group_id") == "joern-swift-common108",
            "native08 plan/control identity is not the pinned pending 4.0.660 context")

    control_result, control_result_ref = _read_json_ref(
        root, CONTROL_RESULT_REF, "native08 control result")
    require(control_result.get("schema") == "v092-native-control-qualification-result/v1" and
            control_result.get("request") == request_ref and
            control_result.get("observer") == EXPECTED_OBSERVER and
            control_result.get("pending_plan") == EXPECTED_PENDING_PLAN and
            control_result.get("evaluation_scope") == "semantic-only" and
            control_result.get("uncontended_timing_certified") is False and
            control_result.get("relative_performance_conclusions_authorized") is False and
            control_result.get("scored_activation") is False and
            control_result.get("automatic_retry") is False,
            "native08 control result is not the exact held semantic-only capture")
    worker, worker_ref = _read_json_ref(root, WORKER_INVOCATION_REF,
                                        "native08 worker invocation")
    environment = worker.get("environment")
    require(worker.get("schema") == "v092-native-control-worker-invocation/v1" and
            worker.get("request") == request_ref and
            worker_ref == WORKER_INVOCATION_REF and
            type(environment) is dict and
            all(type(key) is str and type(value) is str for key, value in environment.items()) and
            environment.get("PATH") == EXPECTED_NEW_PATH and
            worker.get("automatic_retry") is False and
            worker.get("environment_sha256") == sha_bytes(canonical(environment)),
            "native08 worker environment binding does not prove the exact sanitized PATH")
    raw_run = _read_stable(root / CAPTURE_RUN_PATH, MAX_JSON_BYTES,
                           "native08 captured run")
    capture_run_ref = {"path": CAPTURE_RUN_PATH, "sha256": sha_bytes(raw_run)}
    captured_run = _object(raw_run, "native08 captured run")
    require(captured_run == control_result.get("run"),
            "native08 control result and retained capture/run.json differ")

    old_plan, _ = _read_json_ref(root, OLD_PLAN_REF, "immutable retained plan")
    require(old_plan.get("fresh_qualification") == OLD_RECEIPT_REF,
            "retained plan no longer binds the pinned qualification receipt")
    old_receipt, _ = _read_json_ref(root, OLD_RECEIPT_REF, "immutable retained qualification")
    require(old_receipt.get("control_run") == OLD_RUN_REF,
            "retained qualification no longer binds the pinned control run")
    retained_run, _ = _read_json_ref(root, OLD_RUN_REF, "immutable retained control run")
    return (request, control_result, pending_plan, old_plan, retained_run,
            closure_sha256, capture_run_ref, worker_ref, worker["environment_sha256"])


def validate_native08_command_path_delta(root: Path, old_run: dict[str, Any],
                                         new_run: dict[str, Any], *,
                                         helper_ref: dict[str, str]) -> dict[str, Any]:
    """Verify the only declared recorded-field difference between these runs."""
    root = Path(root).resolve()
    require(type(old_run) is dict and type(new_run) is dict,
            "command comparator requires exact run objects")
    require(type(helper_ref) is dict and set(helper_ref) == {"path", "sha256"} and
            helper_ref.get("path") == HELPER_SOURCE_PATH and
            type(helper_ref.get("sha256")) is str and
            SHA256_RE.fullmatch(helper_ref["sha256"]) is not None and
            _read_stable(root / HELPER_SOURCE_PATH, 2 * 1024 * 1024,
                         "pinned command-path helper", helper_ref["sha256"]),
            "command-path helper does not match its separately reviewed hardpin")
    (request, control_result, pending_plan, old_plan, retained_run, closure_sha256,
     capture_run_ref, worker_ref, worker_environment_sha256) = (
        _load_native08_context(root)
    )
    require(old_run == retained_run,
            "comparator old run is not the exact immutable retained run")
    require(new_run == control_result.get("run"),
            "comparator new run is not the exact native08 control result run")
    _check_run_identity(old_run, "retained control run")
    _check_run_identity(new_run, "native08 control run")
    require(old_run.get("identity") == new_run.get("identity") == pending_plan.get("identity") and
            old_run.get("identity_components") == new_run.get("identity_components") ==
            pending_plan.get("identity_components"),
            "retained/native08 runtime identity differs from the frozen pending plan")
    require(new_run.get("control_plan_sha256") == EXPECTED_CONTROL_PLAN["sha256"] and
            new_run.get("execution_plan_projection_sha256") ==
            pending_plan.get("qualification_control_projection_sha256"),
            "native08 run does not bind the exact pending control plan/projection")

    old_rows = old_run["records"]
    new_rows = new_run["records"]
    old_by_key = {_record_key(row): row for row in old_rows}
    new_by_key = {_record_key(row): row for row in new_rows}
    require(len(old_by_key) == len(new_by_key) == 12 and
            len(old_rows) == len(new_rows) == 12 and set(old_by_key) == set(new_by_key),
            "retained/native08 control arms differ or contain duplicate rows")
    cases = {key[1] for key in old_by_key}
    require(len(cases) == 6 and {key[2] for key in old_by_key} == {"off", "on"} and
            all(sum(1 for key in old_by_key if key[1] == case) == 2 for case in cases),
            "retained/native08 six-case off/on roster is incomplete")

    pairs: list[dict[str, Any]] = []
    old_path_sha256: str | None = None
    new_path_sha256: str | None = None
    seen_raw_paths: set[str] = set()
    seen_command_paths: set[str] = set()
    for key in sorted(old_by_key):
        old_record = old_by_key[key]
        new_record = new_by_key[key]
        old_raw, old_raw_ref = _read_json_ref(root, old_record.get("raw"),
                                              f"retained raw {key}")
        new_raw, new_raw_ref = _read_json_ref(root, new_record.get("raw"),
                                              f"native08 raw {key}")
        require(old_raw_ref["path"] != new_raw_ref["path"] and
                old_raw_ref["path"] not in seen_raw_paths and
                new_raw_ref["path"] not in seen_raw_paths,
                f"control raw path was reused across retained/native08 runs: {key}")
        seen_raw_paths.update((old_raw_ref["path"], new_raw_ref["path"]))
        require(all(old_raw.get(field) == new_raw.get(field) == expected
                    for field, expected in (("control", key[0]), ("case_id", key[1]),
                                            ("arm", key[2]))) and
                old_raw.get("schema") == new_raw.get("schema") and
                old_raw.get("identity") == new_raw.get("identity") and
                old_raw.get("identity_components") == new_raw.get("identity_components"),
                f"retained/native08 raw identity changed: {key}")
        old_capture = old_raw.get("capture_directory")
        new_capture = new_raw.get("capture_directory")
        require(type(old_capture) is str and type(new_capture) is str and
                old_capture and new_capture and old_capture != new_capture,
                f"retained/native08 capture directory is not fresh: {key}")
        old_capture_path = Path(old_capture)
        new_capture_path = Path(new_capture)
        expected_new_root = (root / CAPTURE_ROOT).resolve()
        require(new_capture_path.is_absolute() and
                new_capture_path.resolve(strict=False).is_relative_to(expected_new_root) and
                old_capture_path.is_absolute() and
                not old_capture_path.resolve(strict=False).is_relative_to(expected_new_root),
                f"native08 raw is outside its exact fresh capture root: {key}")
        old_commands = old_raw.get("commands")
        new_commands = new_raw.get("commands")
        require(type(old_commands) is list and type(new_commands) is list and
                len(old_commands) == len(new_commands) == len(PHASES),
                f"retained/native08 phase count differs: {key}")
        old_phase_ids: list[str] = []
        new_phase_ids: list[str] = []
        for old_command_ref, new_command_ref in zip(old_commands, new_commands):
            old_command, old_command_ref = _read_json_ref(
                root, old_command_ref, f"retained command {key}")
            new_command, new_command_ref = _read_json_ref(
                root, new_command_ref, f"native08 command {key}")
            require(old_command_ref["path"] != new_command_ref["path"] and
                    old_command_ref["path"] not in seen_command_paths and
                    new_command_ref["path"] not in seen_command_paths,
                    f"retained/native08 command file path was reused: {key}")
            seen_command_paths.update((old_command_ref["path"], new_command_ref["path"]))
            require(Path(old_command_ref["path"]).parent == Path(old_raw_ref["path"]).parent and
                    Path(new_command_ref["path"]).parent == Path(new_raw_ref["path"]).parent,
                    f"command file does not belong to its exact raw capture directory: {key}")
            old_signature = command_input_signature(old_command, old_capture, new_capture)
            new_signature = command_input_signature(new_command, old_capture, new_capture)
            old_path = _matches_path_delta(old_command, new_command,
                                           old_capture, new_capture)
            old_path_digest = sha_bytes(old_path.encode("utf-8"))
            new_path_digest = sha_bytes(new_command["environment"]["PATH"].encode("utf-8"))
            require(old_path_sha256 in {None, old_path_digest} and
                    new_path_sha256 in {None, new_path_digest},
                    "recorded PATH changed within one of the 36 command phases")
            old_path_sha256 = old_path_digest
            new_path_sha256 = new_path_digest
            require(old_signature["phase_id"] in PHASES and
                    new_signature["phase_id"] == old_signature["phase_id"],
                    f"retained/native08 phase identity changed: {key}")
            old_phase_ids.append(old_signature["phase_id"])
            new_phase_ids.append(new_signature["phase_id"])
            pairs.append({
                "control": key[0], "case_id": key[1], "arm": key[2],
                "phase": old_signature["phase_id"],
                "retained_raw": old_raw_ref,
                "native08_raw": new_raw_ref,
                "retained_command": old_command_ref,
                "native08_command": new_command_ref,
            })
        require(old_phase_ids == list(PHASES) and new_phase_ids == list(PHASES),
                f"retained/native08 phase order is incomplete: {key}")

    require(len(pairs) == 36 and len(seen_command_paths) == 72 and
            old_path_sha256 == EXPECTED_OLD_PATH_SHA256 and
            new_path_sha256 == EXPECTED_NEW_PATH_SHA256,
            "full 12-arm/36-phase recorded command delta was not proven")
    runtime_refs = {
        path: {"path": path, "sha256": digest}
        for path, digest in RETAINED_SOURCE_REFS.items()
    }
    return {
        "schema": SCHEMA,
        "status": EXPECTED_STATUS,
        "bindings": {
            "request": REQUEST_REF,
            "control_result": CONTROL_RESULT_REF,
            "worker_invocation": worker_ref,
            "worker_environment_sha256": worker_environment_sha256,
            "retained_control_run": OLD_RUN_REF,
            "native08_control_run": capture_run_ref,
            "source_head": EXPECTED_HEAD,
            "source_closure_sha256": closure_sha256,
            "retained_observer": EXPECTED_OBSERVER,
            "pending_plan": EXPECTED_PENDING_PLAN,
            "control_plan": EXPECTED_CONTROL_PLAN,
            "ledger": EXPECTED_LEDGER,
            "retained_script": runtime_refs["scripts/joern_capability_repair_v092_03.py"],
            "runtime_sources": runtime_refs,
            "native_tools": EXPECTED_TOOL_REFS,
            "command_path_helper": helper_ref,
        },
        "recorded_command_comparison": {
            "retained_record_count": 12,
            "native08_record_count": 12,
            "phase_invocation_count": 36,
            "recorded_input_fields_unchanged_except": "environment.PATH",
            "recorded_environment_keys_equal": True,
            "old_path_sha256": EXPECTED_OLD_PATH_SHA256,
            "native08_path": EXPECTED_NEW_PATH,
            "native08_path_sha256": EXPECTED_NEW_PATH_SHA256,
            "ambient_os_environment_equivalence_proven": False,
            "command_input_equivalence": False,
            "pairs": pairs,
        },
        "interpretation": {
            "scope": "semantic-only",
            "result": "The only changed recorded command-input field is the prescribed PATH; unrecorded historical environment remains unknown.",
            "input_equivalence_claimed": False,
            "uncontended_timing_certified": False,
            "relative_performance_conclusions_authorized": False,
            "full_model_qualification": False,
            "scored_activation": False,
            "publication_approved": False,
            "publication_hold": True,
        },
    }


def make_validator(root: Path, helper_ref: dict[str, str]):
    """Return the narrowly scoped callback expected by the retained shim."""
    root = Path(root).resolve()
    last_audit: dict[str, Any] | None = None

    def validate_control_command_equivalence(_root: Path, old_run: dict[str, Any],
                                             new_run: dict[str, Any]) -> None:
        nonlocal last_audit
        require(Path(_root).resolve() == root,
                "retained comparator was invoked for a different repository root")
        last_audit = validate_native08_command_path_delta(
            root, old_run, new_run, helper_ref=helper_ref)

    def audit() -> dict[str, Any] | None:
        return last_audit

    validate_control_command_equivalence.audit = audit  # type: ignore[attr-defined]
    return validate_control_command_equivalence

