# 2026-09-23 amendment: prospective Swift CodeQL extraction cutoff

The user explicitly approved: “Let's make cut-off 2.5 minutes then”. Future
Swift CodeQL extraction uses a **150-second operational cutoff**. Analysis
continues to use **60 seconds and 512 MiB**. Extraction RSS is reported
separately and is not tested against the analysis memory budget.

The decision follows a single exact PR #236 synthetic-control diagnostic that
completed naturally in 121.10 seconds using isolated Swift 6.3.3, SDK 26.5 and
CodeQL 2.27.1 / swift-all 6.8.4. That contended diagnostic motivates this explicit
prospective choice; it does not certify performance or requalify past results.
No new analyzer execution is required to implement the cutoff.

## Versioned policy and scope

`adapters/codeql/swift-extraction-v1/policy.json` records the approved phase
limits. The current `probe-swift-v2-codeql.py` defaults to 150 seconds for
database creation and retains the policy identity and hash with each new
attempt. Its analysis queries keep their separate 60-second limit and 512-MiB
request. A nondefault diagnostic extraction deadline still requires explicit
unqualified feasibility scope. No other tool's deadline changes.

`run-codeql-swift-case.py`, `run-swift-v2-additions.py`, their adapter
configurations, activation evidence and report hashes remain historical v1/A40
execution contracts. They are not prospective entry points for this policy.
They remain byte-identical so prior evidence can be verified. Before a future
scored Swift CodeQL run, a newly versioned scored adapter configuration must
bind this policy and its runner; the old scored runner must not be silently
reused as a 150-second implementation. This amendment does not activate a new
scored configuration or change any capability partition.

The raw-log gate now recognizes `.log`, `.log.gz`, `.log.txt` and
`.log.txt.gz`. Missing logs and logged errors still block observation.
Historical logs and retrospective correction records remain unchanged.
No pins, opaque-template decisions, corpus runs, freezes or publication change.
