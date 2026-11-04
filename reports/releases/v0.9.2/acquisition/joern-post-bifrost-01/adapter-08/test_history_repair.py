from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import history
import packet


class AnnexAttemptIdentityTests(unittest.TestCase):
    def _fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix="joern08-history-repair-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()

        source_commit = "a" * 40
        plan_commit = "b" * 40
        source_tree = "c" * 40
        contract_raw = packet.canonical({"source_commit": source_commit})
        evidence_raw = packet.canonical({
            "source_commit": source_commit,
            "plan_commit": plan_commit,
        })
        contract_path = root / "current" / "contract.json"
        evidence_path = root / "current" / "source-evidence.json"
        contract_path.parent.mkdir(parents=True)
        contract_path.write_bytes(contract_raw)
        evidence_path.write_bytes(evidence_raw)
        current = {
            "contract": {
                "path": "current/contract.json",
                "sha256": packet.digest(contract_raw),
            },
            "source_commit": source_commit,
            "plan_commit": plan_commit,
            "source_evidence": {
                "path": "current/source-evidence.json",
                "sha256": packet.digest(evidence_raw),
            },
        }

        historical_rows = []
        for index in range(109):
            historical_rows.append({
                "attempt_id": f"historical-attempt-{index + 1:03}-series-01",
                "group_id": "shared-group" if index == 0 else f"historical-group-{index:03}",
                "status": "completed" if index < 89 else "failed",
            })

        annex_rows = []
        for index, global_attempt_number in enumerate(range(111, 132)):
            annex_rows.append({
                "attempt_id": f"c5-annex-attempt-{global_attempt_number}-series-02",
                "group_id": "shared-group" if index == 0 else f"c5-group-{index:03}",
                "status": "completed",
                "global_attempt_number": global_attempt_number,
            })

        raw = b"".join(packet.canonical(row)
                       for row in historical_rows + annex_rows)
        old_raw = b"".join(packet.canonical(row) for row in historical_rows)
        annex_raw = b"".join(packet.canonical(row) for row in annex_rows)
        provider = SimpleNamespace(
            LEDGER_ROWS=130,
            LEDGER_RAW_SHA256=packet.digest(raw),
            TOTAL_STATUS_COUNTS={"completed": 110, "failed": 20},
            SEALED109_RAW_SHA256=packet.digest(old_raw),
            C5_ANNEX_SHA256=packet.digest(annex_raw),
            C5_SOURCE_COMMIT="d" * 40,
            C5_PLAN_COMMIT="e" * 40,
            C5_CONTRACT_SHA256="f" * 64,
        )
        baseline = {
            "schema": "v092-joern05-archived130-history-context/v1",
            "status": "source-only-archived130-baseline-verified",
            "execution_authorized": False,
            "automatic_retry": False,
            "current_live_ledger_validation": "not-performed-by-this-reader",
            "ledger_identity": {
                "rows": 130,
                "raw_sha256": provider.LEDGER_RAW_SHA256,
                "status_counts": provider.TOTAL_STATUS_COUNTS,
            },
            "historical109": {
                "rows": historical_rows,
                "sha256": provider.SEALED109_RAW_SHA256,
            },
            "bifrost0144_c5_annex21": {
                "rows": annex_rows,
                "sha256": provider.C5_ANNEX_SHA256,
                "global_attempt_numbers": list(range(111, 132)),
            },
            "sealed109_lineage": {
                "source_contexts": {f"context-{index}": {} for index in range(9)},
                "retained20": [],
                "consumed_events": [],
            },
            "bifrost0144_scala_partial": {
                "group_id": "bifrost-scala-kernel",
                "global_attempt_number": 128,
                "status": "recorder-error",
                "exit_code": 124,
                "timed_out": True,
                "source_commit": provider.C5_SOURCE_COMMIT,
                "plan_commit": provider.C5_PLAN_COMMIT,
                "contract_sha256": provider.C5_CONTRACT_SHA256,
                "completion_claim": False,
            },
            "current_source_identity": {
                "commit": source_commit,
                "tree": source_tree,
            },
        }
        live_ledger_ref = {
            "path": packet.LIVE_LEDGER_PATH,
            "sha256": provider.LEDGER_RAW_SHA256,
            "rows": 130,
        }
        return root, raw, baseline, provider, current, live_ledger_ref, historical_rows, annex_rows

    def _combine(self, fixture):
        root, raw, baseline, provider, current, live_ledger_ref, *_ = fixture
        return history._combine_live_snapshot(
            root, raw, baseline, provider, current, live_ledger_ref)

    def test_shared_group_keeps_historical_attempt_and_excludes_annex_attempt(self):
        fixture = self._fixture()
        result = self._combine(fixture)

        selected = result["selected_historical_joern_rows"]
        historical, annex = fixture[-2:]
        self.assertEqual(selected["shared-group"]["attempt_id"],
                         historical[0]["attempt_id"])
        self.assertNotEqual(selected["shared-group"]["attempt_id"],
                            annex[0]["attempt_id"])

    def test_annex_attempt_identity_in_selected_map_is_rejected(self):
        fixture = self._fixture()
        annex = fixture[-1]
        with mock.patch.object(
                history, "_selected_historical_rows",
                return_value={"shared-group": annex[0]}):
            with self.assertRaisesRegex(
                    packet.AdapterError,
                    "C5 annex attempt identities leaked"):
                self._combine(fixture)


if __name__ == "__main__":
    unittest.main()
