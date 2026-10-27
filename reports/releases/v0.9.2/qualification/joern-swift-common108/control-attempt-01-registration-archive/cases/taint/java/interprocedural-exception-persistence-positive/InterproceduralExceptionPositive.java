package dataflowbench.taint;

final class InterproceduralExceptionPositive {
    static final class Box {
        int value;
    }

    static final class FlowException extends Exception {
        private static final long serialVersionUID = 1L;
    }

    static int dfb_source() { // DFB-SOURCE: interprocedural-exception-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: interprocedural-exception-sink

    static void store(Box box, int value) throws FlowException {
        box.value = value; // DFB-WITNESS: interprocedural-exception-store
        throw new FlowException(); // DFB-WITNESS: interprocedural-exception-throw
    }

    static int recover(Box box, int value) {
        try {
            store(box, value);
            return -1;
        } catch (FlowException caught) { // DFB-WITNESS: interprocedural-exception-recovery
            return box.value;
        }
    }

    static void run() {
        Box box = new Box();
        dfb_sink(recover(box, dfb_source()));
    }
}
