/** @name Ordered suite-state transitions
 * @kind table
 * @id dfb/swift-suite-transitions
 */
import FoundationSources
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
from DataFlow::Node a, DataFlow::Node b, string suite, boolean fromPost, boolean toPost
where Private::userDefaultsStateTransition(a,b) and
 Private::userDefaultsStateDomain(a,suite,fromPost) and Private::userDefaultsStateDomain(b,suite,toPost)
select a.getLocation().getStartLine(),fromPost,b.getLocation().getStartLine(),toPost,suite
