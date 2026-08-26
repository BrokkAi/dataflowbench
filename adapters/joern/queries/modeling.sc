// DataFlowBench Joern taint-modeling query.
//
// The kernel script (adapters/joern/queries/kernel.sc) is untouched by the
// modeling matrix: it supplies no semantics, and it reads its two endpoint
// identifiers out of each case's own DFB markers. This script is the opposite
// by construction. The modeling matrix scores whether an engine can *be told
// things*, so the endpoints and the flow semantics here come from the
// benchmark's model declarations, never from the case's anchors — an anchored
// endpoint would make every category-S negative pass for a reason that has
// nothing to do with the declaration.
//
// Together with adapters/joern/semantics/model-<language>.semantics, this file
// is the whole of Joern's declaration surface for
// docs/modeling-matrix.md#the-equivalence-contract. Both files are hash-bound
// into every modeling report's `configuration_hash`.
//
// What is declared here, in the document's own vocabulary:
//
//   source      Config.fetchRemote  out: return          (template 1)
//   source      dfb_source          out: return          (the benchmark input)
//   sink        Audit.record        in: 0                (template 2)
//   sink        dfb_sink            in: 0                (the benchmark sink)
//   entry-point Handler.onRequest   in: 0 on entry       (template 9)
//   entry-point Handler.onDeclared  in: 0 on entry       (template 10)
//
// and the propagator, sanitizer, summary, and persistence declarations of
// categories P, Z, O, and B come from the semantics file.
//
// There is no per-case, per-template, or per-polarity branching: the same
// declaration set runs for all twenty-four assertions, and each fixture simply
// contains only the entities its own template names. An undeclared sibling —
// `fetchLocal`, `discard`, `sanitize`, `onIgnored`, `onUndeclared` — is absent
// from every list above, which is what the negatives measure.
//
// Invocation (see adapters/joern/README.md):
//
//   joern --script adapters/joern/queries/modeling.sc \
//     --param inputPath=<workspace> \
//     --param language=<JSSRC|JAVASRC|PYTHONSRC> \
//     --param semanticsPath=<adapters/joern/semantics/model-<lang>.semantics> \
//     --param outputPath=<raw evidence file>

import io.joern.dataflowengineoss.DefaultSemantics
import io.joern.dataflowengineoss.queryengine.EngineContext
import io.joern.dataflowengineoss.semanticsloader.{FlowPath, FlowSemantic, FullNameSemantics}

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

/** The benchmark-declared source APIs whose return value is tainted. */
val declaredSourceMembers = Set("dfb_source", "fetchRemote")

/** The benchmark-declared sink APIs whose argument position 0 is dangerous. */
val declaredSinkMembers = Set("dfb_sink", "record")

/** The benchmark-declared entry points whose parameter 0 is tainted on entry. */
val declaredEntryPointMembers = Set("onRequest", "onDeclared")

/** One line of the committed semantics file, as a `FlowSemantic`.
  *
  * The file is Joern's textual flow-semantics syntax — `"<entity>" s->d ...`,
  * receiver 0, parameters from 1, return value -1 — keyed by the declared
  * member name. It is re-keyed here onto a regex over the frontend's own
  * method full names, because a frontend may name a member by an inferred
  * structural type that says nothing about the entity being declared. Blank
  * lines and `#` comments are ignored.
  */
def parseSemanticsLine(line: String): Option[FlowSemantic] = {
  val trimmed = line.trim
  if (trimmed.isEmpty || trimmed.startsWith("#")) return None
  if (!trimmed.startsWith("\"")) throw new IllegalArgumentException(s"semantics line does not open with a quoted entity: $line")
  val closing = trimmed.indexOf('"', 1)
  if (closing < 0) throw new IllegalArgumentException(s"semantics line has an unterminated entity: $line")
  val member = trimmed.substring(1, closing)
  val mappings = trimmed
    .substring(closing + 1)
    .split("\\s+")
    .filter(_.nonEmpty)
    .map { mapping =>
      mapping.split("->") match {
        case Array(src, dst) => FlowPath.FlowMapping(src.trim.toInt, dst.trim.toInt)
        case _ => throw new IllegalArgumentException(s"semantics mapping is not <src>-><dst>: $mapping")
      }
    }
    .toList
  // A member name is matched as the tail of a method full name, after the
  // frontend's own separator. An entry with no mappings is `NilSemantics`.
  Some(FlowSemantic(".*[.:]" + java.util.regex.Pattern.quote(member) + "$", mappings, regex = true))
}

@main def main(
    inputPath: String,
    language: String,
    semanticsPath: String,
    outputPath: String
): Unit = {
  val header = Seq(
    jsonField("adapter", jsonString("joern")),
    jsonField("evidence_kind", jsonString("joern-modeling-reachable-by-flows")),
    jsonField("input_path", jsonString(inputPath)),
    jsonField("frontend_language", jsonString(language)),
    jsonField("semantics_path", jsonString(semanticsPath)),
    jsonField("declared_sources", jsonArray(declaredSourceMembers.toSeq.sorted.map(jsonString))),
    jsonField("declared_sinks", jsonArray(declaredSinkMembers.toSeq.sorted.map(jsonString))),
    jsonField(
      "declared_entry_points",
      jsonArray(declaredEntryPointMembers.toSeq.sorted.map(jsonString))
    )
  )

  val document =
    try {
      val declared = scala.io.Source
        .fromFile(semanticsPath, "UTF-8")
        .getLines()
        .flatMap(parseSemanticsLine)
        .toList
      importCode(inputPath = inputPath, projectName = "dataflowbench", language = language)
      // The engine's own operator flows stay in place — without them nothing
      // propagates through an assignment — and the benchmark's declarations are
      // layered on top of them. Nothing else is supplied: no language model
      // catalog, no framework semantics.
      val semantics = FullNameSemantics.fromList(DefaultSemantics.operatorFlows ++ declared)
      semantics.initialize(cpg)
      implicit val context: EngineContext = EngineContext(semantics)

      val declaredSourceCalls = cpg.call.filter(call => declaredSourceMembers.contains(call.name)).l
      // An entry-point declaration is a synthesized analysis root: parameter 0
      // of the declared member, whether or not any call site reaches it.
      // `index(1)` is Joern's spelling of the first declared parameter, since
      // it counts the receiver as 0.
      val declaredEntryParameters =
        cpg.method.filter(method => declaredEntryPointMembers.contains(method.name)).parameter.index(1).l
      val sourceNodes = declaredSourceCalls ++ declaredEntryParameters
      // The positional arguments of a declared sink call. `argumentIndex > 0`
      // drops the implicit receiver the JavaScript and Python frontends attach
      // as argument 0; it is not part of the declaration's `in: 0`.
      val sinkNodes =
        cpg.call.filter(call => declaredSinkMembers.contains(call.name)).argument.filter(_.argumentIndex > 0).l
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
        // A frontend, semantics, or engine failure is retained as a runner
        // error. It is never allowed to look like an empty (negative) result.
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
