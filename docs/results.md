# Audited result generation

`generate-results` turns a validated `freeze/v1` manifest into the result
artifacts a release or website may publish. It is the only sanctioned path
from evidence to published numbers: every value on a generated page derives
from the frozen manifest and the case files it binds, never from hand-edited
tables.

```bash
cargo run -- generate-results --manifest reports/freeze.json --output-directory site/results
cargo run -- generate-results --manifest reports/freeze.json --output-directory site/results --check
```

Generation first runs full freeze validation, including the clean-checkout and
HEAD-revision checks, so artifacts cannot be produced from evidence that would
not validate. `--check` regenerates the artifacts in memory and fails if any
checked-in file is stale, missing, or unexpected; CI can use it to prove the
published pages match the freeze they cite.

## Artifacts

The output directory receives:

- `results.json` — the complete machine-readable model, including the manifest
  path and SHA-256 digest, the bound benchmark identity, the claim, and one
  scorecard per frozen report;
- `index.md` — an MDX-compatible overview of the claim, exclusions, and
  scorecard links;
- `scorecards/<id>.md` — one fragment per frozen report, where `<id>` is
  derived from the adapter, track, score dimension, and model profile (with an
  ordinal suffix when one adapter froze several populations of the same
  shape).

Repeated generation from identical evidence is byte-stable: artifacts carry no
timestamps or environment detail, and every collection is emitted in a
deterministic order.

## Partitioning and scoring

Each scorecard covers exactly one frozen report and therefore one adapter, one
semantic track, one score dimension, and one model profile. Within a
scorecard, results are partitioned by language and score tier, then broken out
by semantic dimension and template. Scorecards are never pooled into a
combined leaderboard, and `benchmark-controlled` never mixes with
`tool-native`.

Outcome interpretation follows the [scoring contract](scoring.md):

- positive cases score `reached` as a true positive and `not-reached` as a
  false negative; negative cases score `not-reached` as a true negative and
  `reached` as a false positive;
- `inconclusive`, `unsupported`, and `runner-error` are reported as capability
  and execution coverage with their own counts and are never converted into
  negatives — a dimension with no definitive result publishes a null rate, not
  a zero;
- per-dimension rates are exact fractions with explicit numerators and
  denominators; headline rates are macro-averages over templates and then over
  semantic dimensions, while raw case counts remain visible for audit only;
- `calibration` cases publish outcome coverage but no correctness rates.

Exclusions from the claim are listed verbatim with their reasons, and every
case row links its retained raw evidence path and SHA-256 digest, so a reader
can walk from any published number back to frozen bytes.

## Immutability

Generated artifacts inherit the freeze lifecycle in [freeze.md](freeze.md): a
corrected result means a new freeze and a fresh generation, never an in-place
edit of published pages. If `--check` fails, regenerate from the freeze the
pages cite or create a new freeze — do not patch the artifacts by hand.
