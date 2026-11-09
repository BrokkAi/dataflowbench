import java.util.HashMap;
import java.util.Map;
public final class SameMapEscapingCalleePositive {
    static String dfb_source() { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303";
    }
    static void dfb_sink(String value) { System.out.println(value); } // DFB-SINK: issue303-sink
    static void write_source(Map<String, String> values) {
        values.put("payload", dfb_source()); // DFB-WITNESS: issue303-callee-store
    }
    static void run(String[] args) {
        Map<String, String> values = new HashMap<>();
        values.put("payload", "clean");
        write_source(values); // DFB-WITNESS: issue303-invoke
        dfb_sink(values.get("payload")); // DFB-WITNESS: issue303-read
    }
    public static void main(String[] args) { run(args); }
}
