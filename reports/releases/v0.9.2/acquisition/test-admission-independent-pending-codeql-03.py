#!/usr/bin/env python3
import importlib.util
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "reports/releases/v0.9.2/acquisition/admission-independent-pending-codeql-03.py"


def load():
    spec = importlib.util.spec_from_file_location("admission_independent_pending_codeql_tested", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CodeQLAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def receipt(self):
        return {
            "schema": "v092-codeql-independent-admission/v1",
            "status": "ready-to-execute", "automatic_retry": False,
            "manifest_sha256": "a" * 64, "module_sha256": "b" * 64,
            "supervisor_sha256": "c" * 64, "group_id": "codeql-swift-common108",
            "attempt_id": "codeql-swift-common108-attempt-01-series-01",
            "base_plan_commit": self.m.BASE_PLAN_COMMIT,
            "ledger_prefix": {"rows": 88}, "historical_completed_groups": 82,
            "expected_after_success": {"ledger_rows": 89, "selected_groups": 83,
                                        "partitions": 87, "rows": 4144},
            "phase_remaining_reserved_seconds": 28032,
            "source_projection_max_bytes": 12 * 1024**3,
            "source_working_cap_bytes": 30 * 1024**3,
            "resource_floor_bytes": 127 * 1024**3,
            "materialized_projection_bytes": 10,
            "materialized_preflight": {
                "schema": "v092-codeql-materialized-source-preflight/v1",
                "projected_source_bytes": 10,
                "remaining_group_count": 2,
                "aggregate_working_cap_bytes": 30 * 1024**3,
                "source_projection_max_bytes": 12 * 1024**3,
            },
            "materialized_source": self.m.MATERIALIZED_SOURCE,
            "materialized_preflight_guard_checked": True,
            "materialized_launch_guard_checked": False,
            "runtime_registration": {
                "schema": "v092-codeql-runtime-context-registration/v1",
                "historical_context_sha256": sorted(self.m.module_expected_contexts()),
                "prospective_contract_sha256": "d" * 64,
                "elapsed_wall_seconds": 1.0,
            },
            "source_snapshot": {
                "schema": "v092-codeql-frozen-source-snapshot/v1",
                "verified": True,
                "source_commit": "e" * 40,
                "runner_source_sha256": self.m.FROZEN_EXECUTOR_SHA256,
                "source_input_count": 1,
            },
            "no_expiry_authorization": self.m.NO_EXPIRY_AUTH,
            "source_working_cap_authorization": self.m.SOURCE_CAP_AUTH,
            "breadth_first_authorization": self.m.BREADTH_AUTH,
        }

    def test_exact_receipt_shape_is_accepted(self):
        self.m.validate_receipt_shape(self.receipt(), manifest_sha256="a" * 64,
                                      module_sha256="b" * 64, supervisor_sha256="c" * 64)

    def test_joern_or_extra_tail_denominator_is_rejected(self):
        value = self.receipt()
        value["expected_after_success"]["selected_groups"] = 84
        with self.assertRaises(self.m.CodeQLAdmissionError):
            self.m.validate_receipt_shape(value, manifest_sha256="a" * 64,
                                          module_sha256="b" * 64, supervisor_sha256="c" * 64)

    def test_source_projection_and_authority_are_exact(self):
        value = self.receipt()
        value["source_projection_max_bytes"] = 13 * 1024**3
        with self.assertRaises(self.m.CodeQLAdmissionError):
            self.m.validate_receipt_shape(value, manifest_sha256="a" * 64,
                                          module_sha256="b" * 64, supervisor_sha256="c" * 64)

    def test_output_root_preserves_reviewed_codeql_raw_namespace(self):
        self.assertEqual(self.m.CODEQL_OUTPUT_ROOT,
                         "reports/raw/swift-common-v2/current108-v092-01")

    def test_admission_uses_preterminal_validator_mode(self):
        source = inspect.getsource(self.m.admit)
        self.assertIn("final=True, terminal=False, replay=True", source)
        value = self.receipt()
        value["source_working_cap_authorization"] = dict(self.m.SOURCE_CAP_AUTH, sha256="d" * 64)
        with self.assertRaises(self.m.CodeQLAdmissionError):
            self.m.validate_receipt_shape(value, manifest_sha256="a" * 64,
                                          module_sha256="b" * 64, supervisor_sha256="c" * 64)

    def test_source_snapshot_gate_rejects_missing_or_changed_runner_binding(self):
        value = self.receipt()
        value.pop("source_snapshot")
        with self.assertRaises(self.m.CodeQLAdmissionError):
            self.m.validate_receipt_shape(value, manifest_sha256="a" * 64,
                                          module_sha256="b" * 64, supervisor_sha256="c" * 64)
        value = self.receipt()
        value["source_snapshot"]["runner_source_sha256"] = "f" * 64
        with self.assertRaises(self.m.CodeQLAdmissionError):
            self.m.validate_receipt_shape(value, manifest_sha256="a" * 64,
                                          module_sha256="b" * 64, supervisor_sha256="c" * 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
