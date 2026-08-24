function dfb_source(): string { // DFB-SOURCE: infeasible-branch-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: infeasible-branch-sink

function run(): void {
  let value: string = "clean";
  if (false) {
    value = dfb_source(); // DFB-WITNESS: infeasible-tainted-branch
  }
  dfb_sink(value);
}
