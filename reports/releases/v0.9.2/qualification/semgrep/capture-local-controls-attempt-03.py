#!/usr/bin/env python3
"""Run local-only Semgrep v0.9.2 capability and activation controls."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "reports/releases/v0.9.2/qualification/semgrep/attempt-03-local-scan"
OLD = ROOT / "reports/releases/v0.9.2/qualification/semgrep/attempt-02-local-scan"
STATE = ROOT / "execution-state/v092/semgrep-state/attempt-03"
SEMGREP = ROOT / "execution-state/v092/tools/semgrep-env/bin/semgrep"
CORE = ROOT / "execution-state/v092/tools/semgrep-env/lib/python3.15/site-packages/semgrep/bin/semgrep-core"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": digest(raw)}


def run(identifier: str, argv: list[str], env_overrides: dict[str, str], timeout: int, expectation: str) -> dict:
    proc = subprocess.Popen(
        argv,
        cwd=ROOT,
        env={**os.environ, **env_overrides},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    started = time.monotonic()
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            stdout, stderr = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
    out_path = EVIDENCE / "stdout" / f"{identifier}.bin"
    err_path = EVIDENCE / "stderr" / f"{identifier}.bin"
    out_path.write_bytes(stdout)
    err_path.write_bytes(stderr)
    record = {
        "id": identifier,
        "argv": argv,
        "cwd": str(ROOT),
        "timeout_seconds": timeout,
        "budget_kind": "wall-clock process-group timeout; no OS memory cap applied",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "timed_out": timed_out,
        "exit_code": proc.returncode,
        "expectation": expectation,
        "environment_overrides": env_overrides,
        "stdout": file_record(out_path),
        "stderr": file_record(err_path),
    }
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        record["json_summary"] = {
            "errors": payload.get("errors", []),
            "results": [
                {
                    "check_id": x.get("check_id"),
                    "path": x.get("path"),
                    "start_line": x.get("start", {}).get("line"),
                }
                for x in payload["results"]
                if isinstance(x, dict)
            ],
        }
    return record


def hit(record: dict, rule_id: str, target: Path) -> bool:
    summary = record.get("json_summary")
    if not summary or summary.get("errors"):
        return False
    target = target.resolve()
    return any(
        item.get("check_id", "").endswith(rule_id)
        and Path(item.get("path", "/not-a-real-path")).resolve() == target
        for item in summary["results"]
    )


def main() -> int:
    if (EVIDENCE / "qualification.json").exists():
        raise SystemExit(f"qualification receipt already exists: {EVIDENCE / 'qualification.json'}")
    (EVIDENCE / "stdout").mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "stderr").mkdir(exist_ok=True)
    configs = EVIDENCE / "configs"
    configs.mkdir()
    for name in ("model-sanitizer-default-functions.yaml", "csharp-single-function-taint.yaml"):
        shutil.copyfile(OLD / "configs" / name, configs / name)
    env_paths = {
        "home": STATE / "home",
        "cache": STATE / "cache",
        "settings": STATE / "settings",
        "version_cache": STATE / "version-cache",
    }
    for path in env_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    settings_file = env_paths["settings"] / "settings.yaml"
    if not settings_file.exists():
        settings_file.write_text("has_shown_metrics_notification: true\n", encoding="utf-8")
    env = {
        "PATH": f"{ROOT / 'execution-state/v092/tools/semgrep-env/bin'}:/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": str(env_paths["home"]),
        "XDG_CACHE_HOME": str(env_paths["cache"]),
        "SEMGREP_SETTINGS_FILE": str(settings_file),
        "SEMGREP_LOG_FILE": str(STATE / "semgrep.log"),
        "SEMGREP_VERSION_CACHE_PATH": str(env_paths["version_cache"]),
        "SEMGREP_ENABLE_VERSION_CHECK": "0",
        "SEMGREP_SEND_METRICS": "off",
        "SSL_CERT_FILE": "/etc/ssl/cert.pem",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "ALL_PROXY": "",
        "NO_PROXY": "*",
        "http_proxy": "",
        "https_proxy": "",
        "all_proxy": "",
        "no_proxy": "*",
    }
    commands = [
        run("semgrep-version", ["/usr/bin/env", "semgrep", "--version", "--disable-version-check"], env, 20, "identify pinned Semgrep CLI")
    ]
    prefix = [
        "/usr/bin/env", "semgrep", "scan", "--disable-version-check", "--metrics=off",
        "--oss-only", "--jobs=1", "--no-git-ignore", "--json",
    ]
    model = run(
        "model-sanitizer-default-functions",
        prefix + ["--config", str(configs / "model-sanitizer-default-functions.yaml"),
                  str(ROOT / "cases/taint/python/model-sanitizer-selectivity-positive"),
                  str(ROOT / "cases/taint/python/model-sanitizer-selectivity-negative")],
        env, 60, "declared sanitizer suppresses the negative while undeclared sibling remains visible",
    )
    commands.append(model)
    native: dict[str, dict] = {}
    native_rules = {
        "python": ("insecure-hash-function", "main.py"),
        "java": ("use-snakeyaml-constructor", "Main.java"),
        "javascript": ("detect-eval-with-expression", "main.js"),
    }
    for language, (rule, filename) in native_rules.items():
        pos = EVIDENCE / "controls" / language / "positive"
        neg = EVIDENCE / "controls" / language / "negative"
        record = run(
            f"native-{language}-profile",
            prefix + ["--config", str(ROOT / f"adapters/semgrep/native/v0.9.2/{language}/rules"), str(pos), str(neg)],
            env, 60, f"native {language} profile finds its positive rule and rejects the near-miss",
        )
        commands.append(record)
        native[language] = record
    csharp = run(
        "csharp-single-function-taint",
        prefix + ["--config", str(configs / "csharp-single-function-taint.yaml"),
                  str(ROOT / "cases/taint/csharp/direct-positive"),
                  str(ROOT / "cases/taint/csharp/direct-negative")],
        env, 60, "basic C# single-function taint positive and unrelated-value near-miss",
    )
    commands.append(csharp)

    observations = {
        "model_sanitizer_positive": hit(model, "dfb-taint-python-modeling", ROOT / "cases/taint/python/model-sanitizer-selectivity-positive/clean.py"),
        "model_sanitizer_negative": hit(model, "dfb-taint-python-modeling", ROOT / "cases/taint/python/model-sanitizer-selectivity-negative/clean.py"),
    }
    for language, (rule, filename) in native_rules.items():
        observations[f"native_{language}_positive"] = hit(native[language], rule, EVIDENCE / "controls" / language / "positive" / filename)
        observations[f"native_{language}_negative"] = hit(native[language], rule, EVIDENCE / "controls" / language / "negative" / filename)
    observations["csharp_positive"] = hit(csharp, "dataflowbench-csharp-ce-single-function-taint-probe", ROOT / "cases/taint/csharp/direct-positive/DirectFlow.cs")
    observations["csharp_negative"] = hit(csharp, "dataflowbench-csharp-ce-single-function-taint-probe", ROOT / "cases/taint/csharp/direct-negative/DirectFlow.cs")
    expected = {
        "model_sanitizer_positive": True, "model_sanitizer_negative": False,
        "native_python_positive": True, "native_python_negative": False,
        "native_java_positive": True, "native_java_negative": False,
        "native_javascript_positive": True, "native_javascript_negative": False,
        "csharp_positive": True, "csharp_negative": False,
    }
    failures = [name for name, value in expected.items() if observations.get(name) is not value]
    native_files = []
    for language in native_rules:
        for path in sorted((ROOT / f"adapters/semgrep/native/v0.9.2/{language}").rglob("*")):
            if path.is_file():
                native_files.append(file_record(path))
    core = CORE.read_bytes()
    version = (EVIDENCE / "stdout/semgrep-version.bin").read_bytes().decode("utf-8", "replace").strip()
    report = {
        "schema": "semgrep-v092-local-qualification/2",
        "qualification_kind": "non-scored compatibility and activation controls; fixed-matrix denominator/results unchanged",
        "status": "completed" if not failures and all(not item["timed_out"] for item in commands) else "completed-with-failures",
        "environment": {
            "offline": True, "all_configs_local": True, "auto_config": False,
            "metrics": "off", "version_check": "disabled", "proxy_variables_cleared": True,
            "python_bytecode_writes_disabled": True,
        },
        "tool": {
            "semgrep_cli_version": version,
            "semgrep_cli": file_record(SEMGREP),
            "semgrep_core": {"path": str(CORE.relative_to(ROOT)), "bytes": len(core), "sha256": digest(core),
                             "reported_version": "unavailable: `semgrep-core --version` rejected in attempt-02"},
        },
        "inputs": {
            "configs": [file_record(p) for p in sorted(configs.iterdir()) if p.is_file()],
            "native_rule_files": native_files,
            "custom_control_files": [file_record(p) for p in sorted((EVIDENCE / "controls").rglob("*")) if p.is_file()],
        },
        "observed_rule_hits": observations,
        "expected_rule_hits": expected,
        "failed_expectations": failures,
        "commands": commands,
        "limitations": [
            "These bounded controls are compatibility/activation evidence, not scored analyzer rows.",
            "A C# hit demonstrates basic single-function CE support only; it does not authorize expanding the fixed refresh matrix or preregistering a new adapter.",
        ],
        "controller": file_record(Path(__file__).resolve()),
    }
    (EVIDENCE / "qualification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failed_expectations": failures, "qualification": str(EVIDENCE / 'qualification.json')}, indent=2))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
