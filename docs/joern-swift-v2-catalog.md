# Joern 4.0.628 Swift v2 catalog inventory

This is a bounded inventory for A38 on the pinned installation at
`/Users/dave/.cache/dataflowbench-tools/joern-v4.0.628/joern-cli`. It records
what the shipped Swift frontend, scanner, and dataflow JARs expose. It does not
run Joern against source or a CPG, execute a fixture or native API, activate a
model, assign an unsupported partition, or qualify benchmark semantics.

The captured distribution is the macOS ARM64 archive
`joern-cli-macos-arm64.zip`:

- archive SHA-256:
  `816db0240ffa2b465686a8aa71e0c645c2917b437efbeab5193ad3d9f3a4de7a`
- archive SHA-512:
  `58721b9e5a10a727263c8ab14054a02e35c3bd61ae7a66a831c2819589f1d17abc935033c7647aeb8b5664e1a22b25d20df502b79a672a08a5cfa88b5b7c3726`
- archive size: `1,782,363,862` bytes
- captured installation: `1,349` files and `2,042,712,064` bytes

The complete installation file list and per-file SHA-256 manifest are retained
in [the catalog evidence](../evidence/swift-v2-qualification-220/joern-catalog/).
The catalog content manifest excludes only the manifest and its checksum
sidecar from its own input set. Its SHA-256 is recorded in
`content-manifest.sha256` beside `content-manifest.json`.

## Shipped Swift frontend and compiler-backed route

The archive contains a dedicated Swift frontend:

```text
frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac
frontends/swiftsrc2cpg/bin/swiftsrc2cpg
frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar
frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628-launcher.jar
```

The JAR manifest identifies `io.joern.swiftsrc2cpg.Main` as its main class and
declares `Swift-AstGen-Version: 0.4.4`. The JAR SHA-256 is
`4ff227bc75781d846d1076221032df8b47c0ee7f4fa1687a161c791e59006f19`; the
SwiftAstGen executable SHA-256 is
`af6c202b40247bbd8bd50dd15d9f8c635290227af3dabff96c743ffc63c19374`.

The shipped command help exposes the following frontend controls:

```text
--swift-build
--build-log-path <value>
```

The help says that `--swift-build` builds the project to retrieve full Swift
compiler type information and requires Swift greater than 6.1; `--build-log-path`
also enables that route and requires Swift greater than 6.1. This is the
available candidate path for compiler-derived declaration and call identity.
No source was supplied to it in this inventory.

The public bytecode surface corroborates the command route:

| Shipped class | Relevant interface and role |
| --- | --- |
| `io.joern.swiftsrc2cpg.Main` | `main(String[])`, `run(X2CpgConfig)`, `frontend()`, and `cmdLineParser()` |
| `io.joern.swiftsrc2cpg.Config` | `swiftBuild()`, `buildLogPath()`, `withSwiftBuild(boolean)`, and `withBuildLogPath(Path)`; it implements `X2CpgConfig` and `TypeRecoveryParserConfig` |
| `io.joern.swiftsrc2cpg.SwiftSrc2Cpg` | `createCpg(Config)`, `createCpg(X2CpgConfig)`, `createCpgWithOverlays(X2CpgConfig)`, and `run(X2CpgConfig)` |
| `io.joern.swiftsrc2cpg.utils.AstGenRunner` | Swift AstGen execution service, including `runAstGenNative(...)` |
| `io.joern.swiftsrc2cpg.utils.SwiftTypesProvider` | compiler invocation records, JSON type information, mappings, and resolved type information |
| `io.joern.swiftsrc2cpg.utils.GsonTypeInfoReader` | reads compiler type information from a `Reader` |
| `io.joern.swiftsrc2cpg.utils.ExternalCommand` | captures external command execution and stdout matching used by the frontend service |

This is structural service evidence. It establishes that compiler-backed Swift
identity can be pursued through the shipped frontend; it does not establish
that any A38 declaration resolves in a generated CPG.

## Scanner and query catalog

