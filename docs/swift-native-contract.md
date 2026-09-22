# A38 — 2026-09-22: prospective Swift native API contracts

This is the design contract for the six Swift `tool-native` templates from
[`native-profile.md`](native-profile.md), incorporating the process-entry
correction in [A37](swift-kernel.md#a37--2026-09-22-preserve-the-native-process-entry-contract-for-swift).
It is prospective: no fixture, native denominator, analyzer activation,
unsupported decision, result, or completed Swift scope is claimed here. It
does not amend a historical freeze.

## Contract rules

All identities below are real Apple platform or Swift standard-library
identities. A fixture must resolve the module, receiver, member, labels, arity,
and types; a same-named helper, wrapper, re-export, or source-text match is not
evidence. The future pair is one positive and one minimally different negative
with the same sink call shape. `score_tier` is `modeling` and `model_profile`
is `tool-native`; the six pairs are never pooled with controlled modeling.

The future fixture uses Foundation where stated and has no package dependency.
It must define the shell call but never invoke it during validation. No native
execution, `/bin/sh` call, UserDefaults mutation, or runtime round-trip is part
of this contract. Safe validation is compile-only/typecheck plus static analyzer
extraction and non-scored identity/model probes.

## Six exact contracts

### 1. `dfb-template-native-source-sink` — S

- **Source:** `Foundation.ProcessInfo.processInfo.environment`, specifically
  the `["DFB_NATIVE_INPUT"]` dictionary read and its `String?` result.
- **Sink:** `Foundation.Process.run(_ url: URL, arguments: [String],
  terminationHandler: ((Process) -> Void)? = nil) throws -> Process`, called
  with `URL(fileURLWithPath: "/bin/sh")` and `arguments: ["-c", command]`.
- **Positive:** the environment value reaches `command` and then that exact
  `Process.run` call.
- **Negative:** the same sink call receives a clean constant command;
  `negative_mechanism: unrelated-value`.
- **Capability:** `native-source-sink-coverage`.

### 2. `dfb-template-native-propagator` — P

- **Propagator:** `Swift.String.append(_ other: String)` (`mutating`), with a
  `String` command initialized to `"echo "` before the sink.
- **Positive:** the environment value is appended to the command that reaches
  the exact `/bin/sh`, `-c` `Process.run` sink.
- **Negative:** the same environment value is appended with the same
  `String.append` operation to a dead local; a clean command reaches the same
  sink; `negative_mechanism: unrelated-value`.
- **Capability:** `native-propagator-coverage`.

### 3. `dfb-template-native-sanitizer` — Z

- **Sanitizer:** `Swift.Int.init?<S>(_ text: S, radix: Int = 10)` followed by
  `Swift.String.init<T>(_ value: T, radix: Int = 10, uppercase: Bool = false)`;
  the rendered decimal is embedded after a fixed `echo ` prefix in the shell command; optional parse failure returns without launching. The source is never used in command structure elsewhere.
- **Positive:** the environment string reaches the exact shell sink without
  numeric parsing.
- **Negative:** the same read passes through `Int(raw, radix: 10)` and a safe
  `String(parsed, radix: 10)` rendering before the identical sink;
  `negative_mechanism: sanitizer`.
- **Capability:** `native-sanitizer-credit`.

### 4. `dfb-template-native-summary` — O

- **Round trip:** `Foundation.Data(_: String.UTF8View).base64EncodedString(
  options:)`, then `Foundation.Data.init?(base64Encoded: String,
  options:)`, then `String(data: decoded, encoding: .utf8)`.
- **Positive:** the environment value survives encode/decode and reaches the
  exact shell sink.
- **Negative:** a clean constant makes the identical Base64 round trip into the
  same sink; `negative_mechanism: unrelated-value`.
- **Capability:** `native-summary-coverage`.

### 5. `dfb-template-native-entrypoint` — E

- **Entry identity:** `Swift.CommandLine.arguments: [String]`; the selected
  argument is exactly `CommandLine.arguments[1]` behind a `count > 1` guard.
- **Positive:** that argument reaches the exact shell sink.
- **Negative:** it reads the same `CommandLine.arguments[1]` behind the same
  guard but passes an unrelated clean local to the identical sink;
  `negative_mechanism: unrelated-value`. This is A37's process-entry contract,
  not a callback, lifecycle method, framework registration, or sibling handler.
- **Capability:** `native-entrypoint-convention`.

### 6. `dfb-template-native-persistence` — B

- **Store:** `Foundation.UserDefaults(suiteName: "DataFlowBench.Native.A38")`,
  with `set(_:forKey:)` and `string(forKey:)`. Both pairs first set `"payload"` and `"other"` to fixed clean values so historical store contents cannot determine the negative. The same initialized receiver is retained; the literal key is part of identity.
- **Positive:** write the environment value under `"payload"`, read
  `"payload"` from the same suite, and pass the result to the exact shell sink.
- **Negative:** write under `"payload"`, read `"other"` from the same receiver,
  and pass a clean fallback to the same sink;
  `negative_mechanism: field-separation`.
- **Capability:** `native-persistence-link` with receiver and key
  discrimination. A getter-as-source finding on both cells is a measured
  false-positive behavior, not persistence credit.

## Qualification and boundaries

Before any fixture or scored run, record compiler/SDK witnesses and exact
resolved API nodes. CodeQL must independently inventory the shipped Swift
native query/model surface and its activation, using the pinned CLI **2.27.0**
and extractor pack `codeql/swift-all@6.8.3` only as the existing pinned
qualification context. The checked-in controlled CodeQL queries and models are
benchmark-authored and cannot satisfy a tool-native model requirement. A
separate native query-pack/model pin and content manifest is required.

Joern must independently inventory the shipped native scan/model surface using
Joern **4.0.628**, SwiftAstGen **0.4.4**, `SWIFTSRC`, and the compiler-backed
identity route. `DefaultSemantics`, benchmark semantics, or a listing of names
does not prove a shipped native model. Both tools require, per template, a
positive, a separating negative, wrong-signature/same-name decoys, exact
endpoint resolution, model/catalog evidence, completion evidence, and retained
argv, diagnostics, hashes, and raw graph/query output. Absence remains pending
until that evidence proves the exact declaration surface is absent; names alone
cannot commit `unsupported`.

The retained non-scored reflection controls do not qualify the deferred opacity
contracts: Joern returned `reached` with model-off for the optimistic carry
control, and the positional negative also returned `reached` with model-off.
This is evidence of default propagation/model-control failure, not a native
model activation or an opacity proof. The already committed A39Result work is
separate; A38 adds no reflection fixture, result, or denominator.

Use the unchanged analysis budgets: **60 seconds and 512 MiB**.
Timeout, memory uncertainty, incomplete extraction, or missing exact identity is
not a clean negative or a completed scope claim. Historical fixtures, reports,
freezes, and all existing Swift deferrals remain unchanged.

## Primary API references

[ProcessInfo.environment](https://developer.apple.com/documentation/foundation/processinfo/environment),
[Process.run](https://developer.apple.com/documentation/foundation/process/run%28_%3Aarguments%3Aterminationhandler%3A%29),
[String.append](https://developer.apple.com/documentation/swift/string),
[Int radix parsing](https://developer.apple.com/documentation/swift/int/init%28_%3Aradix%3A%29),
[Data Base64 decoding](https://developer.apple.com/documentation/foundation/data/init(base64encoded:options:)),
[CommandLine.arguments](https://developer.apple.com/documentation/swift/commandline/arguments), and
[UserDefaults.init(suiteName:)](https://developer.apple.com/documentation/foundation/userdefaults/init%28suitename%3A%29)
were checked against Apple documentation and the local pinned SDK where the
Swift interface exposes the declaration. This document adds no fixture,
runtime evidence, model activation, or release/publication claim.
