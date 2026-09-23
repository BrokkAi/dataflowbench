/** Explicit adapter profile: resolved process environment and argv collection values. */
import FoundationIdentity
import codeql.swift.controlflow.CfgNodes

predicate ownedField(FieldDecl field, string moduleName, string ownerName, string fieldName) {
  field.getModule().getName() = moduleName and field.getName() = fieldName and
  exists(Decl owner |
    owner.getAMember() = field and
    owner.asNominalTypeDecl().getModule().getName() = moduleName and
    owner.asNominalTypeDecl().getName() = ownerName
  )
}
predicate stringDictionary(Type t) {
  namedType(t.(DictionaryType).getKeyType(), "Swift", "String") and
  namedType(t.(DictionaryType).getValueType(), "Swift", "String")
}
predicate processInput(DataFlow::Node node, string kind) {
  exists(MemberRefExpr ref, FieldDecl field, PropertyGetterCfgNode getter, Method accessor |
    field = ref.getMember() and getter = node.getCfgNode() and
    getter.getRef() = ref and node.asExpr() = ref and
    accessor = getter.getAccessor() and accessor = field.getAnAccessor() and
    getter.getAccessor().isGetter() and
    (
      kind = "environment" and ownedField(field, "Foundation", "ProcessInfo", "environment") and
      accessor.getModule().getName() = "Foundation" and
      namedType(accessor.getSelfParam().getType(), "Foundation", "ProcessInfo") and
      namedType(ref.getBase().getType(), "Foundation", "ProcessInfo") and
      stringDictionary(field.getType()) and stringDictionary(ref.getType())
      or
      kind = "argv" and ownedField(field, "Swift", "CommandLine", "arguments") and
      accessor.getModule().getName() = "Swift" and accessor.isStaticOrClassMethod() and
      ref.getBase().getType() instanceof MetatypeType and
      stringArray(field.getType()) and stringArray(ref.getType())
    )
  )
}
