# v0.9.2 timing continuation outcome

The resumed 32-command queue reached its terminal state on 22 November 2026.
All 32 commands ran serially: 31 received controller candidate-completion
receipts, and the last Semgrep warm command exited zero but encountered a
validator format error. Its retained aggregate evidence was subsequently
validated under [A29](../../../../docs/latency-v092-20261122-warm-reconciliation.md).
The original failed terminal remains unchanged. No analyzer was rerun to
perform that reconciliation and no active invocation was interrupted.

The user-authorized [A28 background policy](../../../../docs/latency-v092-20261122-background.md)
applied prospectively to the final three commands. Contacts, Spotlight and the
identified Apple VM service were tolerated for dispatch. Raw CPU/process
observations and original qualification flags remain intact. These final
observations do not assert the original five-minute settled-host qualification.

## Exact coverage

Across the preserved November 15, 21 and 22 continuation chain, all 93 ready
commands were attempted. Of the 95 planned entries, two Swift groups remain
blocked. Historical controller states are recorded in
[capture-coverage-01.json](capture-coverage-01.json): 81 cold candidate groups,
one quarantined Joern Rust cold group, nine overhead candidate groups, one
Joern warm candidate group and the Semgrep warm validation failure.
The separate [retrospective receipt](semgrep-warm-audit-02/validation-receipt.json)
recovers Semgrep's ten aggregate batches and 54 derived case observations
across 12 cases as a diagnostic candidate, without revising that history.
The first offline audit was rejected for an incomplete sink-location check;
its [review disposition](audit-01-review-disposition.json) remains explicit.

| Analyzer | Candidate cold groups / planned | Retained cold timing records |
| --- | ---: | ---: |
| Bifrost | 20 / 20 | 1,031 |
| CodeQL | 17 / 18 | 858 |
| FlowDroid | 4 / 4 | 154 |
| Infer | 5 / 5 | 204 |
| Joern | 11 / 13 | 398 |
| OpenTaint | 4 / 4 | 152 |
| Pysa | 3 / 3 | 102 |
| Semgrep | 17 / 17 | 196 |

These are each analyzer's own frozen eligible populations. The 3,095 cold
timing records include invocation costs for incomplete/error outcomes; they
are not all timings of successful analysis. The 3,974 normalized candidate
rows retain 2,687 decisive outcomes, 372 inconclusive outcomes, 36 runner
errors and 879 unsupported outcomes. Rust's additional 62 unqualified rows
remain separate. There is no cross-analyzer or cross-release performance claim.

All nine overhead groups retain three observations each, labelled invocation
overhead. Joern warm retains two repeats at sizes 1,2,4,8,16, including 62
original per-case files. Semgrep warm retains two repeats at sizes 1,2,4,8,12,
including ten original aggregate files and 54 explicitly derived observations.
The derived records contain no invented per-case wall times or hashes of
deleted scratch copies. Cold/warm equivalence remains pending.

## Remaining qualification and runtime work

- Joern Rust changed all 62 frozen inconclusive outcomes to decisive outcomes.
  It is quarantined; accepting that change requires a semantic investigation.
- Joern and CodeQL Swift still need qualified runtime/driver relocation.
  The pinned Swift package is retained but unexpanded. CodeQL additionally
  lacks three retained custom extractor files and the entry2 custom query pack.
- The repaired CodeQL native package cache resolves all three exact pinned
  security suites in an isolated HOME. This proves package discovery only;
  it does not replace the 36 historical native runner-error rows with successful
  analysis. See the retained
  [discovery summary](../preparation-20261122-codeql-native-01/discovery-summary-01.json).
- Original contention flags, process-containment uncertainty, Bifrost raw
  identity differences, semantic uncertainty, equivalence and publication
  acceptance remain independently assessable. No blanket certification is made.

The new results and reconciliation are retained locally on
`dave/v0.9.2-timing-supplement`; this audit does not claim they are published.
The frozen v0.9.2 release, previous failures and original capture files remain
unchanged. The final ownership check found no surviving recorded process
identities and an available serial lock, with approximately 229 GiB free.
The two new capture inventories were verified file by file and their 1,881
files, including the inventories themselves, round-tripped through a compressed
retention bundle. See [retention-verification-01.json](retention-verification-01.json).

## Subsequent untimed runtime recovery

After these captures, the retained Swift 6.3.3 installer was expanded into a
fresh runtime directory. The [full manifest check](../preparation-20261122-swift-01/manifest-verification.json)
verified all 2,877 regular files and 51 symlinks, including their hashes, modes,
targets and exact membership; the version-only smoke also passed. This resolves
the missing expanded payload described above. Fresh driver/path qualification
and the other named Swift prerequisites remain separate, and no Swift timing
completion is inferred from the runtime recovery.
