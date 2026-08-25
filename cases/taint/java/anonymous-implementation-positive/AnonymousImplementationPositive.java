package dataflowbench.taint;

final class AnonymousImplementationPositive {
    interface Handler {
        void handle(int value);
    }

    static int dfb_source() { // DFB-SOURCE: anonymous-implementation-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: anonymous-implementation-sink

    static void run() {
        Handler leaking = new Handler() {
            @Override
            public void handle(int value) { // DFB-WITNESS: anonymous-implementation-handle
                dfb_sink(value);
            }
        };
        Handler dropping = new Handler() {
            @Override
            public void handle(int value) {
                dfb_sink(0);
            }
        };
        leaking.handle(dfb_source()); // DFB-WITNESS: anonymous-implementation-invoke
    }
}
