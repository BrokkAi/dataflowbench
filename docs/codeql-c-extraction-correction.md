# A34 — 2026-09-21: CodeQL C/C++ extraction failures in v0.8.0

Issue [#213](https://github.com/BrokkAi/dataflowbench/issues/213) concerns
the 58 C and 68 C++ kernel results published in v0.8.0. All 126 are
`inconclusive`, with no observed source or sink endpoints. These cells are
failed extractions, not evidence of a CodeQL propagation regression.

## Diagnosis

Every frozen SARIF contains the structured notification
`cpp/bmn/extraction-information` with `extraction_status.#errors = 1`,
`#success = 0`, and `#total = 1`. The failure counts are:

| Population | Signalled | Exit code 4 | Successful translations |
| --- | ---: | ---: | ---: |
| C | 53 | 5 | 0 |
| C++ | 62 | 6 | 0 |

The notification is informational and the enclosing invocation says
`executionSuccessful: true`. The old decoder checked invocation success and
error-level notifications, so it missed this structured extraction failure
and subsequently reported the empty endpoint probe as `inconclusive`.

The controlled reproductions use the same direct-positive fixture bytes,
unchanged endpoint queries, CodeQL CLI **2.27.0** (build
`b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`), and **cpp-all 12.1.0**
(`c6baf479093fafc81d4655dc2014dc583360308e`). Extraction inside the Codex
filesystem sandbox produces `Signalled` and neither endpoint. Extraction on
the host outside that sandbox observes both endpoints in both languages.
Queries against both sets of databases run on the host, isolating extraction
access as the changed variable. This establishes an extraction-access failure;
it does not identify the particular denied operating-system operation or
claim that every historical exit-code-4 failure has the same underlying cause.

The host rerun also exposed partial extraction of C++ fixtures using standard
library headers from the current macOS SDK. The retained `closure-capture`
extractor log reports five parser errors in libc++'s `__algorithm/find.h`.
The corrected decoder rejected these results. The interrupted attempt is
retained separately as incomplete, without claiming a full-population report.
Repeating that fixture with `SDKROOT` explicitly set to the installed macOS
15.2 SDK produced one successful translation and zero errors or partial
translations. The full C++ retry uses this SDK; its path, version, metadata
digest, and compiler identity are recorded. No fixture, header, query, or pack
was patched, and no extractor warning or failure was suppressed.

The unchanged direct-positive query emits one merged SARIF row containing
both roles. The existing multiline decoder already counts both correctly.
There is no evidence here requiring a query API, endpoint matcher, or SARIF
role-decoding workaround.

## Correction

The decoder now treats explicit C/C++ extraction errors, partial extraction,
and extractor-summary failures as `runner-error`, even when CodeQL reports
successful execution. It uses notification identifiers and structured
attributes, without parsing prose, source text, display strings, or filenames.
Other informational notifications remain non-errors.

`BothMustBeObserved` remains unchanged. Successful extraction without both
endpoints is still `inconclusive`; missing endpoints never become a clean
negative. The production queries, pack locks, population, and scoring contract
are unchanged. Full kernel execution uses host access that successfully
extracts the fixtures.

The v0.8.0 reports, raw evidence, freeze, and published scorecards are retained
unchanged. The correction evidence is separate under
[`reports/issues/213`](../reports/issues/213). It is a retrospective correctness
correction, not a replacement release freeze or a new latency comparison.

The C sweep began with the baseline runner before the decoder patch; the C++
retry uses the corrected runner. Both executable digests are recorded. A Rust
regression rereads every new SARIF file through the corrected error decoder,
endpoint gate, and existing callsite reconciliation, and checks the resulting
outcome against each retained report. This independently verifies that the C
report does not rely on the old decoder's failure-handling gap.

## Reproduction and validation

The `reproduction` directory retains create/analyze logs and SARIF for the
sandbox and host direct-positive controls. `identity.json` records CLI,
pack, input, and runner identities. `frozen-audit.json` records the failed
frozen populations.

Run the executable source/sink controls outside the restricted sandbox:

```sh
python3 scripts/test-codeql-c-endpoints.py \
  --codeql /path/to/codeql-2.27.0/codeql \
  --codeql-packs /path/to/frozen-packs \
  --output-dir /path/to/new-control-evidence
```

The controls exercise resolved calls, unused declarations, similarly named
unrelated functions, and source-only/sink-only populations. They supplement
the runner's unit regressions for merged endpoint rows and the unchanged
both-endpoints gate; they do not establish arbitrary C++ overload or namespace
modeling beyond the benchmark's existing controlled endpoint contract.

The full C++ command is:

```sh
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.2.sdk \
  /path/to/dataflowbench run-codeql-cpp-kernel \
  --codeql /path/to/codeql-2.27.0/codeql \
  --codeql-packs /path/to/frozen-packs
```

Run it in a separate checkout/evidence root: kernel commands write their
standard report paths. The C command is `run-codeql-c-kernel`; its successful
sweep used the default SDK. These retrospective environments are recorded
separately and must not be presented as a prospective v0.8.0 measurement.

## Completed correctness comparison

| Population | v0.8.0 decisive | Corrected decisive | Corrected positive recall | Runner errors |
| --- | ---: | ---: | ---: | ---: |
| C | 0/58 | 57/58 | 26/30 (86.7%) | 0 |
| C++ | 0/68 | 67/68 | 21/34 (61.8%) | 0 |

The frozen v0.8.0 positive-recall denominators were empty; its recall is
undefined, not zero. Both corrected populations retain their infeasible-branch
negative as `inconclusive`. No missing endpoint was converted to `not-reached`.

All 106 cells shared with v0.7.1 now have exactly the same normalized outcomes
as that release: 104 decisive and two inconclusive. The shared positive results
remain 22/26 for C and 16/28 for C++; this restores the 38 previously reached
shared positives without claiming an analyzer recall improvement. All 20
additional v0.8.0 cells are decisive in the correction. Per-population counts
and transitions are in [`summary.json`](../reports/issues/213/summary.json).

Recompute the summary with `python3 scripts/summarize-codeql-c-correction.py`.
It checks equal fixture/configuration/CLI identities, exact populations, and
complete extraction before calculating coverage and eligible-positive recall.
