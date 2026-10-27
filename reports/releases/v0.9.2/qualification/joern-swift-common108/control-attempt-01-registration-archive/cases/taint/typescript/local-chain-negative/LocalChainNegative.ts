function dfb_source(): string { // DFB-SOURCE: local-chain-negative-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: local-chain-negative-sink

function run(): void {
  const first: string = dfb_source();
  const second: string = first; // DFB-WITNESS: local-chain-negative-second
  const third: string = second; // DFB-WITNESS: local-chain-negative-third
  dfb_sink("clean");
}
