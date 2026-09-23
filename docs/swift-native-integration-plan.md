# Swift native integration dependencies — 2026-09-23

This prospective implementation plan follows the retained Foundation source
and sink controls and the Joern external-property identity investigation.
It does not amend A40, activate a scored profile, or produce a new result.

## Population and lanes

The immutable `swift-synthetic-v2` population contains 104 inputs: 66 core,
20 benchmark-controlled modeling, 12 tool-native modeling, four calibration,
and two Result language-extension inputs. Its fixture revision is
`sha256:2dc97bb29cdba04c900308be9e3aef016a5a00d2ac11f2bcaa2ac39d9d2484ff`.

The next native integration covers the positive and negative cases for
source-sink, propagator, sanitizer, summary, entrypoint, and persistence.
Preserve their identities and bytes. Keep these two observations separate:

- **Vendor-native:** shipped source, sink, barrier, and transfer predicates.
- **Adapter-assisted:** resolver-backed process-input sources and corrected
  Foundation sink recognition, with the retained vendor propagation semantics.

There are 12 planned inputs per lane and zero new normalized outcomes. The
adapter-assisted lane is diagnostic until its own scoring contract is accepted;
it must never enter the existing tool-native denominator. A vendor-native
absence of flow is not by itself a capability decision or a clean negative.

## Ordered dependencies

1. Bind a new configuration identity to the exact candidate CodeQL CLI 2.27.1
   build `938af3639d0709b587251e45d9f8d2bdc3505696`, swift-all 6.8.4,
   isolated Swift 6.3.3 and SDK 26.5. Bind binary, pack, compiler, query,
   population, runner, and policy digests; reject mismatches before extraction.
   Historical v1 and A40 configurations remain immutable.
2. Use the prospective `swift-extraction-v2` diagnostic policy: extraction
   150 seconds, analysis 60 seconds and 2048 MiB. The canonical case metadata
   retains its historical 512-MiB contract. The larger diagnostic budget does
   not activate or retrospectively qualify those scored cases.
3. Commit the canonical-case qualification selection and query configuration
   before new observations. Start with the balanced source-sink pair, then
   entrypoint. Compile and extract only; never execute fixture binaries.
   Verify archived sources against the immutable population, raw extraction
   logs, resolved source/getter/value identity, exact sink arguments, and
   decoded output. Retain failed attempts and their original paths.
4. Qualify propagator, sanitizer, summary, and persistence independently.
   Endpoint controls establish neither Data summaries, numeric barriers, nor
   UserDefaults store/load semantics. Do not add local transfer rules to make
   vendor-native cases pass. Record exact missing surfaces or unresolved
   evidence rather than extrapolating from endpoint success.
5. Implement a new runner and report integration only after the qualification
   boundary is explicit. Preserve unsupported, inconclusive, and runner-error
   separately. Unproved aggregate memory or completeness cannot become a
   definitive negative. Register any new scored lane by prospective amendment
   before scored execution, with separate report paths and denominators.

## Independent blockers

Joern 4.0.633 remains blocked on external property declaration/value-type
identity in the retained CPG controls. Its investigation emits no new
unsupported partition and admits no adapter profile. The next useful upstream
fix must provide resolver-backed identity, followed by the same positive and
near-miss controls; matching property names is insufficient.

The two opaque modeling identities remain unresolved under the existing
completion contract. The standard-library closure-reflection construction
needs model-off/on evidence and a reviewed semantic decision before fixtures
or exclusion. Neither native endpoint progress nor this plan closes them.

## Evidence and completion boundary

Run the retained Foundation identity/source and Joern identity verifiers before
new integration, and preserve their manifests. Their successful diagnostic
controls establish only their stated scopes. In particular, inspect each
canonical fixture rather than assuming its shape from the control program.

The next deliverable is a versioned, preregistered qualification configuration
and fresh bounded canonical observations. Full-corpus execution requires the
separate all-adapter pin review and common final fixture revision. A new freeze,
release tag, generated scorecard and deployed publication remain later gates.
No historical report, failed attempt, freeze, or published denominator changes
through this plan.

References: [source controls](swift-foundation-sources-profile.md),
[sink controls](swift-foundation-identity-profile.md),
[Joern blocker](swift-joern-native-identity.md),
[completion contract](swift-completion-plan.md), and
[existing v2 partitions](swift-v2-partitions.md).

## Configuration verification

The pending configuration lives in
[`adapters/codeql/swift-native-v3`](../adapters/codeql/swift-native-v3).
Its input manifest binds the complete population and retained correction and
blocker evidence. `activation.json` records candidate pins and the two lane
identities; `partition.json` selects all 12 native inputs and the first balanced
qualification pair. It is not a runnable scored adapter.

Run `python3 scripts/verify-swift-native-integration.py` to check exact input
hashes, population membership, lane attribution, pending state and blockers.
Run `python3 scripts/test-swift-native-integration.py` for promotion, omission,
pin and profile-attribution mutation controls. CI runs both. A fresh qualification
runner must additionally bind its own code and runtime witnesses before it runs;
this configuration alone is not an execution or preregistered scored partition.
