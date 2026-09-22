# Swift candidate compatibility — 2026-09-23

The proposed CodeQL 2.27.1 and Joern 4.0.633 runtimes complete isolated,
non-scored endpoint controls with realistic near misses. Both still report no
flow for either Result example. These observations do not qualify a release,
change active pins, or resolve the two opaque-template choices. Refs #220 and
#215. Both issues remain open; acceptance is incomplete.

## Exact candidate provenance

The [prospective plan](../evidence/swift-candidate-qualification-220/plan.json)
was committed at `39b7934a829806b770e699fe2854853a3fcc5c7c` before the analyzer
controls. The base is merged `a3f22c8325b2cbbafe27823f439b9c32083482a9`, whose
post-merge CI `35797273079` passed all four checks. Candidate selection uses
the [dated all-adapter audit](releases/swift-preparation-2026-09-23.md).

| Artifact | Verified archive bytes | SHA-256 |
| --- | ---: | --- |
| CodeQL 2.27.1 osx64 | 981,846,365 | `412c600764a7835f9548af120d0bdadea1040c6f68b8f6bf04ec72a664891f63` |
| Joern 4.0.633 macOS arm64 | 1,782,451,433 | `e11563c7cf4797db76655524398f108c3469a518fa3ed823de0aac2a1155aec6` |
| Bifrost 0.11.5 universal macOS | 109,840,597 | `8e7c925e178aec27d5851f0cf589bd1d2bb7964e6e51b90e7efdad52caf58c69` |

Each size and hash matches the retained publisher metadata before extraction.
Runtime witnesses confirm all three versions. Bifrost's executable hash is
`f95ef29312b8f408f401c9c251b16416b807fb57556d3a414cc1c5d3a51ea1ec`;
its scope is artifact identity and `--version`, with no scans or benchmarks.
Archives and installations remain outside Git in isolated temporary paths;
compact acquisition records, publisher provenance, selected executable hashes,
and raw version output are retained under
[`evidence/swift-candidate-qualification-220`](../evidence/swift-candidate-qualification-220/).

CodeQL uses Swift library 6.8.4 and Swift queries 1.3.11 plus an exact separate
transitive lock. The first endpoint attempt extracted a finalized Swift
database, then failed because downloading the two roots did not expose all
transitive libraries to the custom query. That attempt remains retained.
After explicit locked transitive downloads into the isolated candidate cache,
the same control succeeded. Both the initial and resolved pack-file manifests
remain visible. The other eleven proposed CodeQL roots have not been runtime
qualified by this tranche.

Joern's verified archive extracted its launcher and frontend executables with
mode 0644. The first launch failed before runtime; a second identified the
additional `bin/repl-bridge` executable. Both failures and the exact isolated
permission repairs are retained. Content hashes did not change. The third
version witness and all subsequent controls succeeded.

## Control observations and limits

The [machine reconciliation](../evidence/swift-candidate-qualification-220/summary.json)
retains seven analyzer attempts: the failed initial CodeQL dependency attempt,
then three completed controls for each tool. The endpoint control resolves
sources only at lines 9 and 11, sinks only at lines 9 and 10, and a flow only
to line 9. Wrong source arity, wrong sink type, and a different declaration
kind remain near misses for both candidates.

| Candidate | Identity and near misses | Result positive | Result negative | Largest individual-command RSS |
| --- | --- | --- | --- | ---: |
| CodeQL 2.27.1 / Swift 6.8.4 | Pass | Exact endpoints; no flow | Exact endpoints; no flow | 629.219 MiB |
| Joern 4.0.633 | Pass | Exact endpoints; no flow | Exact endpoints; no flow | 419.859 MiB |

CodeQL explicitly rounds the requested 512 MiB setting up to its 2 GiB minimum;
measured individual-command RSS also exceeds the scored limit. Joern's
individual-command readings do not establish aggregate memory compliance, and
its graph reports unproven completeness with exhaustion not observable. No-flow
observations therefore remain unqualified; they are not published as clean
negative or false-negative benchmark rows. This candidate check supplies no
new evidence of faithful Result propagation support.

The controls never execute compiled fixture binaries. Analyzer processes run
serially with the committed phase deadlines: CodeQL extraction and queries
60 seconds each, Joern frontend 180 seconds and query 60 seconds. Joern's
180-second frontend allowance is explicitly non-scored feasibility, not a
change to the scored 60-second contract. Process polling cannot prove complete
descendant containment, and individual phase success is not aggregate budget
qualification. Retained scratch and all failed attempts preserve these limits.

Native source/model feasibility and the vendor rule catalogs must be reviewed
again at the new pins before any native capability decision. Old unsupported
decisions are not transferred by this work. No opaque example, new semantic
identity, population exclusion or deferral is selected. The common-population
execution, pin integration, separate merged-main freeze and publication gates
remain blocked as described in the preparation plan.
