function dfb_source(): string { // DFB-SOURCE: local-chain-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: local-chain-sink

function run(): void {
  const first: string = dfb_source();
  const second: string = first; // DFB-WITNESS: local-chain-second
  const third: string = second; // DFB-WITNESS: local-chain-third
  dfb_sink(third);
}
