/**
 * @name DataFlowBench Python kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `PythonKernel.ql` so an empty kernel result set is
 *              read as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/python-kernel-endpoint-probe
 * @tags security
 */

private import python
import semmle.python.dataflow.new.DataFlow

from DataFlow::Node endpoint, string role
where
  exists(DataFlow::CallCfgNode call |
    call.getFunction().asCfgNode().(NameNode).getId() = "dfb_source" and
    endpoint = call and
    role = "source"
  )
  or
  exists(DataFlow::CallCfgNode call |
    call.getFunction().asCfgNode().(NameNode).getId() = "dfb_sink" and
    endpoint = call.getArg(0) and
    role = "sink"
  )
select endpoint.getLocation(), "Benchmark " + role + " endpoint observed."
