# Prospective Swift integration boundary

This proposal follows the live #215/#220 acceptance criteria reviewed on
2026-09-28. It authorizes no new analyzer run, changes no historical result or
control expectation, and does not promote the experimental lane. PR #266 stays
draft pending independent patch/reproduction review.

The original ten-control candidate expectation remains failed: array-negative
reports reached; callback-positive reports not-reached. That historical outcome
must not be relabeled passed. The benchmark's [scoring contract](scoring.md)
allows qualified analyzer false positives and false negatives. Perfect vendor
accuracy is not an epic criterion. Optional array/callback semantic repair is
stopped; these limitations may become truthful scored outcomes only after the
actual coverage, resource and execution gates qualify.

## Closure-critical work

| Step | Remaining acceptance | Kind and bounded next action |
|---|---|---|
| 1. Generic extractor | Compiler-derived owner/index correctness, exact endpoint bindings and SSA sequencing; no false claims about cross-file/library/lazy extraction | **Review and focused implementation if needed.** Independently review the patch's primary/non-lazy/script guard, auxiliary ordering, module/file key, dedup and body membership. Existing controls show dense script sequences and overwrite kill behavior. Before further runs, preregister structural regressions for file ownership, library/lazy non-entry, auxiliary/conditional membership and unchanged wrapped scopes. This does not require array/callback perfect accuracy. |
| 2. Full 108 population | One exact prospective contract/revision; all selected cases represented; correct budgets and artifact integrity | **Implementation and honest reporting.** Keep the original 60-second attempt and failed eight-case 75-second retry immutable. The prospective 75-second correction has not produced a full 108-case report. A fresh named patched-adapter plan and independent report replay are required if this candidate is selected; do not pool old attempts or relabel them as a 75-second run. Preserve timeouts, missing endpoints and unattempted rows with their actual types. No run is started by this proposal. |
| 3. Resources/completeness | Evidence sufficient for each claimed outcome; verified aggregate budget/lifecycle if activating decided scores | **Implementation; external capability only for decided scores.** Existing macOS polling/RSS and JVM flags do not qualify aggregate memory or escaped descendants. The documented candidate route is an isolated macOS VM or host facility with fixed RAM, bounded swap, whole-guest accounting and lifecycle enforcement, tested against fork/reparent/memory/timeout behavior, plus dedicated evidence capacity. No such facility is verified available. The current v3 assembler preserves raw observations but normalizes them to inconclusive while resource qualification is unavailable. The general result/freeze contracts permit honest inconclusive, unsupported and runner-error coverage. A VM is not a schema requirement. The current custom coverage envelope still needs conversion to normal partitioned reports with complete provenance before freeze validation; it is not automatically freeze-ready. Do not invent a boolean qualification override. |
| 4. Joern and applicability | Every family reconciled; current population/tool lane applicability independently supported | **Audit/implementation and reporting.** The historical v1 audit covers 90 assertions and reports nine unresolved identities. All nine have fixtures in current v3: 108 assertions cover 54 applicable identities; four of the 58 contract identities are language-inapplicable. Fixture presence does not prove adapter support. Joern v1/v2 artifacts and the 12 native unsupported decisions cannot silently qualify all current v3 cases. Reconcile exact current Joern pins, population, compiler/CPG completeness and partition decisions. Keep Bifrost Swift explicitly unsupported. Any deferred scope needs an explicit accepted decision. |
| 5. Common release revision | Case/report/population hashes, joins/denominators, new immutable freeze, docs/site and normal next release | **Integration and release workflow.** Select one reviewed common revision; integrate the coverage report with downstream freeze/report schema rather than treating the current v3 coverage envelope as a published freeze. Run required validation/freeze checks, preserve historical freezes, and publish only through the normal next-release process with separate deployed verification. No tag, merge, freeze or publication is implied here. |

## Prospective structural acceptance

A future structural qualification should verify exported entry/declaration
identity and contiguous compiler indices directly, including absent or duplicate
membership and locationless nodes. Locations may label observations but must
never determine order. Verify exact source/sink bindings and CFG/SSA presence,
ordered write/read and overwrite kill, stable wrapped function/closure scopes,
and exclusion of non-executable library/lazy contexts. Unsupported or untested
macro/async/global initialization remains explicit. Use a clearly named patched
adapter with exact extractor/schema/QL/runtime hashes; it must not impersonate
stock CodeQL.

The current rows provide bounded evidence, not every proof above: the entry
query groups by displayed module/file and counts declarations, and the callback
query inspects one static dispatch relation. They do not prove all cross-file
owner uniqueness, full closure dispatch, or complete dynamic-call semantics.

The next concrete action is independent structural patch/reproduction review and
the [prospective structural-control plan](swift-entry-structural-plan.md).
The [acceptance audit](swift-integration-acceptance-audit.md) records the exact
current108/Joern join and report/freeze predicates. In parallel, a read-only audit can identify which current v3 report
and freeze-schema changes are needed for truthful inconclusive reporting. A
resource facility must be demonstrated before promising qualified decided
scores. No optional analyzer-model perfection loop is on the closure path.
