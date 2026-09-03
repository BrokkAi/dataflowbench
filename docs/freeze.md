# Immutable freeze and release evidence

`schemas/freeze.schema.json` defines the versioned `freeze/v1` contract. A
freeze is an evidence manifest, not a generated score table. It is valid only
when `cargo run -- validate-freeze reports/freeze.json` can re-read every
referenced artifact and verify its bytes.

The manifest binds:

- the exact benchmark Git revision, release name, case and normalized-result
  schema versions, fixture revision, and a clean-worktree assertion;
- every selected case, its semantic track/tier/profile metadata, case digest,
  and the SHA-256 digest of every fixture;
- each adapter's version, analyzer version, build identity, configuration hash,
  semantic track, score dimension, and model profile;
- each normalized report, its digest, selected case IDs and outcomes, and one
  retained raw-evidence digest per result; and
- the claim scope, explicit exclusions, score tiers, and model profiles.

Validation rejects missing files, altered bytes, stale case or fixture
metadata, mixed benchmark fixture revisions, duplicate or incomplete result
sets, report/adapter identity drift, dirty checkouts, and raw evidence that
declares `inconclusive`, `unsupported`, or `runner-error` while the normalized
report claims a clean `not-reached`. Those outcomes remain distinct and are
never converted into negatives.

Tracks, score dimensions, and profiles are partitions of the claim. A report
binds one semantic track, one score dimension, and one model profile, and all
of its selected cases must match the track and profile. Witness quality is a
separate dimension that may consume a semantic-flow case without being pooled
with its correctness result. In particular, `benchmark-controlled` and
`tool-native` results cannot be pooled; taint, value-flow, typestate, witness,
and performance evidence remains in independent scorecards.

## Freeze-prep checklist

Freeze-prep is the window between deciding to cut a release and running
`create-freeze`. It is complete only when every step below is done, in this
order, because later steps consume what earlier ones fix.

1. **Fixture revision.** Confirm the fixture set for the release; every
   report the freeze will bind must declare this one revision.
2. **Pin currency.** For every adapter, compare the pin declared in
   `adapters/<tool>/README.md` (and witnessed by that adapter's committed
   reports) against the then-latest stable upstream release, per the
   [pin-currency policy](adapters.md#reference-tool-pin-currency). The
   vendored Semgrep rules snapshot (`adapters/semgrep/native/*`) is a pin in
   this list. For each analyzer the outcome is exactly one of:
   - **bump** to latest stable through a re-pin PR, then re-run *every* slice
     of that adapter at the fixture revision from step 1; or
   - **hold**, with a dated reason written into a new entry under
     [pin-currency reviews](adapters.md#pin-currency-reviews). "Nobody looked"
     is not a reason; a pin with no reason on record is a bump.

   Record the review as a dated table in `docs/adapters.md` before any re-run
   starts, so the declarations move first and the evidence follows. Joern's
   near-daily releases are evaluated here and only here.
3. **Re-runs.** Re-run every freeze-bound report that the release must
   refresh — the bumped adapters from step 2, and any slice deferred by the
   freeze rule since the last release — and commit the evidence.
4. **Amendments.** Confirm every amendment the cycle recorded is in its own
   commit and names which freezes it invalidates.
5. **Validation.** `cargo run -- validate`, `validate-reports`, then
   `create-freeze` and `validate-freeze` from a clean checkout, as the
   lifecycle below describes.
6. **Release notes.** Write `docs/releases/vX.Y.Z.md` from the
   [release-notes template](#release-notes-template), including the pin
   table with each analyzer's distance from upstream latest at freeze time.

An out-of-cycle bump (a Bifrost fix cycle, for example) runs the same steps
scoped to the one adapter: re-pin PR, re-run, freeze. It is never a bump
without a freeze behind it.

## Freeze lifecycle

Create the manifest in a clean checkout after the benchmark and adapter inputs
are fixed:

```bash
cargo run -- create-freeze --report reports/<normalized-report>.json --scope release --release vX.Y.Z
```

`create-freeze` assembles the manifest from committed normalized reports,
computing every case, fixture, report, and raw-evidence digest, and validates
all evidence before writing. Because a commit cannot contain its own hash, the
manifest records the *evidence* commit and is committed on top of it:
validation accepts a `benchmark.revision` that is the checkout HEAD or one of
its ancestors, while the manifest digests — not the revision equality — carry
the byte-immutability guarantee for every referenced artifact. Release and
website claims additionally require a `v`-prefixed tag whose commit contains
the frozen revision. The flow is: commit evidence, run `create-freeze`, commit
the manifest (and any generated result artifacts), then run `validate-freeze`
from the clean checkout.

Keep the manifest and all retained evidence immutable once used for
a release or website claim. A corrected result is a new freeze: it receives a
new benchmark revision/release (and new digests), while the old manifest and
its evidence remain available for audit. Never rewrite an old freeze in place
or silently replace a report behind an existing digest.

The validator intentionally does not generate result pages or scores. Result
generation belongs to the publication workflow in [results.md](results.md):
`generate-results` consumes a successfully validated freeze and derives every
published artifact from its evidence.

## Release-notes template

Release titles are just `DataFlowBench vX.Y.Z`; everything below is the notes
body. The `docs/releases/vX.Y.Z.md` snapshot is the canonical text and the
GitHub release carries the same body. Sections are fixed so that a reader can
diff two releases; a section with nothing to say says so rather than being
dropped.

```markdown
# DataFlowBench vX.Y.Z

One paragraph: what this release is for and how wide its delta is.

## Freeze identity

Benchmark revision, release tag, fixture revision, and the `reports/freeze.json`
digest.

## What re-ran

Which reports were re-executed for this freeze and which carried over, with
the reason for each group.

## Pin currency at freeze time

The full review is in `docs/adapters.md` under a dated heading; this table
is its summary and lists every analyzer, held or not.

| Analyzer | Pin at vX.Y.Z | Upstream latest stable at freeze | Distance | Outcome |
| --- | --- | --- | --- | --- |
| Bifrost | | | | Bumped from … / Held: <dated reason> / Current |
| CodeQL CLI (+ query packs) | | | | |
| Semgrep CE | | | | |
| Semgrep rules snapshot (`semgrep/semgrep-rules@<sha>`) | | | | |
| Joern | | | | |
| OpenTaint | | | | |
| Infer | | | | |
| FlowDroid | | | | |
| Pysa (pyre-check + Pyrefly) | | | | |

Every **Held** row repeats its dated reason here, not only in
`docs/adapters.md`. Distance is stated in upstream releases (or dailies, for
Joern; commits, for the rules snapshot), never as "recent".

## Honest negatives

Regressions taken with a bump, defects found in our own fixtures, anything a
reader could otherwise only find by diffing evidence.

## Amendments first bound by a freeze here

Cite each amendment by number; the notes never hold amendment text.

## Bound evidence

The per-report table: path, digest, tool version and build identity, case
count, carried-over or new.

## Reproduction

The commands that reproduce the freeze from the tagged revision.

## Immutability

The statement that this freeze and its evidence are never rewritten in place.
```
