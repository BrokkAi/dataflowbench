package dataflowbench

object DeepRelayChainPositive {
  def dfb_source(): String = { // DFB-SOURCE: deep-relay-chain-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: deep-relay-chain-sink

  def relay1(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop1
    relay2(value)
  }

  def relay2(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop2
    relay3(value)
  }

  def relay3(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop3
    relay4(value)
  }

  def relay4(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop4
    relay5(value)
  }

  def relay5(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop5
    relay6(value)
  }

  def relay6(value: String): String = { // DFB-WITNESS: deep-relay-chain-hop6
    value
  }

  def run(): Unit = {
    dfb_sink(relay1(dfb_source()))
  }
}
