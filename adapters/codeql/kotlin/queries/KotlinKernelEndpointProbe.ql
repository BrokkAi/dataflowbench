/**
 * @name DataFlowBench Kotlin kernel endpoint-observation probe
 * @description Reports every benchmark-controlled source and sink endpoint the
 *              extracted database resolves. The runner evaluates this probe
 *              alongside `KotlinKernel.ql` so an empty kernel result set is
 *              read as a clean negative only when both endpoints were observed.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/kotlin-kernel-endpoint-probe
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow

/**
 * Mirrors `KotlinKernel.ql`: Kotlin rides the shared `java` extractor, so the
 * probe restricts every node to `.kt` files exactly as the kernel does.
 */
predicate isKotlinFixture(DataFlow::Node node) {
  node.getLocation().getFile().getExtension() = "kt"
}

from DataFlow::Node endpoint, string role
where
  exists(MethodCall call |
    call.getMethod().getName() = "dfb_source" and
    endpoint.asExpr() = call and
    isKotlinFixture(endpoint) and
    role = "source"
  )
  or
  exists(MethodCall call |
    call.getMethod().getName() = "dfb_sink" and
    endpoint.asExpr() = call.getArgument(0) and
    isKotlinFixture(endpoint) and
    role = "sink"
  )
select endpoint, "Benchmark " + role + " endpoint observed."
