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

## Freeze lifecycle

Create the manifest in a clean checkout after the benchmark and adapter inputs
are fixed. Keep the manifest and all retained evidence immutable once used for
a release or website claim. A corrected result is a new freeze: it receives a
new benchmark revision/release (and new digests), while the old manifest and
its evidence remain available for audit. Never rewrite an old freeze in place
or silently replace a report behind an existing digest.

The validator intentionally does not generate result pages or scores. Result
generation belongs to the later publication workflow and must consume a
successfully validated freeze.
