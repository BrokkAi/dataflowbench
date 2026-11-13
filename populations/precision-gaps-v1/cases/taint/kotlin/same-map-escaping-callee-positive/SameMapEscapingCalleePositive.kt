object SameMapEscapingCalleePositive {
    fun dfb_source(): String { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303"
    }
    fun dfb_sink(value: String) { println(value) } // DFB-SINK: issue303-sink
    fun write_source(values: MutableMap<String, String>) {
        values["payload"] = dfb_source() // DFB-WITNESS: issue303-callee-store
    }
    fun run(args: Array<String>) {
        val values = mutableMapOf("payload" to "clean")
        write_source(values); // DFB-WITNESS: issue303-invoke
        dfb_sink(values.getValue("payload")) // DFB-WITNESS: issue303-read
    }
    @JvmStatic fun main(args: Array<String>) { run(args) }
}
