# SAME220 Joern 4.0.633 native mechanism audit

Date: 2026-09-23  
Status: complete bounded read-only sidecar. Parent task retains the final qualification and partition decision.

## Scope and denominators

- Candidate: Joern 4.0.633 macOS arm64 bundle at `/private/tmp/dfb-220-candidate-assets/joern/extracted/joern-cli`.
- Candidate archive SHA-256: `e11563c7cf4797db76655524398f108c3469a518fa3ed823de0aac2a1155aec6`.
- Upstream tag object: `465e3c2b7180ab76bcf0270cde7c08d4fa627b41`.
- Upstream peeled commit: `a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc`; this matches the retained candidate pin metadata.
- Native mechanism scope: 6 A38 role families × 2 cells each = 12 cells: source/sink, propagator, sanitizer, summary, process entrypoint, and persistence.
- Parent-owned catalog denominator: 58 published records, with 0 Swift records. Parent also owns the sorted published-JSON/bundle-loader comparison and the retained two missing-class failures followed by successful full matching runtime classpath.
- Candidate inventory denominator: 1,349 files / 1,191 JARs. This sidecar retains targeted boundary evidence rather than a full JAR listing.

## Observed mechanism findings

The 4.0.633 data-flow engine ships `DefaultSemantics`, `Semantics`, `FullNameSemantics`, `FullNameSemanticsParser`, `FlowSemantic`, and `FlowPath`. Their source and bytecode show caller-supplied method-level argument/return transport mappings, including regex/full-name matching. `DefaultSemantics` contains generic/operator, C, and Java mappings such as `atoi`, `strncpy`, Java string/SQL/HTTP methods, and no inspected A38 Swift role binding.

The bundle ships a dedicated Swift frontend (`io.joern.swiftsrc2cpg-4.0.633.jar`) and Swift type-recovery classes. The inspected Swift source/JAR boundary covers AST creation, metadata, builtin types, compiler AST/type-provider support, demangling, and type recovery. Within that boundary, no native A38 role catalog or role-specific loader was observed for these exact surfaces: `ProcessInfo.processInfo.environment`, `Process.run`, `String.append`, Foundation `Data` Base64/String conversions, `CommandLine.arguments[1]`, or keyed `UserDefaults` persistence.

These are mechanism observations. They do not classify any cell as supported, unsupported, clean, or failed, and they do not transfer the prior Joern 4.0.628 decision.

## Evidence retained

- `candidate-acquisition.json`: candidate acquisition metadata and publisher digest match.
- `provenance.txt`: exact tag refs and bounded source inventory.
- `source-files/`, `targeted-source-excerpts.txt`, `targeted-role-scan.txt`: exact-commit source and numbered role scan.
- `javap/`, `javap-role-keyword-hits.txt`: targeted 4.0.633 API/bytecode evidence.
- `targeted-jar-sha256.txt`: hashes for dataflowengineoss, Swift frontend, x2cpg, and semanticcpg JARs.
- `install-file-count.txt`, `jar-count.txt`, `jar-paths.txt`: inventory counts and paths.
- `checkpoint.md`, `current-findings.tsv`: compact checkpoint and finding ledger.
- Exact source tarball: `joern-a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc.tar.gz`, SHA-256 `55a76de3b3a7467260a7042f7872f7e68f38a71cd3b9779c2308aae100c7a1a9`.

## Omissions and ownership boundary

- No query database acquisition or inspection; no duplication of the main catalog.
- No Joern frontend run, native fixture, CPG query, scored analyzer run, custom model, or runtime native matching.
- No repository edits, pin changes, branch changes, or candidate installation changes by this sidecar.
- No full JAR/member manifest was generated; targeted JAR/API/source evidence was sufficient for this bounded checkpoint.
- Generic caller-supplied semantics remain a transport mechanism observation and are not treated as native Swift role provenance.

## Reproduction boundary

All sidecar outputs are under `/private/tmp/dfb-220-joern-native-candidate`. The prior 4.0.628 methodology/evidence at `/private/tmp/swift232-review.sM6Pj9/evidence/swift-v2-decisions-220/joern-native-mechanisms` was consulted for audit shape only; its decisions were not transferred.
