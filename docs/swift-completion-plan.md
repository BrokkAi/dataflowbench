# Swift unresolved-family completion plan

This is the bounded follow-up plan for #220/#215 after the #217 fixtures and
independent #218 CodeQL and #219 Joern execution work. The nine unresolved families are completion work, not
accepted deferrals:

| Group | Template IDs | Required resolution |
| --- | --- | --- |
| Opaque modeled propagators | `dfb-template-model-opaque-propagator`, `dfb-template-model-propagator-position` | A reviewed Swift body/opacity contract, then fixtures and load-bearing model controls. |
| Tool-native model profile | `dfb-template-native-source-sink`, `dfb-template-native-propagator`, `dfb-template-native-sanitizer`, `dfb-template-native-summary`, `dfb-template-native-entrypoint`, `dfb-template-native-persistence` | Exact API identities, positive/near-miss pairs, and independently witnessed shipped-model partitions for CodeQL and Joern. |
| Swift extension | `dfb-template-result-error-propagation` | A separate Swift `Result` pair contract and extension amendment; it is not the exception-catch row. |

The plan does not change fixtures, populations, adapter scope, or Bifrost
support. No proposal below is evidence of completion.

## Current evidence boundary

The CodeQL reference is fixed to
`/private/tmp/dfb-codeql-swift-218-packs/packages/codeql/swift-all/6.8.3`.
Its witnessed identity is `codeql/swift-all@6.8.3`, pack build SHA
`c6baf479093fafc81d4655dc2014dc583360308e`, and CLI version `2.27.0`. The
repository witness is
`evidence/codeql-swift/activation-218/pack-tree-identities.json` (file SHA-256
`f82fc814996d4187a0ef9b96fe9a14d4da46c00f604520562cb8f108b9d46748`; the
`swift-all@6.8.3` record has 1,493 files and tree digest
`ee11a7254f8220b5805309c8f776963ab1e598b0b6f9c1427dcd81912a4cd0f5`). The
pack lock used by the adapter is
`adapters/codeql/swift/codeql-pack.lock.yml` (SHA-256
`89a6944d734312944b9f30db9c051ce0ac784def357d4a567a29536e9b5bf0f5`).

Relevant pack references audited at that pin are recorded here with their
exact source path and digest:

| Pack reference | What it establishes or leaves open | SHA-256 |
| --- | --- | --- |
| `codeql/swift/dataflow/ExternalFlow.qll` | Exact model-as-data roles and zero-based argument/receiver conventions. | `bae2a16ba1a4176d48f8a83d373d3f1dc869b5df8512022424502a053475ca35` |
| `codeql/swift/dataflow/FlowSources.qll` | Shipped external sources enter through `FlowSource`; defines the source base classes; argv activation is not established by this file alone. | `9ba3b22304b6fdf43925cd97a110a2ee7f4133bc9eb3fb16e9534ec7778e1035` |
| `codeql/swift/security/CommandInjectionExtensions.qll` | `Process.run`/`launchedProcess` command sinks and a command-injection numeric barrier are shipped. | `5985ca26f6b0a38c74951779f9a59f705c55a5add1415fc175be5f6fec4418a4` |
| `codeql/swift/security/CommandInjectionQuery.qll` | The command query consumes shipped `FlowSource`, sink, and barrier roles. | `676a1885527c7be31eebe6dc1f1e329dc0991da5ca81a1f2069dd97281f83164` |
| `codeql/swift/frameworks/StandardLibrary/String.qll` | String append, string/data conversion, and related summaries are present; exact native pair binding still requires a control. | `66932f8c2147d709c531c73db49e9b3cf09e18a6ae0b5342c38878e1ac858168` |
| `codeql/swift/frameworks/StandardLibrary/Data.qll` | Data construction and Base64 encode/decode summaries are present; this is not by itself a complete native summary result. | `9294c0359ce0bb6b521eff6189afb110992d3671461bdf0bd5f84b28bab17c9d` |
| `codeql/swift/frameworks/StandardLibrary/Numeric.qll` | Numeric conversions, including exact/radix forms, are modeled as flow/value steps. | `5589c0c68e8fda7ed9e75c81155d6c1f85db314d6f70cbbf6547d1b870633d1f` |
| `codeql/swift/security/CleartextStoragePreferencesExtensions.qll` | `UserDefaults.set(_:forKey:)` is a preferences-store sink; a keyed write/read propagation link is not established by this observation. | `a4ef5265255bd5952db23478a7d77b5a18c1e6afc354be7efda34fadbbe19636` |

The existing activation records remain non-scored. They establish neither the
native profile nor the two opaque model rows or the `Result` extension. A name
match in a pack is never treated as absent-model or complete-model evidence;
the next audit must inspect resolved declarations, role, signature, argument
position, barrier/summary behavior, and complete positive/negative results.

## Ordered completion work

