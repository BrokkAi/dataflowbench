function dfb_source() { // DFB-SOURCE: branch-join-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: branch-join-sink

function run(overwrite) {
  let value = dfb_source();
  if (overwrite) {
    value = "clean";
  } else {
    value = "clean";
  }
  // DFB-WITNESS: branch-join-value
  dfb_sink(value);
}
