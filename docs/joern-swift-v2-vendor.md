# Joern Swift v2 vendor bundle result

This is the bounded vendor-bundle result for A38 at base `16fd2a93`. It is
scoped to the exact Joern `v4.0.628` release asset
`querydb.zip`; it does not make a claim about another Joern release, another
installation, a generated CPG, or analyzer execution.

The loader-derived release URL was
`https://github.com/joernio/joern/releases/download/v4.0.628/querydb.zip`.
The GitHub release metadata identifies asset `565234087`, size `75,484,243`
bytes, and SHA-256
`5f8da2dab46aeed41c995241b79bbf6166605e3a332c447c5fab445e2bd99933`.
The isolated download has the same size and hash and passed `unzip -tqq`.
The downloaded bytes remain in the isolated temporary directory
`/private/tmp/dfb-joern-vendor-220.yq6t2w/querydb.zip`; the existing Joern
installation was never modified. Release metadata, response headers, both
archive hashes, and integrity checks are retained in
[`release-asset-metadata.json`](../evidence/swift-v2-vendor-result-220/joern-vendor/release-asset-metadata.json)
and [`download-integrity.txt`](../evidence/swift-v2-vendor-result-220/joern-vendor/download-integrity.txt).

The full 65-member ZIP manifest is retained in
[`archive-artifact-manifest.tsv`](../evidence/swift-v2-vendor-result-220/joern-vendor/archive-artifact-manifest.tsv),
with the extracted per-file size and SHA-256 manifest in
[`extracted-file-manifest.tsv`](../evidence/swift-v2-vendor-result-220/joern-vendor/extracted-file-manifest.tsv).
The evidence directory is bound by
[`content-manifest.json`](../evidence/swift-v2-vendor-result-220/joern-vendor/content-manifest.json)
and its SHA-256 sidecar.

## Structural catalog

The extracted vendor loader was run read-only. Its own `io.joern.dumpq.Main`
produced a complete 58-record query catalog, retained as
[`vendor-querydb.json`](../evidence/swift-v2-vendor-result-220/joern-vendor/vendor-querydb.json).
The language counts are:

| Catalog language | Queries |
| --- | ---: |
| Android | 10 |
| C | 27 |
| Ghidra | 2 |
| Java | 7 |
| Kotlin | 3 |
| PHP | 9 |

There are zero Swift query records. The nested vendor
`io.joern.querydb-4.0.628.jar` contains 87 class files. Its scanner packages
are `android`, `c`, `ghidra`, `java`, `kotlin`, and `php`, plus the loader and
query-tag classes; its complete query catalog has no Swift language entry. The complete
class/resource inventories are retained in
[`querydb-jar-members.txt`](../evidence/swift-v2-vendor-result-220/joern-vendor/querydb-jar-members.txt),
[`first-party-members.txt`](../evidence/swift-v2-vendor-result-220/joern-vendor/first-party-members.txt),
and [`service-resource-members.txt`](../evidence/swift-v2-vendor-result-220/joern-vendor/service-resource-members.txt).
The derived structural result is recorded in
[`structural-catalog.json`](../evidence/swift-v2-vendor-result-220/joern-vendor/structural-catalog.json)
and the complete query index in
[`vendor-query-catalog.tsv`](../evidence/swift-v2-vendor-result-220/joern-vendor/vendor-query-catalog.tsv).

The bundle does contain generic Swift frontend/type-recovery runtime classes,
including `SwiftSrcCpgGenerator` and `SwiftTypeRecovery`. Those classes are
frontend services inherited by the runtime. The complete vendor catalog
therefore establishes the following bounded result: this exact
`v4.0.628/querydb.zip` ships no Swift query records for A38. The result is
based on the loader’s complete catalog plus nested-JAR class/resource
inventories, rather than a name-only search. This capture does not establish
that every possible Swift model mechanism is absent.

Accordingly, the six A38 roles remain unqualified for Joern native credit:

- `ProcessInfo.environment["DFB_NATIVE_INPUT"]` to the exact `Process.run` sink;
- `String.append` propagation;
- `Int`/`String` radix sanitization;
- Foundation `Data` Base64 summary round trip;
- `CommandLine.arguments[1]` entrypoint source; and
- receiver/key-sensitive `UserDefaults` persistence.

This is a vendor-catalog absence result for the exact bundle. It does not
claim that the Swift frontend cannot produce structural identity, and it does
not replace a future vendor model, a frontend identity check, or the parent
task’s Result/CodeQL controls.

## Commands, logs, and boundaries

The complete bounded command list is in
[`capture-commands.txt`](../evidence/swift-v2-vendor-result-220/joern-vendor/capture-commands.txt),
with the boundary explanation in
[`commands-and-boundaries.md`](../evidence/swift-v2-vendor-result-220/joern-vendor/commands-and-boundaries.md).
The initial direct launcher failure is retained in
[`direct-launcher-help.stderr`](../evidence/swift-v2-vendor-result-220/joern-vendor/direct-launcher-help.stderr):
the archive launcher omitted a Scala runtime class. The isolated vendor loader
was then run with the extracted vendor JARs first and the already-pinned
Joern 4.0.628 runtime JARs as read-only classpath support; it completed and
wrote the 58-record catalog. Its stdout/stderr are retained in the
`vendor-loader*.stdout` and `vendor-loader*.stderr` files.

No Joern updater or installation command was invoked. No Swift source, CPG,
fixture, native API, shell, or `UserDefaults` operation was run. No
benchmark-authored model or semantics file was created, and no score,
unsupported partition, or analyzer qualification was assigned.
