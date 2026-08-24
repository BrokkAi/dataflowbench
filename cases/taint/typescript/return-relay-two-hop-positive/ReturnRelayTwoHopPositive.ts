function dfb_source(): string { // DFB-SOURCE: return-two-hop-input
  return "tainted";
}

function firstRelay(value: string): string { // DFB-WITNESS: return-two-hop-first
  return value;
}

function secondRelay(value: string): string { // DFB-WITNESS: return-two-hop-second
  return firstRelay(value);
}

function dfb_sink(value: string): void {} // DFB-SINK: return-two-hop-sink

function run(): void {
  const result: string = secondRelay(dfb_source());
  dfb_sink(result);
}
