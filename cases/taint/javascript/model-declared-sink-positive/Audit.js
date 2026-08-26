function dfb_source() { // DFB-SOURCE: model-declared-sink-input
  return "tainted";
}

const Audit = {
  record: function record(value) {}, // DFB-SINK: model-declared-sink-sink
  discard: function discard(value) {}
};

function run() {
  Audit.record(dfb_source());
  Audit.discard("clean");
}
