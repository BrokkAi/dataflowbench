function dfb_source(): string { // DFB-SOURCE: local-overwrite-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: local-overwrite-sink

function run(): void {
  let value: string = dfb_source();
  value = "clean"; // DFB-KILL: local-overwrite-clean
  dfb_sink(value);
}
