fn dfb_source() -> i32 { // DFB-SOURCE: callback-registration-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: callback-registration-sink

struct Registry {
    hooks: Vec<Box<dyn Fn(i32)>>,
}

impl Registry {
    fn register(&mut self, hook: Box<dyn Fn(i32)>) {
        self.hooks.push(hook);
    }

    fn fire(&self, value: i32) {
        for hook in &self.hooks {
            hook(value);
        }
    }
}

fn run() {
    let mut registry = Registry { hooks: Vec::new() };
    registry.register(Box::new(|value| { // DFB-WITNESS: callback-registration-hook
        dfb_sink(value);
    }));
    registry.fire(dfb_source());
}
