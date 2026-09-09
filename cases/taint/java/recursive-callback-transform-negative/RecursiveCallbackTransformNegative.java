package dataflowbench.taint;

final class RecursiveCallbackTransformNegative {
    @FunctionalInterface
    interface Step {
        int apply(int value, int depth);
    }

    static int dfb_source() { // DFB-SOURCE: recursive-callback-transform-input
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-callback-transform-sink

    static int walk(int value, int depth, Step step) {
        if (depth == 0) {
            value = 0; // DFB-KILL: recursive-callback-transform-base-clean
            return value; // DFB-WITNESS: recursive-callback-transform-base
        }
        return step.apply(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
    }

    static int step(int value, int depth) {
        int next = value + 1;
        int recursive = walk(next, depth, RecursiveCallbackTransformNegative::step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
        return recursive + 1; // DFB-WITNESS: recursive-callback-transform-compose
    }

    static void run() {
        dfb_sink(walk(dfb_source(), 3, RecursiveCallbackTransformNegative::step));
    }
}
