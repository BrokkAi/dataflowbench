#!/usr/bin/env python3
"""Capture the frozen 44 Bifrost controls for the v0.14.4 target.

The historical qualifier remains byte-identical. This wrapper patches only
the verified runtime identity and the external-pack environment, then retains
the strict result and a hash-bound capture context even when strict schema-5
qualification fails against schema-6 reports.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[5]
QUALIFICATION_DIR = Path(__file__).resolve().parent
FROZEN_QUALIFIER = ROOT / "scripts/qualify-bifrost-v013.py"
FROZEN_QUALIFIER_SHA256 = "e6ac256769b2f01a3bed30ddcb2b7f15d00fa090fb0cc6dee66414854cf67582"
ACQUISITION_RECEIPT = ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0144-01/acquisition-receipt.json"
ACQUISITION_RECEIPT_SHA256 = "c32c1b0ab396f9e0d5849fc01d4c602b0fcd27e13056944ff16ad6b7a2f16371"
AUTHORIZATION = QUALIFICATION_DIR / "human-authorization-01.json"
EXPECTED_BINARY = Path(
    "/Users/dave/.codex/worktrees/9f01/dataflowbench/execution-state/v092/tools/bifrost0144/"
    "extracted/bifrost-v0.14.4-universal-apple-darwin/bifrost"
)
EXPECTED_BINARY_SHA256 = "a3aa17a18be33e1e841c1bf317c6ca35a6aa3aaef452c607fafbb3b83aeec399"
EXPECTED_VERSION = "0.14.4"
EXPECTED_BUILD_IDENTITY = "ff5cf473f4ad414751911ff93ef79e1df1d35823"
PUBLIC_TAG_COMMIT = "786891f9ed19d2086dfd6242ff15ca904b610620"
GROUPS = (
    "bifrost-c-kernel", "bifrost-cpp-kernel", "bifrost-csharp-kernel", "bifrost-go-kernel",
    "bifrost-java-kernel", "bifrost-java-modeling", "bifrost-java-native",
    "bifrost-javascript-kernel", "bifrost-javascript-modeling", "bifrost-javascript-native",
    "bifrost-kotlin-kernel", "bifrost-php-kernel", "bifrost-python-kernel",
    "bifrost-python-modeling", "bifrost-python-native", "bifrost-ruby-kernel",
    "bifrost-rust-kernel", "bifrost-scala-kernel", "bifrost-smoke", "bifrost-typescript-kernel",
)


class QualificationError(ValueError):
    """A pinned identity, authorization, or capture-path check failed."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QualificationError(f"cannot read JSON evidence: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualificationError(f"JSON evidence is not an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QualificationError(message)


def authorization(root: Path = ROOT) -> tuple[dict, dict]:
    path = root / "reports/releases/v0.9.2/qualification/bifrost-v0144-01/human-authorization-01.json"
    require(path.is_file() and not path.is_symlink(), "human authorization is missing or a symlink")
    value = load_json(path)
    require(value.get("schema") == "v092-new-bifrost-target-human-authorization/v1", "wrong human authorization schema")
    require(value.get("target_version") == EXPECTED_VERSION, "human authorization targets a different Bifrost version")
    require(value.get("supersedes_preparation_only_hold_for_new_target_qualification_and_benchmark") is True,
            "authorization does not supersede the preparation-only hold for this target")
    require(value.get("source_integration_acquisition_tests_qualification_and_fresh_run_authorized") is True,
            "authorization does not cover qualification and a fresh run")
    require(value.get("publication_still_requires_separate_human_review_and_explicit_approval") is True,
            "publication review hold is missing")
    groups = value.get("scope")
    require(isinstance(groups, list) and tuple(groups) == GROUPS, "human authorization has a different Bifrost group scope")
    return value, {"path": str(path.relative_to(root)), "sha256": sha256(path)}


def acquired_identity(root: Path = ROOT) -> tuple[dict, dict]:
    path = root / "reports/releases/v0.9.2/acquisition/bifrost-v0144-01/acquisition-receipt.json"
    require(path == ACQUISITION_RECEIPT, "acquisition receipt path changed")
    require(path.is_file() and not path.is_symlink(), "v0.14.4 acquisition receipt is missing or a symlink")
    receipt_sha = sha256(path)
    require(receipt_sha == ACQUISITION_RECEIPT_SHA256, "v0.14.4 acquisition receipt digest changed")
    receipt = load_json(path)
    source = receipt.get("source", {})
    binary = receipt.get("binary", {})
    require(source.get("tag") == "v0.14.4" and source.get("public_tag_commit") == PUBLIC_TAG_COMMIT,
            "acquisition receipt is not for the pinned public v0.14.4 tag")
    require(binary.get("path") == str(EXPECTED_BINARY) and binary.get("version_output", "").splitlines()[0] ==
            f"bifrost {EXPECTED_VERSION}", "acquisition receipt has a different binary path or version")
    require(binary.get("build_identity_output") == EXPECTED_BUILD_IDENTITY and
            binary.get("sha256") == EXPECTED_BINARY_SHA256, "acquisition receipt has a different binary identity")
    executable = root / Path(str(binary["path"]).removeprefix(str(ROOT) + "/"))
    if Path(str(binary["path"])).is_absolute():
        executable = Path(binary["path"])
    require(executable == EXPECTED_BINARY and executable.is_file() and not executable.is_symlink(),
            "pinned v0.14.4 executable is missing, redirected, or a symlink")
    require(sha256(executable) == EXPECTED_BINARY_SHA256, "pinned v0.14.4 executable digest changed")
    identity = {
        "path": str(executable),
        "version": EXPECTED_VERSION,
        "build_identity": EXPECTED_BUILD_IDENTITY,
        "sha256": EXPECTED_BINARY_SHA256,
        "public_tag_commit": PUBLIC_TAG_COMMIT,
    }
    return identity, {"path": str(path.relative_to(root)), "sha256": receipt_sha}


def controls_for_release():
    """Load the frozen control engine and replace identity constants only."""
    require(FROZEN_QUALIFIER.is_file() and not FROZEN_QUALIFIER.is_symlink(), "frozen qualifier is missing or redirected")
    require(sha256(FROZEN_QUALIFIER) == FROZEN_QUALIFIER_SHA256, "frozen qualifier source digest changed")
    spec = importlib.util.spec_from_file_location("bifrost_v0144_frozen_controls", FROZEN_QUALIFIER)
    require(spec is not None and spec.loader is not None, "cannot import frozen qualifier")
    controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controls)
    controls.EXPECTED_VERSION = EXPECTED_VERSION
    controls.EXPECTED_BUILD_IDENTITY = EXPECTED_BUILD_IDENTITY
    controls.EXPECTED_BINARY_SHA256 = EXPECTED_BINARY_SHA256
    controls.PUBLIC_TAG_COMMIT = PUBLIC_TAG_COMMIT
    require(controls.TIMEOUT_SECONDS == 30 and controls.TOTAL_TIMEOUT_SECONDS == 600,
            "frozen per-control or total timeout changed")
    original_environment = controls._environment

    def environment(**kwargs):
        result = original_environment(**kwargs)
        result["BIFROST_OPEN_PACKS_DISABLE"] = "1"
        return result

    controls._environment = environment
    controls.ENVIRONMENT_ALLOWLIST = tuple(dict.fromkeys((*controls.ENVIRONMENT_ALLOWLIST, "BIFROST_OPEN_PACKS_DISABLE")))
    return controls


