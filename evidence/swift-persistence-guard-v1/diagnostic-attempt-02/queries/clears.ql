/** @name Keyed content overwrite kills
 * @kind table
 * @id dfb/swift-user-defaults-clears
 */
import FoundationSources
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
from DataFlow::Node node, DataFlow::ContentSet contents, DataFlow::Content::UserDefaultsContent content
where contents.isSingleton(content) and Private::clearsContent(node,contents) and
 node.getLocation().getFile().getBaseName()="main.swift"
select node.getLocation().getStartLine(),node.getLocation().getStartColumn(),content.getKey()
