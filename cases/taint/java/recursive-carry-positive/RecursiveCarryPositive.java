package dataflowbench.taint;

final class RecursiveCarryPositive {
    static int dfb_source() { // DFB-SOURCE: recursive-carry-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-carry-sink

    static int carry(int value, int depth) { // DFB-WITNESS: recursive-carry-step
        if (depth == 0) {
            return value; // DFB-WITNESS: recursive-carry-base
        }
        return carry(value, depth - 1);
    }

    static void run() {
        dfb_sink(carry(dfb_source(), 5));
    }
}
