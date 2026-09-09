package dataflowbench.taint;

final class RecursivePayloadTransformPositive {
    static int dfb_source() { // DFB-SOURCE: recursive-payload-transform-input
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-payload-transform-sink

    static int walk(int value, int depth) {
        if (depth == 0) {
            return value; // DFB-WITNESS: recursive-payload-transform-base
        }
        int next = value + 1;
        int recursive = walk(next, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
        return recursive + 1; // DFB-WITNESS: recursive-payload-transform-compose
    }

    static void run() {
        dfb_sink(walk(dfb_source(), 3));
    }
}
