# SAME220 bounded Joern native mechanism audit

Date: 2026-09-23

Status: read-only sidecar evidence; parent orchestrator retains the final admission and partition decision.

## Scope

This audit covers the exact locally pinned Joern 4.0.628 installation at
`/Users/dave/.cache/dataflowbench-tools/joern-v4.0.628/joern-cli` and the
locally retained upstream source snapshot for tag `v4.0.628` (tag object
`c2ad491932291cf67a80f64c15ec94a874d28ef9`, peeled commit
`0b81c759a38b98b3abb4c90406818a90d6b299c1`). It inspects complete file/JAR
inventories, first-party class members, non-class resources, public/private
class APIs, and targeted bytecode for the data-flow and Swift frontend
components. It complements the exact vendor querydb audit retained in
`prior-vendor-evidence/`.

The audit wrote evidence only under `/private/tmp/dfb-220-joern-native-mechanisms`;
it did not intentionally modify repository files. No Joern frontend, native
fixture, CPG query, scored run, custom model, installer, or package operation
was executed. The inspection used archive/class tooling only (`find`, `jar`,
`unzip`, `javap`, `shasum`/hashing) and did not start a heavy analyzer process.

## Pin and provenance

The audit's initial checkout snapshot reported repository commit
`8a0cb6f899b3a7e9ce5485122c69e9445298903c` on branch
`dave/swift-v2-vendor-result-220`. This identifies the input snapshot used at
audit start. The shared worktree was concurrently used and may have moved
after that snapshot; this sidecar makes no claim that it remained clean or
unchanged after inspection.

Key exact input digests are retained in
`pinned-file-inventory.json` and `jar-inventory.json`. The relevant pinned
JARs include:

| Input | SHA-256 |
| --- | --- |
| `frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar` | `4ff227bc75781d846d1076221032df8b47c0ee7f4fa1687a161c791e59006f19` |
| `frontends/swiftsrc2cpg/lib/io.joern.x2cpg-4.0.628.jar` | `5d40b6a1f045495b46337c4a05ed0cf7c6325b4e3d79350e241cf3d8f0c21654` |
| `frontends/swiftsrc2cpg/lib/io.joern.semanticcpg-4.0.628.jar` | `dafa3ed41664922943f901a86c479a954695fb8640ba36b3b486e2e886167cd4` |
| `lib/io.joern.dataflowengineoss-4.0.628.jar` | `e63635788249ef86d87bb75c9f37929ab2309fd557e7e147765b73dbd0ac077b` |
| `lib/io.joern.joern-cli-4.0.628.jar` | recorded in `pinned-file-inventory.json` |
| `frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac` | `af6c202b40247bbd8bd50dd15d9f8c635290227af3dabff96c743ffc63c19374` |

The existing vendor evidence binds `querydb.zip` to SHA-256
`5f8da2dab46aeed41c995241b79bbf6166605e3a332c447c5fab445e2bd99933`, with
the archive integrity check passed. Its structural catalog reports 58 query
records across Android, C, Ghidra, Java, Kotlin, and PHP, and zero Swift query
records. It separately records Swift frontend/type-recovery runtime members;
that distinction is preserved here.

## Shipped mechanism inventory

The full pinned installation contains 1,349 files. The first-party class
inventory and resource inventory were generated from every JAR in the
installation, with exact JAR digests retained. The targeted first-party
classes are:

- `io.joern.dataflowengineoss.DefaultSemantics` and its singleton object;
- `io.joern.dataflowengineoss.semanticsloader.Semantics`;
- `FullNameSemantics`, `FullNameSemanticsParser`, `FlowSemantic`, `FlowPath`,
  `ParameterNode`, `NilSemantics`, `NoSemantics`, and
  `NoCrossTaintSemantics`;
- data-flow query engine classes under
  `io.joern.dataflowengineoss.queryengine`;
- Swift frontend classes under `io.joern.swiftsrc2cpg` and Swift type
  recovery classes under
  `io.joern.x2cpg.frontendspecific.swiftsrc2cpg`.

The resource inventory contains the Swift frontend `application.conf`, normal
JVM/service resources, and compiler/type-recovery resources. It contains no
shipped native endpoint catalog, endpoint resource, or role-specific loader
binding for the six A38 contracts. The querydb first-party inventory is
retained separately and has the non-Swift scanner classes already reported by
the prior audit.

`DefaultSemantics` is concrete but bounded: its public construction surface
is `apply`, `operatorFlows`, `cFlows`, `javaFlows`, and `javaSemantics`. The
bytecode shows `apply()` composing operator, C, and Java flow lists into
`FullNameSemantics`. The embedded labels include generic C/Java/operator
identities such as `<operator>.addition`, `atoi`, `strncpy`, Java string and
prepared-statement methods, and Java HTTP methods. No Swift A38 identity or
Swift Foundation identity appears in those built-in lists.

The exact class/API and bytecode outputs are retained as:

- `javap-DefaultSemantics-object.txt` and
  `javap-DefaultSemantics-object-bytecode.txt`;
- `javap-Semantics.txt`, `javap-FullNameSemantics.txt`,
  `javap-FullNameSemanticsParser.txt`, `javap-FlowSemantic.txt`, and
  `javap-FlowPath.txt`;
- `javap-SwiftSrc2Cpg.txt` and `javap-SwiftSrc2Cpg-bytecode.txt`;
- `javap-SwiftTypeRecovery-correct.txt` and
  `javap-SwiftTypeRecovery-correct-bytecode.txt`.

