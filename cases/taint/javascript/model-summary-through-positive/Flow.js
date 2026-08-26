function dfb_source() { // DFB-SOURCE: model-summary-through-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-summary-through-sink

function run() {
  dfb_sink(Bridge.pass(dfb_source()));
}
