# Prospective Swift Foundation identity correction and 2-GiB analysis policy

On 2026-09-23 the user authorized a resolver-proven correction for Swift native
sink differentiation and increased CodeQL query memory. The prospective v2
policy requests **2048 MiB for analysis**, retaining **60 seconds for queries**
and **150 seconds for extraction**. Joern and all other analyzers are unchanged.
Historical 512-MiB observations and hash-bound configurations remain unchanged;
no old result is retrospectively qualified. The new witness separates the
analysis budget from the canonical fixture's historical budget.

`swift-foundation-identity-v1` is an explicit adapter-corrected diagnostic
profile. It is not the unmodified vendor-native profile and does not replace
A38 native model semantics or activate a scored population. Its intended sink
selection uses resolved declaration, module, receiver and structural type
identity. Vendor roles are retained alongside corrected roles for comparison.
Missing environment/argv source models remain a separate dependency; this sink
correction does not invent those sources. Known shipped sources are used for
positive data-flow controls.

Actual command RSS is retained per phase. A measured resource pass is not a
claim of complete descendant accounting or semantic completeness. No full
corpus run, pin promotion, opaque decision or publication is authorized here.

## Matching contract

The corrected sink set is an intersection with the pinned vendor's
`CommandInjectionSink`. A static call must resolve to a declaration in module
`Foundation`, owned by nominal type `Foundation.Process`, with the selector
`run(_:arguments:terminationHandler:)`, static dispatch, and three explicit
parameters. The first parameter resolves to `Foundation.URL`; the second is
an `ArraySliceType` whose element resolves to `Swift.String`; the third is an
optional function taking exactly one `Foundation.Process` parameter. The sink
node must be the first or second argument of that resolved call.

The arguments setter must resolve to the `Foundation.Process.arguments` field
in module `Foundation`, with optional `[String]` type and a receiver resolving
to `Foundation.Process`. Its vendor post-update sink is tied to the same base
expression through `getPreUpdateNode()`. Unknown or missing identities do not
match. The profile intentionally covers these exact declarations rather than
claiming all subclasses or all process APIs.

The flow query retains the vendor source, barrier, and additional-step
definitions and changes only the sink predicate. No environment or argv source
is added. The known positive source is Foundation's
`String(contentsOfFile:encoding:)`. Control binaries are compiled and extracted
but never executed.

## Diagnostic history

All attempts are retained under `evidence/swift-foundation-identity-v1/`. The
initial corrected predicate underselected the positive because it treated
`[String]` as a bound generic rather than the extractor's `ArraySliceType`.
A signature diagnostic established the actual AST representation. Subsequent
sandbox/process-tracking and database-lock failures are retained separately.
The successful retained-database roles run preserves both genuine static-call
sinks. Reanalysis of the existing benchmark-owned lookalike preserves three
vendor sink roles and its vendor taint-flow finding while selecting no
corrected sinks or flows. These are new analysis invocations; they do not
requalify their historical 512-MiB runs or the positive database's earlier
unbounded extraction.

Two top-level-statement controls produced no vendor or corrected sink roles
despite resolved callable AST records. Their empty results are inconclusive
for sink differentiation. The third control puts the same calls inside a
function, matching the earlier successful diagnostic shape. An explicit third
argument selects the genuine Foundation overload. The earlier two-argument
positive accidentally selected the benchmark-defined extension overload; its
attempt is preserved rather than presented as a positive.

## Verified function control

The final `control-attempt-03` extraction completed in **113.30 seconds** under
the 150-second cutoff. Roles, flow, and signature queries completed in
**6.03 / 3.84 / 2.34 seconds**, with measured command maximum RSS of
**1305.73 / 833.88 / 416.50 MiB**, respectively. The source archived in the
CodeQL database matches the retained control byte-for-byte. The database is
finalized and the raw extractor-log error gate passes; type-mangler warnings
remain evidence of incomplete semantic assurance.

| Observation | Vendor-native | Adapter-corrected |
| --- | ---: | ---: |
| Sink nodes | 10 | 5 |
| Source-to-sink flow pairs | 8 | 3 |
| Genuine setter and static-run positive flows | 3 | 3 |
| Lookalike and wrong-type extension flows | 5 | 0 |
| Safe constant-call flows | 0 | 0 |

The safe call retains two sink roles in both profiles, making its nonflow
meaningful alongside the working positive. The wrong-arity overload is absent
from both profiles; this is a regression guard, not evidence of an additional
correction. Module and parameter-type checks jointly exclude the wrong-type
extension, so this control does not isolate their individual contributions.

Run `python3 scripts/verify-swift-foundation-identity.py` to check retained
query outputs, source/query hashes, phase records, measured RSS, and expected
positive/near-miss distinctions. This verifier checks a reproducible diagnostic
package; it does not run CodeQL or certify a scored population. The prospective
resource policy does not turn command RSS into aggregate-process accounting.
