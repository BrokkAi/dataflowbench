package dataflowbench.taint;

final class ReturnRelayTwoHopNegative {
    static int dfb_source() { // DFB-SOURCE: return-two-hop-negative-input
        return 1;
    }

    static int firstRelay(int value) { // DFB-WITNESS: return-two-hop-negative-first
        return value;
    }

    static int secondRelay(int value) { // DFB-WITNESS: return-two-hop-negative-second
        return firstRelay(value);
    }

    static void dfb_sink(int value) { } // DFB-SINK: return-two-hop-negative-sink

    static void run() {
        int result = secondRelay(dfb_source());
        dfb_sink(0);
    }
}
