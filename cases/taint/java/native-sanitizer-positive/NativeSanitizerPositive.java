package dataflowbench.taint;

/**
 * Tool-native category Z, positive: the unsanitized path from the platform
 * environment source to the platform command sink, which the shipped model
 * set is expected to flag.
 */
final class NativeSanitizerPositive {

    private NativeSanitizerPositive() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String raw = System.getenv("DFB_NATIVE_SECONDS");  // DFB-SOURCE: native-sanitizer-env
        Runtime.getRuntime().exec(raw);  // DFB-SINK: native-sanitizer-exec
    }
}
