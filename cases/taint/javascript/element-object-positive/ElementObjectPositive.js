function dfb_source() { // DFB-SOURCE: element-object-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: element-object-sink

function run() {
  const items = [{ value: "clean" }, { value: "clean" }];
  items[0].value = dfb_source(); // DFB-WITNESS: element-object-store
  dfb_sink(items[0].value);
}
