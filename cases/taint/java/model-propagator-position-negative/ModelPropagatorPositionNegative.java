package dataflowbench.taint;

final class Opaque {
    public static String identity(String value) {
        return value;
    }

    static String select(String first, String second) {
        String target = "identity";
        try {
            return (String) Opaque.class.getMethod(target, String.class)
                .invoke(null, second);
        } catch (ReflectiveOperationException error) {
            return "";
        }
    }
}

final class ModelPropagatorPositionNegative {
    static String dfb_source() {  // DFB-SOURCE: model-propagator-position-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-propagator-position-sink

    static void run() {
        dfb_sink(Opaque.select(dfb_source(), "clean"));
    }
}
