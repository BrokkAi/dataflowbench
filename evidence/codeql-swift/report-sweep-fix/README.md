# Validation-only population sweep correction

The four calibration fixtures completed under prospective configuration commit
f51cb4c9. Their report was atomically written and schema/raw-evidence validated;
the final cross-report sweep then failed because its cached case scan inherited
the active Swift-only population. This falsely changed historical adapter hashes.
`before.*` reproduces that read-only failure using a binary built from f51cb4c9.
It is a reproduction of the failed sweep, not a second fixture execution.

c7a20bca changes only report-local configuration derivation to scan the full
corpus, and adds a regression assertion under active Swift selection. Runner
selection, normalization, query/model files, pin/partition bytes, and execution
configuration remain unchanged. `configuration-byte-equivalence.json` binds
identical configuration hashes across those revisions. All 83 pre-existing report
and freeze JSON files are byte-identical to base f3794bb7, recorded individually
in `historical-reports-unchanged.json`.

`calibration-report-original.json` preserves the successful report bytes before
revalidation; those bytes remain identical to the canonical report. `after.*`
retains the successful corrected sweep under the active Swift population, with
all 67 derivable configuration hashes checked and no stale exceptions.

`stale-binary-attempt.*` retains an intermediate verification failure: using the
same Cargo target for the historical reproduction left the old executable in the
shared output path. The source-commit field records the intended source, not the
actual old binary. A forced rebuild preceded the successful `after` record,
which additionally records the executable SHA-256. No fixture was rerun or
relabeled by that verification attempt.

Core/model processes already running retain the originally launched executable.
Their final sweeps may therefore repeat the same validation-only failure; their
native execution and normalized report bytes are preserved and revalidated with
the corrected executable. The per-case provenance records the contemporaneous
Git HEAD, while this document records the launched executable's f51cb4c9 source.
Analysis configuration bytes are identical throughout.
