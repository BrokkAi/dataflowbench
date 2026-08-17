function dfb_source() { // DFB-SOURCE: return-two-hop-negative-input
  return "tainted";
}

function firstRelay(value) { // DFB-WITNESS: return-two-hop-negative-first
  return value;
}

function secondRelay(value) { // DFB-WITNESS: return-two-hop-negative-second
  return firstRelay(value);
}

function dfb_sink(value) {} // DFB-SINK: return-two-hop-negative-sink

function run() {
  const result = secondRelay(dfb_source());
  dfb_sink("clean");
}
