# Swift CodeQL native recognition diagnosis

The compatible-toolchain controls distinguish three findings:

1. The retained exact Foundation control activates the shipped
   `String(contentsOfFile:encoding:)` source and the two argument sinks for
   `Foundation.Process.run(_:arguments:terminationHandler:)`. Earlier absence
   of these roles in compiler-error databases is not a native-model absence.
2. `Foundation.ProcessInfo.environment` and `Swift.CommandLine.arguments`
   resolve correctly but acquire no shipped source role in this control. The
   positive source works in the same database. This agrees with the previously
   retained shipped-model inventory; it is still a non-scored observation.
3. A fresh benchmark-owned `Process` also receives shipped sink roles:
   `Process.arguments` line 17 gets `[post] process`, and static `Process.run`
   line 19 gets both argument sinks. Declaration rows resolve both to
   `DataFlowBenchTaintSwift`, while the known Foundation source at line 13
   activates. This reproduces the wrong-module match without compiler errors.

## Vendor matching cause and actionable dependency

In the verified `codeql/swift-all/6.8.4` pack,
`codeql/swift/security/CommandInjectionExtensions.qll` lines 43 and 45 model
`Process.run` arguments and `Process.arguments` post-update, respectively,
with an empty namespace and empty signature.
`codeql/swift/dataflow/ExternalFlow.qll` lines 384–392 explicitly documents
that namespace is unused and requires an empty namespace. Its member/field
branches match the nominal type name and member name, without checking the
module of the declaration. The runtime counterexamples agree with that code.

The concrete upstream precision fix is module/receiver identity enforcement
for native model matching, with these positive/wrong-module controls retained
as regressions. Merely filling in a namespace in the CSV is insufficient while
the interpreter requires it empty. Signature constraints are a separate
precision consideration, not a proven standalone fix for this reproducer.
Native environment/argv source modeling is a separate upstream capability
requirement for the A38 contracts. No local model or query filter was added to
hide either behavior. No upstream issue was posted by this task.

## Provenance and qualification boundaries

All 1,493 retained Swift pack files were rehashed before queries. The original
121.0978-second database source archive matched the exact PR #236 control.
Its extraction remains the historical unlimited diagnostic; it was not
relabeled as a prospective 150-second result. Both declaration and role-node
queries were preregistered and completed with 60-second / 512-MiB requests.

The fresh lookalike extraction completed in 97.44096 seconds under the new
150-second cutoff, finalized as Swift, and passed the raw-log compiler-error
gate. Type-mangler warnings remain retained. All four declaration/role queries
completed within 60 seconds but their recorded command maximum RSS exceeded
512 MiB. Thus these are reproducible diagnostic model observations, not
budget-qualified benchmark outcomes or semantic-completeness certification.
No native binaries, custom models, corpus runs, pin changes, capability
partitions, opaque decisions or publication were performed.

The concrete diagnostic blocker is now upstream model identity separation and
missing environment/argv sources; independent analysis resource qualification
also remains unresolved. No additional analyzer run is needed to demonstrate
this observed wrong-module match.
