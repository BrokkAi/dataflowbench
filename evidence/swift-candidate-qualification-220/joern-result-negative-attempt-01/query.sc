// Swift-only compiler-resolved query. No name-only or source-text resolver.
import java.nio.file.{Files, Paths}
import io.shiftleft.codepropertygraph.generated.nodes.*
import io.joern.dataflowengineoss.DefaultSemantics
import io.joern.dataflowengineoss.queryengine.EngineContext
import io.joern.dataflowengineoss.semanticsloader.{FlowSemantic, Semantics}

@main def main(cpgPath: String, configPath: String, outputPath: String): Unit = {
  val config = ujson.read(Files.readString(Paths.get(configPath)))
  try {
    importCpg(cpgPath)
    val declarations = cpg.method.l
    def methods(key: String): List[Method] = {
      val identities = config(key).arr.map(_.str).toList
      require(identities.nonEmpty && identities.distinct.size == identities.size, s"invalid $key identities")
      identities.flatMap { identity =>
        val matches = declarations.filter(n => !n.isExternal && n.fullName == identity)
        require(matches.size == 1, s"$identity must resolve to one native declaration, got ${matches.size}")
        matches
      }
    }
    val sourceMethods = methods("source_methods")
    val sinkMethods = methods("sink_methods")
    val sourceIds = sourceMethods.map(_.id).toSet
    val sinkIds = sinkMethods.map(_.id).toSet
    def exactCall(c: Call, ids: Set[Long]): Boolean = {
      val targets = c.callee.l
      targets.size == 1 && ids.contains(targets.head.id) && c.methodFullName == targets.head.fullName
    }
    def at(n: AstNode, key: String): Boolean = config(key).arr.exists(a => a("file").str == n.location.filename && n.lineNumber.contains(a("line_hint").num.toInt))
    val sourceCalls = cpg.call.filter(c => exactCall(c, sourceIds) && (sourceMethods.exists(n => at(n,"source_anchors")) || at(c,"source_anchors"))).l
    val sinkCalls = cpg.call.filter(c => exactCall(c, sinkIds) && (sinkMethods.exists(n => at(n,"sink_anchors")) || at(c,"sink_anchors"))).l
    val sourceNodes: List[CfgNode] = if (config("source_kind").str == "parameter") {
      sourceMethods.flatMap { method =>
        require(at(method, "source_anchors"), "parameter root declaration is outside the source anchor")
        val parameters = method.parameter.index(1).l
        require(parameters.size == 1, "parameter root requires exactly one declared parameter at index 1")
        parameters
      }
    } else sourceCalls
    val sinkNodes: List[CfgNode] = sinkCalls.flatMap(_.argument.filter(_.argumentIndex == 1).l)
    def node(n: AstNode): ujson.Value = ujson.Obj("id" -> n.id.toString, "label" -> n.label, "file" -> n.location.filename,
      "line" -> n.lineNumber.getOrElse(-1), "code" -> n.code)
    def call(c: Call): ujson.Value = ujson.Obj("node" -> node(c), "method_full_name" -> c.methodFullName,
      "callee_ids" -> ujson.Arr.from(c.callee.id.l.map(_.toString)),
      "arguments" -> ujson.Arr.from(c.argument.map(a => ujson.Obj("index" -> a.argumentIndex, "node" -> node(a))).l))
    def observed(key: String, ms: List[Method], cs: List[Call]): List[AstNode] = (ms.filter(n => at(n,key)) ++ cs.filter(n => at(n,key))).distinct
    val semantics = config("semantics").arr.map(s => FlowSemantic.from(s("method").str, s("flows").arr.map(pair => (pair(0).num.toInt, pair(1).num.toInt)).toList)).toList
    implicit val context: EngineContext = EngineContext(DefaultSemantics().plus(semantics))
    val activeSources = if (config("source_enabled").bool) sourceNodes else List.empty[CfgNode]
    val activeSinks = if (config("sink_enabled").bool) sinkNodes else List.empty[CfgNode]
    val flows = activeSinks.reachableByFlows(activeSources).l
    val result = ujson.Obj(
      "state" -> "analyzed", "frontend" -> "SWIFTSRC",
      "metadata" -> ujson.Arr.from(cpg.metaData.map(n => ujson.Obj("language" -> n.language, "overlays" -> ujson.Arr.from(n.overlays))).l),
      "methods" -> ujson.Arr.from(declarations.map(m => ujson.Obj("id" -> m.id.toString,"full_name" -> m.fullName,"external" -> m.isExternal,
        "node" -> node(m), "parameters" -> ujson.Arr.from(m.parameter.map(p => ujson.Obj("index" -> p.index, "type" -> p.typeFullName, "node" -> node(p))).l)))),
      "calls" -> ujson.Arr.from(cpg.call.map(call).l),
      "source_method_ids" -> ujson.Arr.from(sourceIds.toList.map(_.toString)), "sink_method_ids" -> ujson.Arr.from(sinkIds.toList.map(_.toString)),
      "source_nodes" -> ujson.Arr.from(sourceNodes.map(node)), "sink_nodes" -> ujson.Arr.from(sinkNodes.map(node)),
      "source_observations" -> ujson.Arr.from(observed("source_anchors",sourceMethods,sourceCalls).map(node)),
      "sink_observations" -> ujson.Arr.from(observed("sink_anchors",sinkMethods,sinkCalls).map(node)),
      "semantics" -> config("semantics"),
      "flows" -> ujson.Arr.from(flows.map(p => ujson.Arr.from(p.elements.map(node)))), "query_completed" -> true,
      "analysis_completeness" -> ujson.Obj("status" -> "unproven", "exhaustion_observable" -> false,
        "max_call_depth" -> context.config.maxCallDepth, "max_args_to_allow" -> context.config.maxArgsToAllow,
        "max_output_args_expansion" -> context.config.maxOutputArgsExpansion))
    Files.writeString(Paths.get(outputPath), ujson.write(result, indent=2))
  } catch {
    case error: Throwable =>
      Files.writeString(Paths.get(outputPath), ujson.write(ujson.Obj("state" -> "runner-error", "error" -> error.toString),indent=2))
      throw error
  }
}
