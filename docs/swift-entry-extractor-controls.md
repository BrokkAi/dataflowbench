# Bounded patched-extractor controls

All ten controls completed extraction, schema import and queries. Adoption is blocked by the array negative and callback positive. These are diagnostic observations only.

| Control | Native flow | Top-level blocks | Analysis seconds |
|---|---|---:|---:|
| array-element-negative | reached | 4 | 11.23 |
| array-element-positive | reached | 4 | 13.11 |
| callback-registration-negative | not-reached | 4 | 15.98 |
| callback-registration-positive | not-reached | 4 | 18.25 |
| direct-negative | not-reached | 1 | 10.64 |
| direct-positive | reached | 1 | 59.83 |
| local-overwrite-negative | not-reached | 3 | 10.66 |
| local-overwrite-positive | reached | 3 | 13.73 |
| wrapped | reached | 1 | 16.61 |
| wrapped-negative | not-reached | 1 | 9.03 |

Direct-positive time is the sum of recorded query/decode phases; its runner enforced a shared 75-second wall-clock deadline. Other times are recorded wall-clock analysis intervals. Extraction was limited to 150 seconds per control. All exact source/sink endpoints had CFG and data-flow nodes.

This is not a performance benchmark. Aggregate RSS and descendant containment remain unproven. Initial query compilation raised the requested memory from 2048 to 2638 MiB. No stock scores, fixture expectations, or full-corpus results changed.

Run `python3 scripts/check-swift-entry-evidence.py` to verify the compact archive and replay native observations. Run `python3 scripts/test-swift-entry-observation.py` for fail-closed classifier regressions. Full databases remain in the task-local experiment directory.
