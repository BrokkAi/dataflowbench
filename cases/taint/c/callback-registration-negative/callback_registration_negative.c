struct Registry {
    void (*hooks[4])(int);
    int count;
};

int dfb_source(void) { // DFB-SOURCE: callback-registration-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: callback-registration-sink

void register_hook(struct Registry *registry, void (*hook)(int)) {
    registry->hooks[registry->count] = hook;
    registry->count = registry->count + 1;
}

void fire(struct Registry *registry, int value) { // DFB-WITNESS: callback-registration-fire
    for (int index = 0; index < registry->count; index++) {
        registry->hooks[index](value);
    }
}

void drop(int value) {
    dfb_sink(0);
}

void run(void) {
    struct Registry registry;
    registry.count = 0;
    register_hook(&registry, drop);
    fire(&registry, dfb_source());
}
