# Swift v2 qualification sequence

This plan follows merged A38/A39 and the immutable 104-input population from
#227. It introduces no scored decision or analyzer result.

1. Inventory each pinned tool's actual shipped Swift query/model catalog,
   preserving the full artifact identities and catalog discovery commands.
   CodeQL uses CLI 2.27.0 and the `c6baf479093fafc81d4655dc2014dc583360308e`
   source build: `codeql/swift-all@6.8.3` and the corresponding shipped
   `codeql/swift-queries@1.3.10`. Joern uses 4.0.628 and SwiftAstGen 0.4.4.
   Joern's benchmark query and `DefaultSemantics` cannot stand in for a
   shipped Swift native vulnerability query or model catalog.
2. Record compiler-resolved declarations and analyzer-resolved endpoints for
   every A38 native API and A39 Result path. Retain positive, separating
   negative, and wrong-signature/same-name controls. Compiler declarations
   alone do not prove analyzer endpoint resolution, and catalog entries alone
   do not prove a complete positive/negative analysis.
3. Introduce new versioned adapter configuration and activation identities,
   with explicit v2 selection. Preserve all v1 adapter/configuration/certificate
   bytes. Historical v1 snapshot replays verify only prior certificates; they
   do not activate the current runtime or v2.
4. After independent controls, commit the prospective native and Result
   partitions before any scored execution. Native execution loads only shipped
   models. An unsupported decision requires structural catalog/declaration
   evidence for the exact missing surface. A timeout, extraction failure, or
   unknown declaration is not an unsupported decision or a clean negative.
5. Run only the reviewed v2 partitions to new report and raw-evidence paths,
   binding the full v2 population identity. Keep language-extension results
   separate from core and from both modeling profiles. Retain every attempt.

All bounded analyzer probes and executions preserve the 512 MiB / 60 second
budget. Any resource/completeness uncertainty stays explicit and cannot qualify
correctness. Native fixture binaries are never executed: neither `/bin/sh` nor
UserDefaults mutation is permitted. Compiler/extractor commands only compile
or inspect source. Qualification evidence is non-scored and cannot enter a
freeze denominator by itself.

Two opaque modeling identities remain unresolved. No whole-corpus release run,
new freeze, tag, or publication is authorized by this plan. Final publication
still requires a complete selected population, dated all-adapter pin review,
reviewed versioned execution plan, common fixture revision, and separate freeze
from merged main.
