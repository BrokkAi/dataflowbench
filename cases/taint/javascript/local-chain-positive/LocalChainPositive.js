function dfb_source() { // DFB-SOURCE: local-chain-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: local-chain-sink

function run() {
  const first = dfb_source();
  const second = first; // DFB-WITNESS: local-chain-second
  const third = second; // DFB-WITNESS: local-chain-third
  dfb_sink(third);
}
