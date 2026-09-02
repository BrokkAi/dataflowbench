/**
 * @name DataFlowBench TypeScript kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `TypeScriptKernel.ql` so an empty kernel result set is
 *              read as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/typescript-kernel-endpoint-probe
 * @tags security
 */

import javascript

/**
 * Mirrors `TypeScriptKernel.ql`: the TypeScript kernel is intentionally
 * restricted to `.ts` fixtures, so the probe observes exactly the nodes the
 * kernel's own endpoint predicates could ever bind.
 */
predicate isTypeScriptFixture(DataFlow::Node node) { node.getFile().getExtension() = "ts" }

from DataFlow::Node endpoint, string role
where
  exists(DataFlow::CallNode call |
    call.getCalleeName() = "dfb_source" and
    endpoint = call and
    isTypeScriptFixture(endpoint) and
    role = "source"
  )
  or
  exists(DataFlow::CallNode call |
    call.getCalleeName() = "dfb_sink" and
    endpoint = call.getArgument(0) and
    isTypeScriptFixture(endpoint) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
