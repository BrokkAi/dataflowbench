package dataflowbench.taint;

import java.util.HashMap;
import java.util.Map;

final class MapIterationNegative {
    static int dfb_source() { // DFB-SOURCE: map-iteration-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: map-iteration-sink

    static void run() {
        Map<String, Integer> tainted = new HashMap<>();
        tainted.put("entry", dfb_source()); // DFB-WITNESS: map-iteration-store
        Map<String, Integer> clean = new HashMap<>();
        clean.put("entry", 0);
        for (Map.Entry<String, Integer> entry : clean.entrySet()) { // DFB-WITNESS: map-iteration-entries
            dfb_sink(entry.getValue());
        }
    }
}