The shipped scanner reports version `4.0.628`. The retained commands were:

```text
joern-scan --help
joern-scan --list-query-names
joern-scan --dump-to evidence/swift-v2-qualification-220/joern-catalog/querydb.json
```

`--list-query-names` emitted no query names. The dump exited `0`, printed that
queries were written, and retained `querydb.json` as the empty JSON array
`[]`. The installed `scripts/` tree contains generic, C, and general scripts;
the installation file manifest contains no Swift scanner query or Swift model
pack. This is an actual shipped-catalog result, supported by the scanner
output, archive member listing, and installation manifest, rather than a
name-only absence check.

The top-level plugin list contains generic layers such as `base`, `scan`,
`ossdataflow`, `controlflow`, `typerelations`, and graph dump layers. It does
not list a Swift-native model or query layer.

## Shipped dataflow/model interface

The relevant runtime JARs are present and hash-bound:

| Artifact | SHA-256 | Shipped role |
| --- | --- | --- |
| `lib/io.joern.dataflowengineoss-4.0.628.jar` | `e63635788249ef86d87bb75c9f37929ab2309fd557e7e147765b73dbd0ac077b` | generic OSS dataflow engine and semantics loader |
| `lib/io.joern.semanticcpg-4.0.628.jar` | `dafa3ed41664922943f901a86c479a954695fb8640ba36b3b486e2e886167cd4` | generic semantic CPG traversals/layers |
| `lib/io.joern.console-4.0.628.jar` | `7fcc995ff48ff84f83124e51d043841930ca3ea8f1494ceb3b4b288b559a605b8e` | console and scanner services |

The first two JARs contain class and TASTy entries plus metadata, but no
Swift-specific query/model/semantics data resource. The public dataflow
interfaces are generic:

| Interface/class | Declaration/signature and role |
| --- | --- |
| `Semantics` | `forMethod(Method): Option<FlowSemantic>`; composable semantics service |
| `FlowSemantic` | `(methodFullName: String, mappings: List<FlowPath>, regex: Boolean)`; method-level semantic mapping |
| `FlowPath.FlowMapping` | overloads mapping source/destination indexes, optionally with argument names |
| `FullNameSemantics` | builds/combines semantics by method full name; `serialize()`, `elements()`, `forMethod(Method)` |
| `FullNameSemanticsParser` | `parse(String)` and `parseFile(String)` for generic semantics text |
| `ParameterNode` | `(index: Int, name: Option<String>)`; parameter role in a mapping |
| `DefaultSemantics` | exports `cFlows()`, `javaFlows()`, `operatorFlows()`, `javaSemantics()`, and `apply()` |
| `Engine` | consumes `Semantics`; includes `semanticsForCall(Call, Semantics)` and flow expansion/query methods |

`DefaultSemantics` therefore provides generic defaults for C, Java, and
operators. It is not evidence of an Apple Foundation or Swift standard-library
model. The interface can be a future implementation substrate for exact
method-full-name mappings, but the shipped catalog contains no A38-specific
mapping declarations and no source/sink query definitions.

## A38 declaration and role inventory

The required identities below come from A38. They are the roles a future
compiler-backed qualification must resolve, not results observed by this
catalog-only task.

| A38 pair | Required declaration/signature | Required role |
| --- | --- | --- |
| source/sink | `Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] -> String?`; `Foundation.Process.run(_ url: URL, arguments: [String], terminationHandler: ((Process) -> Void)? = nil) throws -> Process` | exact environment source to exact `/bin/sh`, `-c` sink; negative retains the read but sends a clean constant |
| propagator | `Swift.String.append(_ other: String)` (`mutating`) | same initialized command and same append operation; positive appends the environment value, negative appends a clean literal |
| sanitizer | `Swift.Int.init?<S>(_ text: S, radix: Int = 10)` and `Swift.String.init<T>(_ value: T, radix: Int = 10, uppercase: Bool = false)` | parse/render is the sanitizer boundary; positive bypasses numeric parsing, negative uses radix 10 and a fixed `echo ` prefix |
| summary | `Foundation.Data(_: String.UTF8View).base64EncodedString(options:)`; `Foundation.Data.init?(base64Encoded: String, options:)`; `String(data: Data, encoding: .utf8)` | exact Base64 encode/decode round trip to the same shell sink |
| entrypoint | `Swift.CommandLine.arguments: [String]`, specifically guarded `CommandLine.arguments[1]` | process-entry source to the same shell sink |
| persistence | `Foundation.UserDefaults(suiteName: "DataFlowBench.Native.A38")`; `set(_:forKey:)`; `string(forKey:)` | same initialized receiver and key-sensitive write/read; positive reads `payload`, negative reads `other` |

