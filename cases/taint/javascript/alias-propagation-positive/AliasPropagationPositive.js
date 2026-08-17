function dfb_source() { // DFB-SOURCE: alias-propagation-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: alias-propagation-sink

function run() {
  const original = { value: "clean" };
  const alias = original; // DFB-WITNESS: alias-propagation-alias
  const distinct = { value: "clean" };
  original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
  dfb_sink(alias.value);
}
