package dataflowbench.taint;

/**
 * Tool-native category Z, negative: the identical flow passes through the
 * platform's numeric-coercion idiom — Integer.parseInt(String) rendered back
 * with String.valueOf(int) — before the same sink. A shipped sanitizer model
 * that credits the coercion in the query family owning this sink suppresses
 * it; one that credits it only elsewhere does not.
 */
final class NativeSanitizerNegative {

    private NativeSanitizerNegative() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String raw = System.getenv("DFB_NATIVE_SECONDS");  // DFB-SOURCE: native-sanitizer-env
        String coerced = String.valueOf(Integer.parseInt(raw));
        Runtime.getRuntime().exec(coerced);  // DFB-SINK: native-sanitizer-exec
    }
}
