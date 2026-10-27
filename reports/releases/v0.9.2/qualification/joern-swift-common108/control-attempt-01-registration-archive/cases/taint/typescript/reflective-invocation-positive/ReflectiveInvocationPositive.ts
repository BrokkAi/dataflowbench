function dfb_source(): string { // DFB-SOURCE: reflective-invocation-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: reflective-invocation-sink

const handlers: Record<string, (value: string) => void> = {
  leak(value: string): void { // DFB-WITNESS: reflective-invocation-target
    dfb_sink(value);
  },
  drop(value: string): void {
    dfb_sink("clean");
  }
};

function run(): void {
  const name: string = "leak";
  handlers[name](dfb_source());
}
