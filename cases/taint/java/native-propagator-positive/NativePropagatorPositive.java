package dataflowbench.taint;

/**
 * Tool-native category P, positive: the environment read is carried to the
 * command sink through java.lang.String.concat(String), whose body is inside
 * the platform. Only a shipped propagator summary carries the value across.
 */
final class NativePropagatorPositive {

    private NativePropagatorPositive() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_ARGUMENT");  // DFB-SOURCE: native-propagator-env
        String command = "/bin/echo ".concat(argument);
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-propagator-exec
    }
}
