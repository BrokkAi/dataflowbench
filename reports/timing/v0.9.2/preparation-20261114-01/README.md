# Preparation for the 14 November timing campaign

This directory records daytime setup only. It contains no new analyzer timing
measurements. The prospective campaign is `20261114-01`, earliest dispatch
02:00 SAST on 14 November 2026, conditional on the committed plan and a quiet
host. The frozen release remains
`86092336d8f9ca32fe9e2c4042c2dced76c1feb1`.

The governing preregistration is
[`docs/latency-v092-20261114.md`](../../../../docs/latency-v092-20261114.md).
`prepare_runtime_bindings.py` derives the new bindings from retained receipts;
the new qualified controller derives the campaign plan from those bindings.
Neither preparation nor verification dispatches analyzers.

The admitted inputs are `runtime-bindings-v4.json` and
`../20261114-01/qualified-plan-02.json`. Earlier binding drafts and the first
qualified plan remain as superseded preparation records. They are not launch
inputs. `readiness-v1.json` records the final 41 Python test passes, all 17
runtime-manifest checks, 93 CLI argument-only checks, and a real fixture-mutation
regression against an isolated immutable source snapshot. No analyzer ran in
those checks. Mocked unit-test logs contain simulated dispatch messages.

The restored selection covers all eight analyzer families. The prospective
queue retains all 84 cold groups, with two Swift-specific groups blocked, plus
nine A24 overhead arms and two supported warm arms. A balanced first frontier
contains one cold group per analyzer. Case membership, final analyzer pins,
configs, known semantic limits and original cold deadlines are retained.

Active records and corrections:

- JVM runtime relocation uses `jvm-runtimes/relocated-manifests-receipt-v2.json`.
  The first relocation copies used relative roots and are historical setup
  evidence; they are not admitted by the controller. v2 uses absolute roots.
- Go and Kotlin compiler entries match the selected frozen pins. Their new
  full inventories, and the explicitly selected CLT 27.2 compiler and Rust
  1.97.1 distribution inventories, are prospective environment identities.
  There is no assertion of equality with a historical full compiler inventory
  that did not exist. The retained macOS 26.5 SDK has its full frozen inventory.
- Python recovery uses the exact retained CPython 3.15.0 executable, pinned
  package payloads, CP315 PyYAML and CP315 ruamel wheels. The earlier proposed
  ruamel source build was superseded by recovery of the byte-identical frozen
  extension from the pip wheel cache; no native compile was needed. New venv
  metadata, launchers and bytecode differences are enumerated, not hidden.
- `warm-population/derivation-v1.json` derives inputs from immutable authored
  fixtures. Semgrep has 12 cases with the same resolved rule, so its largest
  batch is 12; Joern's largest batch is 16. Both retain two complete repeats.
- `qualification/observer-preflight-01.json` records an experimental lifecycle
  observer investigation. `scope-decision-02.json` separates it from the
  existing quiet-qualification predicate. That observer is not admitted, and
  PID/start polling's unproven descendant containment remains explicit.

No earlier attempt, frozen report, release tag or raw evidence was rewritten.
Runtime files are retained under the new owned `execution-state` roots; wheel
and archive receipts identify their original retained sources. Large manifests
have compressed copies with compressed and uncompressed hashes.

Before execution, verification must pass again against actual file bytes.
Every group gets a new five-minute quiet window; later CPU activity never
interrupts an active command. Genuine command/resource failures retain evidence
and stop the queue without an automatic retry. Completed commands remain
candidate evidence until the separate acceptance and publication review.
