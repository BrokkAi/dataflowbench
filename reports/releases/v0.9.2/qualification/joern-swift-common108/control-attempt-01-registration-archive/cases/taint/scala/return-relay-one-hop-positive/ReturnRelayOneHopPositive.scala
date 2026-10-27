package dataflowbench

object ReturnRelayOneHopPositive {
  def dfb_source(): Int = { // DFB-SOURCE: return-one-hop-input
    1
  }

  def relay(value: Int): Int = { // DFB-WITNESS: return-one-hop-relay
    value
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: return-one-hop-sink

  def run(): Unit = {
    val result = relay(dfb_source())
    dfb_sink(result)
  }
}
