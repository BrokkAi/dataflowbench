#!/usr/bin/env python3
"""Fail-closed Swift fixture inventory, compile/link, and bounded-control check.

The Swift tranche has an intentionally small execution surface.  Every case is
compiled and linked with all of its declared Swift inputs.  Only the core
population and the one-hop calibration are copied to a temporary directory,
instrumented, and run with source values 7 and 19.  Modeling cases, including
the modeled-summary calibration, are compile-only; this script never treats a
concrete execution as proof of an abstract model.

The compiler, Xcode, host, SDK, and target pins are witnessed before inventory
or fixture work.  Evidence is written to a newly-created directory and keeps
the exact argv, environment, stdout, stderr, and exit status for every command
as well as metadata/source digests and temporary instrumentation differences.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


EXPECTED_TARGET = "arm64-apple-macosx27.0.0"
EXPECTED_SWIFT_VERSION_PARTS = (
    "Apple Swift version 6.4",
    "swiftlang-6.4.0.34.1",
    "clang-2100.3.34.1",
    "swift-driver version: 1.168.6",
)
EXPECTED_XCODE_PARTS = ("Xcode 27.0", "Build version 27A266a")
EXPECTED_SW_VERS_PARTS = (
    "ProductName:\tmacOS",
    "ProductVersion:\t27.0",
    "BuildVersion:\t26A428",
)
EXPECTED_SWIFT_VERSION_LINES = (
    r"^Apple Swift version 6\.4 \(swiftlang-6\.4\.0\.34\.1 clang-2100\.3\.34\.1\)$",
    r"^swift-driver version: 1\.168\.6$",
)
EXPECTED_XCODE_LINES = (
    r"^Xcode 27\.0$",
    r"^Build version 27A266a$",
)
EXPECTED_SDK_VERSION = "27.0"
EXPECTED_SDK_BUILD = "26A425"
MODULE_NAME = "DataFlowBenchTaintSwift"
SOURCE_VALUES = (7, 19)
COMPILE_TIMEOUT_SECONDS = 120
CONTROL_TIMEOUT_SECONDS = 30

CALIBRATION_TEMPLATES = {
    "dfb-template-one-hop-relay",
    "dfb-template-modeled-external-summary",
}

CORE_TEMPLATES = {
    "dfb-template-direct-propagation",
    "dfb-template-local-overwrite-kill",
    "dfb-template-local-multi-step-chain",
    "dfb-template-arithmetic-expression-propagation",
    "dfb-template-call-context-separation",
    "dfb-template-argument-position-separation",
    "dfb-template-return-relay-one-hop",
    "dfb-template-return-relay-two-hop",
    "dfb-template-object-separation",
    "dfb-template-same-object-field-separation",
    "dfb-template-alias-propagation-separation",
    "dfb-template-array-element-separation",
    "dfb-template-infeasible-branch",
    "dfb-template-branch-join",
    "dfb-template-loop-carried-kill",
    "dfb-template-exception-catch",
    "dfb-template-chal-computed-property",
    "dfb-template-chal-dispatch-table",
    "dfb-template-chal-closure-capture",
    "dfb-template-chal-function-field",
    "dfb-template-chal-callback-registration",
    "dfb-template-chal-map-iteration",
    "dfb-template-chal-nested-access-path",
    "dfb-template-chal-element-object",
    "dfb-template-chal-deep-relay-chain",
    "dfb-template-chal-recursive-carry",
    "dfb-template-chal-context-pair-depth2",
    "dfb-template-chal-interprocedural-exception-persistence",
    "dfb-template-chal-recursive-payload-transform",
    "dfb-template-chal-mutual-recursive-transform",
    "dfb-template-chal-recursive-heap-unwind",
    "dfb-template-chal-recursive-callback-transform",
    "dfb-template-chal-recursive-exception-persistence",
}

MODELING_TEMPLATES = {
    "dfb-template-model-declared-source",
    "dfb-template-model-declared-sink",
    "dfb-template-model-sanitizer-kill",
    "dfb-template-model-sanitizer-selectivity",
    "dfb-template-model-summary-through",
    "dfb-template-model-summary-field",
    "dfb-template-model-entrypoint-parameter",
    "dfb-template-model-entrypoint-selectivity",
    "dfb-template-model-store-roundtrip",
    "dfb-template-model-store-separation",
}

EXPECTED_BY_TIER = {
    "calibration": CALIBRATION_TEMPLATES,
    "core": CORE_TEMPLATES,
    "modeling": MODELING_TEMPLATES,
}
EXPECTED_TEMPLATE_TIER = {
    template: tier for tier, templates in EXPECTED_BY_TIER.items() for template in templates
}

SOURCE_DECLARATION = re.compile(
    r"\bfunc\s+dfb_source\s*\(\s*\)\s*->\s*Int\s*\{"
)
SINK_DECLARATION = re.compile(
    r"\bfunc\s+dfb_sink\s*\(\s*_\s*value\s*:\s*Int\s*\)\s*(?:->\s*Void\s*)?\{"
)
RETURN_SEVEN = re.compile(r"(?m)^[ \t]*return[ \t]+7\b")
MARKER = re.compile(r"\bDFB-(?:SOURCE|SINK):\s*[A-Za-z0-9][A-Za-z0-9_-]*")
PURE_INT_SOURCE = re.compile(r"\s*(?:return\s+)?7\s*;?\s*\Z")
PURE_SINK = re.compile(r"\s*print\s*\(\s*value\s*\)\s*;?\s*\Z")

SAFE_ENV_KEYS = {
    "PATH",
    "HOME",
    "TMPDIR",
    "DEVELOPER_DIR",
    "SDKROOT",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "XDG_CACHE_HOME",
    "SWIFT_MODULECACHE_PATH",
    "CLANG_MODULE_CACHE_PATH",
    "LLVM_MODULE_CACHE_PATH",
    "GCC_PRECOMPILE_PREFIX_HEADER",
    "CI",
    "GITHUB_ACTIONS",
    "GITHUB_SHA",
    "GITHUB_WORKFLOW",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_JOB",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REPOSITORY",
    "GITHUB_SERVER_URL",
    "GITHUB_WORKSPACE",
    "ImageOS",
    "ImageVersion",
}


class ValidationError(RuntimeError):
    """A fail-closed validation error."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int | None
    error: str | None = None