1. **Resolve semantic contracts before population.**

   - For the two opaque propagators, amend the modeling contract before writing
     fixtures. No faithful standard-library Swift implementation of the required
     reflective self-dispatch body has yet been demonstrated. A visible forwarding helper or a
     dictionary dispatch table cannot be relabeled opaque. The amendment must
     choose a genuinely in-scope Swift construction that preserves the stated
     opacity and position semantics, or explicitly revise the semantic
     contract with its rationale and affected template IDs. This is a true
     contract decision, not an implementation omission or an analyzer gap.
   - For `dfb-template-result-error-propagation`, retain a separate Swift
     extension. The canonical proposed shape is a `Result` failure payload
     preserved through an explicit `switch` and consumed at the outer sink.
     Swift `switch` preservation is not Rust `?` propagation and must not be
     presented as equivalent until the extension amendment defines that
     relationship. The amendment fixes the positive, failure-preserving
     near-miss, payload witness, and whether the row is comparable only as a
     language extension. This needs a dated adaptation contract preserving failure-payload propagation; it is implementable without adding exception semantics.
   - Treat A37, “preserve the native process-entry contract for Swift”, as the
     current normative correction and a prerequisite to native population. The
     native E row is the canonical process-argv construction: read a fixed
     non-program-name element from `CommandLine.arguments` in both polarities;
     the positive passes it to the same platform sink and the negative passes a
     clean local to that identical sink. The former callback/undeclared-sibling
     interpretation conflicts with `docs/native-profile.md` category E and
     must not be implemented. A37 remains a separate contract commit; this
     plan does not amend it.

2. **Implement the ordinary bounded work after the contracts are fixed.**

   - Add only the missing fixture pairs with stable IDs, schema-v2 metadata,
     exact anchors, witnesses/kills, balanced polarity, and independent
     compilation. Keep opaque and `Result` fixtures out until their amendments
     are landed. The native pairs must use real APIs, never local wrappers or
     `dfb_source`/`dfb_sink` stand-ins for platform identities.
   - Register implemented IDs in a new Swift population identity, preserving
     `swift-synthetic-v1` bytes and all historical populations. Keep genuinely
     unresolved IDs visible outside executable denominators. Add the expected-set,
     profile-disjointness, pair-balance, and omitted-coverage checks before any
     result population is created.
   - Use `score_tier: modeling` with `model_profile: tool-native` for all six
     native rows. Keep them disjoint from benchmark-controlled modeling and
     never pool either profile with core results.

3. **Populate the native API contract and audit the exact candidates.**

   The following are bounded candidates to resolve into exact fully qualified
   identities and safe near misses; they are not yet accepted API contracts:

   | Native row | Candidate construction | Audit question at the pinned tools |
   | --- | --- | --- |
   | S | `Foundation.ProcessInfo.environment` to `Foundation.Process`, executing `/bin/sh -c` with the tainted command argument. | Does the shipped source bind `ProcessInfo.environment`, and does the shipped command sink bind the exact `Process` overload/argument? The reviewed files establish Process sinks; environment-source activation remains unproved. |
   | P | A real `String` transform such as the exact `StringProtocol.appending(_:)` overload between source and sink. | Does the shipped summary bind the resolved receiver/member and preserve the intended operand, with the clean-input near miss separating it? `String.qll` has append summaries, but activation still needs proof. |
   | Z | An `Int` numeric sanitizer, with the exact parse/conversion and safe rendering fixed by contract. | Is the command-query numeric barrier load-bearing for this resolved expression, and does the positive remain unsanitized while the negative is the same sink through the sanitizer? Numeric flow rows alone are not sanitizer credit. |
   | O | `Data` Base64 round trip using exact `Data`/`String` conversion overloads. | Are both encode and decode summaries composed, with a clean-input identical round trip as the near miss? `Data.qll` contains Base64 summaries; this does not establish end-to-end native coverage. |
   | E | A37 canonical `CommandLine.arguments` process-argv read. | Does each tool ship and activate an argv source for this exact element? No argv activation is established yet; inspect all concrete `FlowSource` subclasses, external model rows and threat-model gates before deciding unsupported. |
   | B | `UserDefaults.standard.set(_:forKey:)` and a matching keyed read such as `string(forKey:)`, with a distinct-key negative. | Does the tool link the exact write/read and discriminate keys? The pinned CodeQL pack shows a `UserDefaults` set sink for cleartext preferences, not proof of persistence propagation. |

   For each candidate, record the resolved module/type/member/signature,
   receiver and argument positions, source/sink/barrier/summary role, model
   provenance, and a positive plus minimally changed negative. If the exact
   shipped surface is absent, record `unsupported` with that declaration-surface
   reason. Do not turn an absent model into an analyzer result and do not
   replace an API with a same-named wrapper.

