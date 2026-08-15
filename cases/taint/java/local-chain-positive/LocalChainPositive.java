package dataflowbench.taint;

final class LocalChainPositive {
    static int dfb_source() { // DFB-SOURCE: local-chain-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: local-chain-sink

    static void run() {
        int first = dfb_source();
        int second = first; // DFB-WITNESS: local-chain-second
        int third = second; // DFB-WITNESS: local-chain-third
        dfb_sink(third);
    }
}
