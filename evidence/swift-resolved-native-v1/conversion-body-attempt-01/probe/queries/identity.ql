/** @name Extracted process source property identities
 * @kind table
 * @id dfb/swift-foundation-sources-identity
 */
import FoundationSources
from MemberRefExpr ref, FieldDecl field, Decl owner
where ref.getLocation().getFile().getBaseName() = "main.swift" and
 field = ref.getMember() and field.getName() = ["environment", "arguments"] and
 owner.getAMember() = field
select ref.getLocation().getStartLine(), field.getModule().getName(),
 owner.asNominalTypeDecl().getModule().getName(), owner.asNominalTypeDecl().getName(),
 field.getName(), field.getType().toString(), ref.getBase().getType().getAPrimaryQlClass()
