//! The FlowDroid adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/flowdroid/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ToolIdentity;
use crate::adapters::normalized_report;
use crate::adapters::opentaint::jvm_fixture_package;
use crate::adapters::write_runner_error;
use crate::adapters::{KernelPopulation, select_kernel_cases};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::LoadedCases;
use crate::cases::{fixture_revision, validate_cases};
use crate::evidence::{AnchorDialect, benchmark_endpoint_names};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, OverheadTools, load_average_one_minute,
    overhead_workspace, trivial_fixture,
};
use crate::modeling::{
    ModelingCategory, modeling_anchor_dialect, modeling_category, modeling_partition_outcome,
    modeling_supported_templates, plan_modeling_run,
};
use crate::native::run_native_with_identity;
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, now_seconds, write_case_phase_timings, write_run_environment,
};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command,
    time::Instant,
};
use walkdir::WalkDir;

/// FlowDroid's per-language modeling artifact: a directory of StubDroid
/// summary XMLs — the release's own summary format — activated per case as
/// `-tw STUBDROID -t <dir>`, which *replaces* the release default's bundled
/// `summariesManual` provider so the only summaries in the run are the
/// benchmark's declarations (Amendment A18).
pub(crate) const FLOWDROID_MODELING_SUMMARIES_DIR: &str = "adapters/flowdroid/summaries/model-java";

/// The three committed summary files, individually hash-bound into the
/// modeling report's `configuration_hash` (a directory has no bytes to hash).
pub(crate) const FLOWDROID_MODELING_SUMMARY_FILES: [&str; 3] = [
    "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Bridge.xml",
    "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Clean.xml",
    "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Opaque.xml",
];

/// The taint-wrapper mode a FlowDroid modeling run passes. STUBDROID over the
/// committed summaries is what makes the declarations load-bearing: the
/// engine's only alternative for a summarized callee is reading its body, the
/// opaque bodies carry nothing on the pinned defaults (probed), and no shipped
/// summary is in the run to decide a cell the benchmark's declaration was
/// meant to decide.
pub(crate) const FLOWDROID_MODELING_TAINT_WRAPPER_MODE: &str = "STUBDROID";

/// The declared method identities each committed FlowDroid summary file must
/// carry, checked by [`require_flowdroid_modeling_declarations`]: a scored
/// cell whose declaration is missing is a benchmark defect that fails the
/// run, never an outcome — the same rule every other adapter's artifact gate
/// enforces.
pub(crate) const FLOWDROID_MODELING_DECLARATIONS: [(&str, &str); 6] = [
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Opaque.xml",
        "<method id=\"java.lang.String carry(java.lang.String)\">",
    ),
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Opaque.xml",
        "<method id=\"java.lang.String select(java.lang.String,java.lang.String)\">",
    ),
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Clean.xml",
        "<clear sourceSinkType=\"Parameter\" ParameterIndex=\"0\" />",
    ),
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Bridge.xml",
        "<method id=\"java.lang.String pass(java.lang.String)\">",
    ),
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Bridge.xml",
        "<method id=\"void deposit(java.lang.String,dataflowbench.taint.Box)\">",
    ),
    (
        "adapters/flowdroid/summaries/model-java/dataflowbench.taint.Bridge.xml",
        "AccessPath=\"[dataflowbench.taint.Box: java.lang.String payload]\"",
    ),
];

/// Enforce that every declaration FlowDroid's scored cells rest on is present
/// in the committed summaries. The mirror of the Bifrost, Semgrep, and Infer
/// load-bearing gates: those pin a *default-disabling switch* or refuse a
/// silent configuration, which FlowDroid does not need — replacing the
/// default taint wrapper with the committed summaries directory is itself
/// what removes every shipped model from the run — so what is pinned here is
/// the presence of the declarations themselves.
pub(crate) fn require_flowdroid_modeling_declarations() -> Result<()> {
    for (path, declaration) in FLOWDROID_MODELING_DECLARATIONS {
        let contents = fs::read_to_string(path).map_err(|error| {
            anyhow::anyhow!(
                "FlowDroid's Java modeling population needs its committed summary artifact {path}, which cannot be read: {error}. docs/modeling-matrix.md makes a missing model a benchmark defect that fails the build; it is never `unsupported`, never `not-reached`, and never a result"
            )
        })?;
        if !contents.contains(declaration) {
            bail!(
                "{path} no longer carries the declaration {declaration:?} that a scored FlowDroid modeling cell rests on (docs/modeling-matrix.md, Amendment A18); a missing model is a benchmark defect, never a result"
            );
        }
    }
    Ok(())
}

/// How a FlowDroid native run's `-s` argument is recorded in the pinned
/// activation shape: the shipped catalog is a member of the digest-witnessed
/// jar, extracted verbatim into the run's scratch at run time, so the
/// activation names the jar entry rather than a repository path — there is no
/// vendored copy whose drift a hash would have to catch.
pub(crate) const FLOWDROID_NATIVE_CATALOG_ARGUMENT: &str =
    "jar:soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar!/SourcesAndSinks.txt";

// ---------------------------------------------------------------------------
// FlowDroid kernel runners.
//
// FlowDroid (secure-software-engineering/FlowDroid) is the academic-standard
// Java/Android taint engine. Its released command-line artifact,
// `soot-infoflow-cmd-<version>-jar-with-dependencies.jar`, analyzes APKs
// only — verified in the field: a plain jar of compiled classes is refused
// for lack of an Android manifest, and entry points come exclusively from
// the manifest's declared components. Each case therefore materializes a
// minimal APK in an isolated scratch workspace: the fixtures are compiled
// (`javac` for Java, `kotlinc` for Kotlin), a fixed harness activity whose
// `onCreate` calls the fixture's own entry method is compiled beside them, the
// classes are translated to dex by the pinned r8 jar's D8 entry point — a
// deterministic bytecode translation running on the same JVM, not an Android
// SDK dependency — and the dex is zipped with a committed, benchmark-generated
// binary manifest. All of that is harness materialization, the adapter's
// analogue of the OpenTaint kernels' synthesized `project.yaml` and the Joern
// Rust kernel's synthesized Cargo manifest, and it is deliberately untimed;
// the one FlowDroid invocation is indivisible from the adapter's vantage and
// is timed as `total`.
//
// The benchmark-controlled sources and sinks are FlowDroid's own native
// mechanism, a sources-and-sinks definition file (`-s`): the method names come
// from each case's `DFB-SOURCE:`/`DFB-SINK:` marker lines through the same
// resolver every other kernel uses, and the exact Soot signatures those names
// denote are witnessed from the compiled fixture classes rather than guessed
// from source text. The resolved definition file is retained per case.
//
// Outcome discipline needs one verified guard: the pinned CLI exits zero on
// analysis failures and writes no results XML at all when a run finds no
// leaks, so a naive reading would turn a crashed run into a clean negative.
// The runner therefore requires the analyzer's own completion line ("Found N
// leaks from M sources") in the retained log before any negative is recorded,
// treats the documented failure banner as `runner-error`, and reads the
// results XML's own `TerminationState` — anything but `Success` (timeouts,
// aborts) is incomplete evidence, never `not-reached`.
// ---------------------------------------------------------------------------

/// The pinned FlowDroid release. The jar self-reports its version in its
/// embedded Maven `pom.properties`, and every run witnesses that value from
/// the jar actually invoked, per the identity-witnessing convention (#87).
pub(crate) const FLOWDROID_PINNED_VERSION: &str = "2.15.1";

/// SHA-256 of the pinned `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`
/// Maven Central artifact. The 2.15.x releases publish no GitHub release
/// assets, so Maven Central is the release channel; the digest is witnessed
/// from the bytes actually invoked before any case runs.
pub(crate) const FLOWDROID_JAR_SHA256: &str =
    "51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218";

/// SHA-256 of the pinned Android platform jar (`android-34/android.jar` from
/// Sable/android-platforms @ b439048e). FlowDroid resolves the analyzed
/// framework stubs from this jar — it is the analysis-classpath platform
/// image, not a build tool — so its identity is pinned and witnessed like the
/// analyzer's own.
pub(crate) const FLOWDROID_ANDROID_PLATFORM_SHA256: &str =
    "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad";

/// The zip path of the version-bearing properties file inside the pinned jar.
pub(crate) const FLOWDROID_POM_PROPERTIES: &str =
    "META-INF/maven/de.fraunhofer.sit.sse.flowdroid/soot-infoflow-cmd/pom.properties";

