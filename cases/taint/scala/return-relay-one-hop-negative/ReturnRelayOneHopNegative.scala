package dataflowbench

object ReturnRelayOneHopNegative {
  def dfb_source(): Int = { // DFB-SOURCE: return-one-hop-negative-input
    1
  }

  def relay(value: Int): Int = { // DFB-WITNESS: return-one-hop-negative-relay
    value
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: return-one-hop-negative-sink

  def run(): Unit = {
    val result = relay(dfb_source())
    dfb_sink(0)
  }
}
