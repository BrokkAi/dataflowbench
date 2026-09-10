# DataFlowBench issue #19 — R2 v3 independent review A

## Verdict

**Accept. All nine subjects and all four required fields for each of the six pins are accepted.**

The v3 packet is complete and internally reproducible. All 616 artifacts and all packet path/digest bindings were present and SHA-256-correct. Independent replay reproduced the snapshot population, frame, all E1–E8 decisions, and the seeded draw without discrepancy. Fresh downloads of all 12 pinned vulnerable/fixed source archives exactly matched their recorded content digests and byte lengths. No analyzer output was run or consulted.

## Provenance

- Run ID: `reviewer-a-v3-20260910T100928Z`
- Reviewer record: OpenAI `gpt-5.6-sol`, medium effort
- Started: `2026-09-10T10:09:28Z`
- Completed: `2026-09-10T10:15:06Z`
- Checkout: `/private/tmp/dataflowbench-issue19-r2-v3-review-a`
- Revision: `65441c1a8d5fbe0b1da83a0247ad6eb0eba984c6`
- Checkout state: detached and clean at start and completion
- Evidence copy/output: `/private/tmp/dataflowbench-issue19-r2-v3-evidence-a`
- Packet source: `/Users/dave/.codex/worktrees/5fdf/dataflowbench/corpus/real-project/r2/review-packet-v3/packet.json`
- Packet ID: `dfb-rp-r2-packet-27dd303a928fc0c2d80b13fe`
- Packet SHA-256: `93523f8ee088ef1cb484d03b5c0aa05ece5f857ff26cbc61be7c5163b72ff32c`
- Packet artifact verification: 616 checked; 0 missing; 0 mismatched
- Analyzer evidence consulted: **false**

## Subject verdicts

| Subject | Verdict | Independent basis |
| --- | --- | --- |
| snapshot_completeness | **accept** | Five retained pages form complete contiguous chains ending at `next_url=null`: Maven 90, npm 100+7, and pip 100+77, totaling 374 raw advisories. Status, item count, path, and digest records all match. |
| frame_derivation | **accept** | Offline replay of the admission rule from the five raw pages reproduced the exact 219 retained candidates and counts: Java 48, JavaScript 66, Python 105. |
| eligibility_e1_e8 | **accept** | All E1–E8 outcomes for all 35 walked candidates were independently recomputed from retained evidence. E5 inventory/source bindings and E8 prior-selection states are complete and correct. No discrepancy was found. |
| draw_and_replacement | **accept** | Every seeded SHA-256 draw key, position, eligibility index, disposition, selected identity, and stop at the second passing candidate per stratum was independently reproduced. The before/after-review replacement rule is explicit, fail-closed, and forbids reseeding or analyzer influence; no replacement event occurred. |
| pins_and_archives | **accept** | Six pins bind to selected records and sole-parent vulnerable/fixed pairs. All 12 archive URLs were freshly fetched; every SHA-256 and byte length exactly matched. |
| licenses | **accept** | All 12 retained license payloads decode to the recorded path, SPDX identifier, content digest, and byte length; each vulnerable/fixed pair is identical as recorded. |
| vulnerable_fixed_semantics | **accept** | Each fixed revision is exactly one commit ahead of its proposed vulnerable sole parent, and its retained compare patch substantiates the named remediation behavior at the proposed source boundary. |
| claim_bounds | **accept** | R2 is restricted to named per-repository, per-revision, per-case, per-adapter outcomes. Generalized rates, accuracy metrics, confidence/significance/causal claims, rankings, leaderboards, pooling with R1, and synthetic-core denominator changes are prohibited. |
| descriptive_latency_scope | **accept** | Latency is confined to raw cold/warm observations and the preregistered descriptive per-source-LoC view; the contract does not authorize a comparative or causal latency claim. |

## Per-pin review

| Pin | Remediation location | Vulnerable/fixed semantics | Archive digests | License |
| --- | --- | --- | --- | --- |
| `GHSA-jcrp-x7w3-ffmg` — `deepjavalibrary/djl` | accept | accept | accept | accept |
| `GHSA-6fhj-vr9j-g45r` — `CycloneDX/cyclonedx-core-java` | accept | accept | accept | accept |
| `GHSA-g4cf-pp4x-hqgw` — `haxtheweb/haxcms-nodejs` | accept | accept | accept | accept |
| `GHSA-wphj-fx3q-84ch` — `sebhildebrandt/systeminformation` | accept | accept | accept | accept |
| `GHSA-fhw8-8v9p-7jp7` — `blacklanternsecurity/bbot` | accept | accept | accept | accept |
| `GHSA-6556-fwc2-fg2p` — `mmaitre314/picklescan` | accept | accept | accept | accept |

The fixes are semantically located and bounded as proposed: DJL validates archive entry paths before resolution/write; CycloneDX enables secure XML processing at parsing/validation boundaries; HAXCMS removes the request-controlled git-import route; systeminformation strictly sanitizes the Windows `drive` value before PowerShell interpolation; BBOT atomically claims the extraction directory and aborts on collision; and picklescan expands unsafe-global detection and parent-module wildcard propagation. Each conclusion is based on the immutable source compare and freshly verified revision archives, not analyzer output.

## Validation and independence

The protocol, snapshot manifest, frame, eligibility, draw, and all six pins validate against their retained schemas. Reviewer A did not run or inspect analyzer output, did not inspect reviewer B, and did not edit the detached Git checkout. The freshly fetched archives were stored only in reviewer-local temporary storage.