pub(crate) const FLOWDROID_TEMPLATE_DIR: &str = "adapters/flowdroid/template";
pub(crate) const FLOWDROID_CONFIG_DIR: &str = "adapters/flowdroid/config";
pub(crate) const FLOWDROID_SOURCES_PLACEHOLDER: &str = "__DFB_SOURCE_SIGNATURES__";
pub(crate) const FLOWDROID_SINKS_PLACEHOLDER: &str = "__DFB_SINK_SIGNATURES__";
pub(crate) const FLOWDROID_PACKAGE_PLACEHOLDER: &str = "__DFB_PACKAGE__";
pub(crate) const FLOWDROID_ENTRY_CALL_PLACEHOLDER: &str = "__DFB_ENTRY_CALL__";

/// The failure banner the pinned CLI prints while still exiting zero; its
/// presence disqualifies a run's evidence.
pub(crate) const FLOWDROID_FAILURE_BANNER: &str = "The data flow analysis has failed";

pub(crate) enum FlowdroidKernel {
    Java {
        javac: PathBuf,
    },
    Kotlin {
        kotlinc: PathBuf,
        kotlin_stdlib: PathBuf,
    },
}

impl FlowdroidKernel {
    /// The one package this language's core fixtures declare. The committed
    /// binary manifest names the harness activity inside it, so a fixture
    /// declaring any other package is a benchmark defect the runner refuses,
    /// never a case outcome.
    pub(crate) fn fixture_package(&self) -> &'static str {
        match self {
            Self::Java { .. } => "dataflowbench.taint",
            Self::Kotlin { .. } => "dataflowbench",
        }
    }

    /// The committed binary (AXML) manifest blob for this language's APKs.
    pub(crate) fn manifest(&self) -> String {
        format!(
            "{FLOWDROID_TEMPLATE_DIR}/AndroidManifest-{}.xml",
            self.language()
        )
    }

    /// The committed harness-activity wrapper template.
    pub(crate) fn wrapper_template(&self) -> String {
        format!(
            "{FLOWDROID_TEMPLATE_DIR}/DfbCaseActivity.{}.tmpl",
            self.wrapper_extension()
        )
    }

    pub(crate) fn wrapper_extension(&self) -> &'static str {
        match self {
            Self::Java { .. } => "java",
            Self::Kotlin { .. } => "kt",
        }
    }

    /// Both kernels resolve endpoint names with the Java anchor dialect, as
    /// the OpenTaint kernels do: the Kotlin fixtures satisfy its surface
    /// contract (`fun name(params)` declarations, `//` comments).
    pub(crate) fn dialect(&self) -> AnchorDialect {
        AnchorDialect::Java
    }
}

/// FlowDroid's population over the shared contract.
///
/// The whole core denominator is scored: the analyzer's documented surface
/// fences no construct class off, so there is no documented partition to
/// preregister `unsupported` cells from.
impl KernelPopulation for FlowdroidKernel {
    fn tool(&self) -> &'static str {
        "flowdroid"
    }

    fn language(&self) -> &'static str {
        match self {
            Self::Java { .. } => "java",
            Self::Kotlin { .. } => "kotlin",
        }
    }

    fn display_name(&self) -> &'static str {
        match self {
            Self::Java { .. } => "Java",
            Self::Kotlin { .. } => "Kotlin",
        }
    }

    fn report(&self) -> String {
        format!("reports/flowdroid-{}-kernel.json", self.language())
    }

    fn raw_dir(&self) -> String {
        format!("reports/raw/flowdroid-{}-kernel", self.language())
    }

    fn label(&self) -> String {
        format!("FlowDroid {} kernel", self.display_name())
    }

    /// Every committed template and configuration file, so one hash binds the
    /// whole set.
    fn configuration_paths(&self, _cases: &LoadedCases) -> Result<BTreeSet<PathBuf>> {
        Ok(flowdroid_template_paths())
    }
}

/// Every committed FlowDroid artifact, so one configuration hash binds the
/// whole materialization-and-endpoint surface for both language reports the
/// way the Semgrep kernels' rule set does.
pub(crate) fn flowdroid_template_paths() -> BTreeSet<PathBuf> {
    BTreeSet::from([
        PathBuf::from(format!("{FLOWDROID_TEMPLATE_DIR}/AndroidManifest-java.xml")),
        PathBuf::from(format!(
            "{FLOWDROID_TEMPLATE_DIR}/AndroidManifest-kotlin.xml"
        )),
        PathBuf::from(format!(
            "{FLOWDROID_TEMPLATE_DIR}/DfbCaseActivity.java.tmpl"
        )),
        PathBuf::from(format!("{FLOWDROID_TEMPLATE_DIR}/DfbCaseActivity.kt.tmpl")),
        PathBuf::from(format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt")),
    ])
}

/// Witness the identity of the exact FlowDroid jar and Android platform jar
/// this run invokes: the measured digest of both artifacts' bytes, plus the
/// version the jar self-reports in its embedded Maven `pom.properties`. The
/// pinned version is published only when the witnessed digests and the
/// witnessed version all match the pins; a mismatch fails the run with the
/// measured values in the error, so a report can never carry an asserted
/// identity.
pub(crate) fn witness_flowdroid_identity(
    flowdroid_jar: &Path,
    android_platform: &Path,
) -> Result<ToolIdentity> {
    let jar_digest =
        format!(
            "{:x}",
            Sha256::digest(fs::read(flowdroid_jar).with_context(|| {
                format!("read the FlowDroid jar {}", flowdroid_jar.display())
            })?)
        );
    if jar_digest != FLOWDROID_JAR_SHA256 {
        bail!(
            "the FlowDroid jar at {} has witnessed sha256 {jar_digest}, but the pinned {FLOWDROID_PINNED_VERSION} artifact is {FLOWDROID_JAR_SHA256}; refusing to publish a pinned identity for an artifact that is not the pinned artifact",
            flowdroid_jar.display()
        );
    }
    let platform_digest = format!(
        "{:x}",
        Sha256::digest(fs::read(android_platform).with_context(|| {
            format!(
                "read the Android platform jar {}",
                android_platform.display()
            )
        })?)
    );
    if platform_digest != FLOWDROID_ANDROID_PLATFORM_SHA256 {
        bail!(
            "the Android platform jar at {} has witnessed sha256 {platform_digest}, but the pinned android-34 platform is {FLOWDROID_ANDROID_PLATFORM_SHA256}; refusing to publish a pinned identity for an artifact that is not the pinned artifact",
            android_platform.display()
        );
    }
    let properties = Command::new("unzip")
        .arg("-p")
        .arg(flowdroid_jar)
        .arg(FLOWDROID_POM_PROPERTIES)
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("read {FLOWDROID_POM_PROPERTIES} from the FlowDroid jar"))?;
    if !properties.status.success() {
        bail!(
            "unzip failed with status {} reading {FLOWDROID_POM_PROPERTIES} from {}",
            properties.status,
            flowdroid_jar.display()
        );
    }
    let stdout = String::from_utf8_lossy(&properties.stdout);
    let version = stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("version="))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("the FlowDroid jar's pom.properties reports no version")?
        .to_string();
    if version != FLOWDROID_PINNED_VERSION {
        bail!(
            "the FlowDroid jar at {} self-reports version {version:?}, but this adapter pins {FLOWDROID_PINNED_VERSION:?}; refusing to run",
            flowdroid_jar.display()
        );
    }
    Ok(ToolIdentity::new(
        version,
        format!(
            "soot-infoflow-cmd-{FLOWDROID_PINNED_VERSION}-jar-with-dependencies.jar sha256:{jar_digest}; android-34 platform android.jar sha256:{platform_digest}"
        ),
    ))
}

