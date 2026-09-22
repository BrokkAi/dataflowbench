/**
 * @name Swift resolved declaration inventory
 * @description Non-scored exact resolved declaration references, not display-name matching.
 * @kind table
 * @id dfb/swift-v2-declarations
 */
import swift

from DeclRefExpr ref
where ref.getLocation().getFile().getBaseName() = "main.swift"
select ref.getLocation().getStartLine(), ref.getLocation().getStartColumn(),
  ref.getDecl().getModule().getFullName(), ref.getDecl().getName(), ref.getDecl().getType().toString()
