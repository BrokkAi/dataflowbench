function dfb_source() { // DFB-SOURCE: map-iteration-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: map-iteration-sink

function run() {
  const carrier = { payload: "clean" };
  const other = { payload: "clean" };
  carrier.payload = dfb_source(); // DFB-WITNESS: map-iteration-store
  for (const [key, value] of Object.entries(carrier)) {
    dfb_sink(value);
  }
}
