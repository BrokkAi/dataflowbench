package dataflowbench.taint;

/**
 * Tool-native category B, negative: the write happens under one key and the
 * read happens under a distinct key, with the same store and the same sink.
 * A tool that treats the read as an environment source rather than as a
 * store-read reports this cell and takes a false positive, because the
 * distinct key is exactly what it is not looking at.
 */
final class NativePersistenceNegative {

    private NativePersistenceNegative() {
    }

    @SuppressWarnings("deprecation")
    static void run() throws java.io.IOException {
        String argument = System.getenv("DFB_NATIVE_STORED");  // DFB-SOURCE: native-persistence-env
        System.setProperty("dfb.native.command", argument);
        String command = System.getProperty("dfb.native.other");
        Runtime.getRuntime().exec(command);  // DFB-SINK: native-persistence-exec
    }
}
