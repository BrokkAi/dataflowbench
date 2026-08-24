function dfb_source(): string { // DFB-SOURCE: argument-position-negative-input
  return "tainted";
}

function chooseFirst(first: string, second: string): string { // DFB-WITNESS: argument-position-negative-first
  return first;
}

function dfb_sink(value: string): void {} // DFB-SINK: argument-position-negative-sink

function run(): void {
  const result: string = chooseFirst("clean", dfb_source());
  dfb_sink(result);
}
