/**
 * @name DataFlowBench Go kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `GoKernel.ql` so an empty kernel result set is read
 *              as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/go-kernel-endpoint-probe
 * @tags security
 */

import go

from DataFlow::Node endpoint, string role
where
  exists(DataFlow::CallNode call |
    call.getTarget().getName() = "dfb_source" and
    endpoint = call.getResult() and
    role = "source"
  )
  or
  exists(DataFlow::CallNode call |
    call.getTarget().getName() = "dfb_sink" and
    endpoint = call.getArgument(0) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
