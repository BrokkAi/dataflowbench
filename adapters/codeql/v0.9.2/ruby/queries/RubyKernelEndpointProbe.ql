/**
 * @name DataFlowBench Ruby kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `RubyKernel.ql` so an empty kernel result set is read
 *              as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/ruby-kernel-endpoint-probe
 * @tags security
 */

private import codeql.ruby.AST
import codeql.ruby.DataFlow

from DataFlow::Node endpoint, string role
where
  exists(DataFlow::CallNode call |
    call.getMethodName() = "dfb_source" and
    endpoint = call and
    role = "source"
  )
  or
  exists(DataFlow::CallNode call |
    call.getMethodName() = "dfb_sink" and
    endpoint = call.getArgument(0) and
    role = "sink"
  )
select endpoint.getLocation(), "Benchmark " + role + " endpoint observed."
