package dataflowbench.taint;

import android.app.Activity;
import android.os.Bundle;

// The harness entry-point wrapper. FlowDroid derives its analysis entry
// points from the Android components the APK's manifest declares, and the
// benchmark fixtures declare none, so this activity is materialized beside
// each case's fixtures and its onCreate calls the fixture's own entry method.
// It is the adapter's analogue of OpenTaint's all-methods entry-point
// selector: it decides which code is reachable from an entry point, never
// what the engine claims about a flow. The entry argument for the one
// two-parameter entry shape (`run(boolean)`) is derived from the activity's
// bundle so it stays statically unknown and no fixture branch is decided by
// the harness.
public class DfbCaseActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Some fixtures declare checked exceptions on their entry method
        // (`run() throws Exception`); the rethrow keeps the call compilable
        // without swallowing anything, and no flow inside the fixture is
        // altered.
        try {
            AliasPropagationNegative.run();
        } catch (Throwable throwable) {
            throw new RuntimeException(throwable);
        }
    }
}
