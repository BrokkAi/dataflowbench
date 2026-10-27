package dataflowbench.taint;

final class ArgumentPositionPositive {
    static int dfb_source() { // DFB-SOURCE: argument-position-input
        return 1;
    }

    static int chooseFirst(int first, int second) { // DFB-WITNESS: argument-position-first
        return first;
    }

    static void dfb_sink(int value) { } // DFB-SINK: argument-position-sink

    static void run() {
        int result = chooseFirst(dfb_source(), 0);
        dfb_sink(result);
    }
}
