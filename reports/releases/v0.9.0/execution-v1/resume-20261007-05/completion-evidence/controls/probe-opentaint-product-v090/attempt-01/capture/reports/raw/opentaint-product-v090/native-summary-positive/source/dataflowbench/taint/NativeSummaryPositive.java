package dataflowbench.taint;

import java.util.Base64;

/**
 * Tool-native category O, positive: the environment read makes a Base64 round
 * trip through java.util.Base64 and arrives at the command sink unchanged in
 * meaning. An engine that reads no platform bodies needs a shipped summary on
 * both halves for the value to survive.
 */
final class NativeSummaryPositive {

    private NativeSummaryPositive() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_PAYLOAD");  // DFB-SOURCE: native-summary-env
        String encoded = Base64.getEncoder().encodeToString(argument.getBytes());
        String command = new String(Base64.getDecoder().decode(encoded));
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-summary-exec
    }
}
