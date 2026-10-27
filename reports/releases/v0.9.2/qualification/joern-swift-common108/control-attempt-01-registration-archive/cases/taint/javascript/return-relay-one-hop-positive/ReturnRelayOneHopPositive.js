function dfb_source() { // DFB-SOURCE: return-one-hop-input
  return "tainted";
}

function relay(value) { // DFB-WITNESS: return-one-hop-relay
  return value;
}

function dfb_sink(value) {} // DFB-SINK: return-one-hop-sink

function run() {
  const result = relay(dfb_source());
  dfb_sink(result);
}
