package dataflowbench

func dfb_source() string { // DFB-SOURCE: callback-registration-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: callback-registration-sink

type Registry struct {
	hooks []func(value string)
}

func register(registry *Registry, hook func(value string)) {
	registry.hooks = append(registry.hooks, hook)
}

func fire(registry *Registry, value string) {
	for _, hook := range registry.hooks {
		hook(value)
	}
}

func run() {
	registry := &Registry{}
	register(registry, func(value string) { // DFB-WITNESS: callback-registration-hook
		dfb_sink(value)
	})
	fire(registry, dfb_source())
}
