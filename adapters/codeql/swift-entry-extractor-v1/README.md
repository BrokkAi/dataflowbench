# Experimental compiler-ordered script entry

This lane tests a generic upstream CodeQL Swift extractor/schema/QL patch. It is
not the stock analyzer and does not activate scores, qualify the 108-case corpus,
or close Swift support. The patch introduces a file/module-owned AST entry with
compiler-indexed `TopLevelCodeDecl` children, and integrates that sequence into
CFG scope construction. It does not order by source locations or fixture names.

`repair.patch` applies to public github/codeql revision
`6e9f9e38390175c41b99070a423c875f450759ca`. That source is QL-compatible with CLI
2.27.1; it is not proof of the stock binary's source revision. Upstream code is
MIT-licensed; see `UPSTREAM-LICENSE`. The patch and tests remain experimental.

`semantics.md`, the prospective registration, amendment and control manifest
retain the compiler-order rationale, exact input hashes and execution bounds.
The compiler semantics reference is swiftlang/swift
`064859e41d68596f486c5d724401cb370f260409` (Swift 6.3.3).

Build attempt 01 failed before extractor compilation: the generated Bazel C++
toolchain listed the CLT SDK root but clang selected Xcode's SDK, whose
`SDKSettings.json` was rejected as an undeclared absolute input. Attempt 02
explicitly selected the installed CLT compiler and SDK in task-local flags.
Include checks and sandboxing remained enabled; no global configuration changed.
It built in 102.67 seconds. The resulting x86_64 extractor SHA-256 is
`593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f`.

A 15-second startup probe timed out. The separately recorded 60-second diagnostic
succeeded after 17.05 seconds and reported Swift 6.3.3. Both outcomes are retained.
The isolated package contains the new extractor/schema and pinned compiler
libraries; it does not mutate stock tools. CLI import must read the changed
schema, SHA-256 `a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89`.

Controls run serially: 150 seconds extraction, then 75 seconds total query and
JSON decoding, two threads, 2,048 MiB requested, and a 40 GiB disk reserve.
CodeQL raised the initial query compile request to its 2,638 MiB minimum.
Neither requested memory flags nor process-group RSS establish hard aggregate
memory containment. Descendant polling retains identities but may miss rapidly
reparented children; all resulting observations remain diagnostic.

The ten pinned controls cover direct, overwrite, array, callback and wrapped
positive/negative behavior. The direct fixtures themselves use a wrapper;
they cannot alone prove ordering across multiple top-level declarations.
Positive flow failure or a violated negative prevents adoption. Globals,
cross-file initialization, macros and async behavior are not generally qualified
by this set. The entry is a CFG scope, not a synthesized source callable.

## Observed adoption blocker

The array negative writes tainted data to `array[0]` but reads `array[1]`. The
patched lane reports source-to-sink flow in both array polarities. This violates
the negative control and blocks adoption. Restored endpoint/CFG coverage does
not establish index-sensitive content semantics. The existing expected result
is preserved; the new observation is neither excluded nor blessed. No causal
attribution to the entry patch versus the inherited library model is made.

The callback positive also reports no flow, although both exact endpoints now
have CFG/data-flow nodes. Callback propagation remains unqualified. The negative
is retained separately; an empty positive is not converted into a clean result.

## Actionable model investigation

In the pinned Swift 6.8.4 library, `DataFlowPrivate.qll` subscript assignment
and read rules (stock lines 1081 and 1205; inherited candidate lines 1265 and
1397) both select the same parameterless `CollectionContent`. They do not use
the subscript index. Those rule bodies are unchanged by the entry patch. This
is evidence of an existing index-insensitive representation and a candidate
explanation for the array result, not a witnessed causal path. The retained
native database would allow a bounded read/write-step query to test that
hypothesis without another extraction. No such extra query has been run.

A potential generic fix needs resolver-proven array operations and index-valued
content identity, with an explicit unknown-index policy and correct weak/strong
updates. It must not special-case indices 0/1, fixture names or lines, and must
not remove the current conservative path without preserving unknown-index
coverage. Callback resolution requires a separate diagnosis of stored closure
identity, collection iteration and invocation dispatch; this patch does not
supply that proof. Neither follow-up is silently folded into the candidate.

## Reproduction boundary

Use a separate checkout at the exact CodeQL revision above and apply
`repair.patch` with `git apply`. Acquire only the two compiler archives whose
URLs, sizes and SHA-256 values are in the archived `acquisition.json`, verify
before extraction, and use their headers/libraries via the local repository
override. Bazel is pinned to 9.0.0 and its binary digest is retained. The complete
build argv and task-local SDK environment are in each attempt's `command.json`
and in the two archived runners; paths describe the original machine and must
be explicitly relocated and re-registered for another machine.

The archive also retains package-file hashes, pinned fixture bytes, the exact
extraction/query runners, and every native command result. The isolated QL
package overlays the changed QL files from the patch onto the retained
`6.8.4-dfb.9` lane and uses version `6.8.4-dfb.entry1`; it is not stock 6.8.4.
Native reproduction requires the pinned macOS compiler assets and compatible
host SDK/runtime. Portable replay verifies retained bytes and classifications;
it does not rebuild the extractor or prove the original runtime was contained.

The public archive is a redacted derivative: home-directory names and local
environment values are removed, and binary BQRS stays local. Decoded native JSON
is retained. `publication-transforms.json` records each original digest; full
original artifacts remain unchanged locally. Closure digests refer to those
original artifacts, not byte identity of the redacted derivative.

## Integration acceptance clarification

The historical ten-control candidate expectation failed and remains failed.
Those analyzer misses are not automatically blockers for the benchmark epic: the
scoring contract permits qualified false positives and false negatives. The
generic structural repair is separately reviewable; broader adoption and scoring
still require prospective structural, completeness, resource and population
qualification. See [the prospective integration plan](../../../docs/swift-integration-next-steps.md).
Optional array/callback semantic repair is stopped.
