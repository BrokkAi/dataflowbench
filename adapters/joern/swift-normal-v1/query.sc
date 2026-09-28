// Swift-only compiler-resolved query. No name-only or source-text resolver.
import java.nio.file.{Files, Paths}
import io.shiftleft.codepropertygraph.generated.nodes.*
import io.joern.dataflowengineoss.DefaultSemantics
import io.joern.dataflowengineoss.queryengine.EngineContext
import io.joern.dataflowengineoss.semanticsloader.{FlowSemantic, Semantics}

class IdentityIncomplete(message: String) extends RuntimeException(message)

@main def main(cpgPath: String, configPath: String, outputPath: String): Unit = {
  val config = ujson.read(Files.readString(Paths.get(configPath)))
  def prove(condition: Boolean, message: String): Unit = {
    if (!condition) throw new IdentityIncomplete(message)
  }
  try {
    importCpg(cpgPath)
    val declarations = cpg.method.l
    def methods(key: String): List[Method] = {
      val identities = config(key).arr.map(_.str).toList
      prove(identities.nonEmpty && identities.distinct.size == identities.size, s"invalid $key identities")
      identities.flatMap { identity =>
        val matches = declarations.filter(n => !n.isExternal && n.fullName == identity)
        prove(matches.size == 1, s"$identity must resolve to one native declaration, got ${matches.size}")
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
        prove(at(method, "source_anchors"), "parameter root declaration is outside the source anchor")
        val parameters = method.parameter.index(1).l
        prove(parameters.size == 1, "parameter root requires exactly one declared parameter at index 1")
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
    // Candidate names select declarations; AST ownership, parameter indices,
    // and exact callee edges provide the independent identity witnesses.
    val wrapperSpecs = config("wrappers").arr.toList
    val wrapperMethods = wrapperSpecs.map { spec =>
      val matches = declarations.filter(m => !m.isExternal && m.fullName == spec("method").str)
      prove(matches.size == 1, "missing or ambiguous wrapper declaration")
      val m = matches.head
      val owners = m.astParentOption.toList.collect { case t: TypeDecl => t }
      prove(owners.size == 1 && owners.head.fullName == spec("owner").str, "wrapper AST owner mismatch")
      val indices = m.parameter.index.l.sorted
      prove(indices == spec("parameter_indices").arr.map(_.num.toInt).toList.sorted, "wrapper parameter positions mismatch")
      val parameterTypes = m.parameter.l.map(p => (p.index, p.typeFullName)).sortBy(_._1)
      val expectedTypes = spec("parameter_indices").arr.map(v => (v.num.toInt, if (v.num.toInt == 0) spec("owner").str else "Swift.String")).toList.sortBy(_._1)
      prove(parameterTypes == expectedTypes, "wrapper parameter type mismatch")
      prove(List(m.methodReturn.typeFullName) == List("Swift.String"), "wrapper return type mismatch")
      m
    }
    val selectedWrapper = config("selected_wrapper").str
    if (selectedWrapper.nonEmpty) {
      val wrapper = wrapperMethods.filter(_.fullName == selectedWrapper)
      prove(wrapper.size == 1, "selected wrapper missing")
      val invocations = cpg.call.filter(c => exactCall(c, Set(wrapper.head.id)) && at(c, "sink_anchors")).l
      prove(invocations.size == 1, "selected wrapper call not exactly resolved at sink")
      prove(invocations.head.argument.argumentIndex.l.sorted == wrapper.head.parameter.index.l.sorted,
        "wrapper call argument positions disagree with declaration")
    }
    val wrapperEvidence = wrapperMethods.map { m =>
      val owner = m.astParentOption.toList.collect { case t: TypeDecl => t }.head
      ujson.Obj("method_id" -> m.id.toString, "owner_id" -> owner.id.toString,
        "owner_full_name" -> owner.fullName, "owner_ast_method_ids" -> ujson.Arr.from(owner.method.id.l.map(_.toString)),
        "return_types" -> ujson.Arr.from(List(m.methodReturn.typeFullName)))
    }
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
      "wrapper_evidence" -> ujson.Arr.from(wrapperEvidence),
      "semantics" -> config("semantics"),
      "flows" -> ujson.Arr.from(flows.map(p => ujson.Arr.from(p.elements.map(node)))), "query_completed" -> true,
      "analysis_completeness" -> ujson.Obj("status" -> "unproven", "exhaustion_observable" -> false,
        "max_call_depth" -> context.config.maxCallDepth, "max_args_to_allow" -> context.config.maxArgsToAllow,
        "max_output_args_expansion" -> context.config.maxOutputArgsExpansion))
    Files.writeString(Paths.get(outputPath), ujson.write(result, indent=2))
  } catch {
    case error: IdentityIncomplete =>
      Files.writeString(Paths.get(outputPath), ujson.write(ujson.Obj("state" -> "incomplete", "identity_status" -> "incomplete", "error" -> error.toString, "query_completed" -> false),indent=2))
    case error: Throwable =>
      Files.writeString(Paths.get(outputPath), ujson.write(ujson.Obj("state" -> "runner-error", "error" -> error.toString),indent=2))
      throw error
  }
}