4. **Amend, then partition, then run independent controls.**

   The order is mandatory for each adapter and profile:

   1. land the semantic/API amendment, including A37 as the E prerequisite;
   2. populate fixtures and registry/manifest expectations;
   3. capture exact CodeQL and Joern binary, frontend, compiler/SDK, model,
      configuration, and budget identities;
   4. run non-scored identity and load-bearing controls with separate evidence
      directories; and
   5. commit the prospective per-template scored/unsupported partition before
      any scored execution or publication.

   CodeQL controls must separately show resolved source/sink nodes, positive
   flow, negative independence, model-on/model-off behavior where a benchmark
   model is involved, and complete analysis with no endpoint or extraction
   failure. Joern must perform the equivalent checks through its independently
   pinned Swift frontend and semantics. A native run loads no benchmark-authored
   model. A benchmark-controlled run must prove that the declared model is
   load-bearing rather than relying on optimistic body propagation.

5. **Qualify and publish only after all nine families have a recorded state.**

   A family is complete only when its contract, fixtures, registry population,
   independent controls, and per-tool partition are present. Attempted executions may retain any of the five normalized outcomes.
   Inconclusive, runner-error and verified unsupported evidence can be published
   as honest coverage after the freeze gates, without qualified correctness rates.
   An unmade contract choice or missing fixture remains unresolved scope; neither
   can be disguised as an analyzer outcome. #220 may publish only a new freeze whose manifest, reports,
   raw evidence, configuration hashes, and generated scorecards bind the exact
   candidate revision. No existing freeze is rewritten, and no proposal or
   activation probe is described as a completed result.

## Deliberate boundaries

Ordinary implementation covers fixture authoring, registry/population wiring,
exact identity binding, evidence retention, and validation controls after the
contracts are fixed. The opaque body, Swift `Result` meaning, and any change to
the native API definitions are semantic contract choices requiring dated
amendments. A missing `ProcessInfo`/argv source, missing keyed `UserDefaults`
link, or missing required native summary/barrier in the pinned shipped tool is
an external tool capability gap to partition precisely; it is not permission to
shrink the nine-family scope or to substitute a local model.

## Opaque-body evidence and the remaining semantic choice

Swift's primary [Mirror interface explanation](https://www.swift.org/blog/how-mirror-works/)
describes children as labeled values and exposes stored properties of structs
and classes, rather than a runtime string-to-method invocation API. The
existing [modeling contract](modeling-matrix.md#3-dfb-template-model-opaque-propagator)
requires reflective self-dispatch and evidence that the model is load-bearing.
A `Mirror` read of an integer alone does not meet it. A stored closure selected
by a runtime child label and then invoked is a possible reflection-based
construction to investigate, but it changes declared-method lookup into
reflected function-value lookup; its equivalence and opacity have not been
proved. It must not be reported as impossible merely because direct method
reflection is unavailable, or implemented under these IDs without reconciling
the existing contract. Objective-C selectors and arbitrary hidden helper bodies
remain outside the authorized scope.

The concrete next step is a non-scored, standard-library-only closure-reflection
prototype and independent model-off/on controls. If it preserves the canonical
self-dispatch intent, a prospective adaptation can name its exact construction
and measured opacity before fixtures. If it does not, the remaining semantic
options are a reviewed different opacity construction under a new identity,
or an explicit language-scope decision for these two identities. Neither option
is accepted here. Continue the native and Result work independently.

## Release plan and provenance boundary

The current six Swift reports share fixture revision
`sha256:dcde04f2df2c2c1370241c95bd7cca6984229c33abe6db6db138ca31e557c840`.
The v0.8.0 reports bind
`sha256:4b62280924ed2e141dc8bb8e7b1bddfbd512d0201a3fa82f7b92b223eefca8c9`.
`src/freeze.rs` requires one revision equal to the hash of the selected case
union. Combining old reports with Swift reports cannot satisfy that invariant;
changing their revision strings would relabel evidence and is forbidden.

For the normal next minor release, finish the selected fixture contracts first,
then fix the complete new population. Before reruns, conduct the dated upstream
pin-currency review for every included analyzer and rules/model snapshot, recording
bump or justified hold and exact distribution/configuration identities. No current
pin review or release-wide execution is claimed by this plan. Use a new versioned
execution plan and fresh evidence locations; retain every prior report, attempt,
freeze and digest-bound source. Rerun every included report at the common final
fixture revision, with prospective partitions and unchanged budgets.

After evidence is merged, create the new freeze from clean merged `main` in a
separate publication PR. Preserve v0.8.0's manifest and generated artifacts in
its immutable archive before changing any current pointers. Generate scorecards
only through `generate-results`, retain null rates for partitions without
qualified outcomes, and register the new site snapshot explicitly. Do not inherit
old latency or warm-run evidence into a new revision. The tag-dependent release
validator must run in the documented isolated candidate/tag workflow before
pushing the final annotated tag. Verify final-head CI, the surviving merged
revision, immutable freeze, generated artifacts, tag, and deployed pages
independently. Send the exact plan, pins and freeze provenance to the coordinating
task before irreversible publication.

A six-report Swift-only freeze is structurally possible as a separately scoped
coverage snapshot: its selected case union matches the current Swift revision.
It would not represent the whole corpus, implement the nine unresolved families,
or close the epic. It must not silently replace the whole-corpus current site or
borrow its denominators. The present delivery chooses no such publication and
creates no new freeze.