/// Witness the dex translator's self-reported version. D8 is harness
/// materialization plumbing — it decides whether an APK exists, never what
/// the analyzer claims about it — so its identity rides in the environment
/// stamp rather than gating the run against a pinned constant the way the
/// analyzer's does.
pub(crate) fn witness_flowdroid_d8(java: &Path, d8_jar: &Path) -> Result<String> {
    let output = Command::new(java)
        .arg("-cp")
        .arg(d8_jar)
        .arg("com.android.tools.r8.D8")
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run D8 --version from {}", d8_jar.display()))?;
    if !output.status.success() {
        bail!(
            "D8 --version failed with status {} from {}",
            output.status,
            d8_jar.display()
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let version = stdout
        .lines()
        .map(str::trim)
        .find(|line| line.starts_with("D8 "))
        .context("D8 did not report a version")?
        .to_string();
    let digest = format!(
        "{:x}",
        Sha256::digest(
            fs::read(d8_jar).with_context(|| format!("read the r8 jar {}", d8_jar.display()))?
        )
    );
    Ok(format!("{version}; r8 jar sha256:{digest}"))
}

/// One method of one compiled fixture class.
pub(crate) struct JvmMethod {
    pub(crate) name: String,
    pub(crate) descriptor: String,
    pub(crate) access_flags: u16,
}

impl JvmMethod {
    /// Compiler-synthesized members (bridges, lambda bodies, Kotlin
    /// `access$` shims) never carry a benchmark marker, so they are invisible
    /// to endpoint and entry resolution.
    pub(crate) fn is_synthetic(&self) -> bool {
        const ACC_BRIDGE: u16 = 0x0040;
        const ACC_SYNTHETIC: u16 = 0x1000;
        self.access_flags & (ACC_BRIDGE | ACC_SYNTHETIC) != 0
    }
}

/// One compiled fixture class: its binary name and declared methods, read
/// from the class-file constant pool so the endpoint signatures FlowDroid is
/// given are witnessed from the bytecode the APK actually carries.
pub(crate) struct JvmClass {
    pub(crate) binary_name: String,
    pub(crate) methods: Vec<JvmMethod>,
}

/// Parse the constant pool, class name, and method table of one class file.
/// This is deliberately a minimal reader — names and descriptors only — and
/// every read is bounds-checked so a truncated file is an error, never a
/// panic.
pub(crate) fn parse_class_file(bytes: &[u8]) -> Result<JvmClass> {
    struct Cursor<'a> {
        bytes: &'a [u8],
        offset: usize,
    }
    impl<'a> Cursor<'a> {
        fn take(&mut self, count: usize) -> Result<&'a [u8]> {
            let end = self
                .offset
                .checked_add(count)
                .filter(|end| *end <= self.bytes.len())
                .context("class file is truncated")?;
            let slice = &self.bytes[self.offset..end];
            self.offset = end;
            Ok(slice)
        }
        fn u8(&mut self) -> Result<u8> {
            Ok(self.take(1)?[0])
        }
        fn u16(&mut self) -> Result<u16> {
            let slice = self.take(2)?;
            Ok(u16::from_be_bytes([slice[0], slice[1]]))
        }
        fn u32(&mut self) -> Result<u32> {
            let slice = self.take(4)?;
            Ok(u32::from_be_bytes([slice[0], slice[1], slice[2], slice[3]]))
        }
    }

    let mut cursor = Cursor { bytes, offset: 0 };
    if cursor.u32()? != 0xCAFE_BABE {
        bail!("not a class file: bad magic");
    }
    cursor.u32()?; // minor + major version
    let constant_pool_count = cursor.u16()?;
    let mut utf8 = BTreeMap::new();
    let mut classes = BTreeMap::new();
    let mut index = 1u16;
    while index < constant_pool_count {
        let tag = cursor.u8()?;
        match tag {
            1 => {
                let length = cursor.u16()? as usize;
                let value = String::from_utf8_lossy(cursor.take(length)?).into_owned();
                utf8.insert(index, value);
            }
            7 => {
                classes.insert(index, cursor.u16()?);
            }
            8 | 16 | 19 | 20 => {
                cursor.take(2)?;
            }
            15 => {
                cursor.take(3)?;
            }
            3 | 4 | 9 | 10 | 11 | 12 | 17 | 18 => {
                cursor.take(4)?;
            }
            5 | 6 => {
                cursor.take(8)?;
                index += 1; // longs and doubles occupy two constant-pool slots
            }
            other => bail!("unsupported constant-pool tag {other}"),
        }
        index += 1;
    }
    cursor.u16()?; // access flags
    let this_class = cursor.u16()?;
    let binary_name = classes
        .get(&this_class)
        .and_then(|name_index| utf8.get(name_index))
        .context("class file names no this_class")?
        .replace('/', ".");
    cursor.u16()?; // super class
    let interfaces = cursor.u16()?;
    cursor.take(interfaces as usize * 2)?;
    let skip_attributes = |cursor: &mut Cursor| -> Result<()> {
        let count = cursor.u16()?;
        for _ in 0..count {
            cursor.u16()?; // attribute name
            let length = cursor.u32()? as usize;
            cursor.take(length)?;
        }
        Ok(())
    };
    let fields = cursor.u16()?;
    for _ in 0..fields {
        cursor.take(6)?; // access flags, name, descriptor
        skip_attributes(&mut cursor)?;
    }
    let method_count = cursor.u16()?;
    let mut methods = Vec::with_capacity(method_count as usize);
    for _ in 0..method_count {
        let access_flags = cursor.u16()?;
        let name_index = cursor.u16()?;
        let descriptor_index = cursor.u16()?;
        skip_attributes(&mut cursor)?;
        methods.push(JvmMethod {
            name: utf8
                .get(&name_index)
                .context("method name is not a Utf8 constant")?
                .clone(),
            descriptor: utf8
                .get(&descriptor_index)
                .context("method descriptor is not a Utf8 constant")?
                .clone(),
            access_flags,
        });
    }
    Ok(JvmClass {
        binary_name,
        methods,
    })
}

/// Parse every compiled class under one directory.
pub(crate) fn parse_class_directory(classes: &Path) -> Result<Vec<JvmClass>> {
    let mut parsed = Vec::new();
    let mut paths: Vec<PathBuf> = WalkDir::new(classes)
        .into_iter()
        .filter_map(std::result::Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| entry.into_path())
        .filter(|path| path.extension().is_some_and(|ext| ext == "class"))
        .collect();
    paths.sort();
    for path in paths {
        let bytes = fs::read(&path)?;
        parsed.push(
            parse_class_file(&bytes)
                .with_context(|| format!("parse class file {}", path.display()))?,
        );
    }
    Ok(parsed)
}

/// One parameter or return type of a JVM method descriptor, in the Java
/// source spelling Soot signatures use.
pub(crate) fn jvm_descriptor_type(descriptor: &mut &str) -> std::result::Result<String, String> {
    let mut dimensions = 0usize;
    while let Some(rest) = descriptor.strip_prefix('[') {
        *descriptor = rest;
        dimensions += 1;
    }
    let (base, rest) = match descriptor.chars().next() {
        Some('B') => ("byte".to_string(), &descriptor[1..]),
        Some('C') => ("char".to_string(), &descriptor[1..]),
        Some('D') => ("double".to_string(), &descriptor[1..]),
        Some('F') => ("float".to_string(), &descriptor[1..]),
        Some('I') => ("int".to_string(), &descriptor[1..]),
        Some('J') => ("long".to_string(), &descriptor[1..]),
        Some('S') => ("short".to_string(), &descriptor[1..]),
        Some('Z') => ("boolean".to_string(), &descriptor[1..]),
        Some('V') => ("void".to_string(), &descriptor[1..]),
        Some('L') => {
            let end = descriptor
                .find(';')
                .ok_or_else(|| format!("unterminated object type in {descriptor:?}"))?;
            (descriptor[1..end].replace('/', "."), &descriptor[end + 1..])
        }
        _ => return Err(format!("unsupported descriptor {descriptor:?}")),
    };
    *descriptor = rest;
    Ok(format!("{base}{}", "[]".repeat(dimensions)))
}

/// The Soot method signature — `<a.b.Class: RetType name(P1,P2)>` — that
/// FlowDroid's sources-and-sinks file and its results XML both spell.
pub(crate) fn soot_method_signature(
    class_binary_name: &str,
    method: &JvmMethod,
) -> std::result::Result<String, String> {
    let descriptor = method.descriptor.as_str();
    let mut rest = descriptor
        .strip_prefix('(')
        .ok_or_else(|| format!("descriptor {descriptor:?} does not open a parameter list"))?;
    let mut parameters = Vec::new();
    while !rest.starts_with(')') {
        if rest.is_empty() {
            return Err(format!(
                "descriptor {descriptor:?} never closes its parameter list"
            ));
        }
        parameters.push(jvm_descriptor_type(&mut rest)?);
    }
    let mut rest = &rest[1..];
    let return_type = jvm_descriptor_type(&mut rest)?;
    if !rest.is_empty() {
        return Err(format!("descriptor {descriptor:?} has trailing bytes"));
    }
    Ok(format!(
        "<{class_binary_name}: {return_type} {}({})>",
        method.name,
        parameters.join(",")
    ))
}

