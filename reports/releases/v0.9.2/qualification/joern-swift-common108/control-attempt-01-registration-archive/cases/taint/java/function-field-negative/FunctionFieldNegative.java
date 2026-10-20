package dataflowbench.taint;

import java.util.function.IntConsumer;

final class FunctionFieldNegative {
    static final class Holder {
        IntConsumer fn;
    }

    static int dfb_source() { // DFB-SOURCE: function-field-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: function-field-sink

    static void fire(Holder holder, int value) { // DFB-WITNESS: function-field-fire
        holder.fn.accept(value);
    }

    static void run() {
        Holder leaking = new Holder();
        leaking.fn = value -> dfb_sink(value); // DFB-WITNESS: function-field-store
        Holder dropping = new Holder();
        dropping.fn = value -> dfb_sink(0);
        fire(dropping, dfb_source());
    }
}
