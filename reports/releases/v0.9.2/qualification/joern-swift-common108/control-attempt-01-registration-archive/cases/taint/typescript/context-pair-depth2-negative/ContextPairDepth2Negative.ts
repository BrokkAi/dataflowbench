function dfb_source(): string { // DFB-SOURCE: context-pair-depth2-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: context-pair-depth2-sink

function helper(value: string): string { // DFB-WITNESS: context-pair-depth2-helper
  return value;
}

function wrapper(value: string): string {
  return helper(value);
}

function outerTainted(): string {
  return wrapper(dfb_source());
}

function outerClean(): string {
  return wrapper("clean");
}

function run(): void {
  const tainted: string = outerTainted();
  const clean: string = outerClean();
  dfb_sink(clean);
}
