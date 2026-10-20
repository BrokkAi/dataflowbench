function dfb_source(): string { // DFB-SOURCE: anonymous-implementation-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: anonymous-implementation-sink

interface Handler {
  (value: string): void;
}

function run(): void {
  const leakHandler: Handler = function (value: string): void { // DFB-WITNESS: anonymous-implementation-handler
    dfb_sink(value);
  };
  const dropHandler: Handler = function (value: string): void {
    dfb_sink("clean");
  };
  dropHandler(dfb_source());
}
