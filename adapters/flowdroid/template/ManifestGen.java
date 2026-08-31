// Generates the committed binary (AXML) AndroidManifest.xml blobs beside this
// file. FlowDroid's command-line artifact analyzes APKs only, and an APK's
// manifest is binary Android XML that plain text cannot stand in for; rather
// than depending on the Android SDK's aapt, the blobs are produced once by
// this generator — using the pxb.android.axml writer the pinned
// soot-infoflow-cmd jar itself bundles — and committed. The manifest is
// case-independent: it declares one launcher activity, the fixed harness
// activity whose onCreate calls the fixture's entry method, so one blob per
// language serves every case.
//
// Reproduce the blobs with the pinned jar:
//
//   javac -cp soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar ManifestGen.java
//   java -cp .:soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar ManifestGen \
//     AndroidManifest-java.xml dataflowbench.taint.DfbCaseActivity
//   java -cp .:soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar ManifestGen \
//     AndroidManifest-kotlin.xml dataflowbench.DfbCaseActivity
import pxb.android.axml.AxmlWriter;
import pxb.android.axml.NodeVisitor;
import java.nio.file.Files;
import java.nio.file.Paths;

public class ManifestGen {
    static final String NS = "http://schemas.android.com/apk/res/android";

    public static void main(String[] args) throws Exception {
        String output = args[0];
        String activity = args[1];
        AxmlWriter w = new AxmlWriter();
        w.ns("android", NS, 0);
        NodeVisitor manifest = w.child(null, "manifest");
        manifest.attr(null, "package", -1, NodeVisitor.TYPE_STRING, "dataflowbench.harness");
        manifest.attr(NS, "versionCode", 0x0101021b, NodeVisitor.TYPE_FIRST_INT, 1);
        NodeVisitor usesSdk = manifest.child(null, "uses-sdk");
        usesSdk.attr(NS, "minSdkVersion", 0x0101020c, NodeVisitor.TYPE_FIRST_INT, 21);
        usesSdk.attr(NS, "targetSdkVersion", 0x01010270, NodeVisitor.TYPE_FIRST_INT, 34);
        usesSdk.end();
        NodeVisitor app = manifest.child(null, "application");
        NodeVisitor act = app.child(null, "activity");
        act.attr(NS, "name", 0x01010003, NodeVisitor.TYPE_STRING, activity);
        NodeVisitor filter = act.child(null, "intent-filter");
        NodeVisitor action = filter.child(null, "action");
        action.attr(NS, "name", 0x01010003, NodeVisitor.TYPE_STRING, "android.intent.action.MAIN");
        action.end();
        NodeVisitor category = filter.child(null, "category");
        category.attr(
                NS, "name", 0x01010003, NodeVisitor.TYPE_STRING, "android.intent.category.LAUNCHER");
        category.end();
        filter.end();
        act.end();
        app.end();
        manifest.end();
        w.end();
        Files.write(Paths.get(output), w.toByteArray());
    }
}
