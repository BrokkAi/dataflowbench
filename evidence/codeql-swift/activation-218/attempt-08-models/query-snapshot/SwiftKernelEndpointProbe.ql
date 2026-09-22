/**
 * @name DataFlowBench Swift endpoint observation
 * @description Observe resolved dataflow endpoints before interpreting absence of flow.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dfb/swift-kernel-endpoint-probe
 */
import SwiftEndpoints
from DataFlow::Node endpoint, string role
where benchmarkSource(endpoint) and role = "source"
  or benchmarkSink(endpoint) and role = "sink"
select endpoint.getLocation(), "Benchmark " + role + " endpoint observed."
