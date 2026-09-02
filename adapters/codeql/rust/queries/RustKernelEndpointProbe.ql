/**
 * @name DataFlowBench Rust kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `RustKernel.ql` so an empty kernel result set is read
 *              as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/rust-kernel-endpoint-probe
 * @tags security
 */

import rust
import codeql.rust.dataflow.DataFlow

from DataFlow::Node endpoint, string role
where
  exists(Call call |
    call.getTargetName() = "dfb_source" and
    endpoint.asExpr() = call and
    role = "source"
  )
  or
  exists(Call call |
    call.getTargetName() = "dfb_sink" and
    endpoint.asExpr() = call.getPositionalArgument(0) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
