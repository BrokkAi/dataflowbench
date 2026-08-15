package dataflowbench.taint;

final class BranchJoinPositive {
    static int dfb_source() { // DFB-SOURCE: branch-join-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: branch-join-sink

    static void run(boolean overwrite) {
        int value = dfb_source();
        if (overwrite) {
            value = 0;
        }
        // DFB-WITNESS: branch-join-value
        dfb_sink(value);
    }
}
