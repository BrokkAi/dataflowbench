# Partial Bifrost v0.14.0 to v0.14.4 comparison

19/20 completed groups; 1046/1116 paired report rows.

Verdict transitions: `{"inconclusive->inconclusive": 339, "inconclusive->not-reached": 2, "inconclusive->reached": 4, "not-reached->not-reached": 308, "reached->reached": 308, "unsupported->unsupported": 85}`.

Incomplete groups: `[{"attempt_id": "bifrost-scala-kernel-attempt-03-series-03", "capacity_loss": null, "exit_code": 124, "expected_rows": 70, "group_id": "bifrost-scala-kernel", "state": "recorder-error", "terminal": "reports/releases/v0.9.2/attempts/bifrost-scala-kernel-attempt-03-series-03/completed.json", "terminal_sha256": "d1c090d100f5d7b9776fd2a43f62d4fa7f153e216c3bf773e60d2138ce837014", "timed_out": true}]`.

- bifrost-java-kernel / dfb-taint-java-exception-catch-negative: inconclusive -> not-reached (complete).
- bifrost-java-kernel / dfb-taint-java-exception-catch-positive: inconclusive -> reached (complete).
- bifrost-kotlin-kernel / dfb-taint-kotlin-expression-positive: inconclusive -> reached (complete).
- bifrost-kotlin-kernel / dfb-taint-kotlin-loop-carried-positive: inconclusive -> reached (complete).
- bifrost-smoke / dfb-taint-java-exception-catch-negative: inconclusive -> not-reached (complete).
- bifrost-smoke / dfb-taint-java-exception-catch-positive: inconclusive -> reached (complete).

- Scala v0.14.4 adds PR298 POM and exact local binary/source jars; retained v0.14.0 Scala predates amendment, so cannot isolate engine-only effects.
- Native versioned activation-evidence paths differ intentionally.
- Durations are retained but not a controlled before/after performance certificate.
- Only completed groups have paired normalized rows. Failed raw partial captures are not normalized or scored as completed cases.
- All incomplete groups remain in the expected 1116-row denominator; no full-target or release-readiness claim follows.
- Scala includes the PR298 dependency configuration change. Native activation evidence is versioned.
- One release-target run is not an uncontended controlled performance comparison.
- Raw state changes are distinct from case expectation correctness and engine-only causal attribution.

Full JSON SHA256: `c0dd776cd6cf0336dad769d0eb374d49d2a254b26b78b4d2c5118a959f135c7e`.
CSV SHA256: `73f8afb5e4a215ad8fe2676a2c02b603ce07155d381be1d274f6a1cb33d1dbcc`.
