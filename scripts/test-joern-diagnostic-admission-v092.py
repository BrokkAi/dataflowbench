#!/usr/bin/env python3
"""Positive and near-miss tests for the Joern known-binding-limit admission."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import joern_diagnostic_admission_v092 as admission
import joern_normal_controls_v1 as historical_controls
import joern_normal_runner_v092 as runner


class DiagnosticAdmissionReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cpg = self.root / "cpg.bin"
        self.cpg.write_bytes(b"pinned CPG bytes")
        self.identity = {
            "tool": "joern",
            "tool_version": "4.0.660",
            "tool_build_identity": "joern-cli:4.0.660;engine:" + "a" * 64 + ";frontend:" + "b" * 64,
            "adapter_version": "joern-normal-v092",
        }
        self.components = [{"name": "joern-root", "sha256": "c" * 64}]
        self.plan = {"identity": self.identity, "identity_components": self.components}
        self.config, self.graph = self._graph_and_config()
        self.raw = {
            "case_id": admission.OPAQUE_CASES[1],
            "control": admission.OPAQUE_CASES[1],
            "arm": "on",
            "identity": copy.deepcopy(self.identity),
            "identity_components": copy.deepcopy(self.components),
            "raw_outcome": "inconclusive",
            "state": "inconclusive",
            "diagnostics": [admission.EXPECTED_INCOMPLETE],
        }

    def _graph_and_config(self):
        wrapper_specs = [
            {
                "method": row["method"],
                "owner": row["owner"],
                "parameter_indices": row["parameter_indices"],
                "flows": row["flows"],
            }
            for row in historical_controls.WRAPPERS
        ]
        selected = wrapper_specs[0]
        config = {
            "source_methods": [admission.SOURCE_LOCAL],
            "sink_methods": [admission.SINK_LOCAL],
            "source_anchors": [{"file": "main.swift", "line_hint": 26}],
            "sink_anchors": [{"file": "main.swift", "line_hint": 27}],
            "wrappers": wrapper_specs,
            "selected_wrapper": selected["method"],
        }
        methods = [
            {"id": "src-local", "full_name": admission.SOURCE_LOCAL, "external": False,
             "node": {"id": "src-local", "label": "METHOD", "file": "main.swift", "line": 22},
             "parameters": []},
            {"id": "sink-local", "full_name": admission.SINK_LOCAL, "external": False,
             "node": {"id": "sink-local", "label": "METHOD", "file": "main.swift", "line": 23},
             "parameters": [{"index": 1, "type": "Swift.String", "node": {"id": "sink-param"}}]},
            {"id": "src-external", "full_name": admission.SOURCE_EXTERNAL, "external": True,
             "node": {"id": "src-external", "label": "METHOD", "file": "builtintypes", "line": -1},
             "parameters": []},
            {"id": "sink-external", "full_name": admission.SINK_EXTERNAL, "external": True,
             "node": {"id": "sink-external", "label": "METHOD", "file": "builtintypes", "line": -1},
             "parameters": []},
        ]
        wrapper_ids = []
        for index, spec in enumerate(wrapper_specs):
            method_id = f"wrapper-{index}"
            wrapper_ids.append(method_id)
            params = [
                {"index": parameter_index,
                 "type": spec["owner"] if parameter_index == 0 else "Swift.String",
                 "node": {"id": f"{method_id}-param-{parameter_index}"}}
                for parameter_index in spec["parameter_indices"]
            ]
            methods.append({
                "id": method_id,
                "full_name": spec["method"],
                "external": False,
                "node": {"id": method_id, "label": "METHOD", "file": "main.swift", "line": 8 + index * 4},
                "parameters": params,
            })
        wrapper_evidence = [
            {"method_id": method_id, "owner_id": "owner", "owner_full_name": wrapper_specs[index]["owner"],
             "owner_ast_method_ids": wrapper_ids, "return_types": ["Swift.String"]}
            for index, method_id in enumerate(wrapper_ids)
        ]
        calls = [
            {"node": {"id": "source-call", "label": "CALL", "file": "main.swift", "line": 26},
             "method_full_name": admission.SOURCE_EXTERNAL, "callee_ids": ["src-external"],
             "arguments": []},
        ]
        selected_method_id = wrapper_ids[0]
        wrapper_arguments = [
            {"index": parameter_index, "node": {"id": f"arg-{parameter_index}"}}
            for parameter_index in selected["parameter_indices"]
        ]
        calls.append({
            "node": {"id": "wrapper-call", "label": "CALL", "file": "main.swift", "line": 27},
            "method_full_name": selected["method"], "callee_ids": [selected_method_id],
            "arguments": wrapper_arguments,
        })
        calls.append({
            "node": {"id": "sink-call", "label": "CALL", "file": "main.swift", "line": 27},
            "method_full_name": admission.SINK_EXTERNAL, "callee_ids": ["sink-external"],
            "arguments": [
                {"index": 0, "node": {"id": "self"}},
                {"index": 1, "node": {"id": "wrapper-call", "label": "CALL", "file": "main.swift", "line": 27}},
            ],
        })
        graph = {
            "state": "analyzed",
            "frontend": "SWIFTSRC",
            "query_completed": True,
            "analysis_completeness": copy.deepcopy(admission.ANALYSIS_COMPLETENESS),
            "methods": methods,
            "calls": calls,
            "source_method_ids": ["src-local"],
            "sink_method_ids": ["sink-local"],
            "source_observations": [],
            "sink_observations": [],
            "source_nodes": [],
            "sink_nodes": [],
            "flows": [],
            "wrapper_evidence": wrapper_evidence,
        }
        return config, graph

    def _validate(self, *, graph=None, config=None, raw=None):
        return admission.validate_opaque_endpoint_gap(
            self.graph if graph is None else graph,
            self.config if config is None else config,
            self.raw if raw is None else raw,
            plan=self.plan,
            cpg_path=self.cpg,
            case_id=admission.OPAQUE_CASES[1],
            arm="on",
        )

    def test_exact_native_declarations_and_external_edges_are_admitted_as_incomplete(self) -> None:
        proof = self._validate()
        self.assertEqual([row["role"] for row in proof["endpoint_edges"]], ["source", "sink"])
        self.assertTrue(all(row["callee_external"] for row in proof["endpoint_edges"]))
        self.assertEqual(proof["raw_outcome"], "inconclusive")
        self.assertEqual(proof["flows"], 0)

    def test_internal_callee_edge_is_not_admitted(self) -> None:
        graph = copy.deepcopy(self.graph)
        source_call = next(row for row in graph["calls"] if row["node"]["id"] == "source-call")
        source_call["callee_ids"] = ["src-local"]
        with self.assertRaisesRegex(ValueError, "distinct callee identity"):
            self._validate(graph=graph)

    def test_missing_external_method_proof_is_not_admitted(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["methods"] = [row for row in graph["methods"] if row["id"] != "src-external"]
        with self.assertRaisesRegex(ValueError, "EXTERNAL CPG identity"):
            self._validate(graph=graph)

    def test_sink_argument_must_be_the_exact_selected_wrapper_call(self) -> None:
        graph = copy.deepcopy(self.graph)
        sink_call = next(row for row in graph["calls"]
                         if row.get("method_full_name") == admission.SINK_EXTERNAL)
        sink_argument = next(row for row in sink_call["arguments"] if row["index"] == 1)
        sink_argument["node"]["id"] = "different-call-at-same-line"
        with self.assertRaisesRegex(ValueError, "sink argument 1 is not the exact selected wrapper call node"):
            self._validate(graph=graph)

    def test_expected_configuration_uses_recorded_capture_root(self) -> None:
        capture_root = (self.root / "original-capture-root").resolve()
        raw = {"capture_root": str(capture_root)}
        with mock.patch.object(runner, "_control_config", return_value={"reviewed": True}) as build:
            result = admission._expected_control_config_from_capture_root(
                runner, raw, object(), {"id": "case"}, "on", {"controls": {}}
            )
        self.assertEqual(result, {"reviewed": True})
        self.assertEqual(build.call_args.args[1], capture_root)

    def test_wrong_pinned_runtime_identity_is_not_admitted(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["identity"]["tool_version"] = "4.0.628"
        with self.assertRaisesRegex(ValueError, "wrong pinned Joern/frontend identity"):
            self._validate(raw=raw)

    def test_unknown_incomplete_reason_and_other_typed_states_are_not_admitted(self) -> None:
        for outcome, state, diagnostic in (
            ("inconclusive", "inconclusive", "Incomplete:QueryTimeout"),
            ("unsupported", "unsupported", admission.EXPECTED_INCOMPLETE),
            ("runner-error", "runner-error", admission.EXPECTED_INCOMPLETE),
        ):
            with self.subTest(outcome=outcome):
                raw = copy.deepcopy(self.raw)
                raw.update(raw_outcome=outcome, state=state, diagnostics=[diagnostic])
                with self.assertRaisesRegex(ValueError, "exact EndpointIdentity incomplete state"):
                    self._validate(raw=raw)

    def test_missing_or_changed_cpg_is_not_admitted(self) -> None:
        self.cpg.unlink()
        with self.assertRaisesRegex(ValueError, "CPG binary is missing or empty"):
            self._validate()


if __name__ == "__main__":
    unittest.main(verbosity=2)
