#!/usr/bin/env python3
"""Pinned adapter08 entrypoint for the reviewed Joern observer08 source."""
from __future__ import annotations

import hashlib
import contextlib
import copy
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any


OBSERVER_PATH = (
    "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py"
)
OBSERVER_SHA256 = "5d39a7931cdaa690566b7587142ed9abd2b44ffaf38d51a403028653a40e85b1"
MAX_OBSERVER_BYTES = 1024 * 1024
ATTEMPT_CWD = (
    "execution-state/v092/groups/series-02/joern-swift-common108/attempt-05"
)
CLI_OUTPUT = "reports/raw/joern-common-v2/current108-v092-01"
SNAPSHOT_OUTPUT = "reports/raw/joern-common-v2/current108-v092-01"
ORIGINAL_OUTPUT_ROOT = "reports/raw/joern-common-v2"
PLAN_PATH = (
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
    "native-finalization-03/attempt-07/execution-plan.json"
)
PLAN_SHA256 = "f4ae8f2ca3ece1bb253ce24a70368e969f0a25bc8d35dd2c8f7578d730aff4e9"
EVIDENCE_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "capability-evidence.json"
)
EVIDENCE_SHA256 = "deefa524579114d6fa42271193b6f4def69e296ffd23023f1e72ae7d2ee4a005"
GROUP_ID = "joern-swift-common108"
EXPECTED_REPORT_PARTITIONS = (66, 24, 4, 12, 2)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read_observer(root: Path) -> tuple[Path, bytes]:
    relative = Path(OBSERVER_PATH)
    _require(not relative.is_absolute() and ".." not in relative.parts,
             "observer source path is not repository relative")
    path = root / relative
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        _require(not cursor.is_symlink(), "observer source ancestry contains a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_OBSERVER_BYTES,
                 "observer source is not a bounded regular file")
        chunks = []
        remaining = MAX_OBSERVER_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    raw = b"".join(chunks)
    _require(len(raw) <= MAX_OBSERVER_BYTES and len(raw) == before.st_size and
             (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "observer source changed during bounded read")
    _require(hashlib.sha256(raw).hexdigest() == OBSERVER_SHA256,
             "observer source differs from its reviewed digest")
    return path, raw


def _attempt_root() -> Path:
    wrapper = Path(__file__).resolve()
    _require(wrapper.name == "run-joern-common-v092.py" and
             wrapper.parent.name == "adapter-08",
             "wrapper is outside its reviewed adapter08 location")
    return wrapper.parents[6]


def _no_symlink_ancestry(root: Path, candidate: Path, description: str,
                         *, require_directory: bool = False) -> Path:
    root = Path(root).resolve(strict=True)
    candidate = Path(candidate)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = Path(os.path.abspath(candidate))
    _require(candidate.is_relative_to(root), description + " escaped the repository")
    current = root
    components = candidate.relative_to(root).parts
    for index, component in enumerate(components):
        current = current / component
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            continue
        _require(not stat.S_ISLNK(info.st_mode), description + " ancestry contains a symlink")
        if index + 1 < len(components):
            _require(stat.S_ISDIR(info.st_mode), description + " parent is not a directory")
    if require_directory:
        _require(candidate.is_dir(), description + " is not an existing directory")
    return candidate


def _expected_execute_argv(root: Path) -> list[str]:
    return [
        "execute", "--root", str(root), "--plan", PLAN_PATH,
        "--plan-sha256", PLAN_SHA256, "--evidence", EVIDENCE_PATH,
        "--evidence-sha256", EVIDENCE_SHA256, "--output", CLI_OUTPUT,
    ]


def _validate_execute_invocation(argv: list[str], *, attempt_root: Path | None = None,
                                 cwd: Path | None = None,
                                 environment: dict[str, str] | None = None) -> tuple[Path, Path]:
    """Fail closed unless this is the exact admitted attempt invocation."""
    _require(type(argv) is list and all(type(item) is str for item in argv),
             "execute invocation must be an exact string list")
    _require(len(argv) > 2 and argv[1] == "--root",
             "execute invocation has no exact checkout root")
    root_arg = Path(argv[2])
    _require(root_arg.is_absolute(), "execute checkout root must be absolute")
    root = root_arg.resolve(strict=True)
    _require(root_arg == root, "execute checkout root is not canonical")
    _require(argv == _expected_execute_argv(root),
             "execute invocation differs from the reviewed Joern05 command")
    expected_cwd = root / ATTEMPT_CWD
    source_root = _attempt_root() if attempt_root is None else Path(attempt_root)
    _require(source_root == expected_cwd,
             "materialized adapter root differs from the admitted attempt")
    actual_cwd = Path.cwd() if cwd is None else Path(cwd)
    _require(actual_cwd == expected_cwd,
             "execute working directory differs from the admitted attempt")
    _no_symlink_ancestry(root, expected_cwd, "execute working directory",
                         require_directory=(cwd is None))
    values = os.environ if environment is None else environment
    _require(values.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION") == "1" and
             values.get("DATAFLOWBENCH_V092_GROUP_ID") == GROUP_ID,
             "execute environment markers differ from the admitted Joern05 group")
    output = _no_symlink_ancestry(
        root, expected_cwd / CLI_OUTPUT, "execute output directory")
    return root, output


def _read_regular(root: Path, relative: str, description: str,
                  *, maximum: int = 32 * 1024 * 1024) -> tuple[Path, bytes]:
    relative_path = Path(relative)
    _require(not relative_path.is_absolute() and ".." not in relative_path.parts,
             description + " path is not repository relative")
    path = _no_symlink_ancestry(root, root / relative_path, description)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum,
                 description + " is not a bounded regular file")
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    raw = b"".join(chunks)
    signature = lambda value: (value.st_dev, value.st_ino, value.st_size,
                               value.st_mtime_ns, value.st_ctime_ns)
    _require(len(raw) == before.st_size and len(raw) <= maximum and
             signature(before) == signature(after),
             description + " changed during bounded read")
    return path, raw


