package dataflowbench

object ElementObjectPositive {
    class Item {
        var value: String = "clean"
    }

    fun dfb_source(): String { // DFB-SOURCE: element-object-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: element-object-sink

    fun run() {
        val items = arrayOf(Item(), Item())
        items[0].value = dfb_source() // DFB-WITNESS: element-object-store
        items[1].value = "clean"
        dfb_sink(items[0].value)
    }
}
