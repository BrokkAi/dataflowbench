package dataflowbench.taint;

final class ClosureCapturePositive {
    static int dfb_source() { // DFB-SOURCE: closure-capture-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: closure-capture-sink

    static Runnable capture() {
        int tainted = dfb_source();
        int clean = 0;
        return () -> dfb_sink(tainted); // DFB-WITNESS: closure-capture-body
    }

    static void run() {
        Runnable hook = capture(); // DFB-WITNESS: closure-capture-invoke
        hook.run();
    }
}
