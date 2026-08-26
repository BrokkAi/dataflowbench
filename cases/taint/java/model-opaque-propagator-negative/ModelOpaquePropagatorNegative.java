package dataflowbench.taint;

final class Opaque {
    public static String identity(String value) {
        return value;
    }

    static String carry(String value) {
        String target = "identity";
        try {
            return (String) Opaque.class.getMethod(target, String.class)
                .invoke(null, value);
        } catch (ReflectiveOperationException error) {
            return "";
        }
    }

    static String block(String value) {
        String target = "identity";
        try {
            return (String) Opaque.class.getMethod(target, String.class)
                .invoke(null, value);
        } catch (ReflectiveOperationException error) {
            return "";
        }
    }
}

final class ModelOpaquePropagatorNegative {
    static String dfb_source() {  // DFB-SOURCE: model-opaque-propagator-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-opaque-propagator-sink

    static void run() {
        dfb_sink(Opaque.block(dfb_source()));
    }
}
