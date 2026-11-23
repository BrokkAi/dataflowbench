#!/usr/bin/env python3
"""Prepare a pinned, offline CPython 3.15 ruamel.yaml.clib build.

Default mode records verified source/build inputs and a prospective manifest.
The native compile is gated behind --dispatch-after-quiet and is intentionally
not run during the current busy-host preparation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile


REPO = Path(__file__).resolve().parents[5]
RECEIPT = Path(__file__).resolve().parent
ACQUISITION = REPO / "reports/releases/v0.9.2/acquisition"
PIP_CACHE = Path.home() / "Library/Caches/pip/http-v2"
PYTHON_LINK = Path("/opt/homebrew/opt/python@3.15/bin/python3.15")
PYTHON_BINARY = Path(
    "/opt/homebrew/Cellar/python@3.15/3.15.0/Frameworks/"
    "Python.framework/Versions/3.15/bin/python3.15"
)
PYTHON_SHA256 = "15c72833c1ffc09bc4e05d1e1866784d126721ad548d9c4d8f943641262535cb"
RUAMEL_SDIST_SHA256 = "46e4cc8c43ef6a94885f72512094e482114a8a706d3c555a34ed4b0d20200600"
RUAMEL_SDIST_URL = (
    "https://files.pythonhosted.org/packages/ea/97/60fda20e2fb54b83a61ae14648b0817c8f5d84a3821e40bfbdae1437026a/"
    "ruamel_yaml_clib-0.2.15.tar.gz"
)
RUAMEL_CP310_WHEEL_SHA256 = "9b6f7d74d094d1f3a4e157278da97752f16ee230080ae331fcc219056ca54f77"
EXPECTED_NATIVE_PATH = "lib/python3.15/site-packages/_ruamel_yaml.cpython-315-darwin.so"
EXPECTED_NATIVE_SHA256 = "7b6574966296fb64b0af6cca234c04c6df9ca776b80dc8ae13fc82b4eccd9883"
BUILD_TOOL_PINS = {"setuptools": "84.0.0", "wheel": "0.48.0"}
BUILD_TOOL_SHA256 = {
    ("setuptools", "84.0.0"): "51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670",
    ("wheel", "0.48.0"): "3217dcc807155e45db462d7ef2431f5ddda0d7273b700d05a67b271ceb1287ab",
}
SOURCE_LINK = RECEIPT / "source-archives/ruamel_yaml_clib-0.2.15.tar.gz"
BUILD_WHEELHOUSE = RECEIPT / "build-wheelhouse"
BUILD_ENV = RECEIPT / "ruamel-build-env"
BUILD_OUTPUT = RECEIPT / "ruamel-built-wheel"
LOG = RECEIPT / "ruamel-native-build.log"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def body_metadata(path: Path) -> tuple[str, str, list[str]] | None:
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            metadata = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
            wheel = next((name for name in names if name.endswith(".dist-info/WHEEL")), None)
            if not metadata or not wheel:
                return None
            fields = {}
            for line in archive.read(metadata).decode("utf-8", "replace").splitlines():
                if line.startswith(("Name:", "Version:")):
                    key, value = line.split(":", 1)
                    fields[key] = value.strip()
            tags = [
                line[5:].strip()
                for line in archive.read(wheel).decode("utf-8", "replace").splitlines()
                if line.startswith("Tag: ")
            ]
            if not fields.get("Name") or not fields.get("Version"):
                return None
            return fields["Name"], fields["Version"], tags
    except (BadZipFile, OSError):
        return None


def find_build_wheel(name: str, version: str) -> tuple[Path, list[str]]:
    for path in PIP_CACHE.rglob("*.body"):
        metadata = body_metadata(path)
        if metadata and canonical(metadata[0]) == canonical(name) and metadata[1] == version:
            digest = sha256(path)
            expected = BUILD_TOOL_SHA256[(name, version)]
            if digest != expected:
                continue
            return path, metadata[2]
    raise FileNotFoundError(f"retained wheel artifact missing: {name}=={version}")


def parse_source() -> dict:
    source_body = Path(
        "/Users/dave/Library/Caches/pip/http-v2/d/d/e/0/d/"
        "dde0d323489b78e0857e313758587b15631d8517177e472c43347fff.body"
    )
    if not source_body.is_file() or sha256(source_body) != RUAMEL_SDIST_SHA256:
        raise ValueError("retained ruamel 0.2.15 sdist is missing or differs from PyPI SHA-256")
    SOURCE_LINK.parent.mkdir(parents=True, exist_ok=True)
    if SOURCE_LINK.exists() or SOURCE_LINK.is_symlink():
        if not SOURCE_LINK.is_symlink() or SOURCE_LINK.resolve(strict=True) != source_body:
            raise FileExistsError(f"unexpected source archive already present: {SOURCE_LINK}")
    else:
        SOURCE_LINK.symlink_to(source_body)
    import io
    import tarfile

    with tarfile.open(fileobj=io.BytesIO(source_body.read_bytes()), mode="r:*") as archive:
        project = archive.extractfile("ruamel.yaml.clib-0.2.15/pyproject.toml").read().decode()
        setup = archive.extractfile("ruamel.yaml.clib-0.2.15/setup.py").read().decode()
        source_members = [
            name for name in archive.getnames()
            if name.startswith("ruamel.yaml.clib-0.2.15/")
            and name.endswith((".c", ".h", ".pyx", ".pxd"))
        ]
    requirements_match = 'requires = ["setuptools", "wheel"]' in project
    if not requirements_match:
        raise ValueError("ruamel sdist build-system requirements changed")
    classifier_cap = re.search(r"max_supported_minor_3_version\s*=\s*(\d+)", setup)
    return {
        "cache_body": str(source_body),
        "link": str(SOURCE_LINK),
        "filename": "ruamel_yaml_clib-0.2.15.tar.gz",
        "url": RUAMEL_SDIST_URL,
        "sha256": sha256(source_body),
        "size_bytes": source_body.stat().st_size,
        "pypi_page": "https://pypi.org/project/ruamel.yaml.clib/0.2.15/",
        "build_system_requirements": ["setuptools", "wheel"],
        "cython_required": False,
        "c_sources_in_sdist": source_members,
        "setup_classifier_max_minor": int(classifier_cap.group(1)) if classifier_cap else None,
        "classifier_cap_is_build_blocker": False,
    }


def stage_build_wheels() -> list[dict]:
    BUILD_WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name, version in BUILD_TOOL_PINS.items():
        source, tags = find_build_wheel(name, version)
        filename = f"{name}-{version}-py3-none-any.whl"
        link = BUILD_WHEELHOUSE / filename
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve(strict=True) != source:
                raise FileExistsError(f"unexpected build wheel already present: {link}")
        else:
            link.symlink_to(source)
        artifacts.append({
            "name": name,
            "version": version,
            "filename": filename,
            "cache_body": str(source),
            "sha256": sha256(source),
            "tags": tags,
        })
    return artifacts


def capture(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True, env=controlled_env())
    return result.stdout.strip()


def controlled_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PIP_NO_INDEX": "1",
        "PIP_NO_CACHE_DIR": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_CONFIG_FILE": os.devnull,
    })
    return environment


def record_plan(source: dict, build_wheels: list[dict]) -> dict:
    baseline = json.loads((ACQUISITION / "runtime-manifests/semgrep.json").read_text())
    expected = next(row for row in baseline["files"] if row["path"] == EXPECTED_NATIVE_PATH)
    wheel_link = Path(
        "/Users/dave/.codex/worktrees/cb55/dataflowbench/reports/timing/v0.9.2/"
        "preparation-20261114-01/python-runtimes/cached-wheelhouse/semgrep/"
        "ruamel.yaml.clib-0.2.15-cp310-cp310-macosx_11_0_arm64.whl"
    )
    if sha256(wheel_link) != RUAMEL_CP310_WHEEL_SHA256:
        raise ValueError("retained cp310 ruamel wheel differs from expected PyPI digest")
    with ZipFile(wheel_link) as archive:
        old_native_path = next(name for name in archive.namelist() if name.endswith(".so"))
        old_native_hash = hashlib.sha256(archive.read(old_native_path)).hexdigest()
    # The include tree is under the same framework version as the interpreter.
    python_header = PYTHON_BINARY.parents[1] / "include/python3.15/Python.h"
    clang = capture(["clang", "--version"]).splitlines()[0]
    clang_path = Path(capture(["xcrun", "--find", "clang"]))
    clang_sha256 = sha256(clang_path)
    sdk_path = capture(["xcrun", "--show-sdk-path"])
    sdk_version = capture(["xcrun", "--show-sdk-version"])
    sdk_build = capture(["xcrun", "--show-sdk-build-version"])
    xcode_version = capture(["xcodebuild", "-version"])
    python_sysconfig = capture([
        str(PYTHON_LINK), "-c",
        "import sysconfig; print('CC=' + str(sysconfig.get_config_var('CC'))); "
        "print('CFLAGS=' + str(sysconfig.get_config_var('CFLAGS'))); "
        "print('MACOSX_DEPLOYMENT_TARGET=' + str(sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET')))",
    ])
    normalized_source_files = [
        "ruamel.yaml.clib-0.2.15/_ruamel_yaml.c",
        "ruamel.yaml.clib-0.2.15/_ruamel_yaml.h",
        "ruamel.yaml.clib-0.2.15/api.c",
        "ruamel.yaml.clib-0.2.15/dumper.c",
        "ruamel.yaml.clib-0.2.15/emitter.c",
        "ruamel.yaml.clib-0.2.15/loader.c",
        "ruamel.yaml.clib-0.2.15/parser.c",
        "ruamel.yaml.clib-0.2.15/reader.c",
        "ruamel.yaml.clib-0.2.15/scanner.c",
    ]
    return {
        "schema_version": 1,
        "status": "native_build_prepared_not_dispatched",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "network": "disabled; retained local artifacts only",
        "analyzer_invocations": 0,
        "timing_runs": 0,
        "benchmark_preflights": 0,
        "python": {
            "version": "3.15.0",
            "link": str(PYTHON_LINK),
            "resolved_binary": str(PYTHON_BINARY),
            "sha256": sha256(PYTHON_BINARY),
            "matches_frozen_external_file": sha256(PYTHON_BINARY) == PYTHON_SHA256,
            "header_path": str(python_header),
            "header_exists": python_header.is_file(),
            "sysconfig": python_sysconfig,
        },
        "ruamel": {
            **source,
            "expected_native_path": EXPECTED_NATIVE_PATH,
            "frozen_native_sha256": expected["sha256"],
            "frozen_native_mode": expected["mode"],
            "cached_wrong_abi_wheel": {
                "filename": wheel_link.name,
                "pypi_sha256": RUAMEL_CP310_WHEEL_SHA256,
                "native_path": old_native_path,
                "native_sha256": old_native_hash,
                "accepted_for_python315": False,
            },
            "source_files_to_build": normalized_source_files,
            "source_payload_matches_frozen_package": "source/metadata overlap is version-pinned; compiled extension differs by ABI and has no retained cp315 binary",
            "prospective_extension_sha256": None,
            "prospective_matches_frozen_extension": None,
        },
        "build_tools": build_wheels,
        "toolchain": {
            "clang": clang,
            "clang_path": str(clang_path),
            "clang_sha256": clang_sha256,
            "xcode_developer_dir": capture(["xcode-select", "-p"]),
            "xcode_version": xcode_version,
            "sdk_path": sdk_path,
            "sdk_version": sdk_version,
            "sdk_build_version": sdk_build,
            "target_architecture": "arm64",
            "target_minimum_macos": "11.0 (from the frozen cp310 wheel tag; new build output must be inspected)",
        },
        "command": {
            "summary": "Create a fresh Python 3.15 build venv; install only the two retained hash-pinned build wheels; build the exact ruamel 0.2.15 sdist offline with no dependency resolution; inspect the cp315 wheel and extension hash.",
            "dispatch_flag": "--dispatch-after-quiet",
            "network_flags": ["--no-index", "--no-deps", "--no-cache-dir", "--no-build-isolation"],
            "maximum_parallel_compilers": 1,
        },
        "estimated_footprint": {
            "source_bytes": source["size_bytes"],
            "setuptools_wheel_bytes": next(row["size_bytes"] for row in build_wheels if row["name"] == "setuptools") if "size_bytes" in build_wheels[0] else None,
            "conservative_peak_scratch_bytes": 536870912,
            "basis": "one C extension from a 225.8 kB source archive plus a small isolated Python venv; 512 MiB is a conservative cap, not a measured footprint",
        },
        "relocation_and_identity_notes": [
            "The new root changes pyvenv.cfg and launcher shebangs; interpreter binary remains exact by SHA-256.",
            "The new extension will not be claimed byte-identical to the frozen .so unless its computed SHA-256 equals the frozen digest.",
            "A source-built extension is a prospective candidate until the exact .so path, architecture, linkage, and runtime package inventory are verified.",
            "The original runtime manifests and removed worktree paths remain untouched.",
        ],
    }


def run_build(plan: dict) -> dict:
    if BUILD_ENV.exists() or BUILD_OUTPUT.exists() or LOG.exists():
        raise FileExistsError("build outputs already exist; preserve and inspect them before retrying")
    env = controlled_env()
    subprocess.run([str(PYTHON_LINK), "-m", "venv", str(BUILD_ENV)], check=True, env=env)
    pip = BUILD_ENV / "bin/python"
    wheel_paths = [str(BUILD_WHEELHOUSE / row["filename"]) for row in plan["build_tools"]]
    install = [str(pip), "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", "--only-binary=:all:", *wheel_paths]
    subprocess.run(install, check=True, env=env)
    BUILD_OUTPUT.mkdir(parents=True, exist_ok=False)
    command = [str(pip), "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "--no-cache-dir", "--wheel-dir", str(BUILD_OUTPUT), str(SOURCE_LINK)]
    build_env = env.copy()
    build_env.update({"ARCHFLAGS": "-arch arm64", "MACOSX_DEPLOYMENT_TARGET": "11.0", "MAX_JOBS": "1"})
    with LOG.open("x") as stream:
        stream.write("$ " + shlex.join(install) + "\n")
        stream.write("$ " + shlex.join(command) + "\n")
        stream.flush()
        subprocess.run(command, check=True, env=build_env, stdout=stream, stderr=subprocess.STDOUT)
    wheels = list(BUILD_OUTPUT.glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"expected one built wheel, found {len(wheels)}")
    with ZipFile(wheels[0]) as archive:
        native_name = next((name for name in archive.namelist() if name.endswith("_ruamel_yaml.cpython-315-darwin.so")), None)
        if native_name is None:
            raise ValueError("built wheel did not contain the CPython 3.15 arm64 extension")
        native_hash = hashlib.sha256(archive.read(native_name)).hexdigest()
    output = {
        "schema_version": 1,
        "wheel": str(wheels[0]),
        "wheel_sha256": sha256(wheels[0]),
        "native_path": native_name,
        "native_sha256": native_hash,
        "frozen_native_sha256": EXPECTED_NATIVE_SHA256,
        "matches_frozen_native": native_hash == EXPECTED_NATIVE_SHA256,
        "built_with": plan["build_tools"],
        "build_log": str(LOG),
        "installed_into_runtime": False,
    }
    (RECEIPT / "ruamel-native-build-output.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dispatch-after-quiet",
        action="store_true",
        help="perform the bounded native build only after an externally observed quiet-host window",
    )
    args = parser.parse_args()
    if sha256(PYTHON_BINARY) != PYTHON_SHA256:
        raise ValueError("Python 3.15.0 binary differs from the frozen external_files hash")
    source = parse_source()
    build_wheels = stage_build_wheels()
    for row in build_wheels:
        row["size_bytes"] = (BUILD_WHEELHOUSE / row["filename"]).stat().st_size
    plan = record_plan(source, build_wheels)
    plan_path = RECEIPT / "ruamel-native-build-plan.json"
    if plan_path.exists():
        raise FileExistsError(plan_path)
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    if args.dispatch_after_quiet:
        output = run_build(plan)
        print(json.dumps({"status": "built", "output": output}, indent=2))
    else:
        print(json.dumps({"status": "prepared_not_dispatched", "plan": str(plan_path)}, indent=2))


if __name__ == "__main__":
    main()
