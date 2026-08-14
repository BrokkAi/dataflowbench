package dataflowbench.taint;

final class LocalOverwriteNegative {
    static int dfb_source() { // DFB-SOURCE: local-overwrite-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: local-overwrite-sink

    static void run() {
        int value = dfb_source();
        value = 0; // DFB-KILL: local-overwrite-clean
        dfb_sink(value);
    }
}