/// Every witnessed signature for one marker-derived endpoint name, across all
/// compiled fixture classes. The endpoint contract is name-based, exactly as
/// it is for the Joern, Semgrep, and OpenTaint kernels, whose queries and
/// rules also match every declaration of the marker's name; the compiled
/// classes only make the denoted signatures exact.
pub(crate) fn flowdroid_endpoint_signatures(
    classes: &[JvmClass],
    endpoint_name: &str,
) -> std::result::Result<BTreeSet<String>, String> {
    let mut signatures = BTreeSet::new();
    for class in classes {
        for method in &class.methods {
            if method.name == endpoint_name && !method.is_synthetic() {
                signatures.insert(soot_method_signature(&class.binary_name, method)?);
            }
        }
    }
    if signatures.is_empty() {
        return Err(format!(
            "no compiled fixture class declares a method named {endpoint_name:?}"
        ));
    }
    Ok(signatures)
}

/// The wrapper's call into the fixture's entry method, witnessed from the
/// compiled classes. Every core fixture in both languages declares exactly
/// one method named `run`, with either no parameters or one boolean (the
/// branch-join pair); the boolean argument is derived from the activity
/// bundle so it stays statically unknown and the harness decides no fixture
/// branch. Anything else is unresolvable entry evidence: `inconclusive` with
/// the reason retained, never a synthesized outcome.
pub(crate) fn flowdroid_entry_call(classes: &[JvmClass]) -> std::result::Result<String, String> {
    let mut candidates = Vec::new();
    for class in classes {
        for method in &class.methods {
            if method.name == "run" && !method.is_synthetic() {
                candidates.push((class.binary_name.clone(), method.descriptor.clone()));
            }
        }
    }
    let (class, descriptor) = match candidates.len() {
        1 => candidates.remove(0),
        count => {
            return Err(format!(
                "expected exactly one entry method named \"run\" in the compiled fixtures, found {count}"
            ));
        }
    };
    let simple_name = class
        .rsplit('.')
        .next()
        .filter(|name| !name.contains('$'))
        .ok_or_else(|| format!("entry class {class:?} is not a top-level class"))?;
    match descriptor.as_str() {
        "()V" => Ok(format!("{simple_name}.run()")),
        "(Z)V" => Ok(format!("{simple_name}.run(savedInstanceState == null)")),
        other => Err(format!(
            "entry method {class}.run has unsupported descriptor {other:?}"
        )),
    }
}

/// CRC-32 (the zip polynomial), computed directly; the APK's two or three
/// entries are small enough that a table buys nothing.
pub(crate) fn zip_crc32(bytes: &[u8]) -> u32 {
    let mut crc = 0xFFFF_FFFFu32;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            let mask = (crc & 1).wrapping_neg();
            crc = (crc >> 1) ^ (0xEDB8_8320 & mask);
        }
    }
    !crc
}

/// Write a stored (uncompressed) zip — the minimal APK FlowDroid's dex and
/// manifest readers need. Entries are written in the order given, with fixed
/// timestamps so a rebuilt APK differs only where its contents differ.
pub(crate) fn write_stored_zip(path: &Path, entries: &[(&str, &[u8])]) -> Result<()> {
    let mut file = Vec::new();
    let mut central = Vec::new();
    let mut offsets = Vec::new();
    for (name, bytes) in entries {
        let crc = zip_crc32(bytes);
        offsets.push(file.len() as u32);
        file.extend_from_slice(&0x0403_4B50u32.to_le_bytes());
        file.extend_from_slice(&20u16.to_le_bytes()); // version needed
        file.extend_from_slice(&0u16.to_le_bytes()); // flags
        file.extend_from_slice(&0u16.to_le_bytes()); // stored
        file.extend_from_slice(&0u32.to_le_bytes()); // time + date
        file.extend_from_slice(&crc.to_le_bytes());
        file.extend_from_slice(&(bytes.len() as u32).to_le_bytes()); // compressed
        file.extend_from_slice(&(bytes.len() as u32).to_le_bytes()); // uncompressed
        file.extend_from_slice(&(name.len() as u16).to_le_bytes());
        file.extend_from_slice(&0u16.to_le_bytes()); // extra length
        file.extend_from_slice(name.as_bytes());
        file.extend_from_slice(bytes);
    }
    let central_offset = file.len() as u32;
    for ((name, bytes), offset) in entries.iter().zip(&offsets) {
        let crc = zip_crc32(bytes);
        central.extend_from_slice(&0x0201_4B50u32.to_le_bytes());
        central.extend_from_slice(&20u16.to_le_bytes()); // version made by
        central.extend_from_slice(&20u16.to_le_bytes()); // version needed
        central.extend_from_slice(&0u16.to_le_bytes()); // flags
        central.extend_from_slice(&0u16.to_le_bytes()); // stored
        central.extend_from_slice(&0u32.to_le_bytes()); // time + date
        central.extend_from_slice(&crc.to_le_bytes());
        central.extend_from_slice(&(bytes.len() as u32).to_le_bytes());
        central.extend_from_slice(&(bytes.len() as u32).to_le_bytes());
        central.extend_from_slice(&(name.len() as u16).to_le_bytes());
        central.extend_from_slice(&0u16.to_le_bytes()); // extra length
        central.extend_from_slice(&0u16.to_le_bytes()); // comment length
        central.extend_from_slice(&0u16.to_le_bytes()); // disk number
        central.extend_from_slice(&0u16.to_le_bytes()); // internal attributes
        central.extend_from_slice(&0u32.to_le_bytes()); // external attributes
        central.extend_from_slice(&offset.to_le_bytes());
        central.extend_from_slice(name.as_bytes());
    }
    file.extend_from_slice(&central);
    file.extend_from_slice(&0x0605_4B50u32.to_le_bytes());
    file.extend_from_slice(&0u16.to_le_bytes()); // disk number
    file.extend_from_slice(&0u16.to_le_bytes()); // central directory disk
    file.extend_from_slice(&(entries.len() as u16).to_le_bytes());
    file.extend_from_slice(&(entries.len() as u16).to_le_bytes());
    file.extend_from_slice(&(central.len() as u32).to_le_bytes());
    file.extend_from_slice(&central_offset.to_le_bytes());
    file.extend_from_slice(&0u16.to_le_bytes()); // comment length
    fs::write(path, file).with_context(|| format!("write {}", path.display()))?;
    Ok(())
}

/// Unescape the five XML character entities FlowDroid's writer emits.
pub(crate) fn xml_unescape(value: &str) -> String {
    value
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&")
}

/// The value of one attribute inside one element fragment of FlowDroid's
/// machine-written results XML. The writer always emits `name="value"` with
/// the five entities escaped, so a quote-delimited scan is exact for this
/// document class; anything the scan cannot resolve stays `None` and the
/// caller treats the evidence as unreadable rather than guessing.
pub(crate) fn flowdroid_xml_attribute(fragment: &str, name: &str) -> Option<String> {
    let key = format!("{name}=\"");
    let start = fragment.find(&key)? + key.len();
    let end = fragment[start..].find('"')? + start;
    Some(xml_unescape(&fragment[start..end]))
}

/// The `TerminationState` FlowDroid's results document self-reports.
pub(crate) fn flowdroid_termination_state(xml: &str) -> Option<String> {
    let start = xml.find("<DataFlowResults")?;
    let end = xml[start..].find('>')? + start;
    flowdroid_xml_attribute(&xml[start..end], "TerminationState")
}

/// The sink definition signature of every `<Result>` in the results XML —
/// the `MethodSourceSinkDefinition` FlowDroid echoes back from the
/// sources-and-sinks file, which is what reconciliation matches against the
/// case's witnessed sink signatures.
pub(crate) fn flowdroid_sink_definitions(xml: &str) -> Vec<String> {
    let mut definitions = Vec::new();
    for fragment in xml.split("<Sink ").skip(1) {
        let end = fragment.find('>').unwrap_or(fragment.len());
        if let Some(definition) =
            flowdroid_xml_attribute(&fragment[..end], "MethodSourceSinkDefinition")
        {
            definitions.push(definition);
        }
    }
    definitions
}

/// The leak count from the analyzer's own completion line, or the reason the
/// log disqualifies the run. The pinned CLI exits zero even when the
/// analysis fails outright, so the completion line is the one signal that
/// the analysis actually ran to its end; without it, an absent results file
/// would be indistinguishable from a crash, and the contract forbids reading
/// that as `not-reached`.
pub(crate) fn flowdroid_completion_leaks(log: &str) -> std::result::Result<u64, String> {
    if let Some(line) = log
        .lines()
        .find(|line| line.contains(FLOWDROID_FAILURE_BANNER))
    {
        return Err(format!("the analyzer reported failure: {}", line.trim()));
    }
    for line in log.lines() {
        if let Some(rest) = line.split("Found ").nth(1)
            && let Some((count, rest)) = rest.split_once(" leaks from ")
            && rest.contains("sources")
            && let Ok(count) = count.trim().parse::<u64>()
        {
            return Ok(count);
        }
    }
    Err("the analyzer log carries no completion line, so the analysis cannot be shown to have finished".to_string())
}

