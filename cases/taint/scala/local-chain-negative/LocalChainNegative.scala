package dataflowbench

object LocalChainNegative {
  def dfb_source(): Int = { // DFB-SOURCE: local-chain-negative-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: local-chain-negative-sink

  def run(): Unit = {
    val first = dfb_source()
    val second = first // DFB-WITNESS: local-chain-negative-second
    val third = second // DFB-WITNESS: local-chain-negative-third
    dfb_sink(0)
  }
}
