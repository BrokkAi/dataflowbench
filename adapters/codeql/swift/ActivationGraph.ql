import swift
import codeql.swift.dataflow.DataFlow
import codeql.swift.controlflow.ControlFlowGraph
select count(DataFlow::Node n), count(Expr e), count(Function f | exists(f.getBody())), count(ControlFlowNode n)
