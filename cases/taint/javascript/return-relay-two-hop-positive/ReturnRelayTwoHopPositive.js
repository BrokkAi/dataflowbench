function dfb_source() { // DFB-SOURCE: return-two-hop-input
  return "tainted";
}

function firstRelay(value) { // DFB-WITNESS: return-two-hop-first
  return value;
}

function secondRelay(value) { // DFB-WITNESS: return-two-hop-second
  return firstRelay(value);
}

function dfb_sink(value) {} // DFB-SINK: return-two-hop-sink

function run() {
  const result = secondRelay(dfb_source());
  dfb_sink(result);
}
