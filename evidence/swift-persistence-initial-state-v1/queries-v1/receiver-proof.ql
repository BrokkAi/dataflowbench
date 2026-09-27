/** @name Complete receiver domain proof
 * @kind table
 * @id dfb/swift-receiver-proof
 */
import FoundationSources
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
from MethodCallExpr call, string suite, boolean must, boolean complete
where Private::userDefaultsReceiverProof(call,suite,must,complete)
select call.getLocation().getStartLine(),call.getLocation().getStartColumn(),suite,must,complete
