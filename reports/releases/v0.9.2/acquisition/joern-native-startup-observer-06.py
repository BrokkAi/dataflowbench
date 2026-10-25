#!/usr/bin/env python3
"""Private, source-bound JVM startup observer for the Joern 4.0.660 controls.

This is a preparation artifact. It loads the retained repair candidate only
after checking its exact bytes, patches one private engine for one scoped call,
and records the JVM processes that actually ran. A small Java premain witness
is used for the final ``System.getProperty`` value; shell uptake text is kept
as ordinary stderr evidence and is never treated as property proof.

No analyzer is run by this module's tests. A real invocation additionally
requires the separately reviewed, digest-bound witness jar.
"""

from __future__ import annotations

import argparse
import base64
import calendar
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any, Callable, Mapping


ORIGINAL_SCRIPT = "scripts/joern_capability_repair_v092_03.py"
ORIGINAL_SCRIPT_SHA256 = "8e3d986f20c2262045d8473837d1bf5a56b61da1bc23fee6e778bd0ac47d2b51"
OBSERVER_SCHEMA = "v092-joern-native-startup-observer/v6"
RECEIPT_SCHEMA = "v092-joern-native-startup-receipt/v6"
SUMMARY_SCHEMA = "v092-joern-native-startup-observation-summary/v6"
POLICY_SCHEMA = "v092-joern-jvm-startup-policy/v4"
WITNESS_SCHEMA = "v092-joern-jvm-startup-witness/v4"
AGENT_ENV = "DFB_JOERN_STARTUP_WITNESS_DIR"
AGENT_CLASS = "dfb.joern.StartupWitnessAgent"
AGENT_PATH = "/Users/dave/.codex/worktrees/9f01/dataflowbench/reports/releases/v0.9.2/acquisition/joern-startup-witness-agent-04.jar"
AGENT_SHA256 = "ba02fe9c3782c377279e60198e4b4e1631d9d3431a4ce5fc7376d8dc6eff4eac"

