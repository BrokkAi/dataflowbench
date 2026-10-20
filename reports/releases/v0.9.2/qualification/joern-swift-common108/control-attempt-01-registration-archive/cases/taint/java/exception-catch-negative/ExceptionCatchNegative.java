package dataflowbench.taint;

final class ExceptionCatchNegative {
    static final class FlowException extends Exception {
        private static final long serialVersionUID = 1L;
        int value;
    }

    static int dfb_source() { // DFB-SOURCE: exception-catch-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: exception-catch-sink

    static void run() {
        try {
            FlowException flow = new FlowException();
            int ignored = dfb_source();
            flow.value = 0;
            throw flow; // DFB-WITNESS: exception-catch-throw
        } catch (FlowException caught) {
            dfb_sink(caught.value);
        }
    }
}