A38 requires resolved module, receiver, member, labels, arity, and types. A
same-named helper, wrapper, re-export, or source-text match cannot satisfy that
requirement. It also requires exact native call anchors and no native execution.

## Result and capability conclusion

This inventory finds a compiler-backed Swift frontend and generic dataflow
semantics API. The inspected installation does not expose an active Swift-native
scan/query catalog; this observation is limited to the installed state:

1. the scanner query database is empty;
2. the Swift frontend JAR contains frontend/type-recovery services, not native
   taint model declarations; and
3. the generic semantics API has method-name and parameter/return mapping
   interfaces, with default C/Java/operator semantics only.

The unresolved qualification step is **A38 Joern native catalog activation**.
The empty installed database is not proof of missing vendor Swift support.
The shipped scanner exposes `--updatedb` and `--dbversion`; retained updater
bytecode identifies a separate vendor `querydb.zip` bundle and a version-specific
GitHub release URL. That bundle has not been installed or inspected here.
Qualification must fetch and pin the matching vendor bundle in a separate
location before deciding whether its structural catalog supplies Swift roles. No A38 pair receives Joern native credit from this evidence. In
particular, generic `DefaultSemantics`, a future benchmark-authored semantics
file, a bare-name query, or a successful compiler-backed CPG build would not by
itself prove the six required native roles, exact endpoint bindings, the
sanitizer kill, or UserDefaults receiver/key separation.

The candidate activation path is bounded and concrete: use the shipped
`swiftsrc2cpg --swift-build --build-log-path` route with a fresh non-scored
probe; retain compiler command/type JSON and exact declaration/call identities;
then independently inspect and pin the version-matched vendor query bundle.
Only shipped models can qualify A38; no benchmark-authored query or semantics
may substitute for a missing vendor source, sink, sanitizer, summary, or store
model. Exact endpoint and separating controls remain required. The
primary CodeQL catalog and version plan remain independent qualifications, as
required by A38. This report does not claim that either route has been run or
qualified.

## Evidence and integrity

All retained command lines and outputs are under
`evidence/swift-v2-qualification-220/joern-catalog/`:

- `artifact-identity.txt`, `archive-members.txt`, `installation-files.txt`,
  and `installation-file-manifest.tsv` bind the archive and installed bytes;
- `joern-help.txt`, `joern-plugins.txt`, `joern-scan-help.txt`,
  `joern-scan-query-names.txt`, `joern-scan-dump.*`, and `querydb.json` retain
  scanner/service results;
- `swiftsrc2cpg-help.txt`, `selected-artifact-manifests.txt`, JAR member lists,
  resource surfaces, `javap-catalog-interfaces.txt`, and
  `javap-entrypoints.txt` retain structural frontend/dataflow evidence;
- `catalog-surface.txt` records the derived inventory conclusion;
- `capture-commands.txt` and `commands.txt` record the bounded read-only
  commands; and
- `updater-loader-bytecode.txt`, `updater-loader-public-api.txt`, and
  `updater-loader-strings.txt` retain the separate vendor-bundle discovery; and
- `content-manifest.json` and `content-manifest.sha256` bind this catalog
  directory’s evidence files.

Only catalog/help/bytecode inspection commands ran. No analysis of source or a
CPG, source-fixture execution, native UserDefaults access, or native shell call
was performed.
