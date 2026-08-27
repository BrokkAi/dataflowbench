package dataflowbench.taint;

/**
 * Tool-native category P, negative: the same concat operation is applied to
 * the same environment read, but that result goes nowhere; the value that
 * reaches the identical sink is the clean operand's concat result.
 */
final class NativePropagatorNegative {

    private NativePropagatorNegative() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_ARGUMENT");  // DFB-SOURCE: native-propagator-env
        String unreached = "/bin/echo ".concat(argument);
        String command = "/bin/echo ".concat("ok");
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-propagator-exec
        report(unreached.length());
    }

    private static void report(int length) {
    }
}
