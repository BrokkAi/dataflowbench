package dataflowbench.taint;

import java.util.ArrayList;
import java.util.List;
import java.util.function.IntConsumer;

final class CallbackRegistrationNegative {
    static final class Registry {
        private final List<IntConsumer> hooks = new ArrayList<>();

        void register(IntConsumer hook) {
            hooks.add(hook);
        }

        void fire(int value) { // DFB-WITNESS: callback-registration-fire
            for (IntConsumer hook : hooks) {
                hook.accept(value);
            }
        }
    }

    static int dfb_source() { // DFB-SOURCE: callback-registration-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: callback-registration-sink

    static void run() {
        Registry registry = new Registry();
        registry.register(value -> dfb_sink(0)); // DFB-WITNESS: callback-registration-hook
        registry.fire(dfb_source());
    }
}
