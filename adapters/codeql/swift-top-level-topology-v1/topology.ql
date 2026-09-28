/** @name Extracted top-level structural relationships
 * @kind table
 * @id dfb/swift-top-level-topology-v1
 */
import swift
import codeql.swift.generated.ParentChild

string identity(Element e) {
  result = e.getAPrimaryQlClass() + "@" + e.getLocation().getStartLine().toString() +
    ":" + e.getLocation().getStartColumn().toString()
}

from string relation, string left, string right, int index
where
  exists(TopLevelCodeDecl top |
    top.getLocation().getFile().getBaseName() = "main.swift" and
    relation = "top-body" and left = identity(top) and right = identity(top.getBody()) and index = -1
  )
  or
  exists(TopLevelCodeDecl top, Element parent |
    top.getLocation().getFile().getBaseName() = "main.swift" and
    parent = getImmediateParent(top) and relation = "top-parent" and
    left = identity(top) and right = identity(parent) and index = -1
  )
  or
  exists(Decl parent, Decl member |
    member = parent.getMember(index) and
    member.getLocation().getFile().getBaseName() = "main.swift" and
    relation = "decl-member" and left = identity(parent) and right = identity(member)
  )
  or
  exists(TopLevelCodeDecl top, Element child |
    top.getLocation().getFile().getBaseName() = "main.swift" and
    child = top.getBody().getElement(index) and relation = "body-element" and
    left = identity(top.getBody()) and right = identity(child)
  )
  or
  exists(CallExpr call, Element parent |
    call.getLocation().getFile().getBaseName() = "main.swift" and
    parent = getImmediateParent(call) and relation = "call-parent" and
    left = identity(call) and right = identity(parent) and index = -1
  )
  or
  exists(DeclRefExpr ref, VarDecl declaration |
    ref.getLocation().getFile().getBaseName() = "main.swift" and
    declaration = ref.getDecl() and relation = "variable-reference" and
    left = identity(ref) and right = identity(declaration) and index = -1
  )
select relation, left, right, index
