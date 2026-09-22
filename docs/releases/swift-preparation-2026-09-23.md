# Swift release preparation — 2026-09-23

This is blocked preparation from merged `c155aab98da74e4299d8e38404c1342d41783d4b`.
Post-merge CI passed. No release version, final population, opaque-template
exclusion, full execution, freeze, tag or publication is selected here.
The user choice between deferring the two opaque Swift templates and pursuing
faithful implementation remains pending. Preparation is not acceptance of
either choice, and does not close #220 or #215.

## Current evidence and population

The [successor coverage inventory](../../evidence/swift-release-preparation-220/2026-09-23/coverage-v2.json)
keeps all 58 registry identities visible. Seven A38/A39 families have complete
A40 typed coverage: six native families have prospective unsupported decisions
for both tools and the Result family has fresh inconclusive executions. This
is coverage completion, not a claim that native fixtures ran or that the
analyzers passed those cases. The historical v1 audit remains byte-for-byte
unchanged and still describes its earlier boundary.

The unresolved templates remain:

- `dfb-template-model-opaque-propagator`
- `dfb-template-model-propagator-position`

The [current-input snapshot](../../evidence/swift-release-preparation-220/2026-09-23/current-population.json)
binds 1,104 existing cases: 1,000 pre-Swift cases plus 104 Swift cases. It is
an observed candidate snapshot, not final release membership. Its exact
fixture revision is
`sha256:f4478ffee9d63648290bd6f68364e530677d3e8e37714075388683d9c31d5dde`.
The default input partitions are 952 core, 92 controlled modeling, 48 native
modeling, six language-extension and six calibration cells. Tracks, tiers
and model profiles remain separate. A changed opaque-template decision may
require a successor snapshot; it must not silently mutate this one.

The 92 retained reports contain 4,244 rows across three different fixture
revisions: 82 v0.8.0 reports/4,036 rows, six Swift v1 reports/180 rows, and four
A40 reports/28 rows. These are not common-revision release results. Changing
a report's revision string, concatenating old reports, or reusing old scores
would not establish a fresh release run.

## Dated pin-currency review

The [metadata audit](../../evidence/swift-release-preparation-220/2026-09-23/pin-metadata/next-pin-manifest.json)
retains 49 primary-source requests, response digests, timestamps and publisher
asset digests. The review date is 2026-09-23 in Africa/Johannesburg (collection
occurred on 2026-09-22 UTC). These are proposed future pins, not active adapter
changes or runtime qualifications. Unchanged pins are held because the audited
stable channel still matches the measured pin; they still require fresh runs.

| Adapter or dependency | Measured pin | Audited candidate | Decision |
| --- | --- | --- | --- |
| Bifrost | 0.11.4 | 0.11.5 | Propose bump; qualify |
| CodeQL CLI | 2.27.0 | 2.27.1 | Propose bump; qualify |
| Joern | 4.0.628 | 4.0.633 | Propose bump; qualify |
| Semgrep | 1.177.0 | 1.177.0 | Hold; GitHub and PyPI agree |
| Infer | 1.3.0 | 1.3.0 | Hold latest stable |
| FlowDroid | 2.15.1 | 2.15.1 | Hold latest GitHub stable; Maven artifact requalification pending |
| Pysa / pyre-check | 0.10.0 | 0.10.0 | Hold latest PyPI stable |
| Pyrefly dependency | 1.3.1 | 1.3.1 | Hold latest PyPI stable |
| OpenTaint semantic | 0.4.6 | 0.4.6 | Hold latest immutable semantic channel |
| OpenTaint analyzer / models | analyzer/2026.09.04.c51dc3e | Same | Hold immutable channel |
| OpenTaint rules | rules/v0.3.0 | Same | Hold immutable rules channel |
| Semgrep Rules | 40b8c63f75dc7c22c8a77482d73bfb864b146f7e | a84ff9cc2453ca91d581380de4b8b3f272f6f4be | Propose exact snapshot after rule review |

Semgrep Rules declares `develop` as its default branch. Its audited head is
three commits ahead of the measured snapshot; the earlier `main` branch probe
returned `311ca4e9ba59d700624539bf658e3d29b134ee77`. Both responses remain
retained, but the latter is not represented as the default-branch candidate.
OpenTaint moving aliases are not immutable pins. FlowDroid's GitHub release
has no assets: the historical Maven digest is retained, but the artifact has
not been downloaded or requalified in this audit.

The [13 CodeQL registry roots](../../evidence/swift-release-preparation-220/2026-09-23/codeql-packs.json)
were resolved without prereleases into an isolated directory using CLI 2.27.0.
Each requires a proposed bump and qualification under the selected new CLI:

| Root | Measured | Resolved stable |
| --- | --- | --- |
| `codeql/java-all` | 9.3.0 | 9.3.1 |
| `codeql/javascript-all` | 2.10.1 | 2.10.2 |
| `codeql/python-all` | 7.2.5 | 7.2.6 |
| `codeql/csharp-all` | 7.3.0 | 7.3.1 |
| `codeql/go-all` | 7.3.1 | 7.3.2 |
| `codeql/cpp-all` | 12.1.0 | 12.1.1 |
| `codeql/ruby-all` | 7.0.0 | 7.0.1 |
| `codeql/rust-all` | 0.2.21 | 0.2.22 |
| `codeql/java-queries` | 1.11.10 | 1.11.11 |
| `codeql/javascript-queries` | 2.4.5 | 2.4.6 |
| `codeql/python-queries` | 1.8.10 | 1.8.11 |
| `codeql/swift-all` | 6.8.3 | 6.8.4 |
| `codeql/swift-queries` | 1.3.10 | 1.3.11 |

