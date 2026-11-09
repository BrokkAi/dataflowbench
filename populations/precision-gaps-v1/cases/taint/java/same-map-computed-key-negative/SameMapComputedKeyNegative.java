import java.util.HashMap;
import java.util.Map;
public final class SameMapComputedKeyNegative {
    static String dfb_source() { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303";
    }
    static void dfb_sink(String value) { System.out.println(value); } // DFB-SINK: issue303-sink
    static void run(String[] args) {
        String suffix = args.length > 0 ? args[0] : "payload";
        String key = "private:" + suffix;
        Map<String, String> values = new HashMap<>();
        values.put("payload", "clean");
        values.put(key, dfb_source()); // DFB-WITNESS: issue303-store
        dfb_sink(values.get("payload")); // DFB-WITNESS: issue303-read
    }
    public static void main(String[] args) { run(args); }
}
