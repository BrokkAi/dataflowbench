function dfb_source() { // DFB-SOURCE: local-overwrite-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: local-overwrite-sink

function run() {
  let value = dfb_source();
  value = value; // DFB-WITNESS: local-overwrite-preserved
  dfb_sink(value);
}
