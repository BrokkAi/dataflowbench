function dfb_source(): string { // DFB-SOURCE: nested-access-path-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: nested-access-path-sink

interface Level3 {
  value: string;
  other: string;
}

interface Level2 {
  c: Level3;
}

interface Level1 {
  b: Level2;
}

function run(): void {
  const a: Level1 = { b: { c: { value: "clean", other: "clean" } } };
  a.b.c.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
  dfb_sink(a.b.c.value);
}
