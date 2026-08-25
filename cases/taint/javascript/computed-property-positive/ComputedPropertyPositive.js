function dfb_source() { // DFB-SOURCE: computed-property-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: computed-property-sink

function run() {
  const key = "payload";
  const holder = { payload: "clean", other: "clean" };
  holder[key] = dfb_source(); // DFB-WITNESS: computed-property-store
  dfb_sink(holder[key]);
}
