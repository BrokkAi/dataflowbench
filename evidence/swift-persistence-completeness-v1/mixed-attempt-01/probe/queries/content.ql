/** @name Keyed content heap engagement
 * @kind table
 * @id dfb/swift-user-defaults-content
 */
import FoundationSources
import codeql.swift.dataflow.internal.DataFlowPrivate as Private
from DataFlow::Node a, DataFlow::Node b, DataFlow::ContentSet contents,
 DataFlow::Content::UserDefaultsContent content, string kind
where contents.isSingleton(content) and
 (Private::storeStep(a,contents,b) and kind="store" or Private::readStep(a,contents,b) and kind="read") and
 a.getLocation().getFile().getBaseName()="main.swift" and b.getLocation().getFile().getBaseName()="main.swift"
select kind,a.getLocation().getStartLine(),a.getLocation().getStartColumn(),b.getLocation().getStartLine(),b.getLocation().getStartColumn(),content.getKey()
