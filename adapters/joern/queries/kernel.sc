// DataFlowBench Joern kernel query.
//
// One script serves the Java, JavaScript, and Python kernels. Every canonical
// fixture declares its taint endpoints itself, so the query is parameterized by
// the two benchmark-controlled identifiers the runner reads out of the case's
// `DFB-SOURCE:` and `DFB-SINK:` marker lines rather than by a per-language
// model:
//
//   sources = calls to the declared source function (the returned value)
//   sinks   = the positional arguments of calls to the declared sink function
//
// and asks the OSS data-flow engine for `sinks.reachableByFlows(sources)`.
// There is no per-case, per-template, or per-polarity special casing: the same
// two selectors run for all 32 assertions of every language.
//
// The script always writes one JSON document to `outputPath`. That document is
// the adapter's retained raw evidence; the Rust runner reconciles its flow
// element locations against the case's own anchors and never rewrites it.
//
// Invocation (see adapters/joern/README.md):
//
//   joern --script adapters/joern/queries/kernel.sc \
//     --param inputPath=<workspace> \
//     --param language=<JAVASRC|JSSRC|PYTHONSRC> \
//     --param sourceName=<source function> \
//     --param sinkName=<sink function> \
//     --param outputPath=<raw evidence file>

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
    outputPath: String
): Unit = {
  val header = Seq(
    jsonField("adapter", jsonString("joern")),
    jsonField("evidence_kind", jsonString("joern-reachable-by-flows")),
    jsonField("input_path", jsonString(inputPath)),
    jsonField("frontend_language", jsonString(language)),
    jsonField("source_function", jsonString(sourceName)),
    jsonField("sink_function", jsonString(sinkName))
  )

  val document =
    try {
      importCode(inputPath = inputPath, projectName = "dataflowbench", language = language)
      val sourceNodes = cpg.call.nameExact(sourceName).l
      // The positional arguments of the sink call. `argumentIndex > 0` drops the
      // implicit receiver that the JavaScript and Python frontends attach as
      // argument 0; it is not part of the benchmark's sink contract.
      val sinkNodes = cpg.call.nameExact(sinkName).argument.filter(_.argumentIndex > 0).l
      val flows = sinkNodes.reachableByFlows(sourceNodes).l
      val flowJson = flows.map { path =>
        jsonObject(Seq(jsonField("elements", jsonArray(path.elements.map(nodeJson)))))
      }
      jsonObject(
        header ++ Seq(
          jsonField("state", jsonString("analyzed")),
          jsonField("method_count", cpg.method.size.toString),
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
        // A frontend or engine failure is retained as a runner error. It is
        // never allowed to look like an empty (negative) result set.
        jsonObject(
          header ++ Seq(
            jsonField("state", jsonString("runner-error")),
            jsonField("stage", jsonString("joern-script")),
            jsonField(
              "diagnostic",
              jsonString(s"${throwable.getClass.getName}: ${throwable.getMessage}")
            )
          )
        )
    }

  Files.write(Paths.get(outputPath), (document + "\n").getBytes("UTF-8"))
  println(s"dataflowbench-joern wrote $outputPath")
}
