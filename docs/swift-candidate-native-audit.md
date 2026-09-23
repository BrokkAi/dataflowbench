# Swift candidate native-surface audit — 2026-09-23

This bounded audit records candidate-specific shipped evidence for CodeQL
2.27.1 / Swift 6.8.4 and Joern 4.0.633. It emits no supported/unsupported
partition, changes no active pin and does not transfer the older versions'
capability decisions. Refs #220 and #215. Both issues remain open; acceptance
is incomplete. The two opaque-template choices are still pending.

The base is merged `3ce18d42929a1ce54e1cbdf22a2ac459ab42a829`; post-merge CI
`35799297239` passed all four checks. Runtime/archive qualification is retained
separately in [candidate compatibility](swift-candidate-qualification.md).

## CodeQL shipped source and model evidence

The candidate's own model query enumerated **876 rows: 45 sources, 13 sinks
and 818 summaries**. The query imported the shipped command-injection
configuration and model classes, introduced no benchmark model and reused the
already finalized candidate endpoint-control database. No native fixture was
extracted or executed in this tranche. The exact query, BQRS, decoded rows,
command results and database provenance are retained in
[CodeQL evidence](../evidence/swift-candidate-native-audit-220/codeql-models/).

Catalog matching finds the shipped `UITextField.text` source and
`Process.run(_:arguments:terminationHandler:)` sink, rejects a near-miss text
member, and finds no `ProcessInfo.environment` or `CommandLine.arguments`
source rows. These are catalog recognition controls, not runtime activation
of those endpoints. In particular, the presence of a `Process` sink row does
not prove it instantiates at an A38 native call site.

The file inventory binds all 1,350 QLL files in the resolved library tree,
including bundled dependencies, against the earlier candidate pack manifest.
Nine direct source-class declarations identify two abstract bases and seven
concrete implementations. The selected implementations were inspected:

- local/remote model-row dispatch;
- `contentsOf` initializer heuristics;
- WebKit navigation and JavaScript-export parameters;
- UIApplication launch-option URLs.

Their declared shapes do not supply the required environment/argv source
families. `Customizations.qll` contains no custom model. The command-injection
configuration consumes `FlowSource`; selected implementation copies, source
locations and exact pack metadata are retained. The pack build commit is
`6e9f9e38390175c41b99070a423c875f450759ca`, with its license included.

This does not establish that Swift modeling is absent: summaries, append
heuristics, numeric barriers and Process sink rows are shipped. The source
location scan is a navigation aid; it is not a general structural resolver or
an inability proof. Fresh candidate-native declaration mapping, endpoint
instantiation and scored-budget qualification remain outstanding before a
new native capability decision can be admitted.

## Joern vendor catalog

Both published artifacts match their publisher sizes and digests:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `querydb.json` | 130,570 | `3d7681a7222c4d1c42c6e1f267f824ee77112aa66dac65098602a07dc8b6627f` |
| `querydb.zip` | 75,486,212 | `02d3c87ad7f2fdf97b77bb848311788f5b2e3bb1697e18a03e4cf3820a377735` |

The candidate bundle's own `io.joern.dumpq.Main` produced the same complete
records as the published JSON after sorting by unique query name: **58
queries, zero Swift records**. Counts are C 27, Android 10, PHP 9, Java 7,
Kotlin 3 and Ghidra 2. The JSON comparison, archive/member/file hashes,
classpath hashes and raw loader outputs are retained in
[catalog evidence](../evidence/swift-candidate-native-audit-220/joern-catalog/).

The vendor-only classpath first failed on a missing Scala class. Adding the
candidate Scala libraries then exposed a missing Reflections class. Both
failed attempts remain retained. The third attempt used the exact matching
candidate runtime libraries after the vendor classes and succeeded. No source
file or CPG was supplied, and no query was run against a program. The loader
only materialized catalog records; no updater or installation was invoked.

Positive C-language catalog matching and synthetic case/near-miss matching
validate the census operation. Synthetic rows never enter the vendor catalog.
Zero Swift catalog records is evidence about this exact catalog, not proof
that every possible Joern Swift model mechanism is absent.

## Joern semantics and frontend boundary

The [mechanism checkpoint](../evidence/swift-candidate-native-audit-220/joern-mechanisms/audit.md)
binds candidate archive identity and the upstream tag's peeled commit
`a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc`. It retains four targeted JAR hashes,
API/bytecode inspection, nine selected upstream source files and the license.
The observed installation has 1,349 files and 1,191 JARs; a full JAR/member
manifest was **not** generated in this bounded checkpoint.

`DefaultSemantics` and `FullNameSemantics` provide method-level argument/return
transport mappings. The selected default mappings cover operators, C and
Java. Swift frontend and type-recovery mechanisms are present. No exact A38
native role binding was observed within the inspected source/API boundary.
A real `atoi` mapping and an absent near-miss name check the selected mapping
inspection; they do not qualify Swift endpoint roles.

Generic caller-supplied transport is distinct from a shipped native endpoint
catalog. The omitted runtime-native matching and broader resource review
remain visible. No supported/unsupported decision follows automatically from
these observations, and no historical reports or contracts are rewritten.