def capture(bifrost: Path, output: Path, *, root: Path = ROOT,
            runner: Callable[..., int] | None = None) -> int:
    """Capture one fresh attempt and retain metadata even on strict failure."""
    output = Path(output)
    require(output.is_absolute(), "--output must be an absolute path")
    require(not output.is_symlink(), "--output must not be a symlink")
    output = output.resolve(strict=False)
    qualification_root = (root / "reports/releases/v0.9.2/qualification/bifrost-v0144-01").resolve()
    require(output != qualification_root and output.is_relative_to(qualification_root),
            "--output must be a new child of the v0.14.4 qualification directory")
    require(not output.exists() and not output.is_symlink(), f"--output already exists: {output}")
    identity, acquisition_ref = acquired_identity(root)
    auth, authorization_ref = authorization(root)
    require(Path(bifrost) == Path(identity["path"]), "--bifrost differs from the acquired official binary")
    controls = controls_for_release()
    result = controls.capture(Path(bifrost), output, root=root, runner=runner)
    require(output.is_dir() and (output / "qualification.json").is_file(),
            "strict capture did not retain its qualification receipt")
    context = {
        "schema": "v092-bifrost-v0144-capture-context/v1",
        "tool": identity,
        "acquisition_receipt": acquisition_ref,
        "human_authorization": authorization_ref,
        "capture_implementation": {
            "path": str(Path(__file__).resolve().relative_to(root)),
            "sha256": sha256(Path(__file__).resolve()),
        },
        "frozen_qualifier": {
            "path": str(FROZEN_QUALIFIER.relative_to(root)),
            "sha256": FROZEN_QUALIFIER_SHA256,
        },
        "controls": {"invocations": 44, "per_control_timeout_seconds": 30, "total_timeout_seconds": 600},
        "environment": {"BIFROST_OPEN_PACKS_DISABLE": "1"},
        "attempt_path": str(output.relative_to(root)),
        "strict_exit_code": int(result),
        "strict_status": load_json(output / "qualification.json").get("qualification"),
    }
    (output / "capture-context.json").write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    controls._write_artifact_hashes(output)
    return int(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bifrost", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    status = capture(args.bifrost, args.output)
    receipt = load_json(args.output / "qualification.json")
    print(json.dumps({
        "capture": str(args.output),
        "strict_qualification": receipt.get("qualification"),
        "strict_exit_code": status,
        "invocations": receipt.get("invocations"),
    }, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
