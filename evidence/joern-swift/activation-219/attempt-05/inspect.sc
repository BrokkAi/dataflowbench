import java.nio.file.{Files, Paths}
@main def main(inputPath: String, outputPath: String, sourceLine: Int = 1, sinkLine: Int = 2): Unit = {
 importCode(inputPath = inputPath, projectName = "swift-activation", language = "SWIFTSRC")
 val sourceMethods = cpg.method.filter(n => n.filename == "main.swift" && n.lineNumber.contains(sourceLine) && !n.isExternal && n.name == "probeSource").l
 val sinkMethods = cpg.method.filter(n => n.filename == "main.swift" && n.lineNumber.contains(sinkLine) && !n.isExternal && n.name == "probeSink").l
 val sourceIds = sourceMethods.map(_.id).toSet
 val sinkIds = sinkMethods.map(_.id).toSet
 val sources = cpg.call.filter(n => n.callee.l.exists(m => sourceIds.contains(m.id))).l
 val sinks = cpg.call.filter(n => n.callee.l.exists(m => sinkIds.contains(m.id))).argument(1).l
 val flows = sinks.reachableByFlows(sources).l
 val result = ujson.Obj(
  "source_method_ids" -> ujson.Arr.from(sourceIds.toList.map(_.toString)),
  "sink_method_ids" -> ujson.Arr.from(sinkIds.toList.map(_.toString)),
  "source_call_ids" -> ujson.Arr.from(sources.map(_.id.toString)),
  "sink_argument_ids" -> ujson.Arr.from(sinks.map(_.id.toString)),
  "flows" -> ujson.Arr.from(flows.map(p => ujson.Arr.from(p.elements.map(n => ujson.Obj("id" -> n.id.toString, "label" -> n.label, "file" -> n.location.filename, "line" -> n.lineNumber.getOrElse(-1), "code" -> n.code))))),
  "metadata" -> ujson.Arr.from(cpg.metaData.map(n => ujson.Obj("language" -> n.language, "overlays" -> ujson.Arr.from(n.overlays))).l),
  "methods" -> ujson.Arr.from(cpg.method.map(n => ujson.Obj("id" -> n.id.toString, "name" -> n.name, "fullName" -> n.fullName, "signature" -> n.signature, "file" -> n.filename, "external" -> n.isExternal, "line" -> n.lineNumber.getOrElse(-1), "parameters" -> ujson.Arr.from(n.parameter.map(p => ujson.Obj("name" -> p.name, "type" -> p.typeFullName, "index" -> p.index)).l))).l),
  "calls" -> ujson.Arr.from(cpg.call.map(n => ujson.Obj("id" -> n.id.toString, "name" -> n.name, "methodFullName" -> n.methodFullName, "signature" -> n.signature, "line" -> n.lineNumber.getOrElse(-1), "file" -> n.location.filename, "callees" -> ujson.Arr.from(n.callee.fullName.l), "callee_ids" -> ujson.Arr.from(n.callee.id.l.map(_.toString)), "arguments" -> ujson.Arr.from(n.argument.map(p => ujson.Obj("id" -> p.id.toString, "code" -> p.code, "index" -> p.argumentIndex)).l))).l)
 )
 Files.writeString(Paths.get(outputPath), ujson.write(result, indent = 2))
}
