object ConstantStringSelectorPositive {
    def dfb_source(): String = "source-one" // DFB-SOURCE: constant-selector-input

    def dfb_sink(value: String): Unit = println(value) // DFB-SINK: constant-selector-sink

    def main(args: Array[String]): Unit = {
        val value = "ABC".charAt(2) match {
            case 'C' => dfb_source() // DFB-WITNESS: constant-selector-source-arm
            case 'B' => "safe"
            case _ => "safe"
        }
        dfb_sink(value)
    }
}
