package dataflowbench.taint;

/**
 * Tool-native category E, positive: the platform's own process-entry contract
 * is the source. No framework, no annotation, no registration — the argument
 * vector arrives where the JVM's launch convention says it arrives.
 */
final class NativeEntrypointPositive {

    private NativeEntrypointPositive() {
    }

    @SuppressWarnings("deprecation")
    public static void main(String[] args) throws java.io.IOException {  // DFB-SOURCE: native-entrypoint-argv
        String command = args[0];
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-entrypoint-exec
    }
}
