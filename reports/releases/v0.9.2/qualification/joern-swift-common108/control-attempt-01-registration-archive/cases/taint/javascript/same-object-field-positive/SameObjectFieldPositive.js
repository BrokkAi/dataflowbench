function dfb_source() { // DFB-SOURCE: same-object-field-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: same-object-field-sink

function run() {
  const holder = { tainted: "clean", clean: "clean" };
  holder.tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
  holder.clean = "clean";
  dfb_sink(holder.tainted);
}
