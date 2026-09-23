# Candidate Swift native controls (#220)

This is non-scored diagnostic evidence for CodeQL 2.27.1 with `swift-all`
6.8.4 and Joern 4.0.633. Active pins, scored results, canonical identities,
and the pending opaque decision are unchanged. Candidate native admission
remains blocked; no capability partition is emitted.

## CodeQL controls

The preregistered environment, argv, and benchmark-owned near-miss controls
have all six attempts retained under
`evidence/swift-candidate-native-controls-220/`. The first 60-second extraction
attempts failed; the fresh 180-second feasibility retries finalized Swift
databases and completed declaration and shipped role-node queries. The retry
is not qualification under the scored budget. Phase completion also does not
establish memory compliance or complete descendant containment.

The real Foundation controls returned zero shipped role nodes, including the
known `String(contentsOf:)` positive. Consequently their negative observations
cannot qualify source/sink absence. Declaration observations are retained
separately from role observations.

The near-miss control returned a shipped sink at line 18:
`[18, 5, "shipped-sink", "[post] process"]`. The corresponding declaration is
`DataFlowBenchTaintSwift:arguments:[String]`, owned by the benchmark's lookalike
`Process`. This violates the preregistered near-miss acceptance condition.
It is a concrete native-role qualification blocker, not a scored vulnerability
finding or an end-to-end taint result.

## Joern inventory and mechanism boundary

The complete extracted-candidate census retains 1,349 files, 1,191 JAR paths,
220 unique JAR contents, 179,468 members, 147,755 class members and 15,482
non-class/non-TASTy resources. All members are enumerated per unique JAR hash;
duplicate paths retain their hash mapping. Deterministic compressed JSONL
records preserve the full inventory, resources, first-party class rows and
keyword navigation results. The audit verifies compressed and uncompressed
hashes, sizes, row counts and JAR coverage reconciliation.

The cited API inspection shows `DefaultSemantics` returning
`FullNameSemantics`, whose lookup yields generic `FlowSemantic` mappings by
method full name, including exact/regex matching and a shipped C `atoi`
mapping. A typed Swift Foundation endpoint role mechanism was not established
in these inspected interfaces. No Joern runtime role-matching experiment was
performed. Complete inventory coverage and keyword hits do not prove semantic
absence across all classes. The integration assessment explicitly scopes the
raw sidecar's negative API fields to the inspected interfaces.

## Reproduction and validation

The preregistration, query supplement, source controls, probe runner, all
attempt witnesses, raw query results, candidate asset verification and census
reproduction script are retained with a SHA-256 manifest. Temporary database
paths in witnesses identify retained local scratch, not portable databases.

Run `python3 scripts/audit-swift-native-controls.py` to reconcile observations
and exact evidence bytes, and `python3 scripts/test-swift-native-controls.py`
for incomplete-observation, retry-budget and near-miss regression checks.
Both run in CI. These checks validate retained evidence; they do not rerun the
candidate analyzers or qualify a release.
