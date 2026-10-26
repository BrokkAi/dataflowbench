# Compact review and lossless evidence

`scripts/package-evidence.py` creates a small review alongside a lossless,
compressed snapshot. It uses Python 3.10 or newer and the standard library.
No Git LFS is involved. The existing normalized-report schema, scoring,
freezes, adapter pins and publication gates are unchanged.

## Create a package

Choose one repository-relative directory containing the detail to preserve.
Select review inputs explicitly; the tool never guesses the final attempt or
silently chooses only successful runs. Paths passed to `--report`, `--attempts`
and `--copy` are relative to `--root` and must be inside `--scope`.

```sh
python3 scripts/package-evidence.py pack \
  --root /path/to/source-checkout \
  --scope reports/releases/example \
  --output /path/to/new-package \
  --report reports/releases/example/attempts/run-01/report.json \
  --attempts reports/releases/example/ledger.jsonl \
  --copy reports/releases/example/review/status-and-holds.md
```

Repeat input options to retain multiple reports, ledgers and context files.
For a complete evidence package, the selected scope must also contain the raw
outputs, timing/environment sidecars, failed attempts and other evidence you
intend to deliver. Packing preserves **every regular file in the scope**, not
just the review inputs. References outside that scope are not followed or
claimed to be included. Include expected/missing populations, denominators,
separate unclosed events, uncertainty explanations and active holds as explicit
context with `--copy`; observed row counts cannot establish those facts.

The output must be outside the scope and must not exist. The source is never
changed. Use a quiescent evidence tree: changes to inventoried files during
packing cause failure, and later additions need a separately named supplement.
The inventory is not an atomic filesystem snapshot of a live experiment.

The package has these stable paths:

| Path | Content |
| --- | --- |
| `review/START-HERE.md` | Entry point and authority boundary |
| `review/summary.json` | `dataflowbench-compact-review/v1`: original report identity, observed case counts and all five outcome counts; attempt counts/statuses; source paths, byte counts and hashes |
| `review/cases.csv` | Every selected case, original outcome, duration, memory, raw-output link, JSON pointer and full-result digest |
| `review/attempts.jsonl` | Every input ledger line, all scalar fields, raw-line SHA-256, line number and names of nested detail fields |
| `review/files/<original-path>` | Byte-exact copies of explicitly selected human/context documents |
| `review-manifest.json` | Selected inputs, hashes of review files and the detailed bundle index |
| `detail/bundle.json` | Original scope, counts, sizes, manifest and compressed-part hashes |
| `detail/files.jsonl.gz` | Original path to content SHA-256, byte count, mode and nanosecond modification time |
| `detail/detail.tar.gz.partNNNN` | Consecutive pieces of one gzip/tar stream, at most 40 MiB each |

Review files are derivatives, **not normalized reports or release evidence**.
Cases are never filtered by outcome. `inconclusive`, `unsupported` and
`runner-error` remain distinct; no scores, expected denominator, completion
or publication authorization are inferred. Large diagnostics, anchors,
witnesses and future fields remain in the complete original report. Its
SHA-256 plus `/results/N` identifies each detail row. `result_sha256` hashes
that complete result serialized as sorted-key, compact, ASCII JSON with a
trailing newline and finite numbers. It is a derivative identity; the source
file hash remains the byte identity.
CSV display cells beginning with spreadsheet formula characters are prefixed
with an apostrophe; the original values remain in the referenced detail row.

The review parser rejects duplicate JSON keys, non-finite numbers, duplicate
case IDs, unknown normalized outcomes and malformed rows. This is structural
review validation, not the repository's complete report/raw-evidence validator.
Arbitrary attempt statuses and every attempt line are preserved. Empty or
invalid JSONL lines fail rather than disappearing from the denominator.

## Verify and read

