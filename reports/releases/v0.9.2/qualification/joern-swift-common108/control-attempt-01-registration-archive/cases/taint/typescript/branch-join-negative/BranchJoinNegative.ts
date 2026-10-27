function dfb_source(): string { // DFB-SOURCE: branch-join-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: branch-join-sink

function run(overwrite: boolean): void {
  let value: string = dfb_source();
  if (overwrite) {
    value = "clean";
  } else {
    value = "clean";
  }
  // DFB-WITNESS: branch-join-value
  dfb_sink(value);
}
