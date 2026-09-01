// DataFlowBench Joern warm-marginal batch script (Amendment A13).
//
// This script is **timing-tier auxiliary machinery only**. It never produces a
// correctness outcome, never writes a normalized report, and is not part of
// any scored population. `kernel.sc` remains the one script the kernel runners
// invoke, and its bytes are unchanged — every Joern report's
// `configuration_hash` is a digest over `kernel.sc` alone, so nothing here can
// touch a frozen number.
//
// What it does: import and query *k* cases sequentially inside ONE JVM, so the
// benchmark can observe the marginal wall-clock of one more case in a warm
// process instead of only the cold per-invocation cost. The runner spawns this
// script once per batch size and times the whole subprocess; the slope of
// batch wall-clock against k is the warm marginal cost.
//
// **This script deliberately emits no timestamps.** The latency tier's
// decomposition rule (docs/latency-tier.md) admits only adapter-observable
// subprocess boundaries and explicitly refuses "the benchmark's own script
// timestamping itself". Amendment A13 does not relax that: the only clock in
// the warm measurement is the runner's, around the whole batch subprocess.
//
// Per-case work is byte-identical to `kernel.sc`'s: the same import dispatch,
// the same two selectors, the same `reachableByFlows` call, and the same
// evidence document. A unit test (`joern_warm_batch_script_shares_the_kernel_
// query_block`) asserts the load-bearing block is character-for-character the
// same in both files, so the warm number can never drift into timing different
// work from the cold one.
//
// Each case gets its own Joern project name inside the shared workspace, so no
// case can observe another's CPG — the same isolation the cold runner gets
// from a fresh scratch directory per case.
//
// Invocation (see adapters/joern/README.md):
//
//   joern --script adapters/joern/queries/warm-batch.sc \
//     --param manifestPath=<tab-separated batch manifest> \
//     --param completionPath=<batch completion marker>
//
// Manifest: one case per line, tab-separated, in the order to be analyzed:
//
//   <caseId>\t<inputPath>\t<language>\t<sourceName>\t<sinkName>\t<outputPath>

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

@main def main(manifestPath: String, completionPath: String): Unit = {
  val lines = Files
    .readAllLines(Paths.get(manifestPath))
    .toArray(Array.empty[String])
    .toSeq
    .filter(_.nonEmpty)

  var analyzed = 0
  var failed = 0

  lines.zipWithIndex.foreach { case (line, index) =>
    val parts = line.split("\t", -1)
    val caseId = parts(0)
    val inputPath = parts(1)
    val language = parts(2)
    val sourceName = parts(3)
    val sinkName = parts(4)
    val outputPath = parts(5)
    // A per-case project name inside the one shared workspace: the warm
    // process's stand-in for the cold runner's per-case scratch directory. No
    // case can select another case's CPG through it.
    val projectName = s"dataflowbench-warm-$index"

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
      // The generic `importCode(language = ...)` dispatcher still has no entry
      // for Ruby in Joern 4.0.610: it raises "No CPG generator exists for
      // language: RUBYSRC" even though `rubysrc2cpg` ships in the distribution
      // and `importCode.ruby` reports itself as available. That was re-probed
      // against 4.0.610 rather than assumed, and the named frontend is still
      // the same generator reached by the same console, so Ruby stays
      // dispatched through it rather than left unanalyzable. Every other
      // language keeps the generic path unchanged — including Rust, whose
      // `RUST` identifier the generic dispatcher does accept.
      if (language == "RUBYSRC") {
        importCode.ruby(inputPath = inputPath, projectName = projectName)
      } else {
        importCode(inputPath = inputPath, projectName = projectName, language = language)
      }
      val sourceNodes = cpg.call.nameExact(sourceName).l
      // The positional arguments of the sink call. `argumentIndex > 0` drops the
      // implicit receiver that the JavaScript and Python frontends attach as
      // argument 0; it is not part of the benchmark's sink contract.
      val sinkNodes = cpg.call.nameExact(sinkName).argument.filter(_.argumentIndex > 0).l
      val flows = sinkNodes.reachableByFlows(sourceNodes).l
        val flowJson = flows.map { path =>
          jsonObject(Seq(jsonField("elements", jsonArray(path.elements.map(nodeJson)))))
        }
        analyzed += 1
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
          failed += 1
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
    // Release the project before the next import so a long batch's memory
    // profile stays comparable to the cold runner's one-CPG-per-process shape.
    scala.util.Try(close(projectName))
    scala.util.Try(delete(projectName))
    println(s"dataflowbench-joern-warm analyzed $caseId")
  }

  val completion = jsonObject(
    Seq(
      jsonField("adapter", jsonString("joern")),
      jsonField("evidence_kind", jsonString("joern-warm-batch-completion")),
      jsonField("requested", lines.size.toString),
      jsonField("analyzed", analyzed.toString),
      jsonField("failed", failed.toString)
    )
  )
  Files.write(Paths.get(completionPath), (completion + "\n").getBytes("UTF-8"))
  println(s"dataflowbench-joern-warm wrote $completionPath")
}
