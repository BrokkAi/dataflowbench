/** @name Content steps and resolved dispatch
 * @kind table
 * @id dfb/swift-entry-content-dispatch
 */
import swift
import codeql.swift.dataflow.DataFlow
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
import codeql.swift.dataflow.internal.DataFlowDispatch as Dispatch

from string kind, int line, int otherLine, string detail, int countValue
where
  exists(DataFlow::Node a, DataFlow::Node b, DataFlow::ContentSet c |
    (kind = "store" and Private::storeStep(a, c, b) or
     kind = "read" and Private::readStep(a, c, b)) and
    a.getLocation().getFile().getBaseName() = "main.swift" and
    b.getLocation().getFile().getBaseName() = "main.swift" and
    line = a.getLocation().getStartLine() and otherLine = b.getLocation().getStartLine() and
    detail = c.toString() and countValue = 1
  )
  or
  exists(Dispatch::DataFlowCall call |
    kind = "dispatch" and call.getLocation().getFile().getBaseName() = "main.swift" and
    line = call.getLocation().getStartLine() and otherLine = call.getLocation().getStartColumn() and
    detail = concat(Dispatch::DataFlowCallable target | target = Dispatch::viableCallable(call) | target.toString(), ",") and
    countValue = count(Dispatch::viableCallable(call))
  )
select kind, line, otherLine, detail, countValue
