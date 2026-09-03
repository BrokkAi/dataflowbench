# DataFlowBench frozen results

Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`), benchmark release `v0.6.1` at revision `a8cde574287c93e802d9a9253875db141d8b87be`, fixture revision `sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151`.

Claim scope `release`. Every number on these pages is derived from the immutable freeze evidence above; none are maintained by hand. Tracks, score dimensions, score tiers, and model profiles are separate result populations and are never combined into one leaderboard.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator on these pages, so rate columns cover only each population's conclusive subset. In this freeze every `inconclusive` outcome is produced by: `bifrost-c-kernel` (9), `bifrost-cpp-kernel` (26), `bifrost-csharp-kernel` (24), `bifrost-go-kernel` (24), `bifrost-java-kernel` (18), `bifrost-javascript-kernel` (20), `bifrost-javascript-modeling` (3), `bifrost-kotlin-kernel` (30), `bifrost-php-kernel` (26), `bifrost-python-kernel` (22), `bifrost-ruby-kernel` (36), `bifrost-rust-kernel` (18), `bifrost-scala-kernel` (20), `bifrost-typescript-kernel` (22). Compare rate columns across adapters with that exclusion in mind.

Caveat: the following result populations were frozen under an adapter configuration that has since changed in this repository: `codeql-c-kernel-taint-taint-benchmark-controlled`, `codeql-cpp-kernel-taint-taint-benchmark-controlled`, `codeql-csharp-kernel-taint-taint-benchmark-controlled`, `codeql-go-kernel-taint-taint-benchmark-controlled`, `codeql-java-kernel-taint-taint-benchmark-controlled`, `codeql-javascript-kernel-taint-taint-benchmark-controlled`, `codeql-kotlin-kernel-taint-taint-benchmark-controlled`, `codeql-python-kernel-taint-taint-benchmark-controlled`, `codeql-ruby-kernel-taint-taint-benchmark-controlled`, `codeql-rust-kernel-taint-taint-benchmark-controlled`, `codeql-typescript-kernel-taint-taint-benchmark-controlled`. Their outcomes predate the current adapter configuration; they stand as frozen evidence for the configuration they were measured under until each population is re-run.

- Tracks: `taint`
- Score dimensions: `taint`
- Score tiers: `calibration`, `core`, `language-extension`, `modeling`
- Model profiles: `benchmark-controlled`, `tool-native`

## Exclusions

None.

## Scorecards

- [`bifrost-c-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-c-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-cpp-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-cpp-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-csharp-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-csharp-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-go-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-go-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-java-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-java-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-java-modeling-taint-taint-benchmark-controlled`](scorecards/bifrost-java-modeling-taint-taint-benchmark-controlled.md)
- [`bifrost-java-native-taint-taint-tool-native`](scorecards/bifrost-java-native-taint-taint-tool-native.md)
- [`bifrost-javascript-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-javascript-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-javascript-modeling-taint-taint-benchmark-controlled`](scorecards/bifrost-javascript-modeling-taint-taint-benchmark-controlled.md)
- [`bifrost-javascript-native-taint-taint-tool-native`](scorecards/bifrost-javascript-native-taint-taint-tool-native.md)
- [`bifrost-kotlin-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-kotlin-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-php-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-php-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-python-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-python-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-python-modeling-taint-taint-benchmark-controlled`](scorecards/bifrost-python-modeling-taint-taint-benchmark-controlled.md)
- [`bifrost-python-native-taint-taint-tool-native`](scorecards/bifrost-python-native-taint-taint-tool-native.md)
- [`bifrost-ruby-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-ruby-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-rust-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-rust-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-scala-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-scala-kernel-taint-taint-benchmark-controlled.md)
- [`bifrost-smoke-taint-taint-benchmark-controlled`](scorecards/bifrost-smoke-taint-taint-benchmark-controlled.md)
- [`bifrost-typescript-kernel-taint-taint-benchmark-controlled`](scorecards/bifrost-typescript-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-c-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-c-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-cpp-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-cpp-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-csharp-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-csharp-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-go-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-go-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-java-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-java-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-java-modeling-taint-taint-benchmark-controlled`](scorecards/codeql-java-modeling-taint-taint-benchmark-controlled.md)
- [`codeql-java-native-taint-taint-tool-native`](scorecards/codeql-java-native-taint-taint-tool-native.md)
- [`codeql-javascript-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-javascript-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-javascript-modeling-taint-taint-benchmark-controlled`](scorecards/codeql-javascript-modeling-taint-taint-benchmark-controlled.md)
- [`codeql-javascript-native-taint-taint-tool-native`](scorecards/codeql-javascript-native-taint-taint-tool-native.md)
- [`codeql-kotlin-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-kotlin-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-python-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-python-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-python-modeling-taint-taint-benchmark-controlled`](scorecards/codeql-python-modeling-taint-taint-benchmark-controlled.md)
- [`codeql-python-native-taint-taint-tool-native`](scorecards/codeql-python-native-taint-taint-tool-native.md)
- [`codeql-ruby-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-ruby-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-rust-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-rust-kernel-taint-taint-benchmark-controlled.md)
- [`codeql-typescript-kernel-taint-taint-benchmark-controlled`](scorecards/codeql-typescript-kernel-taint-taint-benchmark-controlled.md)
- [`flowdroid-java-kernel-taint-taint-benchmark-controlled`](scorecards/flowdroid-java-kernel-taint-taint-benchmark-controlled.md)
- [`flowdroid-java-modeling-taint-taint-benchmark-controlled`](scorecards/flowdroid-java-modeling-taint-taint-benchmark-controlled.md)
- [`flowdroid-java-native-taint-taint-tool-native`](scorecards/flowdroid-java-native-taint-taint-tool-native.md)
- [`flowdroid-kotlin-kernel-taint-taint-benchmark-controlled`](scorecards/flowdroid-kotlin-kernel-taint-taint-benchmark-controlled.md)
- [`infer-c-kernel-taint-taint-benchmark-controlled`](scorecards/infer-c-kernel-taint-taint-benchmark-controlled.md)
- [`infer-cpp-kernel-taint-taint-benchmark-controlled`](scorecards/infer-cpp-kernel-taint-taint-benchmark-controlled.md)
- [`infer-java-kernel-taint-taint-benchmark-controlled`](scorecards/infer-java-kernel-taint-taint-benchmark-controlled.md)
- [`infer-java-modeling-taint-taint-benchmark-controlled`](scorecards/infer-java-modeling-taint-taint-benchmark-controlled.md)
- [`infer-java-native-taint-taint-tool-native`](scorecards/infer-java-native-taint-taint-tool-native.md)
- [`joern-java-kernel-taint-taint-benchmark-controlled`](scorecards/joern-java-kernel-taint-taint-benchmark-controlled.md)
- [`joern-java-modeling-taint-taint-benchmark-controlled`](scorecards/joern-java-modeling-taint-taint-benchmark-controlled.md)
- [`joern-java-native-taint-taint-tool-native`](scorecards/joern-java-native-taint-taint-tool-native.md)
- [`joern-javascript-kernel-taint-taint-benchmark-controlled`](scorecards/joern-javascript-kernel-taint-taint-benchmark-controlled.md)
- [`joern-javascript-modeling-taint-taint-benchmark-controlled`](scorecards/joern-javascript-modeling-taint-taint-benchmark-controlled.md)
- [`joern-javascript-native-taint-taint-tool-native`](scorecards/joern-javascript-native-taint-taint-tool-native.md)
- [`joern-php-kernel-taint-taint-benchmark-controlled`](scorecards/joern-php-kernel-taint-taint-benchmark-controlled.md)
- [`joern-python-kernel-taint-taint-benchmark-controlled`](scorecards/joern-python-kernel-taint-taint-benchmark-controlled.md)
- [`joern-python-modeling-taint-taint-benchmark-controlled`](scorecards/joern-python-modeling-taint-taint-benchmark-controlled.md)
- [`joern-python-native-taint-taint-tool-native`](scorecards/joern-python-native-taint-taint-tool-native.md)
- [`joern-ruby-kernel-taint-taint-benchmark-controlled`](scorecards/joern-ruby-kernel-taint-taint-benchmark-controlled.md)
- [`joern-rust-kernel-taint-taint-benchmark-controlled`](scorecards/joern-rust-kernel-taint-taint-benchmark-controlled.md)
- [`opentaint-java-kernel-taint-taint-benchmark-controlled`](scorecards/opentaint-java-kernel-taint-taint-benchmark-controlled.md)
- [`opentaint-java-modeling-taint-taint-benchmark-controlled`](scorecards/opentaint-java-modeling-taint-taint-benchmark-controlled.md)
- [`opentaint-java-native-taint-taint-tool-native`](scorecards/opentaint-java-native-taint-taint-tool-native.md)
- [`opentaint-kotlin-kernel-taint-taint-benchmark-controlled`](scorecards/opentaint-kotlin-kernel-taint-taint-benchmark-controlled.md)
- [`pysa-python-kernel-taint-taint-benchmark-controlled`](scorecards/pysa-python-kernel-taint-taint-benchmark-controlled.md)
- [`pysa-python-modeling-taint-taint-benchmark-controlled`](scorecards/pysa-python-modeling-taint-taint-benchmark-controlled.md)
- [`pysa-python-native-taint-taint-tool-native`](scorecards/pysa-python-native-taint-taint-tool-native.md)
- [`semgrep-c-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-c-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-cpp-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-cpp-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-go-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-go-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-java-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-java-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-java-modeling-taint-taint-benchmark-controlled`](scorecards/semgrep-java-modeling-taint-taint-benchmark-controlled.md)
- [`semgrep-java-native-taint-taint-tool-native`](scorecards/semgrep-java-native-taint-taint-tool-native.md)
- [`semgrep-javascript-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-javascript-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-javascript-modeling-taint-taint-benchmark-controlled`](scorecards/semgrep-javascript-modeling-taint-taint-benchmark-controlled.md)
- [`semgrep-javascript-native-taint-taint-tool-native`](scorecards/semgrep-javascript-native-taint-taint-tool-native.md)
- [`semgrep-kotlin-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-kotlin-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-php-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-php-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-python-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-python-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-python-modeling-taint-taint-benchmark-controlled`](scorecards/semgrep-python-modeling-taint-taint-benchmark-controlled.md)
- [`semgrep-python-native-taint-taint-tool-native`](scorecards/semgrep-python-native-taint-taint-tool-native.md)
- [`semgrep-ruby-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-ruby-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-rust-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-rust-kernel-taint-taint-benchmark-controlled.md)
- [`semgrep-typescript-kernel-taint-taint-benchmark-controlled`](scorecards/semgrep-typescript-kernel-taint-taint-benchmark-controlled.md)