## Mechanism interpretation

The retained upstream source gives the same implementation boundary as the
JAR inspection. `Semantics` answers `forMethod(Method)`, while
`FullNameSemantics` stores a map from method full name to `FlowSemantic` and
can initialize regex matches from CPG methods. `FlowSemantic` contains a
method full name, argument/return `FlowPath` mappings, and an optional regex
flag. `FlowPath` contains parameter mappings and a pass-through mapping. The
parser reads a caller-supplied semantics string/file.

That mechanism can express a generic method-level argument/return transfer
when a caller supplies the method identity and mapping. The audit does not use
that generic facility to claim that no caller-supplied semantics could encode
a barrier or another role. It establishes the narrower point relevant here:
the pinned distribution contains no shipped native endpoint catalog entry,
resource, or loader binding for the six required Swift A38 contracts. A
caller-supplied mapping is therefore outside this native catalog qualification.

The Swift frontend bytecode and retained source show parsing, AST creation,
metadata, built-in type population, Swift type recovery, extension handling,
Objective-C call full-name handling, closure binding, and full-name
uniqueness. They do not show a shipped native endpoint catalog or loader
binding for the six A38 contracts. `SwiftTypesProvider` obtains type
information from Swift compiler AST output; it is a type-information provider,
not endpoint-catalog provenance.

## Six A38 role decisions

The A38 contract defines these exact native families: S source/sink, P
propagator, Z sanitizer, O summary, E process entrypoint, and B persistence.
Each has one positive and one negative cell, so the proposed scope is 12
native cells.

| Role | Exact A38 surface | Shipped Joern mechanism observed | Proposed state at 4.0.628 |
| --- | --- | --- | --- |
| S | `ProcessInfo.processInfo.environment` to exact `Process.run` sink | No shipped native catalog entry, resource, or loader binding for the exact Swift source/sink endpoints | `unsupported` for both cells |
| P | `String.append` preserving taint into the exact sink | No shipped native catalog entry, resource, or loader binding for the exact Swift propagator endpoint | `unsupported` for both cells |
| Z | `Int` radix parse plus safe `String` rendering as a sanitizer | No shipped native catalog entry, resource, or loader binding for the exact Swift sanitizer contract | `unsupported` for both cells |
| O | `Data` Base64 encode/decode and `String` conversion round trip | No shipped native catalog entry, resource, or loader binding for the exact Foundation summary contract | `unsupported` for both cells |
| E | `CommandLine.arguments[1]` under the A37 guard | No shipped native catalog entry, resource, or loader binding for the exact Swift process-entry contract | `unsupported` for both cells |
| B | keyed `UserDefaults` write/read with receiver and key discrimination | No shipped native catalog entry, resource, or loader binding for the exact keyed persistence contract | `unsupported` for both cells |

This is a shipped-surface capability decision, not an execution result. It
does not use the prior Result missing-flow behavior, does not require a
positive flow before admission, and does not alter the unchanged 512 MiB / 60
second scored contracts. It also does not claim that a benchmark-authored
semantics file or a custom model could not approximate some role; those are
outside native qualification.

## Proposed parent decision

The bounded evidence supports recording Joern 4.0.628 as **scoped unsupported
for the 12 A38 native cells** because the exact pinned distribution has no
shipped native catalog entry, resource, or loader binding for the six required
Swift A38 endpoint contracts. The distribution does provide Swift
parsing/type recovery and generic data-flow semantics; those observations do
not establish a shipped native endpoint catalog for these cells. The prior
exact querydb result independently shows zero Swift query records and does not
need to carry the endpoint-catalog conclusion by itself.

The proposed decision is limited to the pinned Joern 4.0.628 distribution and
the six A38 contracts. A future Joern pin, a separately shipped Swift model
pack, or a native loader/resource discovered in a later exact audit would
require a new qualification decision. No claim is made about every possible
future mechanism.

## Evidence files and reproduction

The sidecar directory is `/private/tmp/dfb-220-joern-native-mechanisms`.
Important files are:

- `audit.py`: the bounded inventory and class/archive inspection script;
- `pinned-file-inventory.json` / `.tsv`: all 1,349 pinned installation files,
  sizes, and SHA-256 digests;
- `jar-inventory.json`: every pinned JAR, member counts, relevant-member
  counts, and SHA-256 digests;
- `first-party-class-inventory.json`, `resource-inventory.json`, and
  `keyword-member-inventory.json`: structural class/resource evidence;
- `command-01.txt` through `command-07.txt`: raw archive inventory outputs;
- `repro-commands.txt`: exact bounded reproduction and final verification commands;
- `evidence-manifest.json`: final all-file manifest with byte sizes and SHA-256 digests; the manifest excludes itself.
- `javap-*.txt`: raw public/private API and bytecode observations;
- `upstream-source/` and `upstream-source-manifest.json`: exact locally
  retained upstream source files and digests;
- `prior-vendor-evidence/` and `prior-vendor-evidence-manifest.json`: copied
  querydb/catalog evidence from the repository with source paths and digests.

The script invocation was:

```text
python3 /private/tmp/dfb-220-joern-native-mechanisms/audit.py
```

The raw outputs and inventories were generated without intentionally changing
the repository or the pinned Joern installation. The final manifest and command
record were then written in the sidecar directory.
