package dataflowbench.taint;

import java.util.HashMap;
import java.util.Map;
import java.util.function.IntUnaryOperator;

final class DispatchTablePositive {
    static int dfb_source() { // DFB-SOURCE: dispatch-table-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: dispatch-table-sink

    static void run() {
        Map<String, IntUnaryOperator> table = new HashMap<>();
        table.put("leak", value -> { // DFB-WITNESS: dispatch-table-entry
            dfb_sink(value);
            return value;
        });
        table.put("drop", value -> {
            dfb_sink(0);
            return 0;
        });
        String key = "leak";
        table.get(key).applyAsInt(dfb_source()); // DFB-WITNESS: dispatch-table-lookup
    }
}
