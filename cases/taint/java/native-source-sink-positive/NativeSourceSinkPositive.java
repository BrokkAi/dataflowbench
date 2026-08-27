package dataflowbench.taint;

/**
 * Tool-native category S, positive: a value read from the JDK's own
 * environment API reaches the JDK's own command-execution API in one hop.
 * Both endpoints are real platform identities, so a shipped source model and
 * a shipped sink model have something to bind to.
 */
final class NativeSourceSinkPositive {

    private NativeSourceSinkPositive() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String command = System.getenv("DFB_NATIVE_COMMAND");  // DFB-SOURCE: native-source-sink-env
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-source-sink-exec
    }
}
