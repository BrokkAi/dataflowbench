function dfb_source(): string { // DFB-SOURCE: return-two-hop-negative-input
  return "tainted";
}

function firstRelay(value: string): string { // DFB-WITNESS: return-two-hop-negative-first
  return value;
}

function secondRelay(value: string): string { // DFB-WITNESS: return-two-hop-negative-second
  return firstRelay(value);
}

function dfb_sink(value: string): void {} // DFB-SINK: return-two-hop-negative-sink

function run(): void {
  const result: string = secondRelay(dfb_source());
  dfb_sink("clean");
}
