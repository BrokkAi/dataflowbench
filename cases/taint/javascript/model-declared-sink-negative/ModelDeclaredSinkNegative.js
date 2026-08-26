function dfb_source() { // DFB-SOURCE: model-declared-sink-input
  return "tainted";
}

const Audit = {
  record: function record(value) {},
  discard: function discard(value) {} // DFB-SINK: model-declared-sink-sink
};

function run() {
  Audit.discard(dfb_source());
}
