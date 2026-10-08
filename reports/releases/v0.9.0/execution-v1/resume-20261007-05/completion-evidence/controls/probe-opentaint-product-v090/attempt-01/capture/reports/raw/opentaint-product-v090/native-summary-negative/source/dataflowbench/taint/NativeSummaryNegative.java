package dataflowbench.taint;

import java.util.Base64;

/**
 * Tool-native category O, negative: a fresh constant makes the identical
 * Base64 round trip into the same sink, while the environment read is present
 * and goes nowhere.
 */
final class NativeSummaryNegative {

    private NativeSummaryNegative() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_PAYLOAD");  // DFB-SOURCE: native-summary-env
        String encoded = Base64.getEncoder().encodeToString("/bin/ls".getBytes());
        String command = new String(Base64.getDecoder().decode(encoded));
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-summary-exec
        report(argument.length());
    }

    private static void report(int length) {
    }
}
