/**
 * @name Reflection endpoint identity probe
 * @description Native resolved sources, sinks, and modeled methods.
 * @kind problem
 * @problem.severity warning
 * @id dfb/swift-reflection-endpoints
 */
import ReflectionModels
from DataFlow::Node n, string role
where stringSource(n) and role = "source" or stringSink(n) and role = "sink"
select n.getLocation(), role
