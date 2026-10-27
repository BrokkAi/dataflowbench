function dfb_source(): string { // DFB-SOURCE: element-object-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: element-object-sink

interface Item {
  value: string;
}

function run(): void {
  const items: Item[] = [{ value: "clean" }, { value: "clean" }];
  items[0].value = dfb_source(); // DFB-WITNESS: element-object-store
  dfb_sink(items[0].value);
}
