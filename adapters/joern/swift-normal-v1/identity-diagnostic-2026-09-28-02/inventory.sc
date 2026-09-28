import java.nio.file.{Files, Paths}
import io.shiftleft.codepropertygraph.generated.nodes.*

@main def main(cpgPath: String, outputPath: String): Unit = {
  importCpg(cpgPath)
  def node(n: AstNode): ujson.Value = ujson.Obj("id" -> n.id.toString, "label" -> n.label,
    "file" -> n.location.filename, "line" -> n.lineNumber.getOrElse(-1), "code" -> n.code)
  val methods = cpg.method.l.map { m =>
    val parent: Option[ujson.Value] = m.astParentOption.map {
      case t: TypeDecl => ujson.Obj("id" -> t.id.toString,"label" -> t.label,"full_name" -> t.fullName,
        "method_ids" -> ujson.Arr.from(t.method.id.l.map(_.toString)))
      case n: NamespaceBlock => ujson.Obj("id" -> n.id.toString,"label" -> n.label,"full_name" -> n.fullName)
      case n => ujson.Obj("id" -> n.id.toString,"label" -> n.label)
    }
    ujson.Obj("id" -> m.id.toString,"full_name" -> m.fullName,"external" -> m.isExternal,
      "node" -> node(m),"ast_parent" -> parent.getOrElse(ujson.Null),
      "parameters" -> ujson.Arr.from(m.parameter.map(p => ujson.Obj("index" -> p.index,
        "type" -> p.typeFullName,"node" -> node(p))).l),
      "return" -> ujson.Obj("type" -> m.methodReturn.typeFullName,"node" -> node(m.methodReturn)))
  }
  val calls = cpg.call.l.map { c =>
    ujson.Obj("node" -> node(c),"method_full_name" -> c.methodFullName,
      "callee_ids" -> ujson.Arr.from(c.callee.id.l.map(_.toString)),
      "arguments" -> ujson.Arr.from(c.argument.map(a => ujson.Obj("index" -> a.argumentIndex,
        "node" -> node(a))).l))
  }
  Files.writeString(Paths.get(outputPath),ujson.write(ujson.Obj("schema" -> "joern-structural-inventory/v1",
    "metadata" -> ujson.Arr.from(cpg.metaData.map(m => ujson.Obj("language" -> m.language,"overlays" -> ujson.Arr.from(m.overlays))).l),
    "types" -> ujson.Arr.from(cpg.typ.map(t => ujson.Obj("id" -> t.id.toString,"full_name" -> t.fullName,"type_decl_full_name" -> t.typeDeclFullName)).l),
    "type_declarations" -> ujson.Arr.from(cpg.typeDecl.map(t => ujson.Obj("id" -> t.id.toString,"full_name" -> t.fullName,"external" -> t.isExternal,"filename" -> t.filename,"method_ids" -> ujson.Arr.from(t.method.id.l.map(_.toString)))).l),
    "namespace_blocks" -> ujson.Arr.from(cpg.namespaceBlock.map(n => ujson.Obj("id" -> n.id.toString,"full_name" -> n.fullName,"filename" -> n.filename)).l),
    "methods" -> ujson.Arr.from(methods),"calls" -> ujson.Arr.from(calls)),indent=2))
}
