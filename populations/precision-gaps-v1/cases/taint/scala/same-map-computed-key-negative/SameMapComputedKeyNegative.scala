import scala.collection.mutable
object SameMapComputedKeyNegative {
    def dfb_source(): String = { // DFB-SOURCE: issue303-source
        "DFB_SOURCE_303"
    }
    def dfb_sink(value: String): Unit = println(value) // DFB-SINK: issue303-sink
    def run(args: Array[String]): Unit = {
        val suffix = args.headOption.getOrElse("payload")
        val key = "private:" + suffix
        val values = mutable.Map("payload" -> "clean")
        values.update(key, dfb_source()) // DFB-WITNESS: issue303-store
        dfb_sink(values("payload")) // DFB-WITNESS: issue303-read
    }
    def main(args: Array[String]): Unit = run(args)
}
