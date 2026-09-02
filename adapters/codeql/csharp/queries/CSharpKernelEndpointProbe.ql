/**
 * @name DataFlowBench C# kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `CSharpKernel.ql` so an empty kernel result set is
 *              read as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/csharp-kernel-endpoint-probe
 * @tags security
 */

import csharp
import semmle.code.csharp.dataflow.internal.DataFlowPublic

from DataFlow::Node endpoint, string role
where
  exists(MethodCall call |
    call.getTarget().getName() = "dfb_source" and
    endpoint.asExpr() = call and
    role = "source"
  )
  or
  exists(MethodCall call |
    call.getTarget().getName() = "dfb_sink" and
    endpoint.asExpr() = call.getArgument(0) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
