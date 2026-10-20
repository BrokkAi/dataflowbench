function dfb_source(): string { // DFB-SOURCE: alias-propagation-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: alias-propagation-sink

function run(): void {
  const original: { value: string } = { value: "clean" };
  const alias: { value: string } = original; // DFB-WITNESS: alias-propagation-alias
  const distinct: { value: string } = { value: "clean" };
  original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
  dfb_sink(alias.value);
}
