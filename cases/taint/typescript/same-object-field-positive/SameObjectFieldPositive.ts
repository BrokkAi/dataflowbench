function dfb_source(): string { // DFB-SOURCE: same-object-field-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: same-object-field-sink

function run(): void {
  const holder: { tainted: string; clean: string } = { tainted: "clean", clean: "clean" };
  holder.tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
  holder.clean = "clean";
  dfb_sink(holder.tainted);
}
