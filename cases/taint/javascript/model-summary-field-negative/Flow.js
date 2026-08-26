function dfb_source() { // DFB-SOURCE: model-summary-field-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-summary-field-sink

function run() {
  const box = { payload: "", spare: "" };
  Bridge.deposit(dfb_source(), box);
  dfb_sink(box.spare);
}
