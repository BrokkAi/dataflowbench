object ListRemovalIndexShiftNegative {
    fun dfb_source(): Int { // DFB-SOURCE: list-removal-index-shift-input
        return System.getenv("DFB_INPUT").toInt()
    }

    fun dfb_sink(value: Int) { // DFB-SINK: list-removal-index-shift-sink
        println(value)
    }

    @JvmStatic
    fun main(args: Array<String>) {
        val values = mutableListOf<Int>()
        values.add(0)
        values.add(dfb_source())
        values.add(9)
        values.removeAt(0) // DFB-WITNESS: list-removal-index-shift-remove-first
        dfb_sink(values[1])
    }
}
