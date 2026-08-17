function dfb_source() { // DFB-SOURCE: array-element-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: array-element-sink

function run() {
  const values = ["clean", "clean"];
  values[0] = dfb_source(); // DFB-WITNESS: array-element-store
  values[1] = "clean";
  dfb_sink(values[1]);
}
