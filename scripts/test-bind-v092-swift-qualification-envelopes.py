#!/usr/bin/env python3
"""Hermetic contract tests for the Swift qualification envelope gate."""

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).with_name("bind-v092-swift-qualification-envelopes.py")
SPEC = importlib.util.spec_from_file_location("swift_qualification_envelopes_tested", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def sample(tool_name):
    tool = {"path": "/tools/" + tool_name, "sha256": "a" * 64, "version": "1.0"}
    components = [
        {"name": tool_name + "-runtime", "path": "/runtime/manifest.json", "sha256": "b" * 64,
         "kind": "runtime-tree-manifest"},
        {"name": tool_name + "-schema", "path": "/runtime/schema", "sha256": "c" * 64},
    ]
    if tool_name == "codeql":
        evidence = {
            "swift": {
                "status": "measurement-with-known-limits", "execution_eligible": True,
                "control_count": 22, "entry_extractor_controls": 10,
                "model_activation_case_arms": 4, "sanitizer_activation_case_arms": 8,
                "strict_entry_extractor": False, "scored_activation": False,
                "query_preflight_count": 12, "query_preflight_status": "qualified",
                "query_preflight_mode": "resolve-compile-only",
            },
            "ordinary_query_compatibility": {
                "status": "compatibility-verified", "query_count": 26,
                "resolve_command_count": 26, "compile_command_count": 26,
                "compile_only": True, "flow_detection_claimed": False,
                "activation_qualified": False, "coverage_qualified": False,
                "performance_claimed": False,
            },
        }
        groups = ["codeql-a", "codeql-swift-common108"]
    else:
        evidence = {
            "swift": {
                "status": "measurement-with-known-limits", "execution_eligible": True,
                "diagnostic_execution_eligible": True, "control_case_arms": 12,
                "phase_invocations": 36, "full_model_qualification": False,
                "strict_model_qualification": False, "scored_activation": False,
                "strict_assessment_status": "incomplete", "endpoint_identity_gaps": 8,
            },
            "native_review": {
                "status": "measurement-with-known-limits", "execution_eligible": False,
                "scan_count": 36, "completion_markers": 0,
                "cleanliness_claimed": False, "coverage_claimed": False,
            },
        }
        groups = ["joern-a", "joern-swift-common108"]
    return {
        "schema": MODULE.OUTER_SCHEMA, "tool_name": tool_name,
        "status": "measurement-with-known-limits", "execution_eligible": True,
        "groups": groups, "tool": tool, "identity_components": components,
        "component_aliases": [row["name"] for row in components], "evidence": evidence,
    }, tool, components, groups


class EnvelopeTests(unittest.TestCase):
    def assert_valid(self, envelope, tool, components, groups, tool_name):
        MODULE.validate_envelope_shape(envelope, tool_name=tool_name, groups=groups,
                                       tool=tool, components=components)

    def test_valid_codeql_preserves_compatibility_only_scope(self):
        envelope, tool, components, groups = sample("codeql")
        self.assert_valid(envelope, tool, components, groups, "codeql")

    def test_valid_joern_preserves_diagnostic_and_native_limits(self):
        envelope, tool, components, groups = sample("joern")
        self.assert_valid(envelope, tool, components, groups, "joern")

    def test_rejects_wrong_group_scope(self):
        envelope, tool, components, groups = sample("codeql")
        envelope["groups"] = groups + ["codeql-unregistered"]
        with self.assertRaisesRegex(MODULE.BindError, "group order/scope"):
            self.assert_valid(envelope, tool, components, groups, "codeql")

    def test_rejects_component_order_or_digest_drift(self):
        envelope, tool, components, groups = sample("joern")
        expected_components = copy.deepcopy(components)
        envelope["identity_components"][0]["sha256"] = "c" * 64
        with self.assertRaisesRegex(MODULE.BindError, "component identity/order"):
            self.assert_valid(envelope, tool, expected_components, groups, "joern")

    def test_rejects_component_alias_reordering(self):
        envelope, tool, components, groups = sample("codeql")
        envelope["component_aliases"].reverse()
        with self.assertRaisesRegex(MODULE.BindError, "component alias order"):
            self.assert_valid(envelope, tool, components, groups, "codeql")

    def test_rejects_joern_full_model_overclaim(self):
        envelope, tool, components, groups = sample("joern")
        envelope["evidence"]["swift"]["full_model_qualification"] = True
        with self.assertRaisesRegex(MODULE.BindError, "endpoint-identity gaps"):
            self.assert_valid(envelope, tool, components, groups, "joern")

    def test_rejects_joern_native_eligibility_overclaim(self):
        envelope, tool, components, groups = sample("joern")
        envelope["evidence"]["native_review"]["execution_eligible"] = True
        with self.assertRaisesRegex(MODULE.BindError, "native review limits"):
            self.assert_valid(envelope, tool, components, groups, "joern")

    def test_rejects_joern_native_cleanliness_overclaim(self):
        envelope, tool, components, groups = sample("joern")
        envelope["evidence"]["native_review"]["cleanliness_claimed"] = True
        with self.assertRaisesRegex(MODULE.BindError, "native review limits"):
            self.assert_valid(envelope, tool, components, groups, "joern")

    def test_rejects_ordinary_codeql_flow_detection_overclaim(self):
        envelope, tool, components, groups = sample("codeql")
        envelope["evidence"]["ordinary_query_compatibility"]["flow_detection_claimed"] = True
        with self.assertRaisesRegex(MODULE.BindError, "ordinary CodeQL validation was overclaimed"):
            self.assert_valid(envelope, tool, components, groups, "codeql")

    def test_rejects_codeql_activation_overclaim(self):
        envelope, tool, components, groups = sample("codeql")
        envelope["evidence"]["swift"]["scored_activation"] = True
        with self.assertRaisesRegex(MODULE.BindError, "structural limits"):
            self.assert_valid(envelope, tool, components, groups, "codeql")


if __name__ == "__main__":
    unittest.main()
