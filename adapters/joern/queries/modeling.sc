// DataFlowBench Joern taint-modeling query.
//
// One script serves every language's modeling matrix, the way `kernel.sc`
// serves every language's propagation kernel. It is a *separate* script on
// purpose: the kernel script supplies no semantics and no engine
// configuration, and docs/modeling-matrix.md requires that to stay true, so
// the modeling declarations land here rather than in the kernel's file.
//
// The declarations this script carries are the ones whose native Joern surface
// is a query root — the `source`, `sink`, and `entry-point` roles. The
// `propagator`, `sanitizer`, and `summary` roles, plus the two persistence
// roles, are carried by the per-language flow-semantics file passed as
// `semanticsPath`; both files are hash-bound into the report.
//
// Identity binding. The model declaration language binds by a type-plus-member
// triple. Every modeling fixture gives each declared member a name that occurs
// once in its own fixture — `fetchRemote` beside `fetchLocal`, `record` beside
// `discard`, `onRequest` beside `onIgnored` — so selecting by member name here
// resolves exactly the declared entity and never its undeclared sibling. The
// flow-semantics file, which has to discriminate between fixtures of different
// languages inside one artifact, binds by full method name instead.
//
// Invocation (see adapters/joern/README.md):
//
//   joern --script adapters/joern/queries/modeling.sc \
//     --param inputPath=<workspace> \
//     --param language=<JAVASRC|JSSRC|PYTHONSRC> \
//     --param semanticsPath=<adapters/joern/semantics/model-<language>.semantics> \
//     --param outputPath=<raw evidence file>

import io.joern.dataflowengineoss.queryengine.{EngineConfig, EngineContext}
import io.joern.dataflowengineoss.semanticsloader.{FullNameSemantics, FullNameSemanticsParser}
import java.nio.file.{Files, Paths}

def jsonString(value: String): String = {
  val out = new StringBuilder("\"")
  value.foreach {
    case '"'  => out ++= "\\\""
    case '\\' => out ++= "\\\\"
    case '\n' => out ++= "\\n"
    case '\r' => out ++= "\\r"
    case '\t' => out ++= "\\t"
    case c if c.isControl => out ++= f"\\u${c.toInt}%04x"
    case c    => out += c
  }
  out ++= "\""
  out.toString
}

def jsonArray(items: Seq[String]): String = items.mkString("[", ",", "]")

def jsonField(name: String, value: String): String = jsonString(name) + ":" + value

def jsonObject(fields: Seq[String]): String = fields.mkString("{", ",", "}")

/** One CPG node rendered as retained location evidence. */
def nodeJson(node: io.shiftleft.codepropertygraph.generated.nodes.AstNode): String = {
  val file = scala.util.Try(node.location.filename).getOrElse("<unknown>")
  val line = node.lineNumber.map(_.toString).getOrElse("null")
  val method = scala.util.Try(node.location.methodFullName).getOrElse("<unknown>")
  jsonObject(
    Seq(
      jsonField("label", jsonString(node.label)),
      jsonField("file", jsonString(file)),
      jsonField("line", line),
      jsonField("method", jsonString(method)),
      jsonField("code", jsonString(node.code))
    )
  )
}

/** Members the matrix declares as sources, by the doc's own entity names. */
val declaredSourceCalls = Seq("dfb_source", "fetchRemote")

/** Members the matrix declares as sinks. */
val declaredSinkCalls = Seq("dfb_sink", "record")

/** Members the matrix declares as entry points, with parameter 0 tainted. */
val declaredEntryPoints = Seq("onRequest", "onDeclared")

@main def main(
    inputPath: String,
    language: String,
    semanticsPath: String,
    outputPath: String
): Unit = {
  val header = Seq(
    jsonField("adapter", jsonString("joern")),
    jsonField("evidence_kind", jsonString("joern-reachable-by-flows")),
    jsonField("input_path", jsonString(inputPath)),
    jsonField("frontend_language", jsonString(language)),
    jsonField("semantics_path", jsonString(semanticsPath)),
    jsonField("source_function", jsonString(declaredSourceCalls.mkString("|"))),
    jsonField("sink_function", jsonString(declaredSinkCalls.mkString("|")))
  )

  val document =
    try {
      importCode(inputPath = inputPath, projectName = "dataflowbench", language = language)

      // The benchmark-supplied propagator, sanitizer, summary, and persistence
      // declarations, loaded into the engine as flow semantics. Nothing else
      // is configured: no default catalog is added on top, so an entity with
      // no entry here is one the benchmark did not declare.
      val declared = new FullNameSemanticsParser().parseFile(semanticsPath)
      implicit val context: EngineContext =
        EngineContext(FullNameSemantics.fromList(declared), EngineConfig())

      val sourceCalls = cpg.call.nameExact(declaredSourceCalls: _*).l
      val entryParameters =
        cpg.method.nameExact(declaredEntryPoints: _*).parameter.index(1).l
      val sourceNodes = sourceCalls ++ entryParameters
      // The positional arguments of a declared sink call. `argumentIndex > 0`
      // drops the implicit receiver the JavaScript and Python frontends attach
      // as argument 0; it is not part of any declared sink's bound position.
      val sinkNodes =
        cpg.call.nameExact(declaredSinkCalls: _*).argument.filter(_.argumentIndex > 0).l
      val flows = sinkNodes.reachableByFlows(sourceNodes).l
      val flowJson = flows.map { path =>
        jsonObject(Seq(jsonField("elements", jsonArray(path.elements.map(nodeJson)))))
      }
      jsonObject(
        header ++ Seq(
          jsonField("state", jsonString("analyzed")),
          jsonField("method_count", cpg.method.size.toString),
          jsonField("declared_semantics_count", declared.size.toString),
          jsonField("source_node_count", sourceNodes.size.toString),
          jsonField("sink_node_count", sinkNodes.size.toString),
          jsonField("source_nodes", jsonArray(sourceNodes.map(nodeJson))),
          jsonField("sink_nodes", jsonArray(sinkNodes.map(nodeJson))),
          jsonField("flow_count", flows.size.toString),
          jsonField("flows", jsonArray(flowJson))
        )
      )
    } catch {
      case throwable: Throwable =>
        // A frontend, semantics-loader, or engine failure is retained as a
        // runner error. It is never allowed to look like an empty (negative)
        // result set.
        jsonObject(
          header ++ Seq(
            jsonField("state", jsonString("runner-error")),
            jsonField("stage", jsonString("joern-modeling-script")),
            jsonField(
              "diagnostic",
              jsonString(s"${throwable.getClass.getName}: ${throwable.getMessage}")
            )
          )
        )
    }

  Files.write(Paths.get(outputPath), (document + "\n").getBytes("UTF-8"))
  println(s"dataflowbench-joern-modeling wrote $outputPath")
}
