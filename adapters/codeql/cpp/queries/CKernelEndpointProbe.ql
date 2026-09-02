/**
 * @name DataFlowBench C kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `CKernel.ql` so an empty kernel result set is read as
 *              a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/c-kernel-endpoint-probe
 * @tags security
 */

import cpp
import semmle.code.cpp.dataflow.new.DataFlow

/**
 * Mirrors `CKernel.ql`: C and C++ share the `cpp` extractor, so the probe is
 * restricted to `.c` fixtures exactly as the kernel is.
 */
predicate isCFixture(DataFlow::Node node) { node.getLocation().getFile().getExtension() = "c" }

from DataFlow::Node endpoint, string role
where
  exists(FunctionCall call |
    call.getTarget().getName() = "dfb_source" and
    endpoint.asExpr() = call and
    isCFixture(endpoint) and
    role = "source"
  )
  or
  exists(FunctionCall call |
    call.getTarget().getName() = "dfb_sink" and
    endpoint.asExpr() = call.getArgument(0) and
    isCFixture(endpoint) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
