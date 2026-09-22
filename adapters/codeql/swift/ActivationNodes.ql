import swift
import codeql.swift.dataflow.DataFlow
from CallExpr call, Function f
where f = call.getStaticTarget() and f.getModule().getName() = "DFBActivation"
select f.getName(), count(DataFlow::Node n | n.asExpr() = call), count(DataFlow::Node n | n.asExpr() = call.getArgument(0).getExpr()), f.getNumberOfParams()
