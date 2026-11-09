object SameMapComputedKeyNegative {
    fun dfb_source(): String { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303"
    }
    fun dfb_sink(value: String) { println(value) } // DFB-SINK: issue303-sink
    fun run(args: Array<String>) {
        val suffix = args.firstOrNull() ?: "payload"
        val key = "private:" + suffix
        val values = mutableMapOf("payload" to "clean")
        values[key] = dfb_source() // DFB-WITNESS: issue303-store
        dfb_sink(values.getValue("payload")) // DFB-WITNESS: issue303-read
    }
    @JvmStatic fun main(args: Array<String>) { run(args) }
}
