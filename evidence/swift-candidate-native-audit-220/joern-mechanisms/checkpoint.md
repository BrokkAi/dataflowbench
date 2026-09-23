# SAME220 Joern 4.0.633 native mechanism audit checkpoint

Date: 2026-09-23
Status: bounded read-only checkpoint; mechanism observations only. Parent task retains the final qualification/partition decision.

## Exact inputs

- Candidate bundle: `/private/tmp/dfb-220-candidate-assets/joern/extracted/joern-cli`
- Candidate archive SHA-256: `e11563c7cf4797db76655524398f108c3469a518fa3ed823de0aac2a1155aec6`
- Candidate version observed from launcher: `4.0.633`
- Upstream tag object: `465e3c2b7180ab76bcf0270cde7c08d4fa627b41`
- Upstream peeled commit: `a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc` (matches retained pin metadata)
- Exact source tarball: `/private/tmp/dfb-220-joern-native-candidate/joern-a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc.tar.gz`
- Source tarball SHA-256: `55a76de3b3a7467260a7042f7872f7e68f38a71cd3b9779c2308aae100c7a1a9`

## Current observed findings

1. The shipped data-flow engine exposes `DefaultSemantics`, `Semantics`, `FullNameSemantics`, `FullNameSemanticsParser`, `FlowSemantic`, and `FlowPath`. The source and return/argument mapping APIs support caller-supplied method-level transport semantics.
2. `DefaultSemantics.scala` contains generic/operator, C, and Java mappings (for example `atoi`, `strncpy`, Java string/SQL/HTTP methods). The inspected 4.0.633 source/JAR evidence contains no A38 Swift role binding for `ProcessInfo.processInfo.environment`, exact `Process.run`, `String.append`, the requested Foundation Base64/Data/String conversions, `CommandLine.arguments[1]`, or keyed `UserDefaults` persistence.
3. The Swift frontend is shipped and separately identifiable: `io.joern.swiftsrc2cpg-4.0.633.jar`, `SwiftSrc2Cpg`, AST creation, builtin-type population, metadata, compiler AST/type-provider support, and Swift type recovery. These are frontend/type mechanisms; this audit observed no native A38 endpoint catalog or role loader in the inspected source/JAR paths.
4. The candidate installation contains 1,349 files and 1,191 JAR files. Targeted JAR hashes are retained in `targeted-jar-sha256.txt`.
5. Main-owned complementary evidence is not duplicated here: the complete 58-record published catalog, zero Swift records, sorted published JSON/bundle loader comparison, and the prior two missing-class loader failures followed by successful full matching runtime classpath are treated as parent evidence.

## Scope and omissions

- No query database acquisition, query database inspection, frontend run, native fixture, CPG query, scored analyzer run, or custom model was executed.
- No repository files, branch pins, active pins, or installed candidate files were modified.
- This checkpoint records shipped-surface observations only. It deliberately does not assign `unsupported`, `supported`, `clean`, or any other final decision to the A38 cells.
- Generic caller-supplied semantics may encode some argument/return transport; that does not by itself establish native Swift role provenance. A future native model pack or loader path would require a fresh exact audit.

## Evidence paths

- `candidate-acquisition.json` — retained candidate acquisition and publisher digest match
- `provenance.txt` — exact tag refs and source-path inventory
- `source-files/` — exact-commit source files copied for bounded inspection
- `targeted-source-excerpts.txt` — numbered source excerpts
- `targeted-role-scan.txt` — bounded keyword scan over excerpts
- `javap/` — 4.0.633 bytecode/API inspection for semantics and Swift classes
- `javap-role-keyword-hits.txt` — bounded bytecode keyword scan
- `targeted-jar-sha256.txt` — hashes for dataflow, Swift frontend, x2cpg, and semanticcpg JARs
- `install-file-count.txt`, `jar-count.txt`, `jar-paths.txt` — candidate inventory counts/paths

The retained prior 4.0.628 methodology/evidence remains at `/private/tmp/swift232-review.sM6Pj9/evidence/swift-v2-decisions-220/joern-native-mechanisms`; its decisions are not transferred to this candidate.
