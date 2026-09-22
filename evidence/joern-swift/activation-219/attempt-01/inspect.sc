import java.nio.file.{Files, Paths}
@main def main(inputPath: String, outputPath: String): Unit = {
 importCode(inputPath = inputPath, projectName = "swift-activation", language = "SWIFTSRC")
 val result = ujson.Obj(
  "metadata" -> ujson.Arr.from(cpg.metaData.map(n => ujson.Obj("language" -> n.language, "overlays" -> ujson.Arr.from(n.overlays))).l),
  "methods" -> ujson.Arr.from(cpg.method.map(n => ujson.Obj("id" -> n.id.toString, "name" -> n.name, "fullName" -> n.fullName, "signature" -> n.signature, "file" -> n.filename, "external" -> n.isExternal, "line" -> n.lineNumber.getOrElse(-1), "parameters" -> ujson.Arr.from(n.parameter.map(p => ujson.Obj("name" -> p.name, "type" -> p.typeFullName, "index" -> p.index)).l))).l),
  "calls" -> ujson.Arr.from(cpg.call.map(n => ujson.Obj("id" -> n.id.toString, "name" -> n.name, "methodFullName" -> n.methodFullName, "signature" -> n.signature, "line" -> n.lineNumber.getOrElse(-1), "file" -> n.location.filename, "callees" -> ujson.Arr.from(n.callee.fullName.l), "arguments" -> ujson.Arr.from(n.argument.map(p => ujson.Obj("code" -> p.code, "index" -> p.argumentIndex)).l))).l)
 )
 Files.writeString(Paths.get(outputPath), ujson.write(result, indent = 2))
}
