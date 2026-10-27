function dfb_source(): string { // DFB-SOURCE: callback-registration-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: callback-registration-sink

type Hook = (value: string) => void;

interface Registry {
  hooks: Hook[];
}

function register(registry: Registry, hook: Hook): void {
  registry.hooks.push(hook);
}

function fire(registry: Registry, value: string): void {
  for (const hook of registry.hooks) {
    hook(value);
  }
}

function run(): void {
  const registry: Registry = { hooks: [] };
  register(registry, (value: string): void => { // DFB-WITNESS: callback-registration-hook
    dfb_sink(value);
  });
  fire(registry, dfb_source());
}
