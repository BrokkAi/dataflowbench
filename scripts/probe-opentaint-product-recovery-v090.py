#!/usr/bin/env python3
"""Run the v0.9.0 OpenTaint probe against explicitly pinned recovery inputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = PurePosixPath("scripts/probe-opentaint-product-recovery-v090.py")
IMPLEMENTATION_REL = PurePosixPath("scripts/probe-opentaint-product-v090.py")
CONTRACT_REL = PurePosixPath("reports/releases/v0.9.0/execution-v1/contract.json")
EXECUTION_PREFIX = PurePosixPath("reports/releases/v0.9.0/execution-v1")
COMMAND_TIMEOUT_SECONDS = 300


class RecoveryContractError(ValueError):
    """The recovery contract does not bind the exact reviewed inputs."""


def _load_original_probe():
    source = Path(__file__).resolve().with_name("probe-opentaint-product-v090.py")
    spec = importlib.util.spec_from_file_location("opentaint_product_v090_original", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load original OpenTaint probe: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


_PROBE, _IMPLEMENTATION_SOURCE = _load_original_probe()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value: object, description: str) -> str:
    if (not isinstance(value, str) or len(value) != 64 or
            any(char not in "0123456789abcdef" for char in value)):
        raise RecoveryContractError(f"{description} must be a lowercase SHA-256")
    return value


def _reject_symlink_components(root: Path, path: Path, description: str) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RecoveryContractError(f"{description} escapes the repository") from exc
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise RecoveryContractError(f"{description} traverses a symlink: {current}")


def _execution_file(root: Path, value: object, description: str) -> tuple[str, Path]:
    if not isinstance(value, str) or "\\" in value:
        raise RecoveryContractError(f"{description} path must be execution-v1 relative")
    relative = PurePosixPath(value)
    if (relative.is_absolute() or value != relative.as_posix() or
            any(part in ("", ".", "..") for part in relative.parts) or
            relative.parts[:len(EXECUTION_PREFIX.parts)] != EXECUTION_PREFIX.parts):
        raise RecoveryContractError(f"{description} path must stay inside execution-v1")
    path = root.joinpath(*relative.parts)
    _reject_symlink_components(root, path, description)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RecoveryContractError(f"{description} is missing: {path}") from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise RecoveryContractError(f"{description} is not a regular file inside the repository")
    return relative.as_posix(), resolved


def _implementation_file(root: Path, value: object) -> tuple[str, Path]:
    expected = IMPLEMENTATION_REL.as_posix()
    if value != expected:
        raise RecoveryContractError(f"implementation path must be exactly {expected}")
    path = root.joinpath(*IMPLEMENTATION_REL.parts)
    _reject_symlink_components(root, path, "original OpenTaint probe implementation")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RecoveryContractError(f"original OpenTaint probe implementation is missing: {path}") from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise RecoveryContractError("original OpenTaint probe implementation is not a regular repository file")
    return expected, resolved


def _read_bound_record(root: Path, identities: Mapping[str, object], record: object,
                       description: str) -> tuple[dict, str, Path]:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise RecoveryContractError(f"opentaint_recovery.{description} must contain only path and sha256")
    relative, path = _execution_file(root, record.get("path"), description)
    expected = _digest(record.get("sha256"), f"{description} SHA-256")
    if identities.get(relative) != expected:
        raise RecoveryContractError(f"{description} SHA-256 is not bound by contract input_identities")
    raw = path.read_bytes()
    if _sha256(raw) != expected:
        raise RecoveryContractError(f"{description} bytes differ from the contract SHA-256")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecoveryContractError(f"{description} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RecoveryContractError(f"{description} must be a JSON object")
    return value, relative, path


def _validate_bundle_root(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise RecoveryContractError("recovered OpenTaint bundle_root must be an absolute path")
    bundle = Path(value)
    for temporary in (Path('/tmp'), Path('/private/tmp'), Path('/private/var/folders')):
        if bundle == temporary or temporary in bundle.parents:
            raise RecoveryContractError('recovered bundle must use durable storage; temporary roots are rejected')
    _reject_symlink_components(Path(bundle.anchor), bundle, 'recovered OpenTaint bundle root')
    try:
        resolved = bundle.resolve(strict=True)
    except OSError as exc:
        raise RecoveryContractError('recovered OpenTaint bundle root is missing') from exc
    if resolved != bundle or not bundle.is_dir():
        raise RecoveryContractError('recovered bundle must be a canonical directory')

    return bundle


def _bind_recovery(root: Path, contract_path: str | Path,
                   probe_script_path: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(root).resolve(strict=True)
    raw_contract_path = Path(contract_path)
    if raw_contract_path.is_absolute():
        try:
            raw_contract_path = raw_contract_path.relative_to(root)
        except ValueError as exc:
            raise RecoveryContractError("contract must be inside the repository execution-v1 plan") from exc
    contract_rel, contract_file = _execution_file(root, raw_contract_path.as_posix(), "execution contract")
    if contract_rel == "" or not contract_file.as_posix().startswith((root / EXECUTION_PREFIX).as_posix() + "/"):
        raise RecoveryContractError("contract must be inside the versioned execution-v1 plan")
    try:
        contract = json.loads(contract_file.read_bytes())
    except json.JSONDecodeError as exc:
        raise RecoveryContractError("execution contract is not valid JSON") from exc
    if not isinstance(contract, dict):
        raise RecoveryContractError("execution contract must be a JSON object")

    recovery = contract.get("opentaint_recovery")
    if not isinstance(recovery, dict) or set(recovery) != {"restoration", "runtime_tree", "implementation"}:
        raise RecoveryContractError(
            "contract must provide opentaint_recovery restoration, runtime_tree and implementation refs"
        )
    identities = contract.get("input_identities")
    if not isinstance(identities, dict):
        raise RecoveryContractError("contract input_identities must bind OpenTaint recovery inputs")

    implementation = recovery["implementation"]
    if not isinstance(implementation, dict) or set(implementation) != {"path", "sha256"}:
        raise RecoveryContractError("opentaint_recovery.implementation must contain only path and sha256")
    implementation_rel, implementation_path = _implementation_file(root, implementation.get("path"))
    implementation_sha = _digest(implementation.get("sha256"), "original OpenTaint probe SHA-256")
    if identities.get(implementation_rel) != implementation_sha:
        raise RecoveryContractError("original OpenTaint probe SHA-256 is not bound by contract input_identities")
    implementation_bytes = implementation_path.read_bytes()
    if (_sha256(implementation_bytes) != implementation_sha or
            _sha256(_IMPLEMENTATION_SOURCE.read_bytes()) != implementation_sha):
        raise RecoveryContractError("original OpenTaint probe differs from its contract-bound SHA-256")

    restoration, restoration_rel, _ = _read_bound_record(
        root, identities, recovery["restoration"], "restoration")
    runtime_tree, runtime_rel, _ = _read_bound_record(
        root, identities, recovery["runtime_tree"], "runtime_tree")
    if (restoration.get("schema") != "runtime-restoration/v1" or
            restoration.get("exact_file_membership") is not True or
            restoration.get("runtime_executed") is not False or
            restoration.get("verified_files") != 329):
        raise RecoveryContractError("recovery restoration must verify exact unexecuted 329-file membership")
    if runtime_tree.get("schema") != "release-runtime-tree/v1":
        raise RecoveryContractError("recovered runtime tree has an unsupported schema")
    bundle = _validate_bundle_root(root, restoration.get("bundle_root"))
    if runtime_tree.get("root") != restoration.get("bundle_root"):
        raise RecoveryContractError("recovered runtime manifest root differs from restoration bundle_root")

    probe_path = Path(probe_script_path) if probe_script_path is not None else root / SCRIPT_REL
    if not probe_path.is_absolute():
        probe_path = root / probe_path
    probe_path = probe_path.resolve(strict=True)
    if not probe_path.is_relative_to(root) or not probe_path.is_file():
        raise RecoveryContractError("recovery wrapper must be a regular file inside the repository")

    # Bind the original checker to the prospective references. It retains its
    # independent inventory, wrapper, historical identity and full-tree checks.
    _PROBE.RESTORATION_REL = Path(restoration_rel)
    _PROBE.RUNTIME_TREE_REL = Path(runtime_rel)
    _PROBE.SCRIPT_REL = Path(SCRIPT_REL)
    return contract_file, probe_path


def prepare_recovery(root: Path = ROOT, contract_path: str | Path = CONTRACT_REL,
                     *, probe_script_path: str | Path | None = None) -> dict:
    """Validate recovery refs and the original probe's complete predispatch contract."""
    resolved_root = Path(root).resolve(strict=True)
    contract_file, script_path = _bind_recovery(resolved_root, contract_path, probe_script_path)
    return _PROBE._verify_v090_contract(resolved_root, contract_file, script_path)


def capture(repo_root: Path = ROOT, contract_path: str | Path = CONTRACT_REL,
            output_root: str | Path = "reports/raw/opentaint-product-v090", *,
            probe_script_path: str | Path | None = None,
            runner: Callable[..., object] | None = None,
            timeout: int = COMMAND_TIMEOUT_SECONDS) -> int:
    root = Path(repo_root).resolve(strict=True)
    _, script_path = _bind_recovery(root, contract_path, probe_script_path)
    return _PROBE.capture(root, contract_path, output_root,
                          probe_script_path=script_path, runner=runner, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path(CONTRACT_REL.as_posix()))
    parser.add_argument("--output-root", type=Path,
                        default=Path("reports/raw/opentaint-product-v090"))
    parser.add_argument("--timeout-seconds", type=int, default=COMMAND_TIMEOUT_SECONDS)
    args = parser.parse_args()
    try:
        if args.timeout_seconds < 1:
            raise RecoveryContractError("timeout-seconds must be positive")
        return capture(contract_path=args.contract, output_root=args.output_root,
                       timeout=args.timeout_seconds)
    except (OSError, RecoveryContractError, _PROBE.ProbeError, json.JSONDecodeError) as exc:
        print(f"probe-opentaint-product-recovery-v090: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
