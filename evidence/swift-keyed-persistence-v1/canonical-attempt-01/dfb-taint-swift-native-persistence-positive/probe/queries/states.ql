/** @name Typed suite-state identities
 * @kind table
 * @id dfb/swift-suite-states
 */
import FoundationSources
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
from DataFlow::Node node, string suite, boolean post
where Private::userDefaultsStateDomain(node,suite,post)
select node.getLocation().getStartLine(),node.getLocation().getStartColumn(),suite,post
