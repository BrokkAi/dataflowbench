#!/usr/bin/env python3
"""Bind a fresh v0.14.4 control review to the authorized 20 Bifrost groups."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
QUALIFICATION_DIR = Path(__file__).resolve().parent
AUTHORIZATION = QUALIFICATION_DIR / "human-authorization-01.json"
PARENT_CONTRACT = ROOT / "reports/releases/v0.9.0/execution-v1/contract.json"
LEDGER = ROOT / "reports/releases/v0.9.2/ledger-v1.jsonl"


class BindingError(ValueError):
    """The control review, authorization, scope, or ledger prefix is invalid."""


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
        raise BindingError(f"cannot read JSON evidence: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BindingError(f"JSON evidence is not an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BindingError(message)


def _import_review():
    path = QUALIFICATION_DIR / "review-bifrost-v0144-01.py"
    spec = importlib.util.spec_from_file_location("bifrost_v0144_review", path)
    require(spec is not None and spec.loader is not None, "cannot import v0.14.4 reviewer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approved_binding(review: dict, groups: list[str], authorization: dict,
                     references: dict) -> dict:
    """Build the execution-eligible but limited qualification document."""
    require(review.get("schema") == "v092-bifrost-v0144-control-review/v1" and
            review.get("status") == "measurement-with-known-limits" and
            review.get("execution_eligible") is True,
            "fresh v0.14.4 control review is not execution eligible")
    require(review.get("full_policy_qualification") is False and
            review.get("invocations") == 44 and review.get("unbound_endpoint_controls") == 15 and
            review.get("sanitizer_controls") == 15,
            "control review has an unexpected scope or overstates qualification")
    require(review.get("native", {}).get("interpretation") == "not-evaluated" and
            review.get("native", {}).get("clean") is False,
            "empty native catalog must remain not-evaluated")
    require(review.get("tool", {}).get("version") == "0.14.4" and
            review["tool"].get("build_identity") == "ff5cf473f4ad414751911ff93ef79e1df1d35823" and
            review["tool"].get("sha256") == "a3aa17a18be33e1e841c1bf317c6ca35a6aa3aaef452c607fafbb3b83aeec399" and
            review["tool"].get("public_tag_commit") == "786891f9ed19d2086dfd6242ff15ca904b610620",
            "review is bound to a different Bifrost artifact")
    authorized_groups = authorization.get("scope")
    require(authorization.get("schema") == "v092-new-bifrost-target-human-authorization/v1" and
            authorization.get("target_version") == "0.14.4" and
            authorization.get("source_integration_acquisition_tests_qualification_and_fresh_run_authorized") is True and
            authorization.get("supersedes_preparation_only_hold_for_new_target_qualification_and_benchmark") is True and
            authorization.get("publication_still_requires_separate_human_review_and_explicit_approval") is True,
            "human authorization does not match this qualification/publication boundary")
    require(isinstance(authorized_groups, list) and groups == authorized_groups and len(groups) == 20 and
            len(set(groups)) == 20 and all(group.startswith("bifrost-") for group in groups),
            "qualification group scope differs from the exact authorization")
    return {
        "schema": "v092-bifrost-release-qualification/v1",
        "status": "measurement-with-known-limits",
        "execution_eligible": True,
        "full_policy_qualification": False,
        "groups": groups,
        "tool": review["tool"],
        "identity_components": [],
        "control_review": references["control_review"],
        "capture": references["capture"],
        "authorization": references["authorization"],
        "scope_source": references["scope_source"],
        "append_after_ledger": references["append_after_ledger"],
        "binding_implementation": references["binding_implementation"],
        "strict_capture": review["strict_capture"],
        "limits": [
            "Full policy qualification is false; this receipt only authorizes the reviewed Bifrost groups.",
            "Unbound endpoint controls are not evidence of cleanliness.",
            "The native empty catalog remains not-evaluated.",
            "Any retained partial positive control is inconclusive and matches its exact prior typed proof.",
            "Publication still requires separate human review and explicit approval.",
        ],
    }


def bind(review_path: Path, capture_path: Path, output: Path, *, root: Path = ROOT) -> dict:
    review_path = Path(review_path).absolute()
    capture_path = Path(capture_path).absolute()
    require(not review_path.is_symlink(), "review file is a symlink")
    require(not capture_path.is_symlink(), "capture root is a symlink")
    review_path = review_path.resolve(strict=True)
    capture_path = capture_path.resolve(strict=True)
    output = Path(output)
    qualification_root = (root / "reports/releases/v0.9.2/qualification/bifrost-v0144-01").resolve()
    require(review_path.is_relative_to(qualification_root) and capture_path.is_relative_to(qualification_root),
            "review and capture must be in the v0.14.4 qualification namespace")
    require(review_path.is_file() and not review_path.is_symlink(), "review file is missing or a symlink")
    require(AUTHORIZATION.is_file() and not AUTHORIZATION.is_symlink(), "human authorization is missing or a symlink")
    authorization = load_json(AUTHORIZATION)
    auth_sha = sha256(AUTHORIZATION)
    review_module = _import_review()
    replayed = review_module.review_capture(capture_path, root=root)
    retained = load_json(review_path)
    require(retained == replayed, "retained control review differs from fresh evidence replay")

    require(PARENT_CONTRACT.is_file() and not PARENT_CONTRACT.is_symlink(),
            "v0.9.0 parent contract is missing or a symlink")
    parent = load_json(PARENT_CONTRACT)
    groups = [row["id"] for row in parent.get("groups", []) if row.get("tool") == "bifrost"]
    require(len(groups) == 20 and len(set(groups)) == 20, "historical Bifrost group scope changed")
    require(groups == authorization.get("scope"), "authorization does not match parent contract Bifrost scope")
    require(LEDGER.is_file() and not LEDGER.is_symlink(), "append-only v0.9.2 ledger is missing")
    with LEDGER.open("rb") as ledger_stream:
        ledger_rows = sum(1 for line in ledger_stream if line.strip())
    ledger_sha = sha256(LEDGER)
    ledger_authority = authorization.get("append_after_ledger", {})
    require(ledger_rows == ledger_authority.get("rows") == 109 and
            ledger_sha == ledger_authority.get("sha256"),
            "append-only ledger no longer matches the authorized pre-run prefix")
    review_path_text = str(review_path.relative_to(root))
    capture_path_text = str(capture_path.relative_to(root))
    references = {
        "control_review": {"path": review_path_text, "sha256": sha256(review_path)},
        "capture": {"path": capture_path_text,
                    "manifest_sha256": sha256(capture_path / "artifact-hashes.json"),
                    "qualification_sha256": sha256(capture_path / "qualification.json")},
        "authorization": {"path": str(AUTHORIZATION.relative_to(root)), "sha256": auth_sha},
        "scope_source": {"path": str(PARENT_CONTRACT.relative_to(root)), "sha256": sha256(PARENT_CONTRACT)},
        "append_after_ledger": {"path": str(LEDGER.relative_to(root)), "rows": ledger_rows,
                                 "sha256": ledger_sha},
        "binding_implementation": {"path": str(Path(__file__).resolve().relative_to(root)),
                                   "sha256": sha256(Path(__file__).resolve())},
    }
    result = approved_binding(replayed, groups, authorization, references)
    output = output.absolute()
    require(not output.is_symlink(), "--output must not be a symlink")
    output = output.resolve(strict=False)
    require(output.is_relative_to(qualification_root) and output != qualification_root,
            "--output must be a child of the v0.14.4 qualification directory")
    require(not output.exists() and not output.is_symlink(), f"--output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = bind(args.review, args.capture, args.output)
    print(json.dumps({"status": result["status"], "execution_eligible": True,
                      "full_policy_qualification": False, "groups": len(result["groups"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
