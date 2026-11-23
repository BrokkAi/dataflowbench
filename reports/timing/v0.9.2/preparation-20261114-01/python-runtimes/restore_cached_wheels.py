#!/usr/bin/env python3
"""Restore the frozen Pysa and Semgrep Python runtimes from retained local wheels.

This is an offline materialization helper, not an analyzer or benchmark runner.
It refuses to resolve dependencies, fetch from an index, overwrite existing
runtime roots, or modify the source cache.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile


REPO = Path(__file__).resolve().parents[5]
RECEIPT_DIR = Path(__file__).resolve().parent
ACQUISITION = REPO / "reports/releases/v0.9.2/acquisition"
MANIFEST_DIR = ACQUISITION / "runtime-manifests"
CACHE_DIR = Path.home() / "Library/Caches/pip/http-v2"
OLD_PYSA = Path.home() / ".cache/dataflowbench-tools/pysa-venv"
PYTHON_LINK = Path("/opt/homebrew/opt/python@3.15/bin/python3.15")
PYTHON_CELLAR = Path(
    "/opt/homebrew/Cellar/python@3.15/3.15.0/Frameworks/"
    "Python.framework/Versions/3.15/bin/python3.15"
)
PYTHON_FRAMEWORK = Path(
    "/opt/homebrew/Cellar/python@3.15/3.15.0/Frameworks/"
    "Python.framework/Versions/3.15"
)
PYTHON_SHA256 = "15c72833c1ffc09bc4e05d1e1866784d126721ad548d9c4d8f943641262535cb"
SEMgrep_WHEEL_SHA256 = "05d79ad777fae86f6d914a67bedec1b9e2c3e637f61d49a4ef557e2bf69fed01"
SEMgrep_VERSION = "1.181.0"
TESTSLIDE_VERSION = "2.7.1"
RUNTIME_BASE = REPO / "execution-state/timing-runtime-20261114-01"
TOOLS = ("pysa", "semgrep")


def canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def wheel_name_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "_", value)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_metadata(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(("Name:", "Version:")):
            key, value = line.split(":", 1)
            result[key] = value.strip()
    return result


def load_expected() -> dict[str, dict]:
    result = {}
    for tool in TOOLS:
        manifest_path = MANIFEST_DIR / f"{tool}.json"
        freeze_path = ACQUISITION / f"{tool}-env-freeze.txt"
        manifest = json.loads(manifest_path.read_text())
        expected_files = {row["path"]: row["sha256"] for row in manifest["files"]}
        pins = []
        for line in freeze_path.read_text().splitlines():
            if "==" in line:
                name, version = line.split("==", 1)
                pins.append((canonical_name(name), version))
        result[tool] = {
            "manifest": manifest,
            "manifest_path": manifest_path,
            "freeze_path": freeze_path,
            "expected_files": expected_files,
            "pins": pins,
        }
    return result


def wheel_tags(z: ZipFile, names: list[str]) -> list[str]:
    wheel_metadata = next((name for name in names if name.endswith(".dist-info/WHEEL")), None)
    if not wheel_metadata:
        raise ValueError("cached ZIP has no WHEEL metadata")
    text = z.read(wheel_metadata).decode("utf-8", "replace")
    return [line[5:].strip() for line in text.splitlines() if line.startswith("Tag: ")]


def destination_path(archive_path: str) -> str | None:
    if archive_path.endswith(".dist-info/RECORD"):
        return None
    if archive_path.endswith(".dist-info/WHEEL"):
        return None
    if archive_path.endswith(".dist-info/INSTALLER") or archive_path.endswith(".dist-info/REQUESTED"):
        return None
    if "/__pycache__/" in archive_path or archive_path.endswith(".pyc"):
        return None
    if ".data/scripts/" in archive_path:
        return None
    parts = archive_path.split(".data/", 1)
    if len(parts) == 2:
        section, _, relative = parts[1].partition("/")
        if section not in ("purelib", "platlib"):
            return None
        return "lib/python3.15/site-packages/" + relative
    return "lib/python3.15/site-packages/" + archive_path


def score_wheel(path: Path, tool: str, expected_files: dict[str, str]) -> tuple:
    matches = 0
    mismatches = []
    names: list[str]
    with ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            destination = destination_path(name)
            if destination is None or destination not in expected_files:
                continue
            matches += 1
            actual = sha256_bytes(archive.read(name))
            if actual != expected_files[destination]:
                mismatches.append(destination)
    digest = sha256_file(path)
    return (len(mismatches), -matches, path, digest, mismatches, names)


def index_cached_wheels(expected: dict[str, dict]) -> dict[tuple[str, str], list[Path]]:
    wanted = {pin for item in expected.values() for pin in item["pins"]}
    found: dict[tuple[str, str], list[Path]] = {}
    for path in CACHE_DIR.rglob("*.body"):
        try:
            with ZipFile(path) as archive:
                metadata_path = next(
                    (name for name in archive.namelist() if name.endswith(".dist-info/METADATA")),
                    None,
                )
                if not metadata_path:
                    continue
                metadata = parse_metadata(archive.read(metadata_path).decode("utf-8", "replace"))
                key = (canonical_name(metadata.get("Name", "")), metadata.get("Version", ""))
                if key in wanted:
                    found.setdefault(key, []).append(path)
        except (BadZipFile, OSError):
            continue
    return found


def frozen_semgrep_wheel_name() -> str:
    record = json.loads((ACQUISITION / "semgrep-pypi.json").read_text())
    for file_record in record.get("releases", {}).get(SEMgrep_VERSION, []):
        filename = file_record.get("filename", "")
        if filename.endswith("macosx_11_0_arm64.whl"):
            if file_record.get("digests", {}).get("sha256") != SEMgrep_WHEEL_SHA256:
                raise ValueError("Semgrep frozen PyPI digest does not match the retained wheel")
            return filename
    raise ValueError("frozen Semgrep arm64 wheel filename was not found")


def make_wheel_filename(name: str, version: str, tags: list[str]) -> str:
    triples = [tag.split("-", 2) for tag in tags]
    if not triples or any(len(tag) != 3 for tag in triples):
        raise ValueError(f"cannot form a wheel filename from tags: {tags}")
    python_tags = sorted({tag[0] for tag in triples})
    abi_tags = sorted({tag[1] for tag in triples})
    platform_tags = sorted({tag[2] for tag in triples})
    return (
        f"{wheel_name_part(name)}-{version}-"
        f"{'.'.join(python_tags)}-{'.'.join(abi_tags)}-{'.'.join(platform_tags)}.whl"
    )


def load_frozen_semgrep_wheel_hashes() -> dict[str, str]:
    record = json.loads((ACQUISITION / "semgrep-pypi.json").read_text())
    return {
        row["filename"]: row["digests"]["sha256"]
        for row in record.get("releases", {}).get(SEMgrep_VERSION, [])
        if row.get("filename")
    }


def stage_wheels(expected: dict[str, dict], wheel_sources: dict) -> dict:
    receipt = {"schema_version": 1, "cache_root": str(CACHE_DIR), "runtimes": {}}
    semgrep_filename = frozen_semgrep_wheel_name()
    semgrep_hashes = load_frozen_semgrep_wheel_hashes()
    for tool in TOOLS:
        wheelhouse = RECEIPT_DIR / "cached-wheelhouse" / tool
        wheelhouse.mkdir(parents=True, exist_ok=False)
        expected_files = expected[tool]["expected_files"]
        entries = []
        missing = []
        for key in expected[tool]["pins"]:
            if key == ("testslide", TESTSLIDE_VERSION):
                missing.append(f"{key[0]}=={key[1]}")
                continue
            choices = []
            for source in wheel_sources.get(key, []):
                scored = score_wheel(source, tool, expected_files)
                if not scored[0] and scored[1] < 0:
                    choices.append(scored)
            if not choices:
                raise ValueError(f"no cached wheel with baseline-matching payload for {tool} {key}")
            choices.sort(key=lambda row: (row[0], row[1], row[3]))
            _, negative_matches, source, digest, _, archive_names = choices[0]
            with ZipFile(source) as archive:
                metadata_path = next(name for name in archive_names if name.endswith(".dist-info/METADATA"))
                metadata = parse_metadata(archive.read(metadata_path).decode("utf-8", "replace"))
                tags = wheel_tags(archive, archive_names)
            name, version = metadata["Name"], metadata["Version"]
            if key == ("semgrep", SEMgrep_VERSION):
                wheel_filename = semgrep_filename
                frozen_digest = semgrep_hashes.get(wheel_filename)
                if frozen_digest != digest:
                    raise ValueError("cached Semgrep wheel hash differs from frozen PyPI SHA-256")
            else:
                wheel_filename = make_wheel_filename(name, version, tags)
                frozen_digest = None
            destination = wheelhouse / wheel_filename
            destination.symlink_to(source)
            entries.append(
                {
                    "name": name,
                    "version": version,
                    "wheel_filename": wheel_filename,
                    "cache_body": str(source),
                    "sha256": digest,
                    "frozen_sha256": frozen_digest,
                    "baseline_payload_files_compared": -negative_matches,
                    "wheel_tags": tags,
                }
            )
        if missing and tool != "pysa":
            raise ValueError(f"unexpected missing wheel artifacts for {tool}: {missing}")
        receipt["runtimes"][tool] = {
            "wheelhouse": str(wheelhouse),
            "cached_wheels": entries,
            "missing_wheels": missing,
        }
    (RECEIPT_DIR / "cached-wheel-artifact-lock.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


def run_logged(name: str, command: list[str], environment: dict[str, str]) -> None:
    log = RECEIPT_DIR / f"{name}.log"
    if log.exists():
        raise FileExistsError(log)
    with log.open("x") as stream:
        stream.write("$ " + shlex.join(command) + "\n")
        stream.flush()
        subprocess.run(command, check=True, env=environment, stdout=stream, stderr=subprocess.STDOUT)


def command_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PIP_NO_INDEX": "1",
            "PIP_NO_CACHE_DIR": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_CONFIG_FILE": os.devnull,
        }
    )
    return environment


def pin_args(tool: str) -> list[str]:
    return [
        f"{name}=={version}"
        for name, version in load_expected()[tool]["pins"]
        if not (tool == "pysa" and (name, version) == ("testslide", TESTSLIDE_VERSION))
        and not (tool == "semgrep" and (name, version) == ("semgrep", SEMgrep_VERSION))
    ]


def dry_run_installs(expected: dict[str, dict], environment: dict[str, str]) -> None:
    for tool in TOOLS:
        wheelhouse = RECEIPT_DIR / "cached-wheelhouse" / tool
        command = [
            str(PYTHON_LINK),
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--no-index",
            "--no-deps",
            "--no-compile",
            "--no-cache-dir",
            "--only-binary=:all:",
            f"--find-links={wheelhouse}",
            *pin_args(tool),
        ]
        run_logged(f"{tool}-dependency-wheels-dry-run", command, environment)
    semgrep_wheelhouse = RECEIPT_DIR / "cached-wheelhouse/semgrep"
    command = [
        str(PYTHON_LINK),
        "-m",
        "pip",
        "install",
        "--dry-run",
        "--ignore-installed",
        "--no-index",
        "--no-deps",
        "--no-compile",
        "--no-cache-dir",
        "--only-binary=:all:",
        f"--find-links={semgrep_wheelhouse}",
        "--platform",
        "macosx_11_0_arm64",
        "--python-version",
        "3.14",
        "--implementation",
        "cp",
        "--abi",
        "none",
        f"semgrep=={SEMgrep_VERSION}",
    ]
    run_logged("semgrep-main-wheel-dry-run", command, environment)


def write_testslide_record(site: Path, runtime_root: Path) -> None:
    record_path = site / "testslide-2.7.1.dist-info/RECORD"
    rows = []
    package_paths = [site / "testslide", site / "testslide-2.7.1.dist-info"]
    for package_path in package_paths:
        for path in sorted(package_path.rglob("*")):
            if not path.is_file() or path == record_path or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = path.relative_to(site).as_posix()
            data = path.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            rows.append((relative, "sha256=" + digest, str(len(data))))
    script = runtime_root / "bin/testslide"
    if script.is_file():
        data = script.read_bytes()
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        rows.append(("../../../bin/testslide", "sha256=" + digest, str(len(data))))
    rows.append(("testslide-2.7.1.dist-info/RECORD", "", ""))
    with record_path.open("x", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerows(sorted(rows))


def restore_testslide(runtime_root: Path) -> dict:
    source_site = OLD_PYSA / "lib/python3.14/site-packages"
    destination_site = runtime_root / "lib/python3.15/site-packages"
    copied = []
    for relative in ("testslide", "testslide-2.7.1.dist-info"):
        source = source_site / relative
        destination = destination_site / relative
        if destination.exists():
            raise FileExistsError(destination)
        destination.mkdir(parents=True, exist_ok=False)
        for path in sorted(source.rglob("*")):
            relative_path = path.relative_to(source)
            if "__pycache__" in path.parts or path.suffix == ".pyc" or path.name == "RECORD":
                continue
            target = destination / relative_path
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif path.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied.append((relative + "/" + relative_path.as_posix(), sha256_file(target)))
    old_script = OLD_PYSA / "bin/testslide"
    if not old_script.is_file():
        raise FileNotFoundError(old_script)
    lines = old_script.read_text().splitlines()
    if not lines or not lines[0].startswith("#!"):
        raise ValueError("retained TestSlide launcher has no shebang")
    lines[0] = "#!" + str(runtime_root / "bin/python")
    launcher = runtime_root / "bin/testslide"
    launcher.write_text("\n".join(lines) + "\n")
    launcher.chmod(0o755)
    write_testslide_record(destination_site, runtime_root)
    return {
        "source_root": str(source_site),
        "source_python": "3.14.7",
        "version": TESTSLIDE_VERSION,
        "copied_files": len(copied),
        "copied_sha256": dict(copied),
        "launcher_sha256": sha256_file(launcher),
        "launcher_shebang": lines[0],
        "record_regenerated": True,
    }


def restore_pyyaml_frozen_payload(runtime_root: Path, wheel: Path, expected_files: dict[str, str]) -> dict:
    """Restore only the byte-identical files present in the frozen Pysa manifest.

    The retained PyYAML wheel is cp314 and contains a cp314 extension. The
    frozen Python 3.15 environment has no PyYAML extension at all, so that
    unsupported binary is never copied or loaded. Its source/package payload
    is admitted only when each copied file hash equals the frozen manifest.
    """
    site = runtime_root / "lib/python3.15/site-packages"
    copied = []
    omitted_incompatible = []
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        wheel_meta = next(name for name in names if name.endswith(".dist-info/WHEEL"))
        wheel_text = archive.read(wheel_meta).decode("utf-8", "replace")
        tags = [line[5:].strip() for line in wheel_text.splitlines() if line.startswith("Tag: ")]
        if tags != ["cp314-cp314-macosx_11_0_arm64"]:
            raise ValueError(f"unexpected retained PyYAML wheel tags: {tags}")
        for name in names:
            if name.endswith("/") or name.endswith(".dist-info/RECORD"):
                continue
            if "/__pycache__/" in name or name.endswith(".pyc"):
                continue
            destination = "lib/python3.15/site-packages/" + name
            payload = archive.read(name)
            digest = sha256_bytes(payload)
            expected = expected_files.get(destination)
            if expected is None:
                if name.endswith(".so"):
                    omitted_incompatible.append({"wheel_path": name, "sha256": digest, "reason": "not in frozen Pysa manifest; CPython 3.14 ABI"})
                    continue
                # The wheel's directory entries and records are not payload.
                if name.endswith(".dist-info/INSTALLER") or name.endswith(".dist-info/REQUESTED"):
                    continue
                raise ValueError(f"unexpected PyYAML wheel payload is outside frozen manifest: {name}")
            if digest != expected:
                raise ValueError(f"PyYAML wheel payload differs from frozen manifest: {destination}")
            target = runtime_root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError(target)
            target.write_bytes(payload)
            copied.append({"path": destination, "sha256": digest})
    installer = site / "pyyaml-6.0.3.dist-info/INSTALLER"
    if not installer.exists():
        installer.write_text("pip\n")
    if sha256_file(installer) != expected_files["lib/python3.15/site-packages/pyyaml-6.0.3.dist-info/INSTALLER"]:
        raise ValueError("regenerated PyYAML INSTALLER metadata differs from frozen manifest")
    # pip writes RECORD during a normal install. Rebuild the same metadata form
    # after the manifest-filtered extraction and record the derived difference.
    record_path = site / "pyyaml-6.0.3.dist-info/RECORD"
    rows = []
    dist_info = site / "pyyaml-6.0.3.dist-info"
    package_roots = [site / "yaml", site / "_yaml", dist_info]
    for package_root in package_roots:
        if not package_root.exists():
            continue
        for path in sorted(package_root.rglob("*")):
            if not path.is_file() or path == record_path or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = path.relative_to(site).as_posix()
            data = path.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            rows.append((relative, "sha256=" + digest, str(len(data))))
    rows.append(("pyyaml-6.0.3.dist-info/RECORD", "", ""))
    with record_path.open("x", newline="") as stream:
        csv.writer(stream, lineterminator="\n").writerows(sorted(rows))
    return {
        "wheel": str(wheel),
        "wheel_sha256": sha256_file(wheel),
        "wheel_tags": tags,
        "copied_baseline_matching_files": copied,
        "omitted_incompatible_unfrozen_files": omitted_incompatible,
        "record_regenerated": True,
    }


def immutable_path(relative: str) -> bool:
    lowered = relative.lower()
    if "__pycache__" in relative or relative.endswith(".pyc"):
        return False
    if lowered.endswith(".dist-info/record") or lowered.endswith(".dist-info/wheel"):
        return False
    if lowered.endswith(".dist-info/installer") or lowered.endswith(".dist-info/requested"):
        return False
    return relative.startswith("lib/python3.15/site-packages/")


def compare_payload(tool: str, runtime_root: Path) -> dict:
    baseline = load_expected()[tool]["expected_files"]
    current = {}
    for path in runtime_root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            relative = path.relative_to(runtime_root).as_posix()
            if immutable_path(relative):
                current[relative] = sha256_file(path)
    expected = {path: digest for path, digest in baseline.items() if immutable_path(path)}
    missing = sorted(set(expected) - set(current))
    extra = sorted(set(current) - set(expected))
    mismatches = sorted(path for path in set(expected) & set(current) if expected[path] != current[path])
    generated_metadata_differences = []
    for path, digest in baseline.items():
        if path.startswith("lib/python3.15/site-packages/") and path.endswith(".dist-info/WHEEL"):
            actual = runtime_root / path
            if actual.is_file() and sha256_file(actual) != digest:
                generated_metadata_differences.append(path)
    return {
        "baseline_immutable_files": len(expected),
        "candidate_immutable_files": len(current),
        "matching_files": len(set(expected) & set(current)) - len(mismatches),
        "missing_files": missing,
        "extra_files": extra,
        "mismatches": mismatches,
        "wheel_metadata_differences": sorted(generated_metadata_differences),
        "normalized_payload_match": not missing and not mismatches,
    }


def inventory(runtime_root: Path, output: Path) -> dict:
    script = ACQUISITION / "inventory-runtime.py"
    command = [sys.executable, str(script), "--root", str(runtime_root), "--output", str(output)]
    subprocess.run(command, check=True, env=command_env())
    return json.loads(output.read_text())


def main() -> None:
    if sha256_file(PYTHON_CELLAR) != PYTHON_SHA256:
        raise ValueError("Python 3.15.0 interpreter digest differs from frozen external_files entry")
    if not PYTHON_LINK.exists() or PYTHON_LINK.resolve(strict=True) != PYTHON_CELLAR:
        raise ValueError("Homebrew Python 3.15 opt link does not resolve to the frozen interpreter")
    for tool in TOOLS:
        root = RUNTIME_BASE / tool
        if root.exists() and any(root.iterdir()):
            raise FileExistsError(f"assigned runtime root is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)

    expected = load_expected()
    lock_path = RECEIPT_DIR / "cached-wheel-artifact-lock.json"
    lock = json.loads(lock_path.read_text())
    semgrep_cp315_source = Path(
        "/Users/dave/Library/Caches/pip/wheels/c1/c9/17/995e9586c021473541a66c1099245be5299035534dbfb37847/"
        "ruamel_yaml_clib-0.2.15-cp315-cp315-macosx_27_0_arm64.whl"
    )
    semgrep_cp315_hash = "d554a03aa02eb2daaaf822762d3d7ce102147accc75307b15f8528a72a61070e"
    semgrep_cp315_extension_hash = EXPECTED_RUAMEL_EXTENSION_SHA256 = "7b6574966296fb64b0af6cca234c04c6df9ca776b80dc8ae13fc82b4eccd9883"
    if not semgrep_cp315_source.is_file() or sha256_file(semgrep_cp315_source) != semgrep_cp315_hash:
        raise ValueError("retained cp315 ruamel wheel is missing or differs from the verified artifact digest")
    cp315_link = RECEIPT_DIR / "cached-wheelhouse/semgrep" / semgrep_cp315_source.name
    if cp315_link.exists() or cp315_link.is_symlink():
        if not cp315_link.is_symlink() or cp315_link.resolve(strict=True) != semgrep_cp315_source:
            raise FileExistsError(f"unexpected staged cp315 wheel path: {cp315_link}")
    else:
        cp315_link.symlink_to(semgrep_cp315_source)
    with ZipFile(semgrep_cp315_source) as archive:
        cp315_extension = next(name for name in archive.namelist() if name.endswith("_ruamel_yaml.cpython-315-darwin.so"))
        cp315_extension_hash = sha256_bytes(archive.read(cp315_extension))
        cp315_metadata = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        cp315_wheel = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        cp315_tags = [line[5:].strip() for line in archive.read(cp315_wheel).decode().splitlines() if line.startswith("Tag: ")]
        cp315_package_metadata_hash = sha256_bytes(archive.read(cp315_metadata))
    if cp315_extension_hash != semgrep_cp315_extension_hash:
        raise ValueError("cached cp315 extension differs from frozen Semgrep runtime hash")
    if cp315_tags != ["cp315-cp315-macosx_27_0_arm64"]:
        raise ValueError(f"unexpected cp315 ruamel wheel tags: {cp315_tags}")
    cp315_receipt = {
        "wheel": str(semgrep_cp315_source),
        "wheel_sha256": semgrep_cp315_hash,
        "tag": cp315_tags[0],
        "extension_path": cp315_extension,
        "extension_sha256": cp315_extension_hash,
        "frozen_extension_sha256": semgrep_cp315_extension_hash,
        "extension_matches_frozen": True,
        "metadata_sha256": cp315_package_metadata_hash,
        "staged_link": str(cp315_link),
    }
    (RECEIPT_DIR / "semgrep-ruamel-exact-wheel.json").write_text(json.dumps(cp315_receipt, indent=2) + "\n")
    environment = command_env()

    for tool in TOOLS:
        root = RUNTIME_BASE / tool
        if any(root.iterdir()):
            raise FileExistsError(f"runtime root changed before venv creation: {root}")
        command = [str(PYTHON_LINK), "-m", "venv", str(root)]
        run_logged(f"{tool}-venv-creation", command, environment)

    for tool in TOOLS:
        root = RUNTIME_BASE / tool
        wheelhouse = Path(lock["runtimes"][tool]["wheelhouse"])
        package_wheels = sorted(
            path for path in wheelhouse.glob("*.whl")
            if not (tool == "semgrep" and path.name.startswith("semgrep-1.181.0-"))
            and not (tool == "pysa" and path.name.startswith("PyYAML-6.0.3-"))
            and not (tool == "semgrep" and path.name.startswith("ruamel.yaml.clib-0.2.15-cp310-"))
        )
        command = [
            str(root / "bin/python"),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--no-compile",
            "--no-cache-dir",
            "--only-binary=:all:",
            *[str(path) for path in package_wheels],
        ]
        run_logged(f"{tool}-pinned-wheel-install", command, environment)

    pyyaml_wheel = next(Path(lock["runtimes"]["pysa"]["wheelhouse"]).glob("PyYAML-6.0.3-*.whl"))
    pyyaml_receipt = restore_pyyaml_frozen_payload(
        RUNTIME_BASE / "pysa", pyyaml_wheel, expected["pysa"]["expected_files"]
    )

    semgrep_root = RUNTIME_BASE / "semgrep"
    semgrep_site = semgrep_root / "lib/python3.15/site-packages"
    semgrep_wheelhouse = Path(lock["runtimes"]["semgrep"]["wheelhouse"])
    semgrep_command = [
        str(semgrep_root / "bin/python"),
        "-m",
        "pip",
        "install",
        "--no-index",
        "--no-deps",
        "--no-compile",
        "--no-cache-dir",
        "--only-binary=:all:",
        "--no-warn-script-location",
        f"--find-links={semgrep_wheelhouse}",
        "--target",
        str(semgrep_site),
        "--platform",
        "macosx_11_0_arm64",
        "--python-version",
        "3.14",
        "--implementation",
        "cp",
        "--abi",
        "none",
        f"semgrep=={SEMgrep_VERSION}",
    ]
    run_logged("semgrep-main-pinned-wheel-install", semgrep_command, environment)

    # pip's cross-target install writes console scripts below site-packages/bin;
    # copy them into the venv bin with the relocated interpreter shebang.
    cross_scripts = semgrep_site / "bin"
    copied_scripts = []
    if cross_scripts.is_dir():
        for source in sorted(cross_scripts.iterdir()):
            if not source.is_file():
                continue
            content = source.read_bytes()
            lines = content.splitlines(keepends=True)
            if lines and lines[0].startswith(b"#!"):
                lines[0] = ("#!" + str(semgrep_root / "bin/python") + "\n").encode()
                content = b"".join(lines)
            destination = semgrep_root / "bin" / source.name
            if destination.exists():
                continue
            destination.write_bytes(content)
            destination.chmod(stat.S_IMODE(source.stat().st_mode))
            copied_scripts.append(destination.name)

    testslide = restore_testslide(RUNTIME_BASE / "pysa")

    manifests = {}
    comparisons = {}
    for tool in TOOLS:
        root = RUNTIME_BASE / tool
        output = RECEIPT_DIR / f"{tool}-relocated-runtime-manifest.json"
        manifest = inventory(root, output)
        manifests[tool] = {
            "path": str(output),
            "file_count": len(manifest["files"]),
            "symlink_count": len(manifest["symlinks"]),
            "external_files": manifest["external_files"],
            "pyvenv_cfg_sha256": sha256_file(root / "pyvenv.cfg"),
        }
        comparisons[tool] = compare_payload(tool, root)

    receipt = {
        "schema_version": 1,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "restored" if all(row["normalized_payload_match"] for row in comparisons.values()) else "blocked",
        "network": "disabled; no index access or downloads",
        "analyzer_invocations": 0,
        "timing_runs": 0,
        "benchmark_preflights": 0,
        "python": {
            "version": "3.15.0",
            "executable_link": str(PYTHON_LINK),
            "resolved_executable": str(PYTHON_CELLAR),
            "sha256": PYTHON_SHA256,
            "sha_matches_frozen_manifests": True,
            "ensurepip_pip_version": "26.2.1",
            "ensurepip_wheel_sha256": sha256_file(
                PYTHON_FRAMEWORK / "lib/python3.15/ensurepip/_bundled/pip-26.2.1-py3-none-any.whl"
            ),
        },
        "old_runtime_roots": {
            tool: expected[tool]["manifest"]["root"] for tool in TOOLS
        },
        "new_runtime_roots": {tool: str(RUNTIME_BASE / tool) for tool in TOOLS},
        "artifact_lock": str(RECEIPT_DIR / "cached-wheel-artifact-lock.json"),
        "testslide_from_retained_installed_distribution": testslide,
        "semgrep_cross_target_scripts_copied": copied_scripts,
        "semgrep_exact_cp315_ruamel_wheel": cp315_receipt,
        "pysa_manifest_filtered_pyyaml": pyyaml_receipt,
        "new_manifests": manifests,
        "normalized_payload_comparison": comparisons,
        "relocation_changes": [
            "pyvenv.cfg records the new venv root and creation command",
            "pip and console-script shebangs target the new root",
            "the external Python 3.15.0 binary path resolves through Homebrew opt to the same Cellar file and SHA-256",
            "Python bytecode caches are omitted during restore and will be regenerated by later imports",
            "distribution RECORD files are installer-generated; TestSlide RECORD was regenerated after relocation",
            "Semgrep 1.181.0 wheel is tagged through CPython 3.14; the frozen baseline uses Python 3.15, so this exact digest-bound wheel is installed into the 3.15 venv using a recorded cp314/macOS-arm64 target tag override",
        ],
        "launch_state": "not launched; analyzer invocation binding remains a separate required integration gate",
    }
    (RECEIPT_DIR / "runtime-restoration-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps({"status": receipt["status"], "roots": receipt["new_runtime_roots"], "manifests": manifests}, indent=2))


if __name__ == "__main__":
    main()
