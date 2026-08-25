function dfb_source() { // DFB-SOURCE: nested-access-path-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: nested-access-path-sink

function run() {
  const a = { b: { c: { value: "clean", other: "clean" } } };
  a.b.c.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
  dfb_sink(a.b.c.other);
}
