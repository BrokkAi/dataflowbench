package dataflowbench

object LocalChainPositive {
  def dfb_source(): Int = { // DFB-SOURCE: local-chain-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: local-chain-sink

  def run(): Unit = {
    val first = dfb_source()
    val second = first // DFB-WITNESS: local-chain-second
    val third = second // DFB-WITNESS: local-chain-third
    dfb_sink(third)
  }
}
