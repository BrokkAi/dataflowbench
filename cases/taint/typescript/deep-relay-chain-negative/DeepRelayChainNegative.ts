function dfb_source(): string { // DFB-SOURCE: deep-relay-chain-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: deep-relay-chain-sink

function relay6(value: string): void { // DFB-WITNESS: deep-relay-chain-hop-six
  dfb_sink(value);
}

function relay5(value: string): void {
  relay6(value);
}

function relay4(value: string): void {
  relay5(value);
}

function relay3(value: string): void {
  relay4(value);
}

function relay2(value: string): void {
  relay3(value);
}

function relay1(value: string): void { // DFB-WITNESS: deep-relay-chain-hop-one
  relay2(value);
}

function run(): void {
  const tainted: string = dfb_source();
  relay1("clean");
}
