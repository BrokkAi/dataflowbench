import java.nio.file.{Files, Paths}
import io.shiftleft.codepropertygraph.generated.nodes.*
@main def main(cpgPath: String, outputPath: String): Unit = {
 importCpg(cpgPath)
 def props(n: StoredNode): ujson.Value = ujson.Obj.from(n.properties.toSeq.map { case (k,v) => (k,ujson.Str(v.toString)) })
 def ids(ns: Iterator[StoredNode]): ujson.Value = ujson.Arr.from(ns.map(_.id.toString))
 val nodes = cpg.graph.allNodes.collect { case n: StoredNode => n }.toList
 val result = ujson.Obj("scope" -> "native graph identity diagnostic; no selected sources or sinks", "nodes" -> ujson.Arr.from(nodes.map(n => ujson.Obj(
  "id" -> n.id.toString, "label" -> n.label, "properties" -> props(n),
  "ref" -> ids(n._refOut), "call" -> ids(n._callOut), "ast" -> ids(n._astOut),
  "receiver" -> ids(n._receiverOut), "evalType" -> ids(n._evalTypeOut), "binds" -> ids(n._bindsOut)
 ))))
 Files.writeString(Paths.get(outputPath), ujson.write(result, indent=2))
}
