package dataflowbench

func dfb_source() string { // DFB-SOURCE: deep-relay-chain-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: deep-relay-chain-sink

func relay6(value string) { // DFB-WITNESS: deep-relay-chain-hop-six
	dfb_sink(value)
}

func relay5(value string) {
	relay6(value)
}

func relay4(value string) {
	relay5(value)
}

func relay3(value string) {
	relay4(value)
}

func relay2(value string) {
	relay3(value)
}

func relay1(value string) { // DFB-WITNESS: deep-relay-chain-hop-one
	relay2(value)
}

func run() {
	tainted := dfb_source()
	_ = tainted
	relay1("clean")
}