# This identity is deliberately distinct from the retained v1 policy and the
# v2 prospective candidate. Updating it requires a new reviewed artifact.
STARTUP_POLICY_V4: dict[str, Any] = {
    "schema": POLICY_SCHEMA,
    "java_property": "user.home",
    "option_source": "JAVA_TOOL_OPTIONS",
    "option_template": "-Duser.home={capture_home} -javaagent:{witness_agent_jar}",
    "home_relative": "jvm-home",
    "predef_relative": ".scala-repl-pp.sc",
    "predef_expectation": "absent",
    "ambient_options_cleared": ["_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "CLASSPATH"],
    "retained_java_opts": "-Xmx512m -XX:ActiveProcessorCount=2",
    "agent_directory_env": AGENT_ENV,
    "agent_class": AGENT_CLASS,
    "agent_jar": {"path": AGENT_PATH, "sha256": AGENT_SHA256},
    "property_witness": "in-process-System.getProperty",
}

SELECTED_ENV_FIELDS = (
    "JAVA_HOME", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS",
    "CLASSPATH", "JAVA_OPTS", "HOME", "TMPDIR", "PATH", "SWIFTASTGEN_BIN",
    "LANG", "LC_ALL", AGENT_ENV,
)
AMBIENT_FIELDS = ("_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "CLASSPATH")
USER_HOME_RE = re.compile(r"user[.]home", re.IGNORECASE)
PID_FILE_RE = re.compile(r"^jvm-([0-9]+)[.]json$")

LAUNCHER_REFS = {
    "joern": (
        "execution-state/v092/tools/joern/joern-cli/joern",
        "0df7e8db4282ef2c6fc37998917aca694176e23192de5f0c631511d993e99736",
    ),
    "bridge": (
        "execution-state/v092/tools/joern/joern-cli/bin/repl-bridge",
        "4506312bb53bcc5eb9c93b982fda29cabe2777297ec30e4c65a006bb5759ecc7",
    ),
    "frontend": (
        "execution-state/v092/tools/joern/joern-cli/frontends/swiftsrc2cpg/bin/swiftsrc2cpg",
        "6aaf5a4f53088cb9a1bd515247a92bf8b29b20e2bcd72a684677fb806f626ca4",
    ),
    "query": (
        "adapters/joern/swift-common-v2/v0.9.2/query.sc",
        "8f944335630a79f5cbb444c0921d0515e565c9acff022cd1740fbb66371b8f07",
    ),
}


class ObservationError(ValueError):
    """The startup observation is not safe to interpret."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ObservationError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular(path: Path, description: str) -> None:
    require(path.is_file() and not path.is_symlink(),
            f"{description} is not a regular file: {path}")


def _ref(path: Path) -> dict[str, Any]:
    _regular(path, "captured output")
    return {"path": str(path.resolve()), "sha256": sha(path)}


def load_original(root: Path) -> ModuleType:
    """Load the retained candidate only after proving exact bytes."""
    path = (Path(root).resolve() / ORIGINAL_SCRIPT).resolve()
    _regular(path, "retained startup candidate")
    require(sha(path) == ORIGINAL_SCRIPT_SHA256,
            "retained startup candidate changed; observer must stop")
    scripts = str(path.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "joern_capability_repair_v092_03_observer_v4_pinned", path
    )
    require(spec is not None and spec.loader is not None,
            "cannot load retained startup candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    retained_policy = copy.deepcopy(module.JVM_STARTUP_POLICY)
    require(retained_policy.get("schema") == "v092-joern-jvm-startup-policy/v1",
            "retained v1 startup policy schema changed")
    # Explicit in-memory adapter for successor decision files. It never
    # rewrites the retained source or historical v1 evidence, and a v1
    # decision cannot pass under this v4 observer.
    require(STARTUP_POLICY_V4.get("schema") == POLICY_SCHEMA and
            STARTUP_POLICY_V4.get("property_witness") == "in-process-System.getProperty",
            "successor startup policy is not the sealed v4 shape")
    module.RETAINED_JVM_STARTUP_POLICY_V1 = retained_policy
    module.JVM_STARTUP_POLICY = copy.deepcopy(STARTUP_POLICY_V4)
    return module


def validate_launcher_topology(root: Path) -> dict[str, Any]:
    """Bind the shell launchers without making a false no-fork claim."""
    root = Path(root).resolve()
    refs: dict[str, dict[str, Any]] = {}
    contents: dict[str, str] = {}
    for role, (relative, expected) in LAUNCHER_REFS.items():
        path = root / relative
        _regular(path, f"launcher source {role}")
        observed = sha(path)
        require(observed == expected, f"launcher source drift: {relative}")
        refs[role] = {"path": relative, "sha256": observed}
        contents[role] = path.read_text(errors="strict")
    for role in ("bridge", "frontend"):
        text = contents[role]
        require(len(re.findall(r"java_version_check", text)) == 2,
                f"{role} launcher version-check topology changed")
        require(len(re.findall(r'execRunner \"\$java_cmd\"', text)) == 1,
                f"{role} launcher exec topology changed")
    return {
        "schema": "v092-joern-launch-topology/v2",
        "version_check_java_count": 1,
        "exec_java_count": 1,
        "query_forked_script_java_count": "dynamic-required",
        "sources": refs,
        "roles": {
            "version": ["bridge", "version-check"],
            "typecheck": [],
            "frontend": ["frontend", "version-check"],
            "query": ["bridge", "query-script-fork", "version-check"],
        },
        "required_roles": {
            "version": ["bridge"],
            "typecheck": [],
            "frontend": ["frontend"],
            "query": ["bridge", "query-script-fork"],
        },
        "property_witness": {
            "status": "agent-required",
            "required": "A bounded in-process System.getProperty(\"user.home\") witness for every observed semantic Java process.",
            "uptake_is_not_property_proof": True,
        },
    }


def _policy_agent(policy: Mapping[str, Any], *, sealed: bool = True) -> tuple[Path, str]:
    agent = policy.get("agent_jar")
    require(isinstance(agent, dict), "startup policy agent_jar is malformed")
    path = Path(str(agent.get("path", ""))).resolve()
    digest = str(agent.get("sha256", ""))
    require(path.is_absolute() and path.name.endswith(".jar"),
            "startup witness jar path must be absolute")
    if sealed:
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                "startup witness jar digest is not sealed")
    return path, digest


def _expected_option(policy: Mapping[str, Any], home: Path) -> str:
    require(policy.get("schema") == POLICY_SCHEMA, "startup policy schema changed")
    require(policy.get("java_property") == "user.home" and
            policy.get("option_source") == "JAVA_TOOL_OPTIONS" and
            policy.get("home_relative") == "jvm-home" and
            policy.get("predef_relative") == ".scala-repl-pp.sc" and
            policy.get("agent_directory_env") == AGENT_ENV,
            "startup policy fields changed")
    template = policy.get("option_template")
    require(template == "-Duser.home={capture_home} -javaagent:{witness_agent_jar}",
            "startup option template changed")
    agent_path, _digest = _policy_agent(policy, sealed=False)
    return template.format(capture_home=str(home.resolve()),
                           witness_agent_jar=str(agent_path))


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _unb64(value: Any, field: str) -> str:
    require(isinstance(value, str), f"witness {field} is not base64 text")
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
        return decoded.decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise ObservationError(f"witness {field} is not valid base64 UTF-8") from exc


def _host_start_identity(pid: int) -> str | None:
    """Read the observer process birth identity using the retained helper."""
    try:
        import swift_v2_process  # type: ignore
        value = swift_v2_process.start_identity(pid, None)
        return value if isinstance(value, str) and value else None
    except (ImportError, OSError, RuntimeError, ValueError):
        return None


def _parse_java_birth(payload: Mapping[str, Any], description: str,
                      prefix: str = "process_start") -> tuple[int, int]:
    """Return Java ProcessHandle start epoch seconds/nanoseconds exactly."""
    identity = payload.get(prefix + "_identity")
    seconds = payload.get(prefix + "_epoch_seconds")
    nanos = payload.get(prefix + "_epoch_nanos")
    require(isinstance(identity, str) and identity.endswith("Z"),
            f"{description} Java birth identity is not an Instant")
    require(isinstance(seconds, int) and isinstance(nanos, int) and
            0 <= nanos < 1_000_000_000,
            f"{description} Java birth epoch fields are malformed")
    # Keep the raw ISO identity and numeric fields; this check only binds them.
    # Do not use datetime.fromisoformat here: Python silently truncates a
    # Java Instant with nine fractional digits to microseconds.  Java emits
    # zero, three, six, or nine fractional digits, so parse the exact text.
    from datetime import datetime
    match = re.fullmatch(
        r"([0-9]{4,})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
        r"(?:[.]([0-9]{3}|[0-9]{6}|[0-9]{9}))?Z", identity
    )
    require(match is not None, f"{description} Java birth Instant is malformed")
    assert match is not None
    try:
        year, month, day, hour, minute, second = (int(value) for value in match.groups()[:6])
        datetime(year, month, day, hour, minute, second)
        parsed_seconds = calendar.timegm((year, month, day, hour, minute, second))
    except (OverflowError, ValueError) as exc:
        raise ObservationError(f"{description} Java birth Instant is malformed") from exc
    require(parsed_seconds == seconds,
            f"{description} Java birth Instant and epoch seconds disagree")
    fraction = match.group(7) or ""
    parsed_nanos = int(fraction.ljust(9, "0")) if fraction else 0
    require(parsed_nanos == nanos,
            f"{description} Java birth Instant and epoch nanoseconds disagree")
    return seconds, nanos


def _native_birth_comparison(java_seconds: int, java_nanos: int,
                             native_identity: str, description: str) -> tuple[bool, str]:
    """Compare Java birth with the full native identity at documented precision.

    macOS ``start_identity`` retains seconds and microseconds, while the
    observed Java ``ProcessHandle.startInstant`` is millisecond aligned.  The
    comparison therefore makes the Java-millisecond projection explicit while
    retaining the unmodified native identity in every receipt.  A future Java
    runtime with microsecond precision can use the exact branch; a Java value
    with sub-microsecond precision fails closed rather than being rounded.
    """
    match = re.fullmatch(r"([0-9]+):([0-9]+)", native_identity)
    if match is None:
        raise ObservationError(f"{description} native birth identity has unsupported precision")
    native_seconds = int(match.group(1))
    native_micros = int(match.group(2))
    require(0 <= native_micros < 1_000_000,
            f"{description} native birth microseconds are malformed")
    if java_nanos % 1_000_000 == 0:
        return (
            native_seconds == java_seconds and
            native_micros // 1_000 == java_nanos // 1_000_000,
            "java-millisecond-floor",
        )
    if java_nanos % 1_000 == 0:
        return (
            native_seconds == java_seconds and
            native_micros == java_nanos // 1_000,
            "java-microsecond-exact",
        )
    return False, "java-submicrosecond-unsupported"


def _native_birth_matches(java_seconds: int, java_nanos: int,
                          native_identity: str, description: str) -> bool:
    return _native_birth_comparison(java_seconds, java_nanos,
                                    native_identity, description)[0]


def _process_identity_map(record: Mapping[str, Any]) -> dict[int, str]:
    rows = record.get("tracked_descendants", [])
    require(isinstance(rows, list), "process record tracked_descendants is malformed")
    result: dict[int, str] = {}
    for row in rows:
        require(isinstance(row, dict), "tracked process identity is malformed")
        try:
            pid = int(row["pid"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ObservationError("tracked process identity has no integer pid") from exc
        identity = row.get("start_identity")
        require(pid > 0 and isinstance(identity, str) and bool(identity),
                "tracked process identity is incomplete")
        require(pid not in result, f"tracked process pid duplicated: {pid}")
        result[pid] = identity
    return result


def _classify_command(command: str | None) -> str:
    if not command:
        return "unclassified"
    if re.search(r"(?:^|\s)-version(?:$|\s)", command):
        return "version-check"
    if "io.joern.joerncli.console.ReplBridge" in command:
        return "bridge"
    if ("io.joern.swiftsrc2cpg-4.0.660-launcher.jar" in command or
            "io.joern.swiftsrc2cpg" in command):
        return "frontend"
    if ("replpp.scripting.NonForkingScriptRunner" in command or
            "replpp.scripting.ScriptRunner" in command):
        return "query-script-fork"
    return "unclassified"


class StartupObserver:
    """One scoped observer for one future controls/execute invocation."""

    def __init__(self, root: Path, output: Path, policy: Mapping[str, Any], *,
                 sidecar_root: Path | None = None,
                 process_runner: Callable[..., dict[str, Any]] | None = None,
                 static_check: bool = True) -> None:
        self.root = Path(root).resolve()
        self.output = Path(output).resolve()
        self.policy = copy.deepcopy(dict(policy))
        self.sidecar_root = (sidecar_root or
                             self.output.parent / (self.output.name + ".startup-observation")).resolve()
        self.process_runner = process_runner
        self.static_check = static_check
        self.events: list[dict[str, Any]] = []
        self._event_number = 0
        self.topology = validate_launcher_topology(self.root) if static_check else {
            "schema": "v092-joern-launch-topology/synthetic",
            "roles": {
                "version": ["bridge", "version-check"],
                "typecheck": [],
                "frontend": ["frontend", "version-check"],
                "query": ["bridge", "query-script-fork", "version-check"],
            },
            "required_roles": {
                "version": ["bridge"], "typecheck": [], "frontend": ["frontend"],
                "query": ["bridge", "query-script-fork"],
            },
        }
        require(self.policy.get("schema") == POLICY_SCHEMA,
                "startup observer requires the v4 policy")
        if static_check:
            agent_path, digest = _policy_agent(self.policy)
            _regular(agent_path, "startup witness jar")
            require(sha(agent_path) == digest, "startup witness jar digest changed")
        self._require_fresh_sidecar()
        self.sidecar_root.mkdir(parents=True)

    def _require_fresh_sidecar(self) -> None:
        require(not self.sidecar_root.exists() and not self.sidecar_root.is_symlink(),
                "startup observation sidecar namespace already exists")
        require(self.output.is_relative_to(self.root),
                "startup observation output escaped root")

    @property
    def home(self) -> Path:
        return self.output / str(self.policy["home_relative"])

    @property
    def predef(self) -> Path:
        return self.home / str(self.policy["predef_relative"])

    def ensure_home(self) -> Path:
        require(not self.home.exists() or
                (self.home.is_dir() and not self.home.is_symlink()),
                "startup JVM home is not a directory")
        self.home.mkdir(parents=True, exist_ok=True)
        require(not self.predef.exists() and not self.predef.is_symlink(),
                "reviewed Scala predef is present before invocation")
        return self.home

    def _predef_state(self) -> dict[str, Any]:
        exists = self.predef.exists() or self.predef.is_symlink()
        return {
            "path": str(self.predef),
            "present": exists,
            "symlink": self.predef.is_symlink(),
            "bytes": self.predef.stat().st_size if self.predef.is_file() else None,
            "sha256": sha(self.predef) if self.predef.is_file() and not self.predef.is_symlink() else None,
        }

    def _selected_environment(self, env: Mapping[str, str] | None) -> dict[str, Any]:
        require(env is not None and hasattr(env, "get"),
                "process invocation has no environment")
        return {key: env.get(key) for key in SELECTED_ENV_FIELDS}

    def _roles_for(self, name: str, argv: list[str]) -> list[str]:
        require(name in self.topology["roles"], f"unknown observed phase {name}")
        if self.static_check:
            if name == "typecheck":
                require(argv and argv[-1] == "-typecheck",
                        "typecheck argv does not identify Swift compiler")
            elif name == "frontend":
                require(argv and argv[0].endswith("/swiftsrc2cpg"),
                        "frontend argv does not identify Swift frontend launcher")
            else:
                require(argv and argv[0].endswith("/joern"),
                        f"{name} argv does not identify Joern launcher")
                if name == "query":
                    require("--script" in argv, "query argv lacks --script")
        return list(self.topology["roles"][name])

    def _validate_invocation(self, argv: list[str], directory: Path, name: str,
                             env: Mapping[str, str] | None,
                             cwd: Path | None) -> tuple[dict[str, Any], str]:
        require(isinstance(argv, list) and all(isinstance(item, str) for item in argv),
                f"{name} argv is not a string list")
        require(isinstance(directory, Path), f"{name} directory must be a Path")
        require(cwd is None or Path(cwd).resolve() == directory.resolve(),
                f"{name} cwd differs from process output directory")
        values = self._selected_environment(env)
        for token in argv:
            require(not USER_HOME_RE.search(token),
                    f"{name} argv contains a user.home override")
        require(env is not None, f"{name} invocation has no environment")
        for key, value in env.items():
            if isinstance(key, str) and USER_HOME_RE.search(key):
                raise ObservationError(f"{name} environment key contains a user.home override: {key}")
            if isinstance(value, str) and USER_HOME_RE.search(value) and key != "JAVA_TOOL_OPTIONS":
                raise ObservationError(f"{name} environment contains a user.home override: {key}")
        home = self.ensure_home()
        expected_option = _expected_option(self.policy, home)
        require(values.get("JAVA_TOOL_OPTIONS") == expected_option,
                f"{name} JAVA_TOOL_OPTIONS does not bind the exact capture home and witness jar")
        require(values.get("JAVA_OPTS") == self.policy.get("retained_java_opts"),
                f"{name} JAVA_OPTS drifted from the reviewed value")
        for key in AMBIENT_FIELDS:
            require(values.get(key) in (None, ""),
                    f"{name} retained ambient injection in {key}")
        require(values.get("JAVA_HOME") and values.get("HOME") and values.get("TMPDIR") and
                values.get("PATH"), f"{name} selected process environment is incomplete")
        require(values.get(AGENT_ENV), f"{name} witness directory was not propagated")
        return values, expected_option

    def _event_dir(self, number: int, name: str) -> Path:
        event_dir = self.sidecar_root / "events" / f"{number:03d}-{name}"
        require(not event_dir.exists() and not event_dir.is_symlink(),
                f"startup event namespace already exists: {event_dir}")
        event_dir.mkdir(parents=True)
        return event_dir

    def _witnesses(self, event_dir: Path, phase: str,
                   record: Mapping[str, Any], expected_parent_pid: int | None,
                   expected_parent_identity: str | None) -> list[dict[str, Any]]:
        require(event_dir.is_dir() and not event_dir.is_symlink(),
                "startup witness directory is not a regular directory")
        tracked = _process_identity_map(record)
        seen_pids: set[int] = set()
        witnesses: list[dict[str, Any]] = []
        files = sorted(event_dir.glob("jvm-*.json"))
        require(len(files) <= 128, "startup witness count exceeds 128")
        for path in files:
            _regular(path, "startup witness")
            match = PID_FILE_RE.fullmatch(path.name)
            require(match is not None, f"startup witness filename is malformed: {path.name}")
            require(path.stat().st_size <= 1024 * 1024, "startup witness exceeds 1MiB")
            payload = json.loads(path.read_text())
            require(isinstance(payload, dict) and payload.get("schema") == WITNESS_SCHEMA,
                    f"startup witness schema mismatch: {path.name}")
            require(isinstance(payload.get("agent_version"), str) and
                    bool(payload.get("agent_version")),
                    f"startup witness agent version missing: {path.name}")
            pid = payload.get("pid")
            require(isinstance(pid, int) and pid > 0 and int(match.group(1)) == pid,
                    f"startup witness pid does not bind filename: {path.name}")
            require(pid not in seen_pids, f"startup witness pid duplicated: {pid}")
            seen_pids.add(pid)
            identity = payload.get("process_start_identity")
            require(isinstance(identity, str) and bool(identity),
                    f"startup witness process identity missing: {path.name}")
            birth_seconds, birth_nanos = _parse_java_birth(payload, path.name)
            native_identity = tracked.get(pid)
            command_present_hint = payload.get("java_command_present")
            role_hint = (
                _classify_command(_unb64(payload.get("java_command_b64"), "java_command_b64"))
                if command_present_hint is True else
                "version-check" if command_present_hint is False else
                "unclassified"
            )
            birth_verified = native_identity is not None
            birth_comparison = None
            if native_identity is not None:
                matches, birth_comparison = _native_birth_comparison(
                    birth_seconds, birth_nanos, native_identity, path.name
                )
                require(matches,
                        f"startup witness Java/native birth mismatch: {path.name}")
            else:
                # Very short java -version probes may have exited before the
                # bounded tracker sampled them. They remain diagnostic-only;
                # semantic bridge/frontend/fork JVMs must be tracked exactly.
                require(role_hint == "version-check",
                        f"semantic JVM birth was not tracked: {path.name}")
            parent_pid = payload.get("parent_pid")
            require(parent_pid is None or isinstance(parent_pid, int) and parent_pid >= 0,
                    f"startup witness parent pid malformed: {path.name}")
            parent_identity = payload.get("parent_start_identity")
            if parent_pid not in (None, 0):
                require(isinstance(parent_identity, str) and bool(parent_identity),
                        f"startup witness parent identity missing: {path.name}")
                parent_seconds, parent_nanos = _parse_java_birth(payload, path.name + " parent", "parent_start")
                if parent_pid in tracked:
                    parent_matches, _parent_comparison = _native_birth_comparison(
                        parent_seconds, parent_nanos, tracked[parent_pid],
                        path.name + " parent"
                    )
                    require(parent_matches,
                            f"startup witness parent pid/birth is not tracked: {path.name}")
                else:
                    require(expected_parent_pid is not None and parent_pid == expected_parent_pid,
                            f"startup witness parent pid is outside the invocation: {path.name}")
                    require(expected_parent_identity is not None,
                            f"startup witness host parent birth is unavailable: {path.name}")
                    parent_matches, _parent_comparison = _native_birth_comparison(
                        parent_seconds, parent_nanos, expected_parent_identity,
                        path.name + " host parent"
                    )
                    require(parent_matches,
                            f"startup witness host parent birth is not exact: {path.name}")
            if native_identity is None:
                # A short version probe is retained only as diagnostic evidence
                # when its premain receipt still binds to the exact invocation
                # parent.  Without that parent correlation it could be an
                # unrelated ambient JVM and cannot be admitted as evidence.
                require(parent_pid not in (None, 0),
                        f"untracked version witness lacks exact parent correlation: {path.name}")
            runtime_start = payload.get("runtime_start_millis")
            require(isinstance(runtime_start, int) and runtime_start > 0,
                    f"startup witness runtime start identity missing: {path.name}")
            command_present = payload.get("java_command_present")
            require(isinstance(command_present, bool),
                    f"startup witness command presence missing: {path.name}")
            command = (_unb64(payload.get("java_command_b64"), "java_command_b64")
                       if command_present else None)
            class_path = _unb64(payload.get("java_class_path_b64"), "java_class_path_b64")
            home = _unb64(payload.get("user_home_b64"), "user_home_b64")
            predef_path = _unb64(payload.get("predef_path_b64"), "predef_path_b64")
            witness_directory = _unb64(payload.get("witness_directory_b64"),
                                       "witness_directory_b64")
            require(witness_directory == str(event_dir.resolve()),
                    f"startup witness directory does not bind this phase: {path.name}")
            require(home == str(self.home.resolve()),
                    f"startup witness final user.home differs from capture home: {path.name}")
            require(predef_path == str(self.predef),
                    f"startup witness predef path differs from reviewed path: {path.name}")
            require(payload.get("predef_present") is False and
                    payload.get("predef_symlink") is False,
                    f"startup witness observed a present or symlink predef: {path.name}")
            # ``java -version`` on the reviewed launcher has no
            # ``sun.java.command``.  Keep that receipt diagnostic-only under
            # the version role; semantic roles still require their exact
            # command-bearing bridge/frontend/fork witnesses above.
            role = _classify_command(command) if command_present else "version-check"
            witnesses.append({
                "path": str(path), "sha256": sha(path), "pid": pid,
                "parent_pid": parent_pid, "process_start_identity": identity,
                "native_process_start_identity": native_identity,
                "birth_verified": birth_verified,
                "birth_comparison": birth_comparison,
                "process_start_epoch_seconds": birth_seconds,
                "process_start_epoch_nanos": birth_nanos,
                "runtime_start_millis": runtime_start, "role": role,
                "java_command": command, "java_class_path_b64": _b64(class_path),
                "user_home": home, "predef_path": predef_path,
            })
            self._last_witnesses = list(witnesses)
        unclassified = [row for row in witnesses if row["role"] == "unclassified"]
        require(not unclassified,
                f"startup witness command is unclassified: {unclassified[0]['path'] if unclassified else 'none'}")
        allowed = set(self.topology["roles"][phase])
        require(all(row["role"] in allowed for row in witnesses),
                f"startup witness role is not allowed for phase {phase}")
        required = set(self.topology.get("required_roles", {}).get(phase, []))
        observed = {row["role"] for row in witnesses}
        require(required <= observed,
                f"startup witness missing required semantic roles for {phase}: {sorted(required - observed)}")
        if phase == "typecheck":
            require(not witnesses, "typecheck unexpectedly launched a witnessed JVM")
        return witnesses

    def _failure_evidence(self, event_dir: Path, phase: str, directory: Path,
                          record: dict[str, Any] | None,
                          parent_pid: int, parent_identity: str | None
                          ) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[dict[str, str]]]:
        """Retain bounded failure diagnostics without turning them into a result."""
        raw: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        observed_record = record if isinstance(record, dict) else None
        try:
            files = sorted(event_dir.glob("jvm-*.json"))
            require(len(files) <= 128, "failure witness count exceeds 128")
            for path in files:
                _regular(path, "failure startup witness")
                require(path.stat().st_size <= 1024 * 1024,
                        "failure startup witness exceeds 1MiB")
                raw.append(_ref(path))
        except Exception as exc:
            errors.append({"stage": "raw-witness-capture", "type": type(exc).__name__, "message": str(exc)})
        command = directory / f"{phase}.command.json"
        if record is None and (command.exists() or command.is_symlink()):
            try:
                _regular(command, "failure process record")
                require(command.stat().st_size <= 2 * 1024 * 1024,
                        "failure process record exceeds 2MiB")
                observed_record = json.loads(command.read_text())
                require(isinstance(observed_record, dict), "failure process record is not an object")
            except Exception as exc:
                observed_record = None
                errors.append({"stage": "process-record-capture", "type": type(exc).__name__, "message": str(exc)})
        witness_record = record if isinstance(record, dict) else observed_record
        if witness_record is not None:
            try:
                self._witnesses(event_dir, phase, witness_record, parent_pid, parent_identity)
            except Exception as exc:
                errors.append({"stage": "witness-validation", "type": type(exc).__name__, "message": str(exc)})
        return raw, observed_record, errors

    def _record_sidecar(self, receipt: dict[str, Any]) -> None:
        path = self.sidecar_root / f"{self._event_number:03d}-{receipt['phase']}.json"
        with path.open("x") as stream:
            stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        receipt["sidecar"] = {"path": str(path), "sha256": sha(path)}
        self.events.append(receipt)

    def observed_run(self, argv: list[str], directory: Path, name: str, timeout: float,
                     measure: bool = False, env: Mapping[str, str] | None = None,
                     cwd: Path | None = None) -> dict[str, Any]:
        """Observe one process invocation while preserving its runner result."""
        self._event_number += 1
        event_dir = self._event_dir(self._event_number, name)
        directory = Path(directory).resolve()
        cwd_path = Path(cwd).resolve() if cwd is not None else directory
        before = self._predef_state()
        values: dict[str, Any] = self._selected_environment(env) if env is not None else {}
        observed_env = dict(env) if env is not None else None
        if observed_env is not None:
            observed_env[AGENT_ENV] = str(event_dir)
            values = self._selected_environment(observed_env)
        record: dict[str, Any] | None = None
        error: BaseException | None = None
        violations: list[str] = []
        witnesses: list[dict[str, Any]] = []
        self._last_witnesses = []
        expected_parent_pid = os.getpid()
        expected_parent_identity = _host_start_identity(expected_parent_pid)
        try:
            values, _expected = self._validate_invocation(
                argv, directory, name, observed_env, cwd_path
            )
            if self.process_runner is None:
                raise ObservationError("no process runner supplied to private observer")
            record = self.process_runner(argv, directory, name, timeout,
                                         measure=measure, env=observed_env, cwd=cwd_path)
            require(isinstance(record, dict), f"{name} process runner returned a non-record")
            witnesses = self._witnesses(event_dir, name, record,
                                         expected_parent_pid, expected_parent_identity)
        except BaseException as exc:
            error = exc
            if not witnesses:
                witnesses = list(getattr(self, "_last_witnesses", []))
        stdout = directory / f"{name}.stdout"
        stderr = directory / f"{name}.stderr"
        command = directory / f"{name}.command.json"
        raw_witnesses: list[dict[str, Any]] = []
        failure_record = None
        failure_errors: list[dict[str, str]] = []
        if error is not None:
            raw_witnesses, failure_record, failure_errors = self._failure_evidence(
                event_dir, name, directory, record, expected_parent_pid, expected_parent_identity
            )
            witnesses = list(self._last_witnesses)
        try:
            after = self._predef_state()
        except Exception as exc:
            if error is None:
                raise
            after = {"present": None, "symlink": None, "observation_error": str(exc)}
            failure_errors.append({"stage": "predef-after", "type": type(exc).__name__, "message": str(exc)})
        if before["present"] or before["symlink"]:
            violations.append("predef-present-before")
        if after["present"] or after["symlink"]:
            violations.append("predef-present-after")
        if error is not None and isinstance(error, ObservationError):
            violations.append(str(error))
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "observer_schema": OBSERVER_SCHEMA,
            "phase": name,
            "argv": list(argv),
            "cwd": str(cwd_path),
            "output_directory": str(directory),
            "event_witness_directory": str(event_dir),
            "timeout_seconds": timeout,
            "measurement_wrapper": ["/usr/bin/time", "-l"] if measure else [],
            "environment": values,
            "tracked_processes": record.get("tracked_descendants", []) if record else [],
            "invocation_parent": {"pid": expected_parent_pid,
                                  "start_identity": expected_parent_identity},
            "process_record": _ref(command) if command.is_file() and not command.is_symlink() else None,
            "stdout": _ref(stdout) if stdout.is_file() and not stdout.is_symlink() else None,
            "stderr": _ref(stderr) if stderr.is_file() and not stderr.is_symlink() else None,
            "predef_before": before,
            "predef_after": after,
            "jvm_witnesses": witnesses,
            "jvm_witness_files": raw_witnesses,
            "failure_process_record": failure_record,
            "failure_evidence_errors": failure_errors,
            "property_witness": {
                "status": "failure-only" if error is not None else "exact-in-process-System.getProperty" if witnesses else "unavailable",
                "claim": "Only the private Java premain witness proves final user.home.",
            },
            "result": None if error is not None else record,
            "error": {"type": type(error).__name__, "message": str(error)} if error else None,
            "violations": violations,
        }
        try:
            self._record_sidecar(receipt)
        except Exception as sidecar_error:
            if error is None:
                raise
            raise error from sidecar_error
        if error is not None:
            raise error
        if violations:
            raise ObservationError("startup observation failed: " + "; ".join(violations))
        return record  # type: ignore[return-value]

    def summary(self) -> dict[str, Any]:
        failed = [event for event in self.events if event.get("error") or event.get("violations")]
        return {
            "schema": SUMMARY_SCHEMA,
            "observer": OBSERVER_SCHEMA,
            "policy": copy.deepcopy(self.policy),
            "event_count": len(self.events),
            "phases": [event.get("phase") for event in self.events],
            "status": "failed" if failed else "startup-agent-observed",
            "qualification_safe": not failed and bool(self.events),
            "property_witness": {
                "status": "exact-in-process-System.getProperty" if not failed and self.events else "unavailable",
                "required": "Actual Java semantic processes must emit digest-bound agent witnesses.",
            },
            "failures": [{"phase": event.get("phase"), "error": event.get("error"),
                          "violations": event.get("violations", [])} for event in failed],
            "sidecar_root": str(self.sidecar_root),
            "topology": self.topology,
        }

    def write_summary(self) -> dict[str, Any]:
        summary = self.summary()
        path = self.sidecar_root / "summary.json"
        with path.open("x") as stream:
            stream.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        summary["summary"] = {"path": str(path), "sha256": sha(path)}
        return summary


class ScopedObservation:
    """Patch one private engine and restore all objects, including the runner."""

    def __init__(self, common: ModuleType, observer: StartupObserver) -> None:
        self.common = common
        self.observer = observer
        self.original_factory = common.private_engine
        self.patched: list[tuple[Any, Any, Any, Any]] = []
        self.previous_process_runner = observer.process_runner
        self.bound_process_runner: Any | None = None

    def _patch_engine(self, engine: Any) -> None:
        if any(row[0] is engine for row in self.patched):
            return
        original_env = engine.env_for
        original_phase = engine.phase
        candidate_process_run = engine.process.run
        observer_function = self.observer.observed_run.__func__
        already_observed = (
            getattr(candidate_process_run, "__self__", None) is self.observer and
            getattr(candidate_process_run, "__func__", None) is observer_function
        )
        if already_observed:
            require(self.bound_process_runner is not None,
                    "engine process runner was already observed without an original binding")
            original_process_run = self.bound_process_runner
        else:
            original_process_run = candidate_process_run
        if self.bound_process_runner is None:
            self.bound_process_runner = original_process_run
        else:
            require(self.bound_process_runner is original_process_run,
                    "private engine process runners differ across factory entries")
        if self.observer.process_runner is None:
            self.observer.process_runner = original_process_run
        elif self.observer.process_runner is not original_process_run:
            raise ObservationError("private engine process runner differs from the bound observer runner")

        def env_for(runtime: dict[str, Any]) -> dict[str, str]:
            values = dict(original_env(runtime))
            home = self.observer.ensure_home()
            option = _expected_option(self.observer.policy, home)
            values["JAVA_TOOL_OPTIONS"] = option
            return values

        def phase(*args: Any, **kwargs: Any) -> Any:
            require("invoke" not in kwargs,
                    "phase caller attempted to bypass the startup observer")
            return original_phase(*args, invoke=self.observer.observed_run, **kwargs)

        engine.env_for = env_for
        engine.phase = phase
        engine.process.run = self.observer.observed_run
        self.patched.append((engine, original_env, original_phase, original_process_run))

    def factory(self, *args: Any, **kwargs: Any) -> Any:
        bundle = self.original_factory(*args, **kwargs)
        require(isinstance(bundle, dict) and "runner" in bundle,
                "private engine factory returned an invalid bundle")
        self._patch_engine(bundle["runner"])
        return bundle

    def __enter__(self) -> "ScopedObservation":
        self.common.private_engine = self.factory
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.common.private_engine = self.original_factory
        for engine, original_env, original_phase, original_process_run in reversed(self.patched):
            engine.env_for = original_env
            engine.phase = original_phase
            engine.process.run = original_process_run
        self.patched.clear()
        self.bound_process_runner = None
        self.observer.process_runner = self.previous_process_runner


def _runner_context(root: Path, old: ModuleType, result: dict[str, Any], observer: StartupObserver):
    runner = result["runner"]
    old._assert_canonical_historical_binding(Path(root).resolve())
    common = runner.common
    old_constant = getattr(runner, "EXECUTION_PLAN_PATH", None)
    return runner, old_constant, ScopedObservation(common, observer)


def _summary_finally(observer: StartupObserver, active_error: BaseException | None,
                     holder: dict[str, Any]) -> None:
    try:
        holder["value"] = observer.write_summary()
    except BaseException:
        if active_error is None:
            raise


def controls(root: Path, output: str, **kwargs: Any) -> dict[str, Any]:
    """Expose retained controls with scoped startup observation."""
    root = Path(root).resolve()
    old = load_original(root)
    result = old.validate_bootstrap_inputs(root, **kwargs)
    output_path = Path(output).resolve()
    observer = StartupObserver(root, output_path, STARTUP_POLICY_V4)
    runner, old_constant, scope = _runner_context(root, old, result, observer)
    holder: dict[str, Any] = {}
    active_error: BaseException | None = None
    try:
        runner.EXECUTION_PLAN_PATH = result["new_plan_path"]
        with scope:
            run = runner.run_controls(root, result["new_plan_path"], output_path)
    except BaseException as exc:
        active_error = exc
        raise
    finally:
        if old_constant is not None:
            runner.EXECUTION_PLAN_PATH = old_constant
        _summary_finally(observer, active_error, holder)
    return {"run": run, "startup_observation": holder["value"]}


def execute(root: Path, output: str, **kwargs: Any) -> dict[str, Any]:
    """Expose retained execute with the same scoped startup observation."""
    root = Path(root).resolve()
    old = load_original(root)
    result = old.validate_repair_inputs(root, **kwargs)
    output_path = Path(output).resolve()
    observer = StartupObserver(root, output_path, STARTUP_POLICY_V4)
    runner, old_constant, scope = _runner_context(root, old, result, observer)
    holder: dict[str, Any] = {}
    active_error: BaseException | None = None
    try:
        runner.EXECUTION_PLAN_PATH = result["new_plan_path"]
        with scope:
            run = runner.execute(root, result["new_plan_path"], output_path)
        reports_path = (root / old.REPORTS_PATH).resolve()
        _regular(reports_path, "retained Joern reports exporter")
        require(sha(reports_path) == old.REPORTS_SHA256,
                "retained Joern reports exporter changed")
        scripts = str(reports_path.parent)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        reports_spec = importlib.util.spec_from_file_location(
            "joern_normal_reports_v092_observer_v4_pinned", reports_path
        )
        require(reports_spec is not None and reports_spec.loader is not None,
                "cannot load retained Joern reports exporter")
        reports = importlib.util.module_from_spec(reports_spec)
        reports_spec.loader.exec_module(reports)
        normal_output = (output_path / "normal").resolve()
        require(normal_output.is_relative_to(root),
                "Joern report output escaped the repository root")
        reports.export(root, result["new_plan_path"], run, normal_output)
    except BaseException as exc:
        active_error = exc
        raise
    finally:
        if old_constant is not None:
            runner.EXECUTION_PLAN_PATH = old_constant
        _summary_finally(observer, active_error, holder)
    return {"run": run, "startup_observation": holder["value"]}


def preflight(root: Path, **kwargs: Any) -> dict[str, Any]:
    old = load_original(Path(root).resolve())
    return old.preflight(Path(root).resolve(), **kwargs)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("preflight", "controls", "execute"):
        command = sub.add_parser(mode)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--plan", required=True)
        command.add_argument("--evidence", required=True)
        command.add_argument("--plan-sha256")
        command.add_argument("--evidence-sha256")
        if mode != "preflight":
            command.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    common = {
        "new_plan_path": args.plan,
        "evidence_path": args.evidence,
        "expected_new_plan_sha256": args.plan_sha256,
        "expected_evidence_sha256": args.evidence_sha256,
    }
    try:
        if args.mode == "preflight":
            result = preflight(args.root, **common)
        elif args.mode == "controls":
            result = controls(args.root, args.output, **common)
        else:
            result = execute(args.root, args.output, **common)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ObservationError, OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
