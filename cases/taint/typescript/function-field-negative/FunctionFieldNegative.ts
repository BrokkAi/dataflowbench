function dfb_source(): string { // DFB-SOURCE: function-field-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: function-field-sink

interface Holder {
  fn: (value: string) => void;
}

function invoke(target: Holder, value: string): void {
  target.fn(value);
}

function run(): void {
  const holder: Holder = { fn: (value: string): void => {} };
  const otherHolder: Holder = { fn: (value: string): void => {} };
  holder.fn = (value: string): void => { // DFB-WITNESS: function-field-store
    dfb_sink(value);
  };
  otherHolder.fn = (value: string): void => {
    dfb_sink("clean");
  };
  invoke(otherHolder, dfb_source());
}
