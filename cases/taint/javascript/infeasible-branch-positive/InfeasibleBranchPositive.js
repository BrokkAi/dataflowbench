function dfb_source() { // DFB-SOURCE: infeasible-branch-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: infeasible-branch-sink

function run() {
  let value = "clean";
  if (true) {
    value = dfb_source(); // DFB-WITNESS: feasible-tainted-branch
  }
  dfb_sink(value);
}
