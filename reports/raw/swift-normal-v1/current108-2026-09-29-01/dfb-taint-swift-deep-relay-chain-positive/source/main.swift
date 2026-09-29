func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func relay1(_ value: Int) -> Int { relay2(value) } // DFB-WITNESS: deep-relay-chain-hop1
func relay2(_ value: Int) -> Int { relay3(value) } // DFB-WITNESS: deep-relay-chain-hop2
func relay3(_ value: Int) -> Int { relay4(value) } // DFB-WITNESS: deep-relay-chain-hop3
func relay4(_ value: Int) -> Int { relay5(value) } // DFB-WITNESS: deep-relay-chain-hop4
func relay5(_ value: Int) -> Int { relay6(value) } // DFB-WITNESS: deep-relay-chain-hop5
func relay6(_ value: Int) -> Int { value } // DFB-WITNESS: deep-relay-chain-hop6
let input = dfb_source() // DFB-SOURCE: deep-relay-chain-input
let output = relay1(input)
dfb_sink(output) // DFB-SINK: deep-relay-chain-sink
