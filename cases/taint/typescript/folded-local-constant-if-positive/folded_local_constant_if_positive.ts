function dfb_source(): string { // DFB-SOURCE: folded-local-constant-source
  return "tainted";
}

function dfb_sink(value: string): void { // DFB-SINK: folded-local-constant-sink
  console.log(value);
}

function run(): void {
  const factor: number = 7;
  const num: number = 100;
  const limit: number = 200;
  let value: string;
  if ((factor * 42) - num > limit) {
    value = "safe";
  } else {
    value = dfb_source(); // DFB-WITNESS: folded-local-constant-source-selected
  }
  dfb_sink(value);
}

run();