@dataclass(frozen=True)
class SwiftCase:
    directory: Path
    metadata: dict[str, Any]
    metadata_digest: str
    fixture_files: tuple[str, ...]
    source_records: tuple[dict[str, Any], ...]

    @property
    def case_id(self) -> str:
        return str(self.metadata["id"])

    @property
    def template_id(self) -> str:
        return str(self.metadata["template_id"])

    @property
    def polarity(self) -> str:
        return str(self.metadata["polarity"])

    @property
    def score_tier(self) -> str:
        return str(self.metadata["score_tier"])

    @property
    def fixture_paths(self) -> tuple[Path, ...]:
        return tuple(self.directory / name for name in self.fixture_files)


class Evidence:
    """Incrementally-written JSON evidence for one immutable validation run."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / "evidence.json"
        self.data: dict[str, Any] = {
            "format": "dataflowbench.swift-fixture-validation.v1",
            "status": "running",
            "started_at": utc_now(),
            "commands": [],
            "events": [],
            "metadata_digests": [],
            "cases": [],
        }
        self.write()

    def write(self) -> None:
        self.data["updated_at"] = utc_now()
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(self.data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def event(self, record: dict[str, Any]) -> None:
        self.data["events"].append(record)
        self.write()

    def command(self, record: dict[str, Any]) -> None:
        self.data["commands"].append(record)
        self.write()


def child_environment(profile: str) -> dict[str, str]:
    """Return the exact, non-secret environment passed to every child command."""

    if profile not in {"local", "github-xcode27"}:
        raise ValidationError(f"unknown validation profile: {profile!r}")
    parent = os.environ
    if profile == "github-xcode27":
        if parent.get("GITHUB_ACTIONS") != "true":
            raise ValidationError("github-xcode27 requires GITHUB_ACTIONS=true")
        for key in ("ImageOS", "ImageVersion"):
            if not parent.get(key):
                raise ValidationError(f"github-xcode27 requires non-empty {key}")
    return {key: parent[key] for key in sorted(SAFE_ENV_KEYS) if key in parent}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable_path(value: str) -> str:
    candidate = shutil.which(value) if "/" not in value else value
    if candidate is None:
        return value
    return str(Path(candidate).resolve())


def compiler_hash_path(invocation_path: str) -> Path:
    """Hash the Xcode target behind swiftc without changing the argv spelling."""

    target = Path(invocation_path).resolve()
    if not target.is_file():
        raise ValidationError(f"resolved swiftc target is not a regular file: {target}")
    return target


def create_evidence_directory(requested: Path | None, root: Path) -> Path:
    """Create a directory with exclusive creation; never reuse an old run."""

    if requested is not None:
        directory = requested.expanduser().resolve()
        directory.parent.mkdir(parents=True, exist_ok=True)
        try:
            directory.mkdir()
        except FileExistsError as error:
            raise ValidationError(
                f"evidence directory already exists; refusing to overwrite: {directory}"
            ) from error
        return directory

    base = root.expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for suffix in range(1000):
        name = f"{stamp}-{os.getpid()}" if suffix == 0 else f"{stamp}-{os.getpid()}-{suffix}"
        directory = base / name
        try:
            directory.mkdir()
        except FileExistsError:
            continue
        return directory
    raise ValidationError(f"could not allocate a fresh evidence directory under {base}")


def run_command(
    argv: Iterable[str],
    *,
    evidence: Evidence,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> CommandResult:
    """Run and retain one command, including failed launches and timeouts."""

    command = tuple(str(item) for item in argv)
    # Never inherit the parent environment implicitly.  Production callers
    # pass child_environment(profile), and tests pass an explicit mock env.
    command_env = dict(env or {})
    record: dict[str, Any] = {
        "argv": list(command),
        "cwd": str(cwd) if cwd is not None else None,
        "env": dict(sorted(command_env.items())),
        "stdout": "",
        "stderr": "",
        "exit": None,
    }
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            env=command_env,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        record["error"] = f"timeout after {timeout} seconds"
        record["stdout"] = decode_output(error.stdout)
        record["stderr"] = decode_output(error.stderr)
        evidence.command(record)
        return CommandResult(command, record["stdout"], record["stderr"], None, record["error"])
    except OSError as error:
        record["error"] = f"{type(error).__name__}: {error}"
        evidence.command(record)
        return CommandResult(command, "", "", None, record["error"])

    record["stdout"] = completed.stdout
    record["stderr"] = completed.stderr
    record["exit"] = completed.returncode
    evidence.command(record)
    return CommandResult(command, completed.stdout, completed.stderr, completed.returncode)


def decode_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def require_success(result: CommandResult, description: str) -> None:
    if result.returncode != 0:
        detail = result.error or f"exit {result.returncode}"
        raise ValidationError(
            f"{description} failed ({detail}); stderr={result.stderr.strip()!r}"
        )


def require_parts(output: str, parts: Iterable[str], description: str) -> None:
    missing = [part for part in parts if part not in output]
    if missing:
        raise ValidationError(f"{description} mismatch; missing exact values {missing!r}")


def require_exact_lines(output: str, patterns: Iterable[str], description: str) -> None:
    lines = {line.strip() for line in output.splitlines()}
    missing = [pattern for pattern in patterns if not any(re.fullmatch(pattern, line) for line in lines)]
    if missing:
        raise ValidationError(f"{description} mismatch; missing exact identity lines {missing!r}")


def witness_environment(
    swiftc: str | None,
    evidence: Evidence,
    *,
    profile: str,
    child_env: Mapping[str, str],
    runner: Callable[..., CommandResult] = run_command,
    command_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Witness the immutable compilation pin before inspecting any fixture."""

    paths = {
        name: executable_path(name)
        for name in ("xcodebuild", "sw_vers", "xcrun", "uname")
    }
    if command_paths:
        paths.update(command_paths)

    def invoke(argv: list[str]) -> CommandResult:
        return runner(argv, evidence=evidence, env=child_env)

    resolution: CommandResult | None = None
    if swiftc is None:
        resolution = invoke([paths["xcrun"], "--find", "swiftc"])
        require_success(resolution, "xcrun --find swiftc")
        resolved_lines = [line.strip() for line in resolution.stdout.splitlines() if line.strip()]
        if len(resolved_lines) != 1:
            raise ValidationError(f"xcrun --find swiftc returned {resolved_lines!r}; expected one path")
        # Preserve the lexical Xcode ``swiftc`` path.  Resolving this symlink
        # changes the driver's basename to ``swift-frontend`` and therefore
        # changes its mode.
        compiler = resolved_lines[0]
    else:
        # An explicit path is retained lexically for the same reason; the
        # default production path comes from xcrun above.
        compiler = swiftc
    compiler_file = compiler_hash_path(compiler)
    if not Path(compiler).is_file():
        raise ValidationError(f"swiftc path is not a regular file: {compiler}")
    compiler_sha = sha256_file(compiler_file)

    version = invoke([compiler, "--version"])
    require_success(version, "swiftc --version")
    require_exact_lines(version.stdout + "\n" + version.stderr, EXPECTED_SWIFT_VERSION_LINES, "swiftc --version")

    xcode = invoke([paths["xcodebuild"], "-version"])
    require_success(xcode, "xcodebuild -version")
    require_exact_lines(xcode.stdout, EXPECTED_XCODE_LINES, "xcodebuild -version")

    sw_vers = invoke([paths["sw_vers"]])
    require_success(sw_vers, "sw_vers")
    if profile == "local":
        require_exact_lines(
            sw_vers.stdout,
            (
                r"^ProductName:\s+macOS$",
                r"^ProductVersion:\s+27\.0$",
                r"^BuildVersion:\s+26A428$",
            ),
            "sw_vers",
        )
    else:
        require_parts(sw_vers.stdout, ("ProductName:", "macOS", "ProductVersion:", "BuildVersion:"), "sw_vers")
        version_match = re.search(r"^ProductVersion:\s*27\.[0-9]+(?:\.[0-9]+)?\s*$", sw_vers.stdout, re.MULTILINE)
        build_match = re.search(r"^BuildVersion:\s*\S+\s*$", sw_vers.stdout, re.MULTILINE)
        if version_match is None or build_match is None:
            raise ValidationError("github-xcode27 requires macOS 27.x and a retained non-empty build")

    architecture = invoke([paths["uname"], "-m"])
    require_success(architecture, "uname -m")
    if architecture.stdout.strip() != "arm64":
        raise ValidationError(f"host architecture mismatch: {architecture.stdout.strip()!r}")

    sdk_path_result = invoke([paths["xcrun"], "--sdk", "macosx", "--show-sdk-path"])
    require_success(sdk_path_result, "xcrun --sdk macosx --show-sdk-path")
    sdk_path = sdk_path_result.stdout.strip()
    if not sdk_path or not Path(sdk_path).is_dir():
        raise ValidationError(f"SDK path is missing or not a directory: {sdk_path!r}")

    sdk_version = invoke([paths["xcrun"], "--sdk", "macosx", "--show-sdk-version"])
    require_success(sdk_version, "xcrun --sdk macosx --show-sdk-version")
    if sdk_version.stdout.strip() != EXPECTED_SDK_VERSION:
        raise ValidationError(f"SDK version mismatch: {sdk_version.stdout.strip()!r}")

    sdk_build = invoke([paths["xcrun"], "--sdk", "macosx", "--show-sdk-build-version"])
    require_success(sdk_build, "xcrun --sdk macosx --show-sdk-build-version")
    if sdk_build.stdout.strip() != EXPECTED_SDK_BUILD:
        raise ValidationError(f"SDK build mismatch: {sdk_build.stdout.strip()!r}")

    target_info = invoke([compiler, "-print-target-info"])
    require_success(target_info, "swiftc -print-target-info")
    try:
        target_json = json.loads(target_info.stdout)
        observed_target = target_json["target"]["triple"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValidationError("swiftc -print-target-info did not expose target.triple") from error
    if observed_target != EXPECTED_TARGET:
        raise ValidationError(f"compiler target mismatch: {observed_target!r}")

    host_product = re.search(r"^ProductName:\s*(\S.*)$", sw_vers.stdout, re.MULTILINE)
    host_version = re.search(r"^ProductVersion:\s*(\S+)", sw_vers.stdout, re.MULTILINE)
    host_build = re.search(r"^BuildVersion:\s*(\S+)", sw_vers.stdout, re.MULTILINE)

    witness = {
        "profile": profile,
        "swiftc_resolution": list(resolution.argv) if resolution is not None else None,
        "compiler_path": compiler,
        "compiler_resolved_path": str(compiler_file),
        "compiler_sha256": compiler_sha,
        "swiftc_version": version.stdout,
        "swiftc_version_stderr": version.stderr,
        "xcodebuild_version": xcode.stdout,
        "sw_vers": sw_vers.stdout,
        "host_architecture": architecture.stdout,
        "host_os": host_product.group(1).strip() if host_product else None,
        "host_os_version": host_version.group(1) if host_version else None,
        "host_os_build": host_build.group(1) if host_build else None,
        "github_identity": {
            key: child_env[key]
            for key in ("GITHUB_ACTIONS", "GITHUB_SHA", "GITHUB_WORKFLOW", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "ImageOS", "ImageVersion")
            if key in child_env
        },
        "sdk_path": str(Path(sdk_path).resolve()),
        "sdk_version": sdk_version.stdout.strip(),
        "sdk_build": sdk_build.stdout.strip(),
        "target": observed_target,
        "expected": {
            "swiftc_version_parts": list(EXPECTED_SWIFT_VERSION_PARTS),
            "xcode_parts": list(EXPECTED_XCODE_PARTS),
            "host_sw_vers_parts": list(EXPECTED_SW_VERS_PARTS),
            "host_architecture": "arm64",
            "sdk_version": EXPECTED_SDK_VERSION,
            "sdk_build": EXPECTED_SDK_BUILD,
            "target": EXPECTED_TARGET,
        },
        "command_paths": paths,
    }
    evidence.data["witness"] = witness
    evidence.write()
    return witness


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    state = "code"
    escaped = False
    index = opening
    while index < len(text):
        character = text[index]
        next_character = text[index + 1] if index + 1 < len(text) else ""
        if state == "line-comment":
            if character == "\n":
                state = "code"
        elif state == "block-comment":
            if character == "*" and next_character == "/":
                state = "code"
                index += 1
        elif state == "string":
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                state = "code"
        else:
            if character == "/" and next_character == "/":
                state = "line-comment"
                index += 1
            elif character == "/" and next_character == "*":
                state = "block-comment"
                index += 1
            elif character == '"':
                state = "string"
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return index
        index += 1
    raise ValidationError("unclosed Swift function body")


def find_function(text: str, declaration: re.Pattern[str], label: str) -> list[dict[str, int]]:
    functions = []
    for match in declaration.finditer(text):
        opening = text.find("{", match.start(), match.end())
        if opening < 0:
            raise ValidationError(f"{label}: function declaration has no opening brace")
        functions.append(
            {
                "declaration": match.start(),
                "opening": opening,
                "closing": matching_brace(text, opening),
            }
        )
    return functions


def strip_comments(value: str) -> str:
    value = re.sub(r"//[^\n]*", "", value)
    return re.sub(r"/\*.*?\*/", "", value, flags=re.DOTALL)


def inspect_probe_convention(contents: Mapping[str, str]) -> dict[str, Any]:
    """Require the core worker's exact ``dfb_source``/``dfb_sink`` convention."""

    source_matches = []
    sink_matches = []
    for name, text in contents.items():
        source_matches.extend((name, item) for item in find_function(text, SOURCE_DECLARATION, "dfb_source"))
        sink_matches.extend((name, item) for item in find_function(text, SINK_DECLARATION, "dfb_sink"))
    if len(source_matches) != 1:
        raise ValidationError(f"expected exactly one dfb_source() -> Int definition, found {len(source_matches)}")
    if len(sink_matches) != 1:
        raise ValidationError(f"expected exactly one dfb_sink(_ value: Int) definition, found {len(sink_matches)}")

    source_name, source = source_matches[0]
    source_text = contents[source_name]
    source_body_start = source["opening"] + 1
    source_body = source_text[source_body_start : source["closing"]]
    source_body_without_comments = strip_comments(source_body)
    if PURE_INT_SOURCE.fullmatch(source_body_without_comments) is None:
        raise ValidationError(
            f"{source_name}: dfb_source body must be exactly the pure integer 7 or return 7"
        )
    source_literals = list(re.finditer(r"(?<![A-Za-z0-9_])7(?![A-Za-z0-9_])", source_body))
    if len(source_literals) != 1:
        raise ValidationError(f"{source_name}: dfb_source must contain exactly one numeric 7")

    sink_name, sink = sink_matches[0]
    sink_text = contents[sink_name]
    sink_body = sink_text[sink["opening"] + 1 : sink["closing"]]
    sink_body_without_comments = strip_comments(sink_body)
    if sink_body_without_comments.strip() and PURE_SINK.fullmatch(sink_body_without_comments) is None:
        raise ValidationError(f"{sink_name}: dfb_sink body must be empty or exactly print(value)")

    return {
        "source": {
            "file": source_name,
            "line": line_number(source_text, source["declaration"]),
            "value_line": line_number(source_text, source_body_start + source_literals[0].start()),
        },
        "sink": {
            "file": sink_name,
            "line": line_number(sink_text, sink["declaration"]),
        },
    }


def normalize_marker(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def validate_anchor_group(
    metadata: Mapping[str, Any],
    key: str,
    prefix: str,
    fixture_files: set[str],
    contents: Mapping[str, str],
) -> set[str]:
    anchors = metadata.get(key)
    if not isinstance(anchors, list) or not anchors:
        raise ValidationError(f"{metadata.get('id')}: {key} must be a non-empty list")
    markers: list[str] = []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise ValidationError(f"{metadata.get('id')}: {key} contains a non-object anchor")
        marker = normalize_marker(str(anchor.get("marker", "")))
        if not re.fullmatch(rf"{re.escape(prefix)}: [a-z0-9][a-z0-9_-]*", marker):
            raise ValidationError(f"{metadata.get('id')}: invalid {key} marker {marker!r}")
        file_name = anchor.get("file")
        if not isinstance(file_name, str) or file_name not in fixture_files:
            raise ValidationError(f"{metadata.get('id')}: {key} marker {marker!r} names undeclared file {file_name!r}")
        if marker in markers:
            raise ValidationError(f"{metadata.get('id')}: duplicate anchor marker {marker!r}")
        markers.append(marker)
        occurrences = contents[file_name].count(marker)
        if occurrences != 1:
            raise ValidationError(
                f"{metadata.get('id')}: {marker!r} occurs {occurrences} times in {file_name}; expected exactly once"
            )
        hint = anchor.get("line_hint")
        if hint is not None:
            actual = [line_number(contents[file_name], match.start()) for match in re.finditer(re.escape(marker), contents[file_name])]
            if actual != [hint]:
                raise ValidationError(
                    f"{metadata.get('id')}: {marker!r} line hint {hint} does not match {actual}"
                )
    return set(markers)


def validate_case_metadata(case_path: Path, metadata: dict[str, Any], metadata_digest: str) -> SwiftCase:
    case_directory = case_path.parent
    required = ("schema_version", "id", "template_id", "polarity", "score_tier", "track", "language", "model_profile", "fixture_files")
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValidationError(f"{case_path}: missing required metadata keys {missing}")
    if metadata["schema_version"] != 2:
        raise ValidationError(f"{case_path}: schema_version must be 2")
    if metadata["language"] != "swift" or metadata["track"] != "taint":
        raise ValidationError(f"{case_path}: expected language=swift and track=taint")
    if metadata["model_profile"] != "benchmark-controlled":
        raise ValidationError(f"{case_path}: Swift tranche must use benchmark-controlled profile")
    template = metadata["template_id"]
    tier = metadata["score_tier"]
    capability = metadata.get("expected_analysis_capability")
    if tier == "modeling" and (
        not isinstance(capability, dict) or MODULE_NAME not in str(capability.get("notes", ""))
    ):
        raise ValidationError(
            f"{case_path}: expected_analysis_capability.notes must bind module {MODULE_NAME}"
        )
    if template not in EXPECTED_TEMPLATE_TIER:
        raise ValidationError(f"{case_path}: unexpected Swift template {template!r}")
    if tier != EXPECTED_TEMPLATE_TIER[template]:
        raise ValidationError(f"{case_path}: {template} must use score_tier {EXPECTED_TEMPLATE_TIER[template]!r}")
    if metadata["polarity"] not in {"positive", "negative"}:
        raise ValidationError(f"{case_path}: invalid polarity {metadata['polarity']!r}")
    if metadata["polarity"] == "positive" and "negative_mechanism" in metadata:
        raise ValidationError(f"{case_path}: positive case must not declare negative_mechanism")
    if metadata["polarity"] == "negative" and not isinstance(metadata.get("negative_mechanism"), str):
        raise ValidationError(f"{case_path}: negative case must declare negative_mechanism")
    expected_id = f"dfb-taint-swift-{case_directory.name}"
    if metadata["id"] != expected_id:
        raise ValidationError(f"{case_path}: id {metadata['id']!r} does not match directory name")

    declared = metadata["fixture_files"]
    if not isinstance(declared, list) or not declared or any(not isinstance(item, str) for item in declared):
        raise ValidationError(f"{case_path}: fixture_files must be a non-empty string list")
    if len(set(declared)) != len(declared):
        raise ValidationError(f"{case_path}: fixture_files contains duplicate paths")
    fixture_paths: list[Path] = []
    for name in declared:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".swift":
            raise ValidationError(f"{case_path}: unsafe or non-Swift fixture path {name!r}")
        path = (case_directory / relative).resolve()
        try:
            path.relative_to(case_directory.resolve())
        except ValueError as error:
            raise ValidationError(f"{case_path}: fixture path escapes case directory: {name!r}") from error
        if not path.is_file():
            raise ValidationError(f"{case_path}: declared fixture is missing: {name}")
        fixture_paths.append(path)
    actual_paths = sorted(
        path.resolve().relative_to(case_directory.resolve()).as_posix()
        for path in case_directory.rglob("*.swift")
        if path.is_file()
    )
    if sorted(declared) != actual_paths:
        raise ValidationError(
            f"{case_path}: fixture_files must exactly cover Swift sources; declared={sorted(declared)!r}, actual={actual_paths!r}"
        )
    contents: dict[str, str] = {}
    source_records: list[dict[str, Any]] = []
    for name, path in zip(declared, fixture_paths):
        try:
            raw = path.read_bytes()
            contents[name] = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError(f"{path}: fixture is not valid UTF-8") from error
        source_records.append({"path": name, "sha256": sha256_bytes(raw), "bytes": len(raw)})

    source_markers = validate_anchor_group(metadata, "source_anchors", "DFB-SOURCE", set(declared), contents)
    sink_markers = validate_anchor_group(metadata, "sink_anchors", "DFB-SINK", set(declared), contents)
    if source_markers & sink_markers:
        raise ValidationError(f"{case_path}: source and sink marker sets overlap")
    actual_source_markers = {normalize_marker(match.group(0)) for text in contents.values() for match in MARKER.finditer(text) if match.group(0).startswith("DFB-SOURCE:")}
    actual_sink_markers = {normalize_marker(match.group(0)) for text in contents.values() for match in MARKER.finditer(text) if match.group(0).startswith("DFB-SINK:")}
    if actual_source_markers != source_markers:
        raise ValidationError(f"{case_path}: undeclared or missing DFB-SOURCE markers: expected={sorted(source_markers)!r}, actual={sorted(actual_source_markers)!r}")
    if actual_sink_markers != sink_markers:
        raise ValidationError(f"{case_path}: undeclared or missing DFB-SINK markers: expected={sorted(sink_markers)!r}, actual={sorted(actual_sink_markers)!r}")

    checkpoints = metadata.get("witness_checkpoints", [])
    if not isinstance(checkpoints, list) or len(set(checkpoints)) != len(checkpoints):
        raise ValidationError(f"{case_path}: witness_checkpoints must be a unique list")
    full_text = "\n".join(contents.values())
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, str) or not checkpoint.startswith("DFB-") or full_text.count(checkpoint) != 1:
            raise ValidationError(f"{case_path}: witness checkpoint is missing or duplicated: {checkpoint!r}")

    expected_flows = metadata.get("expected_flows")
    expected_nonflows = metadata.get("expected_nonflows")
    if not isinstance(expected_flows, list) or not isinstance(expected_nonflows, list):
        raise ValidationError(f"{case_path}: expected_flows and expected_nonflows must be lists")
    for collection_name, collection in (("expected_flows", expected_flows), ("expected_nonflows", expected_nonflows)):
        pairs = {(item.get("source"), item.get("sink")) for item in collection if isinstance(item, dict)}
        if len(pairs) != len(collection):
            raise ValidationError(f"{case_path}: {collection_name} contains duplicate or malformed pairs")
        for pair in pairs:
            if pair[0] not in source_markers or pair[1] not in sink_markers:
                raise ValidationError(f"{case_path}: {collection_name} references undeclared anchors: {pair!r}")
    if metadata["polarity"] == "positive" and (not expected_flows or expected_nonflows):
        raise ValidationError(f"{case_path}: positive case must have flows only")
    if metadata["polarity"] == "negative" and (expected_flows or not expected_nonflows):
        raise ValidationError(f"{case_path}: negative case must have nonflows only")

    provenance = metadata.get("fixture_provenance")
    if not isinstance(provenance, dict) or provenance.get("kind") != "authored" or provenance.get("license") != "MIT":
        raise ValidationError(f"{case_path}: Swift fixtures require authored MIT provenance")
    if "swift" not in str(provenance.get("revision", "")).lower():
        raise ValidationError(f"{case_path}: fixture provenance revision must name the Swift tranche")

    return SwiftCase(case_directory, metadata, metadata_digest, tuple(declared), tuple(source_records))


def load_inventory(cases_root: Path, evidence: Evidence | None = None, *, selected_paths: list[Path] | None = None) -> list[SwiftCase]:
    paths = sorted(selected_paths) if selected_paths is not None else (sorted(cases_root.rglob("case.json")) if cases_root.is_dir() else [])
    if not paths:
        raise ValidationError(f"no Swift case.json files found beneath {cases_root}")
    metadata_records: list[dict[str, Any]] = []
    cases: list[SwiftCase] = []
    for path in paths:
        raw = path.read_bytes()
        digest = sha256_bytes(raw)
        metadata_records.append({"path": str(path), "sha256": digest, "bytes": len(raw)})
        try:
            metadata = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValidationError(f"{path}: invalid JSON: {error}") from error
        if not isinstance(metadata, dict):
            raise ValidationError(f"{path}: metadata root must be an object")
        cases.append(validate_case_metadata(path, metadata, digest))
    if evidence is not None:
        evidence.data["metadata_digests"] = metadata_records

    if len(cases) != 90:
        raise ValidationError(f"expected exactly 90 Swift cases, found {len(cases)}")
    ids = [case.case_id for case in cases]
    duplicate_ids = sorted(identifier for identifier, count in Counter(ids).items() if count != 1)
    if duplicate_ids:
        raise ValidationError(f"duplicate case IDs: {duplicate_ids}")
    by_template: dict[str, list[SwiftCase]] = defaultdict(list)
    for case in cases:
        by_template[case.template_id].append(case)
    if set(by_template) != set(EXPECTED_TEMPLATE_TIER):
        raise ValidationError(
            f"template inventory mismatch; missing={sorted(set(EXPECTED_TEMPLATE_TIER) - set(by_template))}, "
            f"extra={sorted(set(by_template) - set(EXPECTED_TEMPLATE_TIER))}"
        )
    for template, expected_tier in EXPECTED_TEMPLATE_TIER.items():
        entries = by_template[template]
        if len(entries) != 2:
            raise ValidationError(f"{template}: expected one pair, found {len(entries)} cases")
        polarities = Counter(case.polarity for case in entries)
        if polarities != Counter({"positive": 1, "negative": 1}):
            raise ValidationError(f"{template}: expected one positive and one negative, found {dict(polarities)}")
        if any(case.score_tier != expected_tier for case in entries):
            raise ValidationError(f"{template}: pair has an unexpected score tier")
    if evidence is not None:
        evidence.data["cases"] = [
            {
                "id": case.case_id,
                "template_id": case.template_id,
                "score_tier": case.score_tier,
                "polarity": case.polarity,
                "metadata_sha256": case.metadata_digest,
                "sources": list(case.source_records),
            }
            for case in sorted(cases, key=lambda item: item.case_id)
        ]
        evidence.data["inventory"] = {
            "case_count": len(cases),
            "pair_count": len(by_template),
            "pairs_by_tier": {tier: len(templates) for tier, templates in EXPECTED_BY_TIER.items()},
        }
        evidence.write()
    return sorted(cases, key=lambda case: case.case_id)


def compile_sources(
    swiftc: str,
    source_paths: Iterable[Path],
    *,
    sdk_path: str,
    output_dir: Path,
    output_name: str,
    cwd: Path,
    evidence: Evidence,
    child_env: Mapping[str, str],
    case_id: str,
    instrumented: bool,
    source_value: int | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    module_cache = output_dir / "module-cache"
    binary = output_dir / output_name
    argv = [
        swiftc,
        "-swift-version",
        "6",
        "-Onone",
        "-sdk",
        sdk_path,
        "-target",
        EXPECTED_TARGET,
        "-module-name",
        MODULE_NAME,
        "-module-cache-path",
        str(module_cache),
        "-o",
        str(binary),
        *(str(path) for path in source_paths),
    ]
    result = run_command(
        argv,
        evidence=evidence,
        env=child_env,
        cwd=cwd,
        timeout=COMPILE_TIMEOUT_SECONDS,
    )
    evidence.event(
        {
            "kind": "compile",
            "case_id": case_id,
            "instrumented": instrumented,
            "source_value": source_value,
            "exit": result.returncode,
            "output": str(binary),
            "module_cache": str(module_cache),
        }
    )
    require_success(result, f"Swift compile/link for {case_id}")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValidationError(f"Swift compile/link for {case_id} did not produce an executable")
    return binary


def instrument_case(case: SwiftCase, destination: Path, source_value: int) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    originals: dict[str, str] = {}
    transformed: dict[str, str] = {}
    for name, source_path in zip(case.fixture_files, case.fixture_paths):
        raw = source_path.read_bytes()
        text = raw.decode("utf-8")
        originals[name] = text
        transformed[name] = text
        (destination / name).parent.mkdir(parents=True, exist_ok=True)
        (destination / name).write_bytes(raw)

    convention = inspect_probe_convention(originals)
    replacements: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    source_file = convention["source"]["file"]
    source_function = find_function(originals[source_file], SOURCE_DECLARATION, "dfb_source")[0]
    body_start = source_function["opening"] + 1
    source_body = originals[source_file][body_start : source_function["closing"]]
    source_literals = list(re.finditer(r"(?<![A-Za-z0-9_])7(?![A-Za-z0-9_])", source_body))
    if len(source_literals) != 1:
        raise ValidationError(f"{case.case_id}: temporary source substitution found {len(source_literals)} literals")
    literal_start = body_start + source_literals[0].start()
    replacements[source_file].append((literal_start, literal_start + 1, str(source_value)))

    sink_file = convention["sink"]["file"]
    sink_function = find_function(originals[sink_file], SINK_DECLARATION, "dfb_sink")[0]
    sink_body = originals[sink_file][sink_function["opening"] + 1 : sink_function["closing"]]
    if PURE_SINK.fullmatch(strip_comments(sink_body)) is None:
        replacements[sink_file].append(
            (sink_function["opening"] + 1, sink_function["closing"], "\n    print(value)\n")
        )

    differences = []
    for name, text in originals.items():
        updated = text
        for start, end, replacement in sorted(replacements.get(name, []), reverse=True):
            updated = updated[:start] + replacement + updated[end:]
        transformed[name] = updated
        (destination / name).write_text(updated, encoding="utf-8")
        differences.append(
            {
                "path": name,
                "before_sha256": sha256_bytes(text.encode("utf-8")),
                "after_sha256": sha256_bytes(updated.encode("utf-8")),
                "diff": "".join(
                    difflib.unified_diff(
                        text.splitlines(keepends=True),
                        updated.splitlines(keepends=True),
                        fromfile=name,
                        tofile=name,
                    )
                ),
            }
        )
    return {"source_value": source_value, "convention": convention, "differences": differences}


def parse_single_integer(stdout: str, case_id: str) -> int:
    lines = stdout.strip().splitlines()
    if len(lines) != 1:
        raise ValidationError(f"{case_id}: instrumented sink must print exactly one integer, got {lines!r}")
    try:
        return int(lines[0].strip())
    except ValueError as error:
        raise ValidationError(f"{case_id}: instrumented sink output is not an integer: {lines[0]!r}") from error


def check_control_observation(
    polarity: str, observed: Mapping[int, int], case_id: str = "Swift control"
) -> None:
    if set(observed) != set(SOURCE_VALUES):
        raise ValidationError(f"{case_id}: control did not produce both source values: {dict(observed)!r}")
    dependent = observed[SOURCE_VALUES[0]] != observed[SOURCE_VALUES[1]]
    expected_dependent = polarity == "positive"
    if dependent != expected_dependent:
        raise ValidationError(
            f"{case_id}: source values {SOURCE_VALUES} observed sink values "
            f"{observed[SOURCE_VALUES[0]]}, {observed[SOURCE_VALUES[1]]}; "
            f"expected {'dependence' if expected_dependent else 'independence'}"
        )


def run_control(
    case: SwiftCase,
    swiftc: str,
    sdk_path: str,
    evidence: Evidence,
    child_env: Mapping[str, str],
) -> None:
    contents = {name: path.read_text(encoding="utf-8") for name, path in zip(case.fixture_files, case.fixture_paths)}
    convention = inspect_probe_convention(contents)
    evidence.event({"kind": "probe-convention", "case_id": case.case_id, **convention})
    observed: dict[int, int] = {}
    with tempfile.TemporaryDirectory(prefix="dfb-swift-control-") as temporary:
        temporary_root = Path(temporary)
        for source_value in SOURCE_VALUES:
            instrumented_root = temporary_root / str(source_value)
            instrumentation = instrument_case(case, instrumented_root, source_value)
            evidence.event(
                {
                    "kind": "instrumentation",
                    "case_id": case.case_id,
                    **instrumentation,
                }
            )
            source_paths = tuple(instrumented_root / name for name in case.fixture_files)
            binary = compile_sources(
                swiftc,
                source_paths,
                sdk_path=sdk_path,
                output_dir=instrumented_root / "build",
                output_name="fixture",
                cwd=instrumented_root,
                evidence=evidence,
                child_env=child_env,
                case_id=case.case_id,
                instrumented=True,
                source_value=source_value,
            )
            execution = run_command(
                [str(binary)],
                evidence=evidence,
                env=child_env,
                cwd=instrumented_root,
                timeout=CONTROL_TIMEOUT_SECONDS,
            )
            require_success(execution, f"instrumented execution for {case.case_id} source {source_value}")
            observed[source_value] = parse_single_integer(execution.stdout, case.case_id)
        check_control_observation(case.polarity, observed, case.case_id)
        evidence.event(
            {
                "kind": "control-result",
                "case_id": case.case_id,
                "observed": observed,
                "expected": "dependence" if case.polarity == "positive" else "independence",
            }
        )


def validate(
    root: Path,
    swiftc: str | None,
    evidence: Evidence,
    *,
    profile: str,
    child_env: Mapping[str, str],
    cases_root: Path | None = None,
) -> list[SwiftCase]:
    witness = witness_environment(
        swiftc,
        evidence,
        profile=profile,
        child_env=child_env,
    )
    fixture_root = cases_root or root / "cases" / "taint" / "swift"
    # This validator retains v1's 90-case compilation/control contract. New
    # immutable populations have separate validation, never widen historical runs.
    selected = None if cases_root else [root / entry["path"] for entry in
        json.loads((root / "populations/swift-synthetic-v1.json").read_text())["cases"]]
    cases = load_inventory(fixture_root, evidence, selected_paths=selected)
    evidence.data["policy"] = {
        "compile": "all 90 cases, all declared .swift inputs, -swift-version 6 -Onone explicit SDK and target",
        "controls": "core plus dfb-template-one-hop-relay only; source values 7 and 19",
        "compile_only": "modeling plus dfb-template-modeled-external-summary; no abstract model verification",
    }
    evidence.write()
    for index, case in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] compile/link {case.case_id}", flush=True)
        with tempfile.TemporaryDirectory(prefix="dfb-swift-compile-") as temporary:
            compile_sources(
                witness["compiler_path"],
                case.fixture_paths,
                sdk_path=witness["sdk_path"],
                output_dir=Path(temporary),
                output_name="fixture",
                cwd=case.directory,
                evidence=evidence,
                child_env=child_env,
                case_id=case.case_id,
                instrumented=False,
                source_value=None,
            )
    for index, case in enumerate(cases, 1):
        if case.score_tier == "core" or case.template_id == "dfb-template-one-hop-relay":
            print(f"[{index}/{len(cases)}] bounded control {case.case_id}", flush=True)
            run_control(case, witness["compiler_path"], witness["sdk_path"], evidence, child_env)
        else:
            evidence.event(
                {
                    "kind": "control-skipped",
                    "case_id": case.case_id,
                    "reason": "model-summary and modeling cases are compile-only; no abstract model verification",
                }
            )
    return cases


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cases-root", type=Path)
    parser.add_argument("--profile", choices=("local", "github-xcode27"), default="local")
    parser.add_argument("--output", "--evidence-dir", dest="output", type=Path)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("evidence/swift-fixtures"),
        help="parent for unique evidence directories when --output is omitted",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    try:
        evidence_root = args.evidence_root
        if not evidence_root.is_absolute():
            evidence_root = root / evidence_root
        evidence_directory = create_evidence_directory(args.output, evidence_root)
        evidence = Evidence(evidence_directory)
        environment = child_environment(args.profile)
        evidence.data["profile"] = args.profile
        evidence.data["validator"] = {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        }
        evidence.data["execution_environment"] = {
            "allowlist": sorted(SAFE_ENV_KEYS),
            "sanitized": environment,
        }
        evidence.write()
        cases_root = args.cases_root
        if cases_root is not None and not cases_root.is_absolute():
            cases_root = root / cases_root
        cases = validate(
            root,
            None,
            evidence,
            profile=args.profile,
            child_env=environment,
            cases_root=cases_root,
        )
        evidence.data["status"] = "passed"
        evidence.data["finished_at"] = utc_now()
        evidence.write()
        print(f"validated Swift fixtures: {len(cases)} cases, evidence={evidence.path}")
        return 0
    except (ValidationError, OSError) as error:
        if "evidence" in locals():
            evidence.data["status"] = "failed"
            evidence.data["error"] = str(error)
            evidence.data["finished_at"] = utc_now()
            evidence.write()
            print(f"Swift fixture validation failed; evidence={evidence.path}", file=sys.stderr)
        print(f"Swift fixture validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
