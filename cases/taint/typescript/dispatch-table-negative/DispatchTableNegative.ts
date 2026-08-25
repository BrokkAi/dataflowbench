function dfb_source(): string { // DFB-SOURCE: dispatch-table-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: dispatch-table-sink

type Handler = (value: string) => void;

const table: Record<string, Handler> = {
  leak: (value: string): void => { // DFB-WITNESS: dispatch-table-entry
    dfb_sink(value);
  },
  drop: (value: string): void => {
    dfb_sink("clean");
  }
};

function run(): void {
  const key: string = "drop";
  const selected: Handler = table[key];
  selected(dfb_source());
}
