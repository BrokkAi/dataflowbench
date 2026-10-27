function dfb_source(): string { // DFB-SOURCE: object-separation-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: object-separation-sink

function run(): void {
  const tainted: { value: string } = { value: "clean" };
  const clean: { value: string } = { value: "clean" };
  tainted.value = dfb_source(); // DFB-WITNESS: object-separation-store
  clean.value = "clean";
  dfb_sink(tainted.value);
}
