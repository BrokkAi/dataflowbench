function dfb_source(): string { // DFB-SOURCE: argument-position-input
  return "tainted";
}

function chooseFirst(first: string, second: string): string { // DFB-WITNESS: argument-position-first
  return first;
}

function dfb_sink(value: string): void {} // DFB-SINK: argument-position-sink

function run(): void {
  const result: string = chooseFirst(dfb_source(), "clean");
  dfb_sink(result);
}
