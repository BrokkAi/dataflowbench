function dfb_source() { // DFB-SOURCE: call-context-input
  return "tainted";
}

function relay(value) { // DFB-WITNESS: call-context-relay
  return value;
}

function dfb_sink(value) {} // DFB-SINK: call-context-sink

function run() {
  const tainted = relay(dfb_source());
  const clean = relay("clean");
  dfb_sink(tainted);
}
