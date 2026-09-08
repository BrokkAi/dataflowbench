package dataflowbench.taint;

final class DfbTrivial {
    static int dfb_source() { // DFB-SOURCE: trivial-overhead-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: trivial-overhead-sink

    static void run() {
        dfb_source();
        dfb_sink(0);
    }
}
