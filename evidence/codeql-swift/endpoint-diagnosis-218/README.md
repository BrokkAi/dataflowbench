# Bounded endpoint diagnosis — #218

This is **post-execution, non-scored diagnosis**. Original reports, fixtures,
query/model configuration, budgets and partitions are unchanged. It does not
replace or relabel any of the 90 executions. The diagnostic runs use a 2048 MiB
query hint and cannot qualify the original 512 MiB benchmark outcomes.

## What the 54 rows actually show

The retained SARIF contains no endpoint observations for 52 assertions, and only
the correctly anchored sink for the two callback-registration assertions.
`missing-endpoint-groups.json` binds each SARIF digest and native observations;
`affected-constructs.json` enumerates all 27 paired templates with their existing
semantic dimensions. These are diagnostic groups, not revised score partitions:

| Construct family | Assertions |
| --- | ---: |
| Local arithmetic/chains, overwrite, branches and loops | 10 |
| Heap, containers, access paths and object separation | 12 |
| Recursive propagation/heap/exception constructs | 12 |
| Interprocedural exception persistence | 2 |
| Calls, return relays, callbacks, closures, properties and context | 18 |

An anchor-normalization error cannot explain the 52 empty native probe result
sets: there is no native endpoint location for normalization to discard. The
callback sink observation already matches canonical line 13 exactly.

## Native node reproductions

`EndpointCoverageDiagnostic.ql` examines resolved `FreeFunction` identity and
native dataflow-node existence independently of report normalization. Its columns
are target name, call line, exact identity (1/0), enclosing callable count,
call-expression dataflow-node count, and argument-zero dataflow-node count.
The two registry fixtures were re-extracted unchanged with the original pinned
compiler, module, target and SDK. Their input digests, commands, native BQRS and
JSON decode outputs are retained. The existing independent function-body
positive database is the third control; no scored fixture was transformed.

| Native expression | Exact identity | Callable | Relevant native nodes |
| --- | ---: | ---: | ---: |
| Array source, line 5 | 1 | 0 | 0 call nodes |
| Array sink, line 7 | 1 | 0 | 0 argument nodes |
| Callback source, line 15 | 1 | 0 | 0 call nodes |
| Callback sink in closure, line 13 | 1 | 1 | 1 argument node |
| Function-body control source, line 4 | 1 | 1 | 1 call node |
| Function-body control sink, line 5 | 1 | 1 | 1 argument node |

The registry reproductions rule out a wrong module, overload, parameter/result
identity, or line anchor for these examples. They establish that AST extraction
succeeded but top-level expressions lack native CFG/dataflow nodes; the same
query recognizes the closure and function-body expressions.

## Primary implementation evidence and scope

`pinned-library-evidence.json` retains line-numbered excerpts and full-file
SHA-256 identities from the actual `codeql/swift-all@6.8.3` package, whose entire
byte tree is already bound by activation. The corresponding CodeQL source pin is
c6baf479093fafc81d4655dc2014dc583360308e.

- `controlflow/internal/Scope.qll` restricts callable/scope ranges to functions,
  key paths and closures, and discovers enclosing scopes through AST parents.
- `ControlFlowGraphImpl.qll` derives CFG scope through that same scope relation.
- `dataflow/internal/DataFlowPublic.qll` represents expression nodes using CFG
  nodes; `DataFlowPrivate.qll` constructs them from expression/property CFG nodes.

This supports a pinned upstream CFG/dataflow scope limitation, not failed Swift
compilation or a demonstrated adapter-normalization bug. The 54 original rows
remain individually classified as runner errors; the three probes establish the
mechanism on minimal representative cases, not a new execution of every row.

No small, faithful endpoint-predicate change can create absent native CFG nodes.
A potential fix needs upstream top-level CFG/dataflow support (or a separately
pinned, independently activated library revision/fork). Wrapping canonical
fixtures, inventing AST/text taint edges, treating a missing node as clean, or
retrospectively excluding cells would violate this study's constraints. None is
implemented. The original resource failures also remain unchanged.

## Acceptance assessment

The integration criteria in #218 require verified activation, execution of the
applicable declared tiers, exact evidence, honest normalization/failure handling,
and documented capability decisions. Those actions are implemented and tested;
unfavorable measured outcomes do not by themselves leave an execution criterion
unmet. This diagnosis identifies no remaining in-scope identity/anchor fix in the
probed pipeline. What is unavailable is qualified top-level reachability and
512 MiB-compliant execution, which must remain explicit in any later publication.
The parent review decides issue acceptance/closure; this PR does not close it
implicitly or advance the queue.
