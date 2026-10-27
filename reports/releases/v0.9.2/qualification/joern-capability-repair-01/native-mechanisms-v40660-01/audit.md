# Joern 4.0.660 static shipped-runtime audit

Status: static capture complete; six native role classifications remain unresolved.

The exact installed runtime contains 1,201 regular files, all matching the sealed runtime manifest without added, missing or changed files. The capture enumerated 1,044 JAR paths (210 distinct hashes), their complete central directories and manifests, 25,369 non-class/non-TASTy resources, and 41,627 first-party class entries. These counts include duplicate libraries shipped with different frontends. No runtime files were changed.

The root launcher classpath has 94 JARs. The Swift launcher manifest resolves 62 dependency entries, all present and hashed. Successfully disassembled classes have consistent provider bytes across the inspected root and Swift libraries. No nested archive resources were found in those two classpath scopes. Nested archives in unrelated frontend distributions are recorded but not recursively inspected.

Static `javap -p -c` inspections captured default semantics, semantic parser/model APIs, Swift frontend/type provider/type recovery, console bridges, query database and scan machinery. No Joern/frontend/CPG/query/fixture/benchmark was invoked. Two initial class-name guesses failed and are preserved; the correct names were discovered from member inventories and captured successfully.

`DefaultSemantics.apply` concretely composes operator, C and Java flow lists. `FullNameSemanticsParser.parseFile` reads a caller-supplied file. `QueryDatabase` defaults to `io.joern.scanners` and reflects `QueryBundle` subtypes through context/static classloaders; no class in the scanner namespaces exists in the installed top-level JAR inventory. `BridgeBase.buildRunBeforeCode` incorporates caller startup code. Launchers admit JVM/config/agent options. These are concrete mechanisms, not mere textual search results.

The capture does not establish complete semantic closure of every Swift generated helper/pass or every possible externally loaded bundle/startup state. Generic caller-supplied transfer semantics are not shipped native endpoint provenance. Complete file enumeration does not itself prove absence of a native role. Therefore all six role conclusions remain unresolved in `six-role-conclusions.json`; no Unsupported decision is issued, and no old 4.0.628 identity is relabelled.

The exact six contracts are source/sink (`ProcessInfo.environment` to `Process.run`), propagator (`String.append`), sanitizer (radix `Int` parse plus `String` rendering), summary (Data Base64/String round trip), entrypoint (`CommandLine.arguments[1]` with guard), and persistence (receiver/key-discriminating `UserDefaults` round trip). The machine-readable conclusions preserve separate role cells and evidence limitations.

Independent review should decide whether the intended shipped-only boundary excludes arbitrary external additions and whether the actual loader/default/Swift call closure suffices, or identify the next concrete static targets. Until then, this audit supplies reproducible current-version inventory and bytecode observations, not twelve current-version capability decisions.

Reproduction scripts are `capture.py`, `follow-loaders.py`, and `resolve-static-classpaths.py`. Each writes only fresh outputs and refuses existing capture files. Their literal invocation records and the hashing manifest bind this capture. No network, source plan changes, cleanup or production admission occurred.
