import scala.collection.mutable
object SameMapConstantKeysNegative {
    def dfb_source(): String = { // DFB-SOURCE: issue303-source
        "DFB_SOURCE_303"
    }
    def dfb_sink(value: String): Unit = println(value) // DFB-SINK: issue303-sink
    def run(args: Array[String]): Unit = {
        val values = mutable.Map("payload" -> "clean", "tainted" -> "clean")
        values.update("tainted", dfb_source()) // DFB-WITNESS: issue303-store
        dfb_sink(values("payload")) // DFB-WITNESS: issue303-read
    }
    def main(args: Array[String]): Unit = run(args)
}
