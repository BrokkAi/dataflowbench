# CodeQL current108 diagnostic results

The serial run `reports/raw/swift-normal-v1/current108-2026-09-29-01`
actually attempted all 108 current Swift cases under the unchanged registered
plan `adapters/codeql/swift-normal-v1/plan-2026-09-28-06/plan.json`
(SHA-256 `a91c0571b588e63977611064d649914827d1497b9988e52b4f8b8622540c7bcd`).
It finished without a stop marker. Raw observations are 55 `reached`,
52 `not-reached`, and one `runner-error`. The five normal reports retain
107 `inconclusive` and one `runner-error`; scored activation remains false.
These are diagnostic observations, not an accuracy score, freeze, or publication.

The error is `dfb-taint-swift-infeasible-branch-negative` with
`MissingExactEndpoints`. Its commands succeeded, but the decoded query evidence
could not establish the required exact endpoints. The result is preserved as
`runner-error`, not converted to clean, unsupported, or inconclusive.

## Execution and provenance

The registered toolchain is CodeQL 2.27.1 with the plan-bound patched Swift
extractor, compiler 6.3.3, SDK, query packs, fixtures, and configuration files.
The deleted CLI/compiler installations were restored from the same SHA-256
verified installers. Their complete file, symlink, and permission inventories
were checked against the registered plan before launch. The CodeQL launcher
permission was restored to the registered `0555` after archive extraction.
The retained runtime version witness binds the observed CLI build.

Plan 06 was registered by commit
`83003d1e52f9501eb50eb4c811873174a54f1881`. Its query-revalidation record retains
only the original plan-04 compile-compatibility claim; it is not execution
qualification. The execution checkout was commit
`540b5990cb88a679ddaaf7f55fdaeb85d80a033b`
(the same tracked tree as merged main `3b53cf35c84f9f5129d1373b850b9073aba94a89`).

The run took 112.83 minutes. All 656 case commands exited zero without timeout
and recorded `tracked-processes-stopped`. The maximum recorded extraction was
124.675 seconds; the maximum shared analysis duration was 69.087 seconds.
The unchanged contract allowed 150 seconds for extraction and 75 seconds shared
across analysis, with 2048 MiB requested and two threads. These requested resource
settings and cleanup observations do not establish aggregate process/memory
containment. `AggregateResourceQualificationUnavailable` remains on every report.

Launch free space was approximately 266 GiB, above the 64 GiB launch threshold;
the 40 GiB runtime reserve was maintained. The local heavy-work slot was
coordinated with the Bifrost owners and checked for active analyzers/builds.
No uncontended performance certification is claimed.

## Replay boundary

```sh
python3 -O scripts/check-codeql-current108-results-v1.py
python3 -O scripts/test-codeql-current108-results-v1.py
```

The checker verifies exact membership, plan/configuration/identity bindings,
command arguments, phase order and budgets, retained fixture sources, decoded
query observations (including persistence coverage), and report/audit equality.
Its observation derivation is separate from trusting the recorded raw outcome;
it reuses the registered semantic observation helpers. It preserves the typed
missing-endpoint error. Regression tests reject missing rows, promoted reports,
and altered decoded rows.

`portable-files.json` lists the SHA-256 of every retained portable run file.
The committed evidence includes raw records, commands, stdout/stderr, BQRS and
decoded query rows, fixture sources, finalization records, database-closure
inventories, identity witness, and five normal reports. It excludes full database
payloads, compiler caches, generated executables, and the local reservation's
full process listing. The original databases and caches remain local.
This is compact command/source/query replay, not full CodeQL database replay.
Local database closure verification is separate from that portable boundary.

Validation passed for all 108 locally retained database closures, archived
fixture sources, finalization metadata, and schemas. The compact checker and
five regression tests also passed from a separate staged-files-only copy with
no full databases or compiler caches. The runner/exporter focused suites passed
30 tests before launch. Original compiler-output and fixture whitespace is
retained byte-for-byte, including Git whitespace-check warnings in that evidence.
