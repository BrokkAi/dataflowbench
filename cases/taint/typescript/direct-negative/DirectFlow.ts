function dfb_source(): string { // DFB-SOURCE: direct-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: direct-sink

function run(): void {
  dfb_source();
  dfb_sink("clean");
}

