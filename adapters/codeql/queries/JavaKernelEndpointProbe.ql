/**
 * @name DataFlowBench Java kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `JavaKernel.ql` so an empty kernel result set is read
 *              as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/java-kernel-endpoint-probe
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow

from DataFlow::Node endpoint, string role
where
  exists(MethodCall call |
    call.getMethod().getName() =
      ["dfb_source", "directUntrustedInput", "explicitNegativeUntrustedInput"] and
    endpoint.asExpr() = call and
    role = "source"
  )
  or
  exists(MethodCall call |
    call.getMethod().getName() = ["dfb_sink", "recordDirect", "recordExplicitNegative"] and
    endpoint.asExpr() = call.getArgument(0) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
