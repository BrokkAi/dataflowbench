/** Non-scored diagnosis: resolved identity and native nodes before normalization. */
import queries.SwiftEndpoints
int exactIdentity(FreeFunction f) {
 if (
  f.getName() = "dfb_source()" and f.getNumberOfParams() = 0 and
  benchmarkInt(f.getInterfaceType().(AnyFunctionType).getResult())
  or
  f.getName() = "dfb_sink(_:)" and f.getNumberOfParams() = 1 and
  benchmarkInt(f.getParam(0).getType()) and
  f.getInterfaceType().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0
 ) then result = 1 else result = 0
}
from CallExpr call, FreeFunction f
where call.getStaticTarget() = f and
 f.getModule().getName() = "DataFlowBenchTaintSwift" and
 f.getName() = ["dfb_source()", "dfb_sink(_:)"]
select f.getName(), call.getLocation().getStartLine(), exactIdentity(f),
 count(Callable c | c = call.getEnclosingCallable()),
 count(DataFlow::Node n | n.asExpr() = call),
 count(DataFlow::Node n | n.asExpr() = call.getArgument(0).getExpr())
