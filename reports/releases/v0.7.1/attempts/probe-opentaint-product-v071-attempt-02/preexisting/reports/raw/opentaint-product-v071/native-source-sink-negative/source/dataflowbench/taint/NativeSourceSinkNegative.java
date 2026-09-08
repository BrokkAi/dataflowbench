package dataflowbench.taint;

/**
 * Tool-native category S, negative: the same environment read is present and
 * the same command sink is present at the same callsite shape, but the value
 * that reaches the sink is a clean constant. The sink is deliberately not
 * removed, so a rule that fires on sink existence alone takes a false
 * positive here rather than an unearned true negative.
 */
final class NativeSourceSinkNegative {

    private NativeSourceSinkNegative() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String fromEnvironment = System.getenv("DFB_NATIVE_COMMAND");  // DFB-SOURCE: native-source-sink-env
        String command = "/bin/ls";
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-source-sink-exec
        report(fromEnvironment.length());
    }

    private static void report(int length) {
    }
}
