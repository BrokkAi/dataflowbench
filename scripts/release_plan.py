#!/usr/bin/env python3
"""Shared release-plan loading and execution guards."""

from __future__ import annotations

import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def release_base(release: str) -> pathlib.Path:
    if not release.startswith("v") or "/" in release or ".." in release:
        raise ValueError(f"invalid release name: {release}")
    return ROOT / "reports" / "releases" / release


def load_plan(release: str) -> tuple[pathlib.Path, pathlib.Path, dict]:
    base = release_base(release)
    candidates = [base / "plan.json", base / "rerun-plan.json"]
    plan_path = next((path for path in candidates if path.is_file()), None)
    if plan_path is None:
        raise ValueError(f"no release plan found under {base.relative_to(ROOT)}")
    plan = json.loads(plan_path.read_text())
    if plan.get("release") != release:
        raise ValueError(
            f"{plan_path.relative_to(ROOT)} declares {plan.get('release')!r}, expected {release!r}"
        )
    return base, plan_path, plan


def require_executable_plan(plan_path: pathlib.Path, plan: dict) -> None:
    status = plan.get("status")
    if status in {"preparation-not-executable", "preparation"}:
        raise ValueError(
            f"{plan_path.relative_to(ROOT)} is {status}; finalize exact argv, identities, "
            "and current case membership before execution"
        )
    if "fixture_revision" not in plan or "input_commits" not in plan:
        raise ValueError(
            f"{plan_path.relative_to(ROOT)} lacks fixture_revision or input_commits"
        )
    if "population" not in plan:
        raise ValueError(f"{plan_path.relative_to(ROOT)} lacks an exact population identity")


def command_steps(base: pathlib.Path, plan: dict, stage: str) -> list[dict]:
    supplemental_path = base / "supplemental-plan.json"
    supplemental = (
        json.loads(supplemental_path.read_text()).get("commands", [])
        if supplemental_path.is_file()
        else []
    )
    if stage == "reports":
        return [row for row in plan["reports"] if not row["id"].endswith("-native")]
    if stage == "native":
        return [row for row in plan["reports"] if row["id"].endswith("-native")]
    if stage == "repeats":
        repeat_path = base / "overlap-rerun-plan.json"
        if not repeat_path.is_file():
            raise ValueError(f"{repeat_path.relative_to(ROOT)} is required for repeats")
        ids = json.loads(repeat_path.read_text())["repeat_once"]
        reports = {row["id"]: row for row in plan["reports"]}
        return [reports[identifier] for identifier in ids]
    if stage == "probes":
        return [*plan.get("script_probes", []), *supplemental]
    return list(plan[stage])


def display_argv(step: dict) -> list[str]:
    return step.get("argv") or step.get("command_template") or []


def require_executable_steps(steps: list[dict]) -> None:
    incomplete = []
    for step in steps:
        unresolved_membership = step.get("case_membership") in {
            "pending",
            "must preregister current runner selection before execution; old release membership is not reused",
        }
        if not step.get("argv") or unresolved_membership:
            incomplete.append(step.get("id", "<missing-id>"))
    if incomplete:
        shown = ", ".join(incomplete[:8])
        suffix = " ..." if len(incomplete) > 8 else ""
        raise ValueError(f"release steps are not executable: {shown}{suffix}")