pub(crate) fn select_flowdroid_cases(kernel: &FlowdroidKernel) -> Result<LoadedCases> {
    select_kernel_cases(kernel)
}

/// Everything a FlowDroid run needs beyond the kernel's own toolchain: the
/// analyzer jar, the platform jar, the dex translator, and the JVM that runs
/// both jars.
pub(crate) struct FlowdroidTools {
    pub(crate) flowdroid_jar: PathBuf,
    pub(crate) android_platform: PathBuf,
    pub(crate) d8_jar: PathBuf,
    pub(crate) java: PathBuf,
}

pub(crate) fn run_flowdroid_kernel(tools: &FlowdroidTools, kernel: FlowdroidKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_flowdroid_cases(&kernel)?;
    let configuration_paths = kernel.configuration_paths(&selected)?;
    let sources_sinks_template_path = format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt");
    let sources_sinks_template =
        fs::read_to_string(&sources_sinks_template_path).with_context(|| {
            format!("read the FlowDroid endpoint template {sources_sinks_template_path}")
        })?;
    for placeholder in [FLOWDROID_SOURCES_PLACEHOLDER, FLOWDROID_SINKS_PLACEHOLDER] {
        if !sources_sinks_template.contains(placeholder) {
            bail!(
                "FlowDroid endpoint template {sources_sinks_template_path} does not carry {placeholder}"
            );
        }
    }
    let wrapper_template_path = kernel.wrapper_template();
    let wrapper_template = fs::read_to_string(&wrapper_template_path)
        .with_context(|| format!("read the FlowDroid wrapper template {wrapper_template_path}"))?;
    for placeholder in [
        FLOWDROID_PACKAGE_PLACEHOLDER,
        FLOWDROID_ENTRY_CALL_PLACEHOLDER,
    ] {
        if !wrapper_template.contains(placeholder) {
            bail!(
                "FlowDroid wrapper template {wrapper_template_path} does not carry {placeholder}"
            );
        }
    }
    let manifest_path = kernel.manifest();
    let manifest = fs::read(&manifest_path)
        .with_context(|| format!("read the committed manifest blob {manifest_path}"))?;
    let raw_dir = PathBuf::from(kernel.raw_dir());
    fs::create_dir_all(&raw_dir)?;
    let started = now_seconds()?;
    let mut identity = witness_flowdroid_identity(&tools.flowdroid_jar, &tools.android_platform)?;
    let d8_identity = witness_flowdroid_d8(&tools.java, &tools.d8_jar)?;
    identity.build_identity = format!("{}; dexed by {d8_identity}", identity.build_identity);
    write_run_environment(&raw_dir, "flowdroid", &identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_flowdroid_case(
            tools,
            &kernel,
            &sources_sinks_template,
            &wrapper_template,
            &manifest,
            &path,
            &case,
            &raw_dir,
            &[],
            FlowdroidPhaseMode::KernelTotal,
            kernel.dialect(),
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = normalized_report(
        kernel.tool(),
        &identity,
        &configuration_hash,
        &revision,
        started,
        results,
    )?;
    let report_path = kernel.report();
    write_and_validate_report(Path::new(&report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

pub(crate) fn flowdroid_case_scratch(kernel: &FlowdroidKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-flowdroid-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

pub(crate) fn write_flowdroid_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    write_runner_error("flowdroid", raw_dir, id, stage, diagnostic, output)
}

/// Record an `inconclusive` decision with its retained reason: evidence the
/// runner cannot use, never a clean negative.
pub(crate) fn write_flowdroid_inconclusive(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    reason: &str,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "flowdroid",
            "case_id": id,
            "state": "inconclusive",
            "stage": stage,
            "reason": reason,
            "evidence_kind": "retained-anchor-resolution"
        }))? + "\n",
    )?;
    Ok(error_path)
}

/// Which phase boundaries a FlowDroid case's timing sidecar records.
///
/// The kernels time the one analyzer subprocess as `total` and leave the APK
/// materialization untimed, per the latency tier's preregistered FlowDroid
/// row. The modeling population records all three adapter-observable
/// subprocess boundaries — `compile` (both javac invocations), `dex` (the D8
/// translation), and `analyze` (the FlowDroid invocation) — declared by the
/// latency tier's Amendment A20; only `analyze` is an analyzer number, and it
/// is the phase comparable to the kernels' `total`.
#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum FlowdroidPhaseMode {
    KernelTotal,
    CompileDexAnalyze,
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn run_flowdroid_case(
    tools: &FlowdroidTools,
    kernel: &FlowdroidKernel,
    sources_sinks_template: &str,
    wrapper_template: &str,
    manifest: &[u8],
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
    extra_analyzer_args: &[String],
    phase_mode: FlowdroidPhaseMode,
    // The dialect endpoint *names* are resolved under. The kernels use the
    // kernel Java dialect; the modeling population resolves the declared
    // entities' member-qualified callsites (`Audit.record(v)`) under the same
    // `JavaMember` dialect every other adapter's modeling run uses.
    // Reconciliation is unaffected either way: FlowDroid outcomes are decided
    // against the echoed sink definitions, never against source lines.
    dialect: AnchorDialect,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let xml_path = raw_dir.join(format!("{id}-results.xml"));
    let sources_sinks_path = raw_dir.join(format!("{id}-sources-sinks.txt"));
    let wrapper_path = raw_dir.join(format!("{id}-wrapper.{}", kernel.wrapper_extension()));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [
        &raw_path,
        &error_path,
        &xml_path,
        &sources_sinks_path,
        &wrapper_path,
        &timing_path,
    ] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence: `inconclusive` with a retained reason, never a
    // clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, dialect) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled FlowDroid endpoints: {reason}");
            let path =
                write_flowdroid_inconclusive(raw_dir, id, "endpoint-resolution", &diagnostic)?;
            return Ok(("inconclusive", vec![diagnostic], path));
        }
    };

    let scratch = flowdroid_case_scratch(kernel, id)?;
    let result = (|| {
        // Materialize the fixtures on their package paths, exactly as the
        // OpenTaint kernels do. The committed manifest names the harness
        // activity inside the language's one fixture package, so a fixture
        // declaring any other package is a benchmark defect the runner
        // refuses, never a case outcome.
        let source_root = scratch.join("source");
        let classes = scratch.join("classes");
        for directory in [&source_root, &classes] {
            fs::create_dir_all(directory)?;
        }
        let fixture_root = case_path.parent().expect("case path has parent");
        let mut compile_inputs = Vec::new();
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            let body = fs::read_to_string(fixture_root.join(fixture))?;
            let package = jvm_fixture_package(fixture, &body)?;
            if package != kernel.fixture_package() {
                bail!(
                    "fixture {fixture} declares package {package:?}, but the committed {} manifest expects {:?}",
                    kernel.display_name(),
                    kernel.fixture_package()
                );
            }
            let package_dir = source_root.join(package.replace('.', "/"));
            fs::create_dir_all(&package_dir)?;
            let target = package_dir.join(fixture);
            fs::copy(fixture_root.join(fixture), &target)?;
            compile_inputs.push(target);
        }

        // The fixture compile, the wrapper compile, the dex translation, and
        // the APK assembly are all harness materialization — this adapter's
        // input encoding, like the OpenTaint kernels' compiled classes — so
        // none of them is timed, per docs/adapters.md.
        let mut compile = match kernel {
            FlowdroidKernel::Java { javac } => Command::new(javac),
            FlowdroidKernel::Kotlin { kotlinc, .. } => Command::new(kotlinc),
        };
        compile
            .arg("-nowarn")
            .arg("-d")
            .arg(&classes)
            .args(&compile_inputs)
            .stdin(std::process::Stdio::null());
        let fixture_compile_started = Instant::now();
        let compiled = match compile.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the {} fixture compiler: {error}",
                    kernel.display_name()
                );
                let path =
                    write_flowdroid_error(raw_dir, id, "fixture-compile", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let fixture_compile_elapsed = fixture_compile_started.elapsed();
        if !compiled.status.success() {
            let diagnostic = format!(
                "{} fixture compilation failed with status {}",
                kernel.display_name(),
                compiled.status
            );
            let path = write_flowdroid_error(
                raw_dir,
                id,
                "fixture-compile",
                &diagnostic,
                Some(&compiled),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        // Witness the entry shape and the endpoint signatures from the
        // compiled classes: what the APK will actually carry, not what
        // source-text parsing guesses.
        let parsed_classes = parse_class_directory(&classes)?;
        let entry_call = match flowdroid_entry_call(&parsed_classes) {
            Ok(call) => call,
            Err(reason) => {
                let diagnostic = format!("cannot derive the harness entry call: {reason}");
                let path =
                    write_flowdroid_inconclusive(raw_dir, id, "entry-resolution", &diagnostic)?;
                return Ok(("inconclusive", vec![diagnostic], path));
            }
        };
        let signatures =
            |endpoint_name: &str| flowdroid_endpoint_signatures(&parsed_classes, endpoint_name);
        let source_signatures = match signatures(&endpoints.source_function) {
            Ok(signatures) => signatures,
            Err(reason) => {
                let diagnostic = format!("cannot witness the source endpoint signature: {reason}");
                let path =
                    write_flowdroid_inconclusive(raw_dir, id, "endpoint-resolution", &diagnostic)?;
                return Ok(("inconclusive", vec![diagnostic], path));
            }
        };
        let sink_signatures = match signatures(&endpoints.sink_function) {
            Ok(signatures) => signatures,
            Err(reason) => {
                let diagnostic = format!("cannot witness the sink endpoint signature: {reason}");
                let path =
                    write_flowdroid_inconclusive(raw_dir, id, "endpoint-resolution", &diagnostic)?;
                return Ok(("inconclusive", vec![diagnostic], path));
            }
        };

        let sources_sinks = sources_sinks_template
            .replace(
                FLOWDROID_SOURCES_PLACEHOLDER,
                &source_signatures
                    .iter()
                    .map(|signature| format!("{signature} -> _SOURCE_"))
                    .collect::<Vec<_>>()
                    .join("\n"),
            )
            .replace(
                FLOWDROID_SINKS_PLACEHOLDER,
                &sink_signatures
                    .iter()
                    .map(|signature| format!("{signature} -> _SINK_"))
                    .collect::<Vec<_>>()
                    .join("\n"),
            );
        fs::write(&sources_sinks_path, &sources_sinks)?;

        let wrapper = wrapper_template
            .replace(FLOWDROID_PACKAGE_PLACEHOLDER, kernel.fixture_package())
            .replace(FLOWDROID_ENTRY_CALL_PLACEHOLDER, &entry_call);
        fs::write(&wrapper_path, &wrapper)?;
        let wrapper_source = source_root
            .join(kernel.fixture_package().replace('.', "/"))
            .join(format!("DfbCaseActivity.{}", kernel.wrapper_extension()));
        fs::write(&wrapper_source, &wrapper)?;

        let classpath = format!("{}:{}", tools.android_platform.display(), classes.display());
        let mut wrapper_compile = match kernel {
            FlowdroidKernel::Java { javac } => {
                let mut command = Command::new(javac);
                command.arg("-nowarn").arg("-cp").arg(&classpath);
                command
            }
            FlowdroidKernel::Kotlin { kotlinc, .. } => {
                let mut command = Command::new(kotlinc);
                command.arg("-nowarn").arg("-classpath").arg(&classpath);
                command
            }
        };
        wrapper_compile
            .arg("-d")
            .arg(&classes)
            .arg(&wrapper_source)
            .stdin(std::process::Stdio::null());
        let wrapper_compile_started = Instant::now();
        let wrapper_compiled = match wrapper_compile.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the {} wrapper compiler: {error}",
                    kernel.display_name()
                );
                let path =
                    write_flowdroid_error(raw_dir, id, "wrapper-compile", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let compile_elapsed = fixture_compile_elapsed + wrapper_compile_started.elapsed();
        if !wrapper_compiled.status.success() {
            let diagnostic = format!(
                "{} wrapper compilation failed with status {}",
                kernel.display_name(),
                wrapper_compiled.status
            );
            let path = write_flowdroid_error(
                raw_dir,
                id,
                "wrapper-compile",
                &diagnostic,
                Some(&wrapper_compiled),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        // Translate the compiled classes (and, for Kotlin, the pinned
        // standard library the fixtures link against) to dex.
        let mut class_files: Vec<PathBuf> = WalkDir::new(&classes)
            .into_iter()
            .filter_map(std::result::Result::ok)
            .filter(|entry| entry.file_type().is_file())
            .map(|entry| entry.into_path())
            .filter(|path| path.extension().is_some_and(|ext| ext == "class"))
            .collect();
        class_files.sort();
        let mut dex = Command::new(&tools.java);
        dex.arg("-cp")
            .arg(&tools.d8_jar)
            .arg("com.android.tools.r8.D8")
            .arg("--release")
            .arg("--min-api")
            .arg("21")
            .arg("--lib")
            .arg(&tools.android_platform)
            .arg("--output")
            .arg(&scratch)
            .args(&class_files)
            .stdin(std::process::Stdio::null());
        if let FlowdroidKernel::Kotlin { kotlin_stdlib, .. } = kernel {
            dex.arg(kotlin_stdlib);
        }
        let dex_started = Instant::now();
        let dexed = match dex.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!("failed to spawn the D8 dex translator: {error}");
                let path = write_flowdroid_error(raw_dir, id, "dex", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let dex_elapsed = dex_started.elapsed();
        if !dexed.status.success() {
            let diagnostic = format!("D8 dex translation failed with status {}", dexed.status);
            let path = write_flowdroid_error(raw_dir, id, "dex", &diagnostic, Some(&dexed))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let mut dex_files: Vec<PathBuf> = fs::read_dir(&scratch)?
            .filter_map(std::result::Result::ok)
            .map(|entry| entry.path())
            .filter(|path| {
                path.extension().is_some_and(|ext| ext == "dex")
                    && path
                        .file_name()
                        .and_then(|name| name.to_str())
                        .is_some_and(|name| name.starts_with("classes"))
            })
            .collect();
        dex_files.sort();
        if dex_files.is_empty() {
            let diagnostic = "D8 exited cleanly but produced no dex file".to_string();
            let path = write_flowdroid_error(raw_dir, id, "dex", &diagnostic, Some(&dexed))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        let mut entries: Vec<(String, Vec<u8>)> =
            vec![("AndroidManifest.xml".to_string(), manifest.to_vec())];
        for dex_file in &dex_files {
            entries.push((
                dex_file
                    .file_name()
                    .and_then(|name| name.to_str())
                    .expect("dex file names are ASCII")
                    .to_string(),
                fs::read(dex_file)?,
            ));
        }
        let apk_path = scratch.join("case.apk");
        write_stored_zip(
            &apk_path,
            &entries
                .iter()
                .map(|(name, bytes)| (name.as_str(), bytes.as_slice()))
                .collect::<Vec<_>>(),
        )?;

        // One FlowDroid invocation, indivisible from the adapter's vantage:
        // `total`, per the timing convention.
        let out_xml = scratch.join("out.xml");
        let resolved_sources_sinks =
            fs::canonicalize(&sources_sinks_path).unwrap_or_else(|_| sources_sinks_path.clone());
        let mut invocation = vec![
            tools.java.display().to_string(),
            "-jar".to_string(),
            tools.flowdroid_jar.display().to_string(),
            "-a".to_string(),
            apk_path.display().to_string(),
            "-p".to_string(),
            tools.android_platform.display().to_string(),
            "-s".to_string(),
            resolved_sources_sinks.display().to_string(),
            "-o".to_string(),
            out_xml.display().to_string(),
        ];
        invocation.extend(extra_analyzer_args.iter().cloned());
        let mut command = Command::new(&tools.java);
        command
            .args(&invocation[1..])
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the FlowDroid {} kernel analysis with {}: {error}",
                    kernel.display_name(),
                    tools.java.display()
                );
                let path = write_flowdroid_error(raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        match phase_mode {
            FlowdroidPhaseMode::KernelTotal => {
                write_case_phase_timings(raw_dir, "flowdroid", id, &[("total", invoked.elapsed())])?
            }
            FlowdroidPhaseMode::CompileDexAnalyze => write_case_phase_timings(
                raw_dir,
                "flowdroid",
                id,
                &[
                    ("compile", compile_elapsed),
                    ("dex", dex_elapsed),
                    ("analyze", invoked.elapsed()),
                ],
            )?,
        }
        if !output.status.success() {
            let diagnostic = format!(
                "FlowDroid {} kernel analysis failed with status {}",
                kernel.display_name(),
                output.status
            );
            let path = write_flowdroid_error(
                raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let log = format!(
            "{}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
        let leaks = match flowdroid_completion_leaks(&log) {
            Ok(leaks) => leaks,
            Err(reason) => {
                let diagnostic = format!("the analysis did not complete: {reason}");
                let path = write_flowdroid_error(
                    raw_dir,
                    id,
                    "analyzer-completion",
                    &diagnostic,
                    Some(&output),
                )?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };

        let xml = if out_xml.exists() {
            let xml = fs::read_to_string(&out_xml)
                .with_context(|| format!("read {}", out_xml.display()))?;
            fs::write(&xml_path, &xml)?;
            Some(xml)
        } else {
            None
        };

        let mut raw_document = json!({
            "adapter": "flowdroid",
            "case_id": id,
            "invocation": invocation,
            "exit_status": output.status.code(),
            "leaks_reported": leaks,
            "log": log,
            "results_xml": xml,
            "evidence_kind": "retained-analyzer-output"
        });

        let (outcome, diagnostics) = match &xml {
            Some(xml) => match flowdroid_termination_state(xml) {
                None => {
                    let diagnostic =
                        "the results XML carries no TerminationState and cannot be read"
                            .to_string();
                    let path = write_flowdroid_error(
                        raw_dir,
                        id,
                        "analyzer-output",
                        &diagnostic,
                        Some(&output),
                    )?;
                    return Ok(("runner-error", vec![diagnostic], path));
                }
                Some(state) if state != "Success" => {
                    // An incomplete analysis (a data-flow or path timeout, an
                    // abort) is never a negative.
                    let diagnostic = format!(
                        "FlowDroid self-reports TerminationState {state:?}; the analysis is incomplete"
                    );
                    ("inconclusive", vec![diagnostic])
                }
                Some(_) => {
                    let definitions = flowdroid_sink_definitions(xml);
                    let matched: Vec<&String> = definitions
                        .iter()
                        .filter(|definition| sink_signatures.contains(*definition))
                        .collect();
                    if !matched.is_empty() {
                        let diagnostic = format!(
                            "flow reported to anchored sink {}",
                            matched
                                .iter()
                                .map(|signature| format!("{signature:?}"))
                                .collect::<Vec<_>>()
                                .join(", ")
                        );
                        ("reached", vec![diagnostic])
                    } else if definitions.is_empty() {
                        ("not-reached", Vec::new())
                    } else {
                        let diagnostic = format!(
                            "the results XML reports {} flow(s), none reconcilable against the anchored sink signatures",
                            definitions.len()
                        );
                        ("inconclusive", vec![diagnostic])
                    }
                }
            },
            // The pinned CLI writes no results file at all for a leak-free
            // run; the completion line above is what proves the analysis
            // finished, so this — and only this — reads as a clean negative.
            None if leaks == 0 => ("not-reached", Vec::new()),
            None => {
                let diagnostic =
                    format!("the analyzer reported {leaks} leak(s) but wrote no results XML");
                let path = write_flowdroid_error(
                    raw_dir,
                    id,
                    "analyzer-output",
                    &diagnostic,
                    Some(&output),
                )?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        if outcome == "inconclusive" {
            raw_document["state"] = json!("inconclusive");
        }
        fs::write(
            &raw_path,
            serde_json::to_string_pretty(&raw_document)? + "\n",
        )?;
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("FlowDroid case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "FlowDroid case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Run the Java benchmark-controlled modeling matrix through the pinned
/// FlowDroid release (Amendment A18).
///
/// The kernel's per-case machinery is reused unchanged — APK materialization,
/// endpoint resolution from the fixture's own marker lines, witnessed Soot
/// signatures, the leak-line and failure-banner guards, and the echoed
/// sink-definition reconciliation. What differs is the model layer: the
/// analyzer runs under `-tw STUBDROID -t` the committed summaries directory,
/// which replaces the release default's bundled `summariesManual` provider so
/// the benchmark's declarations are the only summaries in the run, and the
/// timing sidecar records the three adapter-observable subprocess boundaries
/// (`compile`, `dex`, `analyze`) the latency tier's Amendment A20 declares
/// for this population.
pub(crate) fn run_flowdroid_modeling(
    tools: &FlowdroidTools,
    javac: PathBuf,
    language: ModelingLanguage,
) -> Result<()> {
    if language != ModelingLanguage::Java {
        bail!(
            "FlowDroid's modeling partition row applies to Java alone (docs/modeling-matrix.md, Amendment A18): the analyzer consumes JVM bytecode, so the {} modeling population is outside the adapter's language reach — which is different from a declined category",
            language.display_name()
        );
    }
    let plan = plan_modeling_run(ModelingTool::Flowdroid, language)?;
    fs::create_dir_all(&plan.raw_dir)?;

    let kernel = FlowdroidKernel::Java { javac };
    let sources_sinks_template_path = format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt");
    let sources_sinks_template =
        fs::read_to_string(&sources_sinks_template_path).with_context(|| {
            format!("read the FlowDroid endpoint template {sources_sinks_template_path}")
        })?;
    for placeholder in [FLOWDROID_SOURCES_PLACEHOLDER, FLOWDROID_SINKS_PLACEHOLDER] {
        if !sources_sinks_template.contains(placeholder) {
            bail!(
                "FlowDroid endpoint template {sources_sinks_template_path} does not carry {placeholder}"
            );
        }
    }
    let wrapper_template_path = kernel.wrapper_template();
    let wrapper_template = fs::read_to_string(&wrapper_template_path)
        .with_context(|| format!("read the FlowDroid wrapper template {wrapper_template_path}"))?;
    for placeholder in [
        FLOWDROID_PACKAGE_PLACEHOLDER,
        FLOWDROID_ENTRY_CALL_PLACEHOLDER,
    ] {
        if !wrapper_template.contains(placeholder) {
            bail!(
                "FlowDroid wrapper template {wrapper_template_path} does not carry {placeholder}"
            );
        }
    }
    let manifest_path = kernel.manifest();
    let manifest = fs::read(&manifest_path)
        .with_context(|| format!("read the committed manifest blob {manifest_path}"))?;
    // The committed summaries are the model; the analyzer's working directory
    // is the per-case scratch, so the path is resolved once, absolutely.
    let summaries = fs::canonicalize(FLOWDROID_MODELING_SUMMARIES_DIR)
        .context("resolve the FlowDroid modeling summaries directory")?;
    let analyzer_args = vec![
        "-tw".to_string(),
        FLOWDROID_MODELING_TAINT_WRAPPER_MODE.to_string(),
        "-t".to_string(),
        summaries.display().to_string(),
    ];

    let started = now_seconds()?;
    let mut identity = witness_flowdroid_identity(&tools.flowdroid_jar, &tools.android_platform)?;
    let d8_identity = witness_flowdroid_d8(&tools.java, &tools.d8_jar)?;
    identity.build_identity = format!("{}; dexed by {d8_identity}", identity.build_identity);
    write_run_environment(&plan.raw_dir, "flowdroid", &identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "modeling case")?;
        let start = Instant::now();
        // The preregistered partition is consulted first and decided from the
        // template identity, so a declined cell is never handed to the
        // analyzer and cannot produce an empty finding list that later reads
        // as a negative.
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            modeling_partition_outcome(
                ModelingTool::Flowdroid,
                case,
                &plan.raw_dir,
                &identity.version,
            )? {
            (outcome, vec![reason], raw_path)
        } else {
            run_flowdroid_case(
                tools,
                &kernel,
                &sources_sinks_template,
                &wrapper_template,
                &manifest,
                path,
                case,
                &plan.raw_dir,
                &analyzer_args,
                FlowdroidPhaseMode::CompileDexAnalyze,
                modeling_anchor_dialect(language)?,
            )?
        };
        results.push(normalized_result(
            case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }
    let report = normalized_report(
        "flowdroid",
        &identity,
        &hash_paths(&plan.configuration_paths)?,
        &revision,
        started,
        results,
    )?;
    write_and_validate_report(&plan.report, &report)?;
    let scored = modeling_supported_templates(ModelingTool::Flowdroid);
    let scored_assertions = plan
        .cases
        .iter()
        .filter(|(_, case)| {
            case["template_id"]
                .as_str()
                .is_some_and(|template| scored.contains(&template))
        })
        .count();
    let scored_categories: BTreeSet<ModelingCategory> = scored
        .iter()
        .filter_map(|template| modeling_category(template))
        .collect();
    println!(
        "wrote {} ({scored_assertions} scored, {} preregistered-unsupported, {} of six categories scored for {})",
        plan.report.display(),
        plan.cases.len() - scored_assertions,
        scored_categories.len(),
        ModelingTool::Flowdroid.pinned_identity()
    );
    Ok(())
}

/// Run the Java tool-native probe set for the pinned FlowDroid release
/// (Amendment A19).
///
/// The A16 activation partition declines all six templates from the shipped
/// catalog's own text, so no fixture is ever handed to the analyzer — but the
/// run still witnesses the pinned jar identity by digest exactly the way the
/// kernels do, because a report whose every cell is a retained capability
/// decision has nothing *but* that identity as evidence of which build the
/// decisions were pinned against.
pub(crate) fn run_flowdroid_native(
    flowdroid_jar: &Path,
    android_platform: &Path,
    language: ModelingLanguage,
) -> Result<()> {
    if language != ModelingLanguage::Java {
        bail!(
            "FlowDroid's tool-native activation row applies to Java alone (docs/native-profile.md, Amendment A19): the analyzer consumes JVM bytecode, so the {} native population is outside the adapter's language reach — which is different from a declined activation",
            language.display_name()
        );
    }
    let identity = witness_flowdroid_identity(flowdroid_jar, android_platform)?;
    run_native_with_identity(ModelingTool::Flowdroid, flowdroid_jar, language, identity)
}

/// FlowDroid: one analyzer invocation over a materialized APK.
///
/// The per-case APK materialization — the two compiles, the D8 dex
/// translation, the stored-zip assembly — is **outside** the timed window,
/// exactly as Amendment A12 puts it outside every cold FlowDroid number. The
/// estimate is the analyzer subprocess and nothing else, so it is the same
/// kind of quantity as the row it annotates.
pub(crate) fn overhead_run_flowdroid(
    tools: &OverheadTools,
    language: OverheadLanguage,
    run: usize,
    raw_dir: &Path,
) -> Result<OverheadRun> {
    let (package, wrapper_extension, manifest_file, wrapper_template_file, compiler) =
        match language {
            OverheadLanguage::Java => (
                "dataflowbench.taint",
                "java",
                format!("{FLOWDROID_TEMPLATE_DIR}/AndroidManifest-java.xml"),
                format!("{FLOWDROID_TEMPLATE_DIR}/DfbCaseActivity.java.tmpl"),
                &tools.javac,
            ),
            other => bail!("no FlowDroid overhead arm for {}", other.as_str()),
        };
    let sources_sinks_template =
        fs::read_to_string(format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt"))?;
    let wrapper_template = fs::read_to_string(&wrapper_template_file)?;
    let manifest = fs::read(&manifest_file)?;

    let (scratch, _) = overhead_workspace(OverheadTool::Flowdroid, language, run)?;
    let source_root = scratch.join("source");
    let classes = scratch.join("classes");
    for directory in [&source_root, &classes] {
        fs::create_dir_all(directory)?;
    }
    let (fixture_name, fixture_text) = trivial_fixture(language);
    let package_dir = source_root.join(package.replace('.', "/"));
    fs::create_dir_all(&package_dir)?;
    let fixture_path = package_dir.join(fixture_name);
    fs::write(&fixture_path, fixture_text)?;

    let compile = |inputs: &[PathBuf], classpath: Option<&str>| -> Result<()> {
        let mut command = Command::new(compiler);
        command.arg("-nowarn");
        if let Some(classpath) = classpath {
            command.arg("-cp").arg(classpath);
        }
        command
            .arg("-d")
            .arg(&classes)
            .args(inputs)
            .stdin(std::process::Stdio::null());
        let output = command
            .output()
            .with_context(|| format!("compile with {}", compiler.display()))?;
        if !output.status.success() {
            bail!(
                "the trivial FlowDroid fixture did not compile:\n{}",
                String::from_utf8_lossy(&output.stderr)
            );
        }
        Ok(())
    };
    compile(&[fixture_path.clone()], None)?;

    // The entry call and the endpoint signatures are witnessed from the
    // compiled classes, the way the cold runner witnesses them: what the APK
    // will actually carry, not what source-text parsing guesses.
    let parsed_classes = parse_class_directory(&classes)?;
    let entry_call = flowdroid_entry_call(&parsed_classes)
        .map_err(|reason| anyhow::anyhow!("cannot derive the harness entry call: {reason}"))?;
    let source_signatures = flowdroid_endpoint_signatures(&parsed_classes, "dfb_source")
        .map_err(|reason| anyhow::anyhow!("cannot witness the source signature: {reason}"))?;
    let sink_signatures = flowdroid_endpoint_signatures(&parsed_classes, "dfb_sink")
        .map_err(|reason| anyhow::anyhow!("cannot witness the sink signature: {reason}"))?;
    let sources_sinks = sources_sinks_template
        .replace(
            FLOWDROID_SOURCES_PLACEHOLDER,
            &source_signatures
                .iter()
                .map(|signature| format!("{signature} -> _SOURCE_"))
                .collect::<Vec<_>>()
                .join("\n"),
        )
        .replace(
            FLOWDROID_SINKS_PLACEHOLDER,
            &sink_signatures
                .iter()
                .map(|signature| format!("{signature} -> _SINK_"))
                .collect::<Vec<_>>()
                .join("\n"),
        );
    let sources_sinks_path = scratch.join("sources-sinks.txt");
    fs::write(&sources_sinks_path, &sources_sinks)?;
    fs::write(raw_dir.join("resolved-sources-sinks.txt"), &sources_sinks)?;

    let wrapper = wrapper_template
        .replace(FLOWDROID_PACKAGE_PLACEHOLDER, package)
        .replace(FLOWDROID_ENTRY_CALL_PLACEHOLDER, &entry_call);
    let wrapper_source = package_dir.join(format!("DfbCaseActivity.{wrapper_extension}"));
    fs::write(&wrapper_source, &wrapper)?;
    let classpath = format!("{}:{}", tools.android_platform.display(), classes.display());
    compile(&[wrapper_source], Some(&classpath))?;

    let mut class_files: Vec<PathBuf> = WalkDir::new(&classes)
        .into_iter()
        .filter_map(std::result::Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| entry.into_path())
        .filter(|path| path.extension().is_some_and(|ext| ext == "class"))
        .collect();
    class_files.sort();
    let dexed = Command::new(&tools.java)
        .arg("-cp")
        .arg(&tools.d8_jar)
        .arg("com.android.tools.r8.D8")
        .arg("--release")
        .arg("--min-api")
        .arg("21")
        .arg("--lib")
        .arg(&tools.android_platform)
        .arg("--output")
        .arg(&scratch)
        .args(&class_files)
        .stdin(std::process::Stdio::null())
        .output()
        .context("run the D8 dex translator")?;
    if !dexed.status.success() {
        bail!(
            "D8 dex translation failed with status {}:\n{}",
            dexed.status,
            String::from_utf8_lossy(&dexed.stderr)
        );
    }
    let mut dex_files: Vec<PathBuf> = fs::read_dir(&scratch)?
        .filter_map(std::result::Result::ok)
        .map(|entry| entry.path())
        .filter(|path| {
            path.extension().is_some_and(|ext| ext == "dex")
                && path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .is_some_and(|name| name.starts_with("classes"))
        })
        .collect();
    dex_files.sort();
    if dex_files.is_empty() {
        bail!("D8 exited cleanly but produced no dex file");
    }
    let mut entries: Vec<(String, Vec<u8>)> =
        vec![("AndroidManifest.xml".to_string(), manifest.clone())];
    for dex_file in &dex_files {
        entries.push((
            dex_file
                .file_name()
                .and_then(|name| name.to_str())
                .expect("dex file names are ASCII")
                .to_string(),
            fs::read(dex_file)?,
        ));
    }
    let apk_path = scratch.join("case.apk");
    write_stored_zip(
        &apk_path,
        &entries
            .iter()
            .map(|(name, bytes)| (name.as_str(), bytes.as_slice()))
            .collect::<Vec<_>>(),
    )?;

    // Everything above is materialization. Only what follows is timed.
    let resolved_sources_sinks =
        fs::canonicalize(&sources_sinks_path).unwrap_or_else(|_| sources_sinks_path.clone());
    let mut command = Command::new(&tools.java);
    command
        .arg("-jar")
        .arg(&tools.flowdroid_jar)
        .arg("-a")
        .arg(&apk_path)
        .arg("-p")
        .arg(&tools.android_platform)
        .arg("-s")
        .arg(&resolved_sources_sinks)
        .arg("-o")
        .arg(scratch.join("out.xml"))
        .current_dir(&scratch)
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run FlowDroid with {}", tools.java.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the FlowDroid overhead invocation failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before,
    })
}
