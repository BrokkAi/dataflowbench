/** @name Script entry identities
 * @kind table
 * @id dfb/swift-entry-identities-v1
 */
import swift
from TopLevelEntryPoint e, int i, TopLevelCodeDecl d
where d = e.getDeclaration(i)
select e, e.getSourceFile(), e.getModule(), i, d, d.getBody()
