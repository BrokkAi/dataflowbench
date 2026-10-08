package dataflowbench

import android.app.Activity
import android.os.Bundle

// The harness entry-point wrapper; see DfbCaseActivity.java.tmpl. The Kotlin
// kernel's fixtures declare their entry method on a file-stem object in the
// fixture package, so the wrapper is Kotlin and lives in that package too.
class DfbCaseActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        InfeasibleBranchNegative.run()
    }
}
