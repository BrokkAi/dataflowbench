function dfb_source(): string { // DFB-SOURCE: closure-capture-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: closure-capture-sink

function makeHandler(): () => void {
  const tainted: string = dfb_source(); // DFB-WITNESS: closure-capture-store
  const captured: string = "clean";
  return (): void => {
    dfb_sink(captured);
  };
}

function run(): void {
  const handler: () => void = makeHandler();
  handler();
}
