/** Exact resolved benchmark declarations, independent of fixture or polarity. */
import swift
import codeql.swift.dataflow.DataFlow

predicate benchmarkInt(Type t) {
  t.(NominalType).getDeclaration().getModule().getName() = "Swift" and
  t.(NominalType).getDeclaration().getName() = "Int"
}

predicate benchmarkSource(DataFlow::Node source) {
  exists(CallExpr call, FreeFunction f |
    f = call.getStaticTarget() and
    f.getModule().getName() = "DataFlowBenchTaintSwift" and
    f.getName() = "dfb_source()" and f.getNumberOfParams() = 0 and
    benchmarkInt(f.getInterfaceType().(AnyFunctionType).getResult()) and
    source.asExpr() = call
  )
}

predicate benchmarkSink(DataFlow::Node sink) {
  exists(CallExpr call, FreeFunction f |
    f = call.getStaticTarget() and
    f.getModule().getName() = "DataFlowBenchTaintSwift" and
    f.getName() = "dfb_sink(_:)" and f.getNumberOfParams() = 1 and
    benchmarkInt(f.getParam(0).getType()) and
    f.getInterfaceType().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0 and
    sink.asExpr() = call.getArgument(0).getExpr()
  )
}
