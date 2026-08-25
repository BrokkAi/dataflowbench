function dfb_source(): string { // DFB-SOURCE: computed-property-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: computed-property-sink

interface Holder {
  payload: string;
  other: string;
}

function run(): void {
  const writeKey: keyof Holder = "payload";
  const readKey: keyof Holder = "other";
  const holder: Holder = { payload: "clean", other: "clean" };
  holder[writeKey] = dfb_source(); // DFB-WITNESS: computed-property-store
  dfb_sink(holder[readKey]);
}
