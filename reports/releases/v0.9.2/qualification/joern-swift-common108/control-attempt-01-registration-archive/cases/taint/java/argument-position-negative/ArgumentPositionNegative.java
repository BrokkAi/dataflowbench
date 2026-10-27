package dataflowbench.taint;

final class ArgumentPositionNegative {
    static int dfb_source() { // DFB-SOURCE: argument-position-negative-input
        return 1;
    }

    static int chooseFirst(int first, int second) { // DFB-WITNESS: argument-position-negative-first
        return first;
    }

    static void dfb_sink(int value) { } // DFB-SINK: argument-position-negative-sink

    static void run() {
        int result = chooseFirst(0, dfb_source());
        dfb_sink(result);
    }
}
