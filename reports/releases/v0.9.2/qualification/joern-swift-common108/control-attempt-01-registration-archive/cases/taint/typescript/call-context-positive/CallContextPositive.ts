function dfb_source(): string { // DFB-SOURCE: call-context-input
  return "tainted";
}

function relay(value: string): string { // DFB-WITNESS: call-context-relay
  return value;
}

function dfb_sink(value: string): void {} // DFB-SINK: call-context-sink

function run(): void {
  const tainted: string = relay(dfb_source());
  const clean: string = relay("clean");
  dfb_sink(tainted);
}
