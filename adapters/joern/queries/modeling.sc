// DataFlowBench Joern taint-modeling query.
//
// The sibling `kernel.sc` supplies no semantics at all, which is exactly right
// for the propagation kernels: they ask whether the engine can follow flow it
// can see. This script asks the other question — whether the engine can be told
// things — so it does the one thing the kernel script must never do: it loads
// a benchmark-supplied flow-semantics file and runs the OSS data-flow engine
// under it.
//
// `docs/modeling-matrix.md` fixes what is declared; this file is only how Joern
// is told it. The declarations themselves live in
// `adapters/joern/semantics/model-<language>.semantics`, in the distribution's
// own textual `FullNameSemanticsParser` format, and both files are hash-bound
// into the report's `configuration_hash`.
//
// Two selector shapes, decided by the runner from the case's *template
// identity* and never from an observed result:
//
//   sourceKind=call-return      sources are calls to the declared source
//                               function — categories S, P, Z, O, and B, whose
//                               source is a call whose returned value is
//                               tainted.
//   sourceKind=method-parameter sources are the first declared parameter of the
//                               declared handler method — category E, whose
//                               whole point is that the fixture never calls it,
//                               so there is no call site to select. Joern's
//                               `reachableByFlows` takes arbitrary CPG nodes as
//                               sources, so a parameter of an uncalled method
//                               is a valid analysis root; selectivity is this
//                               script's own `nameExact` predicate, which is
//                               what template 10 measures.
//
// Sinks are the positional arguments of calls to the declared sink function, as
// in the kernel script. `argumentIndex > 0` drops the receiver the Python and
// JavaScript frontends attach as argument 0.
//
// The script always writes one JSON document to `outputPath`; the Rust runner
// reconciles its flow element locations against the case's own anchors and
// never rewrites it.
//
// Invocation (see adapters/joern/README.md):
//
//   joern --script adapters/joern/queries/modeling.sc \
//     --param inputPath=<workspace> \
//     --param language=<JAVASRC|JSSRC|PYTHONSRC> \
//     --param sourceName=<declared source function or handler method> \
//     --param sinkName=<declared sink function> \
//     --param sourceKind=<call-return|method-parameter> \
//     --param semanticsPath=<flow-semantics file> \
//     --param outputPath=<raw evidence file>

import io.joern.dataflowengineoss.DefaultSemantics
import io.joern.dataflowengineoss.queryengine.EngineContext
import io.joern.dataflowengineoss.semanticsloader.{FullNameSemanticsParser, Semantics}

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

@main def main(
    inputPath: String,
    language: String,
    sourceName: String,
    sinkName: String,
    sourceKind: String,
    semanticsPath: String,
    outputPath: String
): Unit = {
  val header = Seq(
    jsonField("adapter", jsonString("joern")),
    jsonField("evidence_kind", jsonString("joern-modeled-reachable-by-flows")),
    jsonField("input_path", jsonString(inputPath)),
    jsonField("frontend_language", jsonString(language)),
    jsonField("source_function", jsonString(sourceName)),
    jsonField("sink_function", jsonString(sinkName)),
    jsonField("source_kind", jsonString(sourceKind)),
    jsonField("semantics_path", jsonString(semanticsPath))
  )

  val document =
    try {
      // The benchmark's declarations are layered *on top of* the distribution's
      // own operator and standard-library flows rather than replacing them:
      // dropping `<operator>.assignment` would break propagation the modeling
      // matrix is not measuring, and every cell would fail for a reason that
      // has nothing to do with the model.
      val declared = new FullNameSemanticsParser().parseFile(semanticsPath)
      // The pinned parser fails *silently*: a semantics file with a blank line
      // in it, or one commented with `//`, yields an empty declaration list and
      // no error, and every scored cell would then be decided by the absence of
      // a model rather than by the model. A missing model is a benchmark defect
      // and never a result, so an empty parse is raised here and retained as a
      // runner error rather than answered.
      if (declared.isEmpty) {
        throw new IllegalStateException(
          s"$semanticsPath parsed to zero declarations; the pinned FullNameSemanticsParser " +
            "drops every entry on a blank line or a `//` comment, and a scored cell with no " +
            "declaration behind it is a benchmark defect rather than an outcome"
        )
      }
      val semantics: Semantics = DefaultSemantics().plus(declared)
      implicit val context: EngineContext = EngineContext(semantics)

      importCode(inputPath = inputPath, projectName = "dataflowbench", language = language)

      val sourceNodes = sourceKind match {
        case "call-return" => cpg.call.nameExact(sourceName).l
        // Joern counts the receiver as parameter 0, so the declaration's
        // position 0 — the first *declared* parameter — is index 1.
        case "method-parameter" => cpg.method.nameExact(sourceName).parameter.index(1).l
        case other => throw new IllegalArgumentException(s"unknown sourceKind: $other")
      }
      val sinkNodes = cpg.call.nameExact(sinkName).argument.filter(_.argumentIndex > 0).l
      val flows = sinkNodes.reachableByFlows(sourceNodes).l
      val flowJson = flows.map { path =>
        jsonObject(Seq(jsonField("elements", jsonArray(path.elements.map(nodeJson)))))
      }
      jsonObject(
        header ++ Seq(
          jsonField("state", jsonString("analyzed")),
          jsonField("method_count", cpg.method.size.toString),
          jsonField("declared_semantic_count", declared.size.toString),
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
