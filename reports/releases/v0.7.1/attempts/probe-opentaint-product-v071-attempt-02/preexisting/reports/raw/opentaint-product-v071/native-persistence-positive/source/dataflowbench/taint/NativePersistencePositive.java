package dataflowbench.taint;

/**
 * Tool-native category B, positive: the environment read is written into the
 * JVM's process-wide system-property store under a key and read back out of
 * the same store under the same key. Only a shipped store-write / store-read
 * link carries the taint across.
 */
final class NativePersistencePositive {

    private NativePersistencePositive() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_STORED");  // DFB-SOURCE: native-persistence-env
        System.setProperty("dfb.native.command", argument);
        String command = System.getProperty("dfb.native.command");
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-persistence-exec
    }
}
