function dfb_source(): string { // DFB-SOURCE: return-one-hop-input
  return "tainted";
}

function relay(value: string): string { // DFB-WITNESS: return-one-hop-relay
  return value;
}

function dfb_sink(value: string): void {} // DFB-SINK: return-one-hop-sink

function run(): void {
  const result: string = relay(dfb_source());
  dfb_sink(result);
}
