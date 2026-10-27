function dfb_source() { // DFB-SOURCE: callback-registration-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: callback-registration-sink

function register(registry, hook) {
  registry.hooks.push(hook);
}

function fire(registry, value) {
  for (const hook of registry.hooks) {
    hook(value);
  }
}

function run() {
  const registry = { hooks: [] };
  register(registry, (value) => { // DFB-WITNESS: callback-registration-hook
    dfb_sink(value);
  });
  fire(registry, dfb_source());
}
