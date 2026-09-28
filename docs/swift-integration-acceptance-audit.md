# Swift integration acceptance audit, 2026-09-28

Read-only audit at `3007c9df0960b397f9f312548ffca81b28eb7163` against
the live acceptance criteria of #215/#220. No analyzer execution, activation,
freeze, or publication is established by this document.

| Question | Decision | Repository evidence and remaining work |
|---|---|---|
| Is perfect analyzer accuracy required? | No | `docs/scoring.md` counts qualified false positives/negatives. Keep the original ten-control candidate failure intact; assess generic structural correctness under a new prospective registration. |
| Is a macOS VM mandatory? | No | Neither `schemas/result.schema.json` nor `src/freeze.rs` requires a VM. The existing Swift normalizer cannot qualify aggregate resources; a verified containment facility is required before claiming decided scores under that contract. A VM is one possible implementation. |
| Can incomplete outcomes be frozen? | Yes, with full provenance | Result schema line 63 admits all five outcomes. `validate_frozen_report` checks schema, identity, partition and exact case sets; `validate_frozen_outcomes` checks agreement, not a reached/not-reached whitelist. `validate_raw_evidence` and `raw_special_outcome` reject downgrading special outcomes. `src/tests/freeze.rs::freeze_rejects_special_outcome_downgrade` exercises this boundary. This is code inspection, not a newly validated Swift freeze. |
| Is the v3 coverage envelope freeze-ready? | No | `scripts/swift_v3_reports.py::assemble` emits `swift-v3-coverage-report/v1`, not result/v1. Integrate witnessed tool/build/adapter identity, configuration digest, timing/cache metadata, anchors, durations and raw evidence; split model profiles and bind exact current fixture revision. Never invent absent metadata. |
| Can a caller set qualified=true? | No | `swift_integration_v3.py::normalize` always records `AggregateResourceQualificationUnavailable`; unsupported additionally requires a verified prospective partition. `test-swift-v3-reports.py::test_all108_retained_and_no_claimed_qualification` rejects claimed qualification. The assembler keeps runner-error, otherwise inconclusive. |
| Are nine current fixture families missing? | No | `audit-swift-coverage.py:47` loads v1 (90 assertions). The v3 population has 108 assertions across 54 identities; all nine historical deferrals now have fixtures. The four absent identities are the contract's language-inapplicable constructions. Adapter evidence remains a separate question. |
| Does Joern cover the current population at one revision? | No | Five reports cover 104 distinct IDs across two old fixture revisions, not the v3 revision. Four opaque assertions have no rows in those reports. Reconcile current fixtures/configuration/pins and prospective decisions before new reports; do not pool the old rows. |

## Exact Joern join

Current v3 fixture revision:
`sha256:f9f2afd8566f7d0d833eb6b3b1383b5ed633eafba43320a6477d1c61472323af`.

| Report under reports/ | Rows | Recorded outcomes | Fixture revision |
|---|---:|---|---|
| joern-swift-kernel.json | 66 | 66 inconclusive | `dcde04f2df2c2c1370241c95bd7cca6984229c33abe6db6db138ca31e557c840` |
| joern-swift-calibration.json | 4 | 4 inconclusive | same v1 revision |
| joern-swift-modeling.json | 20 | 14 inconclusive, 6 unsupported | same v1 revision |
| joern-swift-v2-native.json | 12 | 12 unsupported | `2dc97bb29cdba04c900308be9e3aef016a5a00d2ac11f2bcaa2ac39d9d2484ff` |
| joern-swift-v2-result.json | 2 | 2 inconclusive | same v2 revision |

The missing IDs are positive/negative pairs for
`dfb-taint-swift-model-opaque-propagator` and
`dfb-taint-swift-model-propagator-position`. There are no foreign IDs in this
join. Matching IDs alone cannot transfer qualification across revisions.
Joern v2 activation pins 4.0.628 and expressly disclaims aggregate memory and
semantic completeness qualification; its native scope is capability decisions
only. Bifrost Swift remains unsupported.

## Resource facility discovery

The narrow local check found Docker.app, no UTM/Parallels/VMware application,
and no `tart`, `limactl`, `colima`, `virsh`, `prlctl`, or `VBoxManage` on PATH.
This does not prove that no external facility exists, nor does Docker presence
establish a compatible Darwin guest. No facility was provisioned or configured.
Do not block truthful coverage publication on an unmandated VM requirement.
Decided scores still require demonstrated aggregate accounting/limits and
lifecycle behavior; polling, per-process RSS and JVM flags are insufficient.

Incomplete publication may claim the exact attempted population and typed
coverage outcomes. It cannot claim qualified accuracy, performance, or completed
adapter execution. #220 remains open until its integration and release criteria
are met; a valid incomplete freeze alone does not close the epic.