Retained pack metadata and file manifests bind the observed downloaded trees,
including bundled dependencies. They are not a newly accepted transitive lock
or compatibility certificate. Re-resolve and commit exact root/transitive locks
under the chosen CLI, verify downloaded asset hashes against publisher digests,
and run realistic positive and near-miss activation controls before the full
common-revision run. New Swift pins also require renewed vendor source and
model feasibility review; old unsupported decisions cannot simply be reused.

## Required versioned execution work

The [blocked execution plan](../../evidence/swift-release-preparation-220/2026-09-23/execution-plan.json)
records all 92 lanes, exact historical case memberships and report digests,
but leaves executable commands and new output roots unset. It is deliberately
outside the executable release directory and has no release name. The
existing executor must not consume it as an approved run.

After the semantic choice and full-population review, register a versioned
common population and qualify each runner against it. Existing Swift runners
are scoped to 90 or 104 inputs; their separate versioned successors must bind
the approved common revision without changing historical input manifests or
activation certificates. New report paths, raw paths, configuration-hash
routing and freeze selections are required before execution. Current runners
that overwrite historical paths or refuse a second write cannot simply be
invoked against those destinations.

Every freeze-bound lane must rerun, including unchanged pins. Prospective
capability decisions must be reviewed at the selected pin and common
population; unsupported remains a decision record, not fabricated analysis.
Retain all pin/control failures, retries, native outputs, cold sidecars, warm
observations and invocation-overhead records. Preserve the unchanged
512 MiB/60-second scored contracts and typed incompleteness. No native Swift
fixture binary may run.

Adapter READMEs and `docs/adapters.md` are bound by accepted R2 review inputs.
This dated supplementary audit does not silently rewrite them. Pin integration
must resolve that versioned-input dependency and land the required declarations
and successor review before measurement. Real-project R2 work remains a
separate evidence and freeze lifecycle.

## Resource and timing reservation

The [dated resource checkpoint](../../evidence/swift-release-preparation-220/2026-09-23/resources.json)
records a historical serial sum of **16.927 hours**: 15.726 hours for the
latest completed observations in the 82 old lanes plus 1.201 hours for the
Swift lanes. The old lanes use attempt wall times; Swift uses summed per-case
durations and therefore omits any additional outer-runner overhead. This is a
planning reference, not a future runtime guarantee.
The full retained ledger has 128 starts and 127 completions; the unfinished
`codeql-go-kernel-attempt-02` remains visible. Warm coverage is only Joern Java
and Semgrep Java; overhead coverage is nine groups with one OpenTaint retry.
The selected-lane sum does not include a complete future control/warm/overhead
matrix, new-pin qualification, or unbounded failure diagnosis.

Reserve a provisional **24-hour quiet serial window** for the observed scope
(about seven hours beyond the historical sum), with separate time for pin
qualification before that window. This is an operational proposal requiring
review, not a certified upper bound. Re-estimate after population selection,
new-pin controls and runner qualification; stop and retain incomplete evidence
if the reserved window is exhausted.

The audit host is an Apple M4 with 10 cores and 32 GB RAM, with 140 GiB free
at observation. Existing scoped evidence occupies about 228 MiB (159.6 MiB
release tree plus 68.4 MiB evidence); the tool cache is about 15.32 GiB and the
shared build target about 1.20 GiB. These retained sizes do not bound temporary
analyzer databases or downloaded/unpacked replacement tools. Provisionally
reserve **40 GiB additional free space**, recheck disk and memory pressure
before qualification and every execution stage, and measure temporary peaks
in controls before accepting this reservation. No shared cache or target
cleanup is authorized by this plan. Run one analyzer process at a time and
check other agents' builds before beginning; the scored 512 MiB limit stays
unchanged regardless of host RAM.

## Release gate order

1. Resolve the opaque-template choice; review the final full population and release version.
2. Review all dated pin bumps/holds and qualify immutable assets, runtime identities, root/transitive packs and realistic activation controls; commit the new adapter configurations.
3. Review the exact common-revision plan, selected case IDs, commands, new output paths, resource reservation and quiet-host timing gates.
4. Run serially and retain all attempts, cold/warm/overhead evidence and typed outcomes. Validate and merge the evidence PR with terminal green CI.
5. From clean merged main, create the freeze in a separate PR; generate results and release notes, and validate the freeze, generated output and exact tag tree.
6. Perform only the explicitly authorized tagging/publication step, then independently verify deployment and public availability.

The existing annotated `v0.8.0` tag still peels to
`9c0916338abc42ab13565b5d9e6f310d46134afc`. The GitHub release-object endpoint
returned HTTP 404 during this audit. A tag and deployed snapshot do not imply
a GitHub release object; none was created here.
