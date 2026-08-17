function dfb_source() { // DFB-SOURCE: object-separation-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: object-separation-sink

function run() {
  const tainted = { value: 0 };
  const clean = { value: 0 };
  tainted.value = dfb_source(); // DFB-WITNESS: object-separation-store
  clean.value = "clean";
  dfb_sink(tainted.value);
}
