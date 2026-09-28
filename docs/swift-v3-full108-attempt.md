# Swift v3 full attempt and eight-case budget retry

These attempts are diagnostic and unreportable. Neither produced a verified
coverage report, scored activation, a freeze or publication.

## Original full108 attempt

Source `926f70e98c6c23478c0ac55da4aecef689a4e660` ran all108 cases under
150-second extraction,60-second shared analysis and requested2048MiB. Launch
was2026-09-28T08:10:48Z with87.71GiB free. Concurrent workloads appeared later;
timings are contended diagnostics. Raw census:20 reached,26 not-reached,
54 runner-error (`MissingExactEndpoints`),8 inconclusive (7 extraction budget,
1 flow-analysis budget). All108 were attempted; none was silently omitted.

The strict verifier rejected the persistence negative: the final decode took
0.345s with0.239s remaining, and recorded analysis totaled60.106s. The runner
incorrectly marked completion; the evidence is preserved without reclassification.
A subsequent full-artifact audit also found three added compiler files and two
changed artifacts in the source/sink positive's extraction-timeout database.
That closure is not intact. No old analyzer processes were observed before retry.

## Exact eight-case retry

Source `a94b254700aaba3dec9ef50ee50406cf8f8e2b51` preregistered exactly the eight
`BudgetExhausted` cases, bound to original run/observation hashes. The persistence
overrun and54 endpoint errors were excluded. A separate entrypoint enforced
150-second extraction,75-second shared analysis and requested2048MiB. Launch
was2026-09-28T10:30:11Z, PID65421, with44.58GiB free after a competing Rust build
finished. Historical60s code, contract and raw observations stayed unchanged.

| Case | Execution | Raw result |
|---|---|---|
| native-propagator-positive | completed | reached |
| native-sanitizer-negative | extraction timeout | inconclusive |
| native-sanitizer-positive | extraction timeout | inconclusive |
| native-source-sink-negative | completed | not-reached |
| native-source-sink-positive | completed | reached |
| native-summary-negative | completed | not-reached |
| native-summary-positive | not attempted: DiskReserveReached | inconclusive |
| model-opaque-propagator-negative | not attempted: DiskReserveReached | inconclusive |

Free space fell below30GiB during the sixth case. The runner finished that case,
then started no further analyzer work. Terminal free space was29.41GiB. No
CodeQL/Swift/extractor/clang processes were observed in the terminal check.
This observation is not proof of aggregate containment.

The retry verifier rejected symlinks in the two timed-out sanitizer extraction
copy-roots. Its plan also retained stale descriptive `analysis_total_seconds:60`,
although the bound contract and actual executable enforced75. This inconsistent
preregistration is preserved and is not coherent qualification. Two reached,
two not-reached and four inconclusive are raw observations only. No normalized
subset report was emitted. The propagator's34.94s analysis does not demonstrate
that the increased cutoff caused its success.

## Prospective correction and retained evidence

The current prospective75 plan now consistently declares150/75/2048 for8 cases;
both launch and verification reject resource-envelope mismatches. Strict late
successful-command and post-analysis elapsed checks produce typed timeout rather
than completed overrun. Boundary, scope and mismatch tests cover these rules.
This correction has not been executed. No further run is authorized by this
record; capacity/context must be reviewed before another attempt.

`evidence/swift-v3-full108-60s-record` and
`evidence/swift-v3-budget8-75s-record` contain compressed byte-exact portable
slices, original plans, command records, source archives, BQRS/decoded rows,
logs, complete original artifact manifests and explicit audit failures. Run
`python3 scripts/check-swift-v3-failed-attempt.py` to check portable bytes and
reproduce the known per-case rejection. Omitted database/cache bytes remain
local; hashes and audit records do not establish portable full database replay.

Full local attempts remain under
`/private/tmp/dfb-220-full108-20260928/reports/raw/swift-v3/`, named
`full108-20260928-01` and `budget8-75s-20260928-01`. No retained artifacts were
cleaned. The original `/private/tmp/dfb-220-extraction150` checkout had72,724
pre-existing tracked deletions and was left untouched; its old smoke completeness
was not reasserted. Missing runtime assets were recovered into a new directory
from exact publisher archives: CodeQL2.27.1 SHA-256
`412c600764a7835f9548af120d0bdadea1040c6f68b8f6bf04ec72a664891f63` and signed,
notarized Swift6.3.3 SHA-256
`ee82e57774d6650f94aa06302435d6f44a055b9411698db8ecb85d9a3bcc91d0`.
All286 source pins and6796 required pack-file hashes passed before launch.

Remaining work includes endpoint binding, strict artifact/cleanup qualification,
the two unattempted retries, unresolved extraction budgets, aggregate resource
containment, current Joern v3 qualification, common-revision report reconciliation
and a new validated freeze through normal release. Bifrost Swift stays unsupported;
#220/#215 stay open. A full75-second report requires all108 cases actually run
under that contract; neither attempt may be relabeled to manufacture one.