def _json_object(raw: bytes, description: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(description + " is not strict JSON") from exc
    _require(type(value) is dict, description + " must be a JSON object")
    return value


def _translate_report_raw_outputs(root: Path, output_path: Path,
                                  run: dict[str, Any]) -> None:
    """Translate only raw_output values after verifying exact raw files/hashes."""
    root = Path(root).resolve(strict=True)
    output_path = _no_symlink_ancestry(root, output_path,
                                       "attempt output directory", require_directory=True)
    normal = _no_symlink_ancestry(root, output_path / "normal",
                                  "normalized report directory", require_directory=True)
    _require(type(run) is dict and run.get("schema") == "joern-common-run/v092",
             "observer run record has an unexpected schema")
    rows = run.get("results")
    _require(type(rows) is list and len(rows) == sum(EXPECTED_REPORT_PARTITIONS),
             "observer run does not retain all108 raw rows")
    raw_by_case = {}
    for row in rows:
        _require(type(row) is dict and isinstance(row.get("case_id"), str) and
                 row["case_id"] not in raw_by_case,
                 "observer run has a malformed or duplicate case result")
        raw_ref = row.get("raw")
        _require(type(raw_ref) is dict and set(raw_ref) == {"path", "sha256"} and
                 isinstance(raw_ref.get("path"), str) and
                 len(raw_ref.get("sha256", "")) == 64 and
                 all(c in "0123456789abcdef" for c in raw_ref["sha256"]),
                 "observer raw result reference is malformed")
        case_id = row["case_id"]
        _require(case_id not in {".", ".."} and Path(case_id).name == case_id,
                 "observer case id is not a single safe path component")
        expected_file = output_path / case_id / "raw.json"
        expected_file = _no_symlink_ancestry(root, expected_file,
                                             "case raw output", require_directory=False)
        expected_relative = expected_file.relative_to(root).as_posix()
        _require(raw_ref["path"] == expected_relative,
                 "observer raw result path differs from the exact attempt output")
        actual_file, raw_bytes = _read_regular(root, expected_relative,
                                               "case raw output")
        _require(actual_file == expected_file and
                 hashlib.sha256(raw_bytes).hexdigest() == raw_ref["sha256"],
                 "case raw output SHA differs from the observer run binding")
        raw_by_case[case_id] = raw_ref

    report_updates: list[tuple[Path, bytes, bytes]] = []
    seen: set[str] = set()
    partition_sizes = []
    for ordinal, expected_size in enumerate(EXPECTED_REPORT_PARTITIONS):
        relative = (output_path / "normal" / f"report-{ordinal}.json").relative_to(root).as_posix()
        report_path, original_bytes = _read_regular(root, relative,
                                                    "Joern normalized report")
        report = _json_object(original_bytes, "Joern normalized report")
        report_rows = report.get("results")
        _require(type(report_rows) is list and len(report_rows) == expected_size,
                 "Joern report partition size differs")
        partition_sizes.append(len(report_rows))
        before_report = copy.deepcopy(report)
        for report_row in report_rows:
            _require(type(report_row) is dict and
                     isinstance(report_row.get("case_id"), str),
                     "Joern normalized report row is malformed")
            case_id = report_row["case_id"]
            _require(case_id not in seen and case_id in raw_by_case,
                     "Joern report case membership is duplicated or unbound")
            seen.add(case_id)
            raw_ref = raw_by_case[case_id]
            new_value = f"{SNAPSHOT_OUTPUT}/{case_id}/raw.json"
            _require(report_row.get("raw_output") == raw_ref["path"] and
                     report_row.get("raw_sha256") == raw_ref["sha256"],
                     "Joern report raw path or SHA differs from the observer run")
            report_row["raw_output"] = new_value
        _require(report_path == normal / f"report-{ordinal}.json",
                 "Joern report path changed during translation")
        expected_report = copy.deepcopy(before_report)
        for before_row, after_row in zip(expected_report["results"], report_rows):
            before_row["raw_output"] = after_row["raw_output"]
        _require(report == expected_report,
                 "report translation changed fields outside raw_output")
        updated_bytes = (json.dumps(report, indent=2) + "\n").encode("utf-8")
        report_updates.append((report_path, original_bytes, updated_bytes))
    _require(tuple(partition_sizes) == EXPECTED_REPORT_PARTITIONS and
             seen == set(raw_by_case),
             "Joern normalized reports do not preserve the exact108-case partition")

    for path, original_bytes, updated_bytes in report_updates:
        relative = path.relative_to(root).as_posix()
        _current_path, current_bytes = _read_regular(root, relative,
                                                     "Joern normalized report")
        _require(current_bytes == original_bytes,
                 "Joern normalized report changed before snapshot translation")
        path.write_bytes(updated_bytes)


@contextlib.contextmanager
def _scoped_observer_output(observer: ModuleType, root: Path,
                            output: Path):
    """Temporarily bind exact plan validation and report paths to one output."""
    root = Path(root).resolve(strict=True)
    output = _no_symlink_ancestry(root, output, "attempt output directory")
    output_relative = output.relative_to(root).as_posix()
    observer_path = Path(getattr(observer, "__file__", "")).resolve()
    attempt_root = _attempt_root()
    _require(observer_path == attempt_root / OBSERVER_PATH and
             _read_observer(attempt_root)[0] == observer_path,
             "output scope requires the exact pinned observer08 module")
    original_context = getattr(observer, "_runner_context", None)
    original_execute = getattr(observer, "execute", None)
    _require(callable(original_context) and callable(original_execute),
             "pinned observer execute hooks are missing")

    def scoped_context(candidate_root, old, result, observer_state):
        _require(Path(candidate_root).resolve() == root,
                 "observer runner context escaped the original checkout")
        runner, old_constant, original_scope = original_context(
            candidate_root, old, result, observer_state)
        sealed = result.get("new_plan")
        _require(type(sealed) is dict and result.get("new_plan_path") == PLAN_PATH and
                 result.get("new_plan_sha256") == PLAN_SHA256 and
                 sealed.get("output_root") == ORIGINAL_OUTPUT_ROOT and
                 sealed.get("status") == "execution-eligible" and
                 sealed.get("execution_eligible") is True and
                 sealed.get("full_model_qualification") is False and
                 sealed.get("scored_activation") is False,
                 "observer result is not the exact eligible semantic-only plan")
        plan_path, plan_raw = _read_regular(root, PLAN_PATH, "eligible Joern plan")
        _require(hashlib.sha256(plan_raw).hexdigest() == PLAN_SHA256 and
                 _json_object(plan_raw, "eligible Joern plan") == sealed,
                 "eligible plan bytes differ from observer validation")
        original_validate = runner.validate_plan

        def validate_plan(call_root, plan_path_value, *args, **kwargs):
            _require(Path(call_root).resolve() == root and
                     plan_path_value == PLAN_PATH and not args and not kwargs,
                     "runner validation escaped the bound plan call")
            _path, current_raw = _read_regular(root, PLAN_PATH, "eligible Joern plan")
            _require(current_raw == plan_raw,
                     "eligible plan changed before original runner validation")
            plan, evidence, context = original_validate(call_root, plan_path_value)
            _path, after_raw = _read_regular(root, PLAN_PATH, "eligible Joern plan")
            _require(after_raw == plan_raw and plan == sealed and
                     plan.get("output_root") == ORIGINAL_OUTPUT_ROOT,
                     "original runner validation differs from the sealed plan")
            projected = copy.deepcopy(plan)
            projected["output_root"] = output_relative
            return projected, evidence, context

        @contextlib.contextmanager
        def scoped_validate_plan():
            runner.validate_plan = validate_plan
            try:
                with original_scope:
                    yield
            finally:
                changed = runner.validate_plan is not validate_plan
                runner.validate_plan = original_validate
                _require(not changed,
                         "runner validator changed before identity-safe restore")

        return runner, old_constant, scoped_validate_plan()

    def translated_execute(candidate_root, candidate_output, **kwargs):
        _require(Path(candidate_root).resolve() == root and
                 Path(candidate_output).resolve() == output,
                 "observer execute escaped the exact root/output binding")
        result = original_execute(candidate_root, candidate_output, **kwargs)
        _require(type(result) is dict and type(result.get("run")) is dict,
                 "observer returned no exact run record")
        _translate_report_raw_outputs(root, output, result["run"])
        return result

    observer._runner_context = scoped_context
    observer.execute = translated_execute
    try:
        yield
    finally:
        context_changed = observer._runner_context is not scoped_context
        execute_changed = observer.execute is not translated_execute
        observer._runner_context = original_context
        observer.execute = original_execute
        _require(not context_changed and not execute_changed,
                 "observer hooks changed before identity-safe restore")


def load_observer() -> ModuleType:
    """Execute only the exact observer08 bytes and return its module."""
    wrapper = Path(__file__).resolve()
    root = _attempt_root()
    _require(wrapper.name == "run-joern-common-v092.py" and
             wrapper.parent.name == "adapter-08",
             "wrapper is outside its reviewed adapter08 location")
    path, raw = _read_observer(root)
    module = ModuleType("_dfb_joern_native_startup_observer_08_pinned")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    _require(callable(getattr(module, "main", None)),
             "pinned observer08 has no callable CLI entrypoint")
    return module


def main(argv: list[str] | None = None) -> int:
    """Keep preflight/controls passthrough and gate only official execute."""
    forwarded = sys.argv[1:] if argv is None else argv
    _require(type(forwarded) is list and all(type(item) is str for item in forwarded),
             "observer CLI arguments must be an exact string list")
    observer = load_observer()
    if forwarded and forwarded[0] == "execute":
        root, output = _validate_execute_invocation(
            forwarded, attempt_root=_attempt_root())
        _require(not output.exists() and not output.is_symlink(),
                 "attempt output directory already exists")
        with _scoped_observer_output(observer, root, output):
            return observer.main(forwarded)
    return observer.main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
