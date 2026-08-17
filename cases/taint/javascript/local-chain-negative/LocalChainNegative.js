function dfb_source() { // DFB-SOURCE: local-chain-negative-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: local-chain-negative-sink

function run() {
  const first = dfb_source();
  const second = first; // DFB-WITNESS: local-chain-negative-second
  const third = second; // DFB-WITNESS: local-chain-negative-third
  dfb_sink("clean");
}
