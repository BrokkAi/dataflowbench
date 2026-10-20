package dataflowbench.taint;

/**
 * Tool-native category E, negative: the argument-vector read is present in
 * the same entry method and goes nowhere; a constant local declared beside it
 * reaches the same sink.
 */
final class NativeEntrypointNegative {

    private NativeEntrypointNegative() {
    }

    @SuppressWarnings("deprecation")
    public static void main(String[] args) throws java.io.IOException {  // DFB-SOURCE: native-entrypoint-argv
        String fromArgv = args[0];
        String command = "/bin/ls";
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-entrypoint-exec
        report(fromArgv.length());
    }

    private static void report(int length) {
    }
}
