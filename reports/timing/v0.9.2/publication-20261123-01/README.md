# Accepted diagnostic timing publication — 23 November 2026

Separately versioned descriptive publication for the immutable v0.9.2 release
`86092336d8f9ca32fe9e2c4042c2dced76c1feb1`, authorized by David's request to
publish the accepted timing results and update the aggregated website overview.
No analyzer was rerun to produce these files. CodeQL Swift execution remains paused.

The 84 cold groups contain 82 accepted diagnostic report groups, one quarantined
Joern Rust group, and one blocked CodeQL Swift group. Across all retained groups,
4,144 report rows preserve 3,191 accepted invocation costs, 891 unsupported cases
with no invocation, and 62 excluded quarantined timings. All eight analyzer
families contribute accepted costs. The 96 Joern Swift costs retain inconclusive
outcomes, including four partial invocations; the twelve unsupported Swift rows
have no invocation. No successful-analysis latency is certified.

The nine overhead groups retain 27 separate upper-bound observations. The two
warm families retain 20 batches, with 62 Joern per-case timings and 54 Semgrep
derived case observations that have no per-case wall times. The original failed
Semgrep controller record and its separate A29 recovery receipt remain explicit.
All certification/full-model/publication-eligibility flags remain false.

`manifest.json` binds the downloadable JSON and portable source ZIP by SHA-256.
`source-index.json` enumerates its byte-exact retained inputs. Verification
extracts those inputs into a temporary snapshot and replays the pure export,
including population, identity, source-digest, outcome, cost and aggregate gates.
It requires no host execution-state, analyzer binaries or analyzer invocations.

FlowDroid modeling follows A20's analysis-only boundary, excluding APK compilation
and DEX preparation. Infer and CodeQL retain their declared subprocess sums.
All original phases remain in the source archive. These are different-case
invocation distributions, not repeated-trial variance, a matched speed comparison,
a baseline change, or a cross-release performance claim.

The public page is `/snapshots/v0-9-2/timing-20261123-v1/`; downloads are below
`/evidence/timing/v0-9-2/20261123-v1/`. The 13 November supplement and frozen
correctness outputs keep their original identities.
