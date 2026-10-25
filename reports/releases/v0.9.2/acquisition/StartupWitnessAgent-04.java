package dfb.joern;

import java.io.OutputStream;
import java.lang.instrument.Instrumentation;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Base64;
import java.util.Optional;

/**
 * A read-only premain witness. It calls no Instrumentation API and performs no
 * class transformation. The parent observer binds the output directory and
 * verifies this record against the invocation's tracked PID/birth identities.
 */
public final class StartupWitnessAgent {
    private static final String SCHEMA = "v092-joern-jvm-startup-witness/v4";
    private static final String VERSION = "joern05-native-control-04";
    private static final String DIRECTORY_ENV = "DFB_JOERN_STARTUP_WITNESS_DIR";

    private StartupWitnessAgent() {}

    public static void premain(String ignoredArgs, Instrumentation ignoredInstrumentation) {
        try {
            writeWitness();
        } catch (Throwable error) {
            // A missing or ambiguous witness must fail closed. The observer
            // records the resulting process failure and never treats stderr as
            // a substitute for this record.
            throw new IllegalStateException("startup witness failed", error);
        }
    }

    private static void writeWitness() throws Exception {
        ProcessHandle self = ProcessHandle.current();
        long pid = self.pid();
        long runtimeStart = ManagementFactory.getRuntimeMXBean().getStartTime();
        Instant processStart = self.info().startInstant().orElseThrow(
                () -> new IllegalStateException("ProcessHandle startInstant unavailable"));
        String processIdentity = processStart.toString();
        Optional<ProcessHandle> parent = self.parent();
        Long parentPid = parent.map(ProcessHandle::pid).orElse(null);
        Instant parentStart = parent.flatMap(handle -> handle.info().startInstant()).orElse(null);
        if (parentPid != null && parentStart == null) {
            throw new IllegalStateException("parent ProcessHandle startInstant unavailable");
        }
        String parentIdentity = parentStart == null ? null : parentStart.toString();

        String home = requiredProperty("user.home");
        Path homePath = Paths.get(home).toAbsolutePath().normalize();
        Path predef = homePath.resolve(".scala-repl-pp.sc");
        boolean predefSymlink = Files.isSymbolicLink(predef);
        boolean predefPresent = Files.exists(predef, LinkOption.NOFOLLOW_LINKS) || predefSymlink;
        String javaCommand = System.getProperty("sun.java.command");
        String classPath = System.getProperty("java.class.path", "");
        String witnessDirectory = System.getenv(DIRECTORY_ENV);
        if (witnessDirectory == null || witnessDirectory.isEmpty()) {
            throw new IllegalStateException("missing " + DIRECTORY_ENV);
        }
        Path configuredDirectory = Paths.get(witnessDirectory);
        if (!configuredDirectory.isAbsolute()) {
            throw new IllegalStateException("witness directory must be absolute: " + witnessDirectory);
        }
        Path directory = configuredDirectory.normalize();
        if (Files.isSymbolicLink(directory) ||
                !Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)) {
            throw new IllegalStateException("invalid witness directory: " + directory);
        }

        StringBuilder json = new StringBuilder();
        json.append("{\n");
        field(json, "schema", SCHEMA, true);
        field(json, "agent_version", VERSION, true);
        number(json, "pid", pid, true);
        if (parentPid == null) {
            json.append("  \"parent_pid\": null,\n");
        } else {
            number(json, "parent_pid", parentPid, true);
        }
        field(json, "process_start_identity", processIdentity, true);
        number(json, "process_start_epoch_seconds", processStart.getEpochSecond(), true);
        number(json, "process_start_epoch_nanos", processStart.getNano(), true);
        if (parentIdentity == null) {
            json.append("  \"parent_start_identity\": null,\n");
        } else {
            field(json, "parent_start_identity", parentIdentity, true);
            number(json, "parent_start_epoch_seconds", parentStart.getEpochSecond(), true);
            number(json, "parent_start_epoch_nanos", parentStart.getNano(), true);
        }
        if (parentIdentity == null) {
            json.append("  \"parent_start_epoch_seconds\": null,\n");
            json.append("  \"parent_start_epoch_nanos\": null,\n");
        }
        number(json, "runtime_start_millis", runtimeStart, true);
        field(json, "user_home_b64", encode(homePath.toString()), true);
        json.append("  \"java_command_present\": ").append(javaCommand != null).append(",\n");
        field(json, "java_command_b64", encode(javaCommand == null ? "" : javaCommand), true);
        field(json, "java_class_path_b64", encode(classPath), true);
        field(json, "predef_path_b64", encode(predef.toString()), true);
        json.append("  \"predef_present\": ").append(predefPresent).append(",\n");
        json.append("  \"predef_symlink\": ").append(predefSymlink).append(",\n");
        field(json, "witness_directory_b64", encode(directory.toString()), false);
        json.append("\n}\n");

        Path destination = directory.resolve("jvm-" + pid + ".json");
        try (OutputStream stream = Files.newOutputStream(destination,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            stream.write(json.toString().getBytes(StandardCharsets.UTF_8));
        } catch (FileAlreadyExistsException duplicate) {
            throw new IllegalStateException("duplicate JVM witness: " + destination, duplicate);
        }
    }

    private static Optional<String> startIdentity(ProcessHandle handle) {
        return handle.info().startInstant().map(Instant::toString);
    }

    private static String requiredProperty(String key) {
        String value = System.getProperty(key);
        if (value == null || value.isEmpty()) {
            throw new IllegalStateException("missing System property: " + key);
        }
        return value;
    }

    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static void field(StringBuilder json, String key, String value, boolean comma) {
        json.append("  \"").append(key).append("\": \"").append(value).append("\"");
        if (comma) json.append(',');
        json.append('\n');
    }

    private static void number(StringBuilder json, String key, long value, boolean comma) {
        json.append("  \"").append(key).append("\": ").append(value);
        if (comma) json.append(',');
        json.append('\n');
    }
}
