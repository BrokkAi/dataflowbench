#!/usr/bin/env python3
"""Assemble an immutable replacement-23 packet without running experiments.

Identity and review are separate steps: review binds the already written core,
then sealing adds those reviews in the outer wrapper.  Neither step imports a
frozen analyzer executor or grants permission to dispatch.  Missing future
source/ledger artifacts fail closed rather than receiving placeholder values.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-23.py"


def _protocol(root: Path) -> Any:
    path = root / PROTOCOL_PATH
    spec = importlib.util.spec_from_file_location("replacement23_packet_protocol", path)
    if spec is None or spec.loader is None:
        raise ValueError("replacement-23 protocol is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_core_fields(root: Path | str, core: Mapping[str, Any], *,
                        policy_source: Mapping[str, str],
                        policy_runtime: Mapping[str, str],
                        incoming_recovery: Mapping[str, str],
                        runtime_module_graph: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    """Derive only graph/closure fields from existing exact root artifacts.

    The runtime and policy adapters are explicit reviewed inputs, never guessed from
    filenames. This is read-only preparation; no module in the graph is loaded.
    Source inputs come from the actual replacement contract, not its historical
    continuation. Final manifest SHA remains an external post-sealing argument.
    """
    root = Path(root).resolve()
    protocol = _protocol(root)
    contract = protocol._json(protocol._bound(root, core["contract"], "packet replacement contract"),
                              "packet replacement contract")
    refs = {"bridge18":dict(core["frozen_bridge_source"]),
            "replacement23":dict(core["implementation"]), **protocol.RUNTIME_FROZEN_REFS,
            "incoming_recovery":dict(incoming_recovery),
            "policy_source":dict(policy_source), "policy_runtime":dict(policy_runtime),
            "protocol23":dict(core["implementation"]),
            "admission23":dict(core["bifrost_admission_source"]),
            "supervisor23":dict(core["bifrost_supervisor_source"])}
    protocol.require(isinstance(runtime_module_graph, dict), "packet requires an explicit complete runtime graph")
    for name, ref in refs.items():
        protocol.require(runtime_module_graph.get(name) == ref,
                         f"explicit runtime graph {name} differs from packet role binding")
    result = {"manifest_path":protocol.MANIFEST_PATH,
              "runtime_module_graph":{name:dict(ref) for name, ref in runtime_module_graph.items()},
              "source_inputs":contract.get("source_inputs")}
    protocol.validate_runtime_core(root, {**core, **result})
    return result


def prepare_identity(root: Path | str, core: Mapping[str, Any]) -> dict[str, str]:
    """Validate all static bindings before writing the immutable core."""
    root = Path(root).resolve()
    protocol = _protocol(root)
    value = dict(core)
    raw = protocol.canonical_json(value)
    ref = {"path": protocol.IDENTITY_PATH, "sha256": protocol.sha256(raw)}
    protocol._validate_core(root, value, ref)
    return protocol.write_immutable(root, protocol.IDENTITY_PATH, value)


def seal(root: Path | str, independent_review: Mapping[str, str],
         final_review: Mapping[str, str]) -> dict[str, str]:
    """Add exact reviews and deterministic ordered slots to an existing core.

    This checks review bytes and builds the complete wrapper in memory before
    writing it; a failed review cannot leave a finalized wrapper on disk.
    """
    root = Path(root).resolve()
    protocol = _protocol(root)
    raw = protocol._read(root, protocol.IDENTITY_PATH)
    core = protocol._json(raw, "packet core")
    identity = {"path": protocol.IDENTITY_PATH, "sha256": protocol.sha256(raw)}
    protocol._validate_core(root, core, identity)
    reviews = {"independent_review": dict(independent_review), "final_review": dict(final_review)}
    for name, kind in zip(reviews, protocol.REVIEW_TYPES):
        review = protocol._json_ref(root, reviews[name], name)
        protocol.require(review.get("status") == "approved" and
                         review.get("automatic_retry") is False and
                         review.get("review_type") == kind and
                         review.get("core_identity") == identity and
                         review.get("reviewed_sources") == core["review_policy"]["reviewed_sources"],
                         f"{name} does not approve this exact immutable core")
    prefix = protocol._jsonl(protocol._bound(root, core["continuation_prefix"],
                                            "continuation prefix", rows=True), "continuation prefix")
    slots = {}
    predecessors = []
    for index, group in enumerate(core["replacement_groups"]):
        retained = [row for row in prefix if row.get("group_id") == group and
                    row.get("status") == "completed"]
        protocol.require(len(retained) == 1, f"expected exactly one completed predecessor: {group}")
        row = retained[0]
        protocol._successful_identity(row, group_id=group, attempt_id=row["attempt_id"],
                                      source_commit=row.get("source_commit"),
                                      plan_commit=row.get("plan_commit"),
                                      contract_sha256=row.get("contract_sha256"),
                                      execution_series=1, label=f"packet predecessor {group}")
        expected = f"{group}-attempt-{2 if group == 'bifrost-c-kernel' else 1:02d}-series-01"
        protocol.require(row["attempt_id"] == expected, f"historical attempt counters differ: {group}")
        original_path = f"reports/releases/v0.9.2/attempts/{expected}/completed.json"
        original_raw = protocol._read(root, original_path)
        original = protocol._json(original_raw, "retained completed receipt")
        protocol._successful_identity(
            original, group_id=group, attempt_id=expected,
            source_commit=row["source_commit"], plan_commit=row["plan_commit"],
            contract_sha256=row["contract_sha256"], execution_series=1,
            label=f"retained completed receipt {group}")
        for key in ("status", "group_id", "attempt_id", "source_commit", "plan_commit",
                    "contract_sha256", "exit_code", "timed_out", "capacity_loss", "execution_series", "tool"):
            protocol.require(original.get(key) == row.get(key),
                             f"retained completed receipt differs from prefix for {group}: {key}")
        directory = f"{core['sidecar_namespace']}/{index:02d}-{group}"
        slots[group] = {
            "group_id": group, "attempt_id": protocol._attempt_id(group),
            "admission_path": f"{directory}/admission.json",
            "completion_path": f"{directory}/completion.json",
            "phase_gate_path": f"{directory}/phase-gate.json",
            "predecessor_attempt_id": expected,
            "predecessor_receipt_path": f"{directory}/predecessor.json",
        }
        predecessors.append((slots[group]["predecessor_receipt_path"], original_raw))
    config = f"{core['sidecar_namespace']}/configuration"
    wrapper = {
        "schema": protocol.MANIFEST_SCHEMA, "finalized": True,
        "core_identity": identity, **reviews,
        "bifrost_admission_source": core["bifrost_admission_source"],
        "bifrost_supervisor_source": core["bifrost_supervisor_source"],
        "execution_admission_slots": slots,
        "configuration_admission_slot": {"admission_path": f"{config}/admission.json",
                                          "receipt_path": f"{config}/receipt.json"},
    }
    # Validate every original receipt before publishing any sidecar.  Keep
    # exact historical bytes, including formatting, and retain the originals.
    # A partial publication is immutable and can only be resumed identically.
    for path, raw in predecessors:
        protocol.write_immutable_bytes(root, path, raw)
    return protocol.write_immutable(root, protocol.MANIFEST_PATH, wrapper)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    identity = commands.add_parser("identity")
    identity.add_argument("--core", type=Path, required=True)
    wrapper = commands.add_parser("seal")
    wrapper.add_argument("--independent-review", required=True, help="JSON path/SHA reference")
    wrapper.add_argument("--final-review", required=True, help="JSON path/SHA reference")
    args = parser.parse_args()
    if args.command == "identity":
        value = json.loads(args.core.read_bytes())
        result = prepare_identity(args.root, value)
    else:
        result = seal(args.root, json.loads(args.independent_review), json.loads(args.final_review))
    print(json.dumps({"status": "static-packet-written", "execution_authorized": False,
                      "artifact": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
