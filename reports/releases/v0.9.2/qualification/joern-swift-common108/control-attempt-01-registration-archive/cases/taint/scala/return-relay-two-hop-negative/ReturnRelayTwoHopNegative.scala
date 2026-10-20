package dataflowbench

object ReturnRelayTwoHopNegative {
  def dfb_source(): Int = { // DFB-SOURCE: return-two-hop-negative-input
    1
  }

  def firstRelay(value: Int): Int = { // DFB-WITNESS: return-two-hop-negative-first
    value
  }

  def secondRelay(value: Int): Int = { // DFB-WITNESS: return-two-hop-negative-second
    firstRelay(value)
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: return-two-hop-negative-sink

  def run(): Unit = {
    val result = secondRelay(dfb_source())
    dfb_sink(0)
  }
}
