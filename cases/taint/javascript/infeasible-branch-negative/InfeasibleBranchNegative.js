function dfb_source() { // DFB-SOURCE: infeasible-branch-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: infeasible-branch-sink

function run() {
  let value = "clean";
  if (false) {
    value = dfb_source(); // DFB-WITNESS: infeasible-tainted-branch
  }
  dfb_sink(value);
}
