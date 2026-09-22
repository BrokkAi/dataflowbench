# Swift reflection follow-up: candidate remains unqualified

This non-scored #220 investigation follows the separately committed design in
`contract/README.md`. It adds no registry case, population, capability partition,
qualified result or score. All three attempts and ownership controls are retained
with complete per-directory digest manifests. Run
`python3 scripts/verify-swift-followup-probes.py` to verify the observations.

## Candidate and fidelity question

`probe/template.swift` stores identity and second-position closures as properties
of `Implementation`. `Mirror` selects a property by a runtime string label,
casts its value to the function type, then invokes it. This is reflected
function-value lookup; the canonical modeling matrix specifies reflective
self-dispatch to a declared method. Neither a passing compiler nor a favorable
analyzer result settles that semantic difference. No new identity or exclusion
is enacted by this experiment.

## Attempts

- `attempt-01` at `93ae367e7` retains CodeQL query compilation failure (reserved
  identifier `from`) and concrete printing failures. Joern completed its native
  observations. Those failed controls are not qualified or replaced.
- `attempt-02` at `4323e8f7d` fixes the query and replaces printing with explicit
  preconditions. The concrete program exits `-10` (`SIGBUS`); the harness stopped
  before either analyzer. `failure.json` makes that partial attempt explicit.
- `attempt-03` at `a9b611717` retains concrete failures while continuing independent
  static diagnostics. All source/sink observations are tied to exact resolved
  identities. CodeQL direct positive is visible model-off/on, direct negative is
  absent in both, carry and second-position positive appear only model-on, and
  block/second-position negative are absent. This is a bounded model sensitivity
  observation, not concrete fidelity or completeness proof.

Joern in attempts 01 and 03 observes native paths in model-off carry, block and
both select polarities. Model-on blocks the declared no-flow sibling, but still
observes a path for the positional negative. Therefore the model is not
load-bearing for carry under that configuration, and select lacks positional
separation. This can reflect optimistic native propagation/model application;
it is not evidence of language impossibility or proof that the source body is
semantically incapable of preserving the template. Joern completion remains
explicitly separate from unproven bounded semantic completeness.

## Bounded ownership control

`lifetime-controls/` removes force casts, gives the owner and mirror named local
lifetimes, uses `as?` with an explicit checked failure branch, and invokes the
callback within `withExtendedLifetime` for both owner and mirror. The direct
control uses the same stored closure and owner without reflection. Under the
same witnessed Swift 6.4 compiler, target, SDK and `-Onone` settings,
`lifetime-attempt-01` compiles both: direct exits 0; retained reflection exits
`-10`. This rules out the particular temporary-owner/force-cast assumptions in
the first prototype as a sufficient explanation. It does **not** establish the
root cause as a compiler or runtime bug, nor prove no other faithful Swift
construction exists. No external bug or language-impossibility claim is made.

## Decision boundary and independent next work

This candidate cannot qualify the existing opaque IDs: concrete fidelity fails,
Joern's model-off behavior is optimistic, and declared-method versus stored
function-value equivalence remains unsettled. Any further candidate must preserve
canonical semantics rather than merely defeat an analyzer. If a faithful working
candidate cannot be established, a material choice remains between a reviewed
change to the opacity construction/identity and an explicit language-scope
classification. Neither is accepted here; no family is silently omitted.

[A38 native contracts](../../docs/swift-native-contract.md) and the
[A39 Result extension](../../docs/swift-result-contract.md) are independent.
The latter's concrete prototype passes both polarities for source values 7 and
19 in `../swift-result-220/attempt-01`; this still does not activate registry
or analyzer participation. Follow-on fixtures require a new immutable population
and prospectively committed independent adapter partitions.

All timings are diagnostic. Probe deadlines do not alter the registry's 60-second,
512-MiB budget; no performance or memory-compliance qualification is claimed.
