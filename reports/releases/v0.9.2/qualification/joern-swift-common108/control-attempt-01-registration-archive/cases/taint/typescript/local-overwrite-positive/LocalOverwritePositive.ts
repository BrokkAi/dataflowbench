function dfb_source(): string { // DFB-SOURCE: local-overwrite-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: local-overwrite-sink

function run(): void {
  let value: string = dfb_source();
  value = value; // DFB-WITNESS: local-overwrite-preserved
  dfb_sink(value);
}