```sh
python3 scripts/package-evidence.py check /path/to/new-package
python3 scripts/package-evidence.py read /path/to/new-package \
  reports/releases/example/attempts/run-01/report.json --pointer /results/0
python3 scripts/package-evidence.py read /path/to/new-package \
  reports/releases/example/ledger.jsonl --line 1
```

`check` hashes every manifest/part, verifies every uncompressed content object
and regenerates the review from those verified originals. `read` also verifies
the whole detailed bundle before emitting selected bytes; without a selector,
stdout is the byte-exact original file. `--pointer` uses RFC 6901 JSON pointers;
`--line` is one-based and returns the exact ledger line, including its original
line ending. Reading does not execute embedded commands or contact a service.

Hashes detect corruption and bind derivatives to the supplied detailed index;
they are not signatures. Obtain the root manifests through a trusted channel.
Verification is proportional to the complete compressed bundle, even for one
file. Avoid repeatedly reading individual files from a multi-gigabyte package;
materialize the needed set once instead.

## Use existing report readers and CLI

```sh
python3 scripts/package-evidence.py materialize /path/to/new-package \
  --output /path/to/new-evidence-root
```

This restores all original relative paths beneath a **new** directory. Repeat
`--path <original-path>` for a selected subset; all bundle objects are still
verified. Duplicate content restores as independent files. Files retain their
bytes, modes and modification times. Ownership, access times, directory
metadata, hardlink identity, ACLs and extended attributes are not represented;
symlinks and special files are refused. Verification failure does not publish
a partial restore, and existing destinations are refused.

Readers that expect repository-relative raw outputs must run against the
restored root with the matching repository source/schema/configuration files
available. Materialization alone does not satisfy a freeze's Git-revision or
configuration gates. Specialized historical audits continue to use their
original interfaces and path contracts.

For the ordinary report comparison consumer, the wrapper accepts a package,
normalized report or report directory on either side:

```sh
python3 scripts/package-evidence.py compare \
  --baseline /path/to/baseline-package \
  --current /path/to/current-package \
  --binary /path/to/dataflowbench \
  --output /path/to/new-comparison
```

Run this from the matching source checkout, as with `compare-reports` itself.
The wrapper verifies packages, materializes their explicitly selected reports
as byte-exact originals, then invokes `dataflowbench compare-reports`.
It preserves the Rust CLI's status and configuration-mismatch gate; explicit
`--allow-configuration-mismatch` has the same diagnostic meaning as in that
CLI. No analyzer is run. `comparison.json` is the existing CLI's output;
`package-inputs.json` binds packaged inputs to their original paths/hashes and
records the command and exit code. Materialized inputs remain in the output
directory for provenance inspection, including after comparison failure.
The review summaries themselves never enter scoring or comparison.

## Existing bundle compatibility

Sealed `dataflowbench-lossless-evidence-bundle/v1` detail bundles remain
compatible with the standalone library CLI:

```sh
python3 scripts/evidence_bundle.py check /path/to/sealed-snapshot/detail
python3 scripts/evidence_bundle.py check /path/to/sealed-snapshot/detail \
  --restore /path/to/new-evidence-root
```

An older release-specific review manifest is not the new generic review format;
keep its original review/verifier and delivery receipts. Do not repack a sealed
snapshot merely to adopt this feature. Use the generic tool for future
snapshots or supplements, with current holds and incomplete matrix status
copied explicitly.

## Git size and delivery limits

This feature is an additive packaging and reader workflow. Compression copies
do not remove raw evidence from the working tree or large blobs already in
Git history. Tracking both copies increases Git storage; splitting a stream
below individual-file limits does not make a multi-gigabyte commit suitable
for review. Keep large delivery packages outside the source PR and adopt a
separately authorized delivery/storage policy before changing what future
evidence is tracked. This PR neither migrates historical evidence nor adds an
upload, publication, Git LFS or history-rewrite workflow.

Focused fixture tests (no production archives or analyzers):

```sh
python3 scripts/test-evidence-bundle.py
python3 scripts/test-package-evidence.py
```
