function dfb_source() { // DFB-SOURCE: deep-relay-chain-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: deep-relay-chain-sink

function relay6(value) { // DFB-WITNESS: deep-relay-chain-hop-six
  dfb_sink(value);
}

function relay5(value) {
  relay6(value);
}

function relay4(value) {
  relay5(value);
}

function relay3(value) {
  relay4(value);
}

function relay2(value) {
  relay3(value);
}

function relay1(value) { // DFB-WITNESS: deep-relay-chain-hop-one
  relay2(value);
}

function run() {
  relay1(dfb_source());
}
