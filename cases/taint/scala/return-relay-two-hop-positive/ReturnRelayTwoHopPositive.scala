package dataflowbench

object ReturnRelayTwoHopPositive {
  def dfb_source(): Int = { // DFB-SOURCE: return-two-hop-input
    1
  }

  def firstRelay(value: Int): Int = { // DFB-WITNESS: return-two-hop-first
    value
  }

  def secondRelay(value: Int): Int = { // DFB-WITNESS: return-two-hop-second
    firstRelay(value)
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: return-two-hop-sink

  def run(): Unit = {
    val result = secondRelay(dfb_source())
    dfb_sink(result)
  }
}
