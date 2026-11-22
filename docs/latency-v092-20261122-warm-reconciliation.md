# A29: retrospective Semgrep warm evidence reconciliation

The final `warm-semgrep-java` invocation in `20261122-02` exited zero and
produced all ten planned batches. The controller recorded it as failed because
its validator required Joern's `run-*-batch-*-evidence/` directory layout for
Semgrep. This was a validator error, not the layout emitted by the frozen
Semgrep producer.

The Semgrep warm implementation and latency producer are byte-identical to
release `86092336d8f9ca32fe9e2c4042c2dced76c1feb1`. Joern calls the per-case
sidecar retention helper. Semgrep instead retains one full
`run-<repeat>-batch-<k>-findings.json` for each batch, containing its scanned
paths, findings, errors and tool version, plus the warm artifact with each
batch's ordered case IDs. Its temporary copied inputs are then removed.

## Corrected validation and derived evidence

This correction recognizes that released, family-specific format. It requires
the exact preregistered prefixes and sizes `1,2,4,8,12`, both repeats, frozen
fixture and tool identities, and unchanged source case/fixture bytes. The
released producer deterministically copies each case's declared fixtures to
`source-<index>` within its repeat/batch temporary directory. The index follows
the recorded ordered case list; it is not guessed from a finding's display
name or from an expected score.

Every batch must have unique scanned paths exactly equal to all expected input
fixture paths. Empty error, skipped-rule and fixpoint-timeout lists are
required explicitly; absence is not treated as success. Every retained finding
must belong to those inputs and the controlled rule and engine. Derived
per-case outcomes are checked against the hash-bound frozen common-kernel
report. A finding must also reconcile its start line with the frozen producer's
anchored sink callsite contract; membership in the fixture file alone is not
proof of reaching that sink. Missing or ambiguous locations remain unresolved.
Wrong paths, missing inputs, duplicates, stray findings, identity drift,
unknown states and outcome differences fail validation. No case is pruned or
replaced based on these observations.

The original aggregate files remain unchanged. An independently named audit
package under `reports/timing/v0.9.2/reconciliation-20261122-01/` holds explicitly
derived per-case records. Each binds the original batch raw SHA-256, the warm
artifact, the source-index/case/fixture mapping and fixture hashes, and the
unchanged raw findings subset. These are derived records, not files emitted
by the analyzer, and are not inserted into the original capture's missing
sidecar directories. They do not prove byte equality with cold per-case reports
or independently retain the removed temporary input copies.

The first offline audit was rejected by independent review for omitting the
sink-location check. It and its rejection disposition are retained. Only a new
audit produced with the corrected validator can support recovery.

## Historical and qualification limits

Validation occurred after the measurement timestamps. The new receipt is
labelled retrospective and the original controller terminal remains `failed`.
No analyzer is rerun, no wall time or fitted value is replaced, and no frozen
report, tag, fixture, binary or prior raw file is rewritten. The measured
invocation boundary and selected population are unchanged.

Recovery supports an auditable diagnostic candidate, not original settled A24
certification or a new prospective timing attempt. The A28 background policy,
original CPU observations, process-containment uncertainty, pending cold/warm
equivalence and independent publication gates remain. Rust's earlier semantic
mismatch, blocked Swift groups and historical CodeQL native runner errors
are unchanged. The separate CodeQL cache discovery checks demonstrate suite
lookup only; they are not new analysis results.
