# Prospective Joern current108 integration

This versioned adapter prepares the current 108 Swift cases without transferring
historical v1/v2 observations or unsupported decisions. Preparation leaves every
case `pending-capability`. Full execution requires a reviewed activation receipt
and a fresh, fully resolved current-population partition. No activation or
unsupported decision is inferred from missing configuration.

## Prospective budget amendment, 2026-09-28

The prior Joern v1/v2 runners and fixtures keep their 60-second total contracts.
Under the authorized prospective 75-second cutoff, this new lane gives each
case one 75-second monotonic total across typecheck, frontend import, query,
JSON output decoding, identity validation and intervening overhead. It does not
borrow CodeQL's separate 150-second extraction allowance. Closure retention is
outside analysis timing and cannot rescue failed or over-budget observations.
Fixture memory remains 512 MiB; a JVM heap request of 512 MiB is not process-tree
memory enforcement. Aggregate qualification remains unavailable; report results
are inconclusive except explicit runner errors or freshly justified unsupported
decisions. Raw reached/not-reached observations remain available for diagnosis.

## Pin and API boundary

Hold Joern 4.0.628 for this bounded comparison. The September 28 pin review in
the CodeQL normal adapter recorded 4.0.640 as then-latest; this is an intentional
hold, not a current-latest claim. Preparation checks retained engine/frontend/
launcher/SwiftAstGen/compiler/Java hashes and binds full installed runtime trees.
The new Scala query has not yet been compiled or run. Existing historical query
execution demonstrates the core `FlowSemantic.from`, `EngineContext`,
`reachableByFlows`, callee and parameter APIs; new owner/return checks require
native validation before any activation claim.

The supplied candidate models are carry parameter 1 to return -1, block with no
flows, and select parameter 2 to return -1. Printed method names select candidate
declarations; unique internal declaration, native AST owner edge, exact callee
join, parameter and call-argument positions, and return type must agree. Receiver
position 0 never becomes a modeled input. Missing or ambiguous proof remains
`Incomplete`, never a clean negative or an unsupported partition. The query does
not infer Objective-C selector resolution from text or claim dynamic-dispatch
completeness.

## Bounded control registration

Prepare emits a separate control plan for the four exact opaque population IDs
plus canonical direct positive/negative baselines, each off/on. This is twelve
case arms, at most 36 native phase invocations and 900 seconds total phase budget.
Off/on compare baseline stability, carry load-bearing propagation, block kill,
and second-argument selection versus first-argument near miss. The registration
is a proposed test, not observed compatibility. A failed model-off requirement
is a fidelity/activation gap, not permission to patch analyzer accuracy.

The initial scratch allowance is 2 GiB for serial retained CPGs/caches across this
bounded control matrix; this has not been measured on these fixtures. Launch
requires 42 GiB free, an exact-plan and exact-control hash reservation, and an
exclusive analyzer slot. Every phase preserves the 40 GiB reserve; no fixture
binary is executed. Requested JVM memory and disk polling are not hard aggregate
containment. Actual elapsed/free-space deltas are retained; future reservations
must use the observed cost. Preparation alone never reserves capacity or authorizes a full corpus run.
A live byte-level check is required before each separately reserved control run.

Timeout, uncertain cleanup, reserve breach or artifact closure failure stops the
serial run with partial records. No fabricated rows or full report follow an
incomplete population. The separate Joern normal exporter checks its own total
budget contract and emits standard result/v1 groups only for all 108 exact IDs.
No score, freeze, release or publication follows from this implementation.

### Scratch estimate provenance

Retained historical artifacts are small: the direct model-on diagnostic is
40 KiB, the Result identity slice 112 KiB, and the six-case reflection off/on
collection 1,224 KiB on disk. Those exports omit ephemeral CPG/compiler caches
and therefore cannot measure peak scratch. The 2 GiB allowance is an explicitly
unqualified envelope above these retained sizes, not a measured projection.
Controls stop before another arm if retained output exceeds that allowance or
if free space cannot cover the reserve plus allowance. No old report footprint
is represented as a current peak-memory/disk measurement. First-run observed
retained size and free-space deltas will inform a later prospective reservation.

A read-only sample of three retained actual Joern scratch directories measured
532, 536 and 544 KiB including CPG and workspace copies. Twelve arms at the
largest retained sample total about 6.4 MiB. The 2 GiB allowance adds substantial
headroom for cold compilation/runtime caches and larger current graphs, but the
old final directory sizes still do not establish peak scratch for this run.

The opaque-negative off=reached/on=not-reached pair is a prospective model-kill
activation-separation expectation: without the declared block summary, the
analyzer must demonstrate its generic propagation baseline for this control.
Failure leaves activation incomplete. It does not assert runtime taint should
vanish, certify absence completeness, or justify an analyzer accuracy repair.
Independent CPG parameter types must be Opaque at receiver 0 and Swift.String at
positions 1/2; a printed signature cannot substitute for these typed nodes.
Query runtime failures remain runner-error, while missing structural identity
proof in a completed query remains typed Incomplete.

The 900-second bound covers twelve analysis arms only. A separately bounded
30-second version witness, preflight hashing and evidence closure are outside
that phase sum. Prelaunch fixture/configuration failures retain a stop record
with `executed: false`, never a fabricated command. Export independently replays
the activation receipt and controls and requires identical query, model,
helper, runtime-tree and phase-contract inputs between control and corpus plans.

## Prospective correction after controls-01

The first attempt recorded six `Incomplete:SwiftImport` arms and no query
execution: preparation resolved the supplied `swiftc` driver symlink to the
`swift-frontend` filename. SwiftAstGen's build-log parser then reported zero
type-map entries, unlike retained successful driver-spelled commands. The next
plan preserves the compiler launcher name while inventorying its target bytes.
It also stops on any incomplete direct baseline, and retains cancellation.
The initial `--version` flag was unsupported, but the process printed a 4.0.628
REPL banner and exited successfully at EOF. Future version witnessing invokes
the launcher without that unsupported flag, retaining its actual banner.
Earlier registration and failure evidence remain immutable. This is a runner
correction, not a claim about analyzer accuracy or opaque capability.
