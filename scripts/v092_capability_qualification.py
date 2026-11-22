"""v0.9.2 qualification validator restricted to the capability lane.

The original shared validator remains unchanged. This adapter permits only the
single new append-only qualification root while delegating receipt and control
replay validation to the original implementation.
"""

from __future__ import annotations

from pathlib import Path

import v092_qualification as original


QUALIFICATION_ROOT = (
    "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/capability-qualification/"
)

expected_identity_components = original.expected_identity_components
plan_projection = original.plan_projection
plan_projection_sha256 = original.plan_projection_sha256
read_json = original.read_json


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _check_new_root_reference(reference: object) -> None:
    require(
        isinstance(reference, dict) and set(reference) == {"path", "sha256"},
        "fresh qualification receipt must be an exact path/SHA reference",
    )
    path_text = reference["path"]
    require(
        isinstance(path_text, str) and path_text.startswith(QUALIFICATION_ROOT),
        "fresh qualification evidence must use the v0.9.2-03 capability preparation root",
    )
    path = Path(path_text)
    require(
        not path.is_absolute() and ".." not in path.parts,
        "fresh qualification evidence path is unsafe",
    )


def validate_common_receipt(root: Path, plan: dict, reference: object, *, group_id: str):
    """Apply the shared replay validator after constraining its accepted root."""
    _check_new_root_reference(reference)
    prior_root = original.QUALIFICATION_ROOT
    try:
        original.QUALIFICATION_ROOT = QUALIFICATION_ROOT
        return original.validate_common_receipt(
            root, plan, reference, group_id=group_id
        )
    finally:
        original.QUALIFICATION_ROOT = prior_root


def validate_capability_binding(root: Path, plan: dict) -> dict:
    """Validate the immutable v0.9.0 case capability source before dispatch."""
    import joern_normal_runner_v092_capability as runner

    return runner.validate_capability_binding(root, plan)


def verify_raw_capability_rows(root: Path, plan: dict, run: dict) -> dict:
    """Verify all measured raw rows against the immutable case-bound source."""
    import joern_normal_runner_v092_capability as runner

    return runner.verify_raw_capability_rows(root, plan, run)
