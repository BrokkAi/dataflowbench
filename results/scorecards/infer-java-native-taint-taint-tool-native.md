# Scorecard `infer-java-native-taint-taint-tool-native`

Adapter `infer-java-native`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62 — v1.3.0 shipped Pulse checker, no taint configuration`, adapter version `0.1.0`, configuration `751e6ca8c79a2cc269e26a2c302b8fe8035780127b1b5f9e9753565f51368114`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/infer-java-native.json` (`sha256:ad6461b1b1fa5573f127fa1fb169e7ded76c4a0c30cf19aafc297e269a457ce2`, normalized `sha256:ad6461b1b1fa5573f127fa1fb169e7ded76c4a0c30cf19aafc297e269a457ce2`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `298f15e4f7796d36c0fb774bad5063ef2bd2a7089237513f807922a50542107f` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `c394b817642c0360a461abab2cf8a16866cb112cedce693331f82a155a9c993d` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `0654ce5e94ef1b595e4ba8833f86352c943b3434c26081d35d861119b5b8795d` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `7b2454c5af0cbced6ea11e937b88c0a8b723350047eca72d4983241354590f2a` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `546c5312693ca6281e948586ec6f046c351f860f32e1e6cd64e25b8089016d76` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `0624b47897d0992c79c1fefa233dba692eae28e26fc191f41cc09c43bf9dfd6e` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `75c87103263c792a35fbeb4f29fc00364ad84e32eebf89276260088173545ea7` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `dcd7de13f53c7a90e31a1078c249f45153e668101ac715c1379c4f41df678f7b` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `b79cce21c8dd7cdaa186a02ddacc9ee3f2b05f154c971b11e056353af1f97562` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `958712effe59a19527a1c2ff000cfd310075cbbe7a7458166774dd26bc8ef9f0` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `0380555add6c55c3cf77debae78cf8a349c4a59da10f9a1a95dc47771006973a` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `3716de158b2a78718e73534a84cf711dab9cbaee9c07528ce6a53fd6568e77c9` |
