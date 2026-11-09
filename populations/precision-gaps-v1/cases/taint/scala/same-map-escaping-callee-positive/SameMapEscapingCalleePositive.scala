import scala.collection.mutable
object SameMapEscapingCalleePositive {
    def dfb_source(): String = { // DFB-SOURCE: issue303-source
        "DFB_SOURCE_303"
    }
    def dfb_sink(value: String): Unit = println(value) // DFB-SINK: issue303-sink
    def write_source(values: mutable.Map[String, String]): Unit = {
        values.update("payload", dfb_source()) // DFB-WITNESS: issue303-callee-store
    }
    def run(args: Array[String]): Unit = {
        val values = mutable.Map("payload" -> "clean")
        write_source(values); // DFB-WITNESS: issue303-invoke
        dfb_sink(values("payload")) // DFB-WITNESS: issue303-read
    }
    def main(args: Array[String]): Unit = run(args)
}
