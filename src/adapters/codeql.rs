//! The CodeQL adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/codeql/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ModelingLanguage;
use crate::adapters::bifrost::{BIFROST_C_POLICY, BIFROST_CPP_POLICY};
use crate::cases::{
    LoadedCases, case_paths, csharp_core_case, fixture_revision, go_core_case, kotlin_core_case,
    ruby_core_case, validate_cases, validate_kernel_population_with,
};
use crate::evidence::{
    AnchorDialect, callsite_anchored_outcome, sarif_anchor_outcome, sarif_execution_errors,
    sarif_messages, sarif_result_count, sink_anchor_file_matches,
};
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, load_average_one_minute, overhead_workspace,
    trivial_fixture,
};
use crate::native::{NativeRunPlan, native_sarif_outcome};
use crate::report::{ADAPTER_VERSION, hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, clear_stale_case_timing, command_output, now_seconds,
    write_case_phase_timings, write_run_environment,
};
use crate::templates::expected_core_templates;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{
    collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Duration,
    time::Instant,
};

/// Every CodeQL kernel run evaluates the kernel query **and** its companion
/// endpoint-observation probe in one `database analyze` invocation, so the
/// retained SARIF is the evidence for both. The probe reports each benchmark
/// endpoint the extracted database resolves; a run that never observed both
/// endpoints is normalized to `inconclusive` on the same terms as
/// `JoernEndpointRule::BothMustBeObserved`, never to a clean `not-reached`.
pub(crate) const CODEQL_JAVA_ENDPOINT_PROBE: &str =
    "adapters/codeql/queries/JavaKernelEndpointProbe.ql";
pub(crate) const CODEQL_JAVASCRIPT_QUERY: &str =
    "adapters/codeql/javascript/queries/JavaScriptKernel.ql";
pub(crate) const CODEQL_JAVASCRIPT_ENDPOINT_PROBE: &str =
    "adapters/codeql/javascript/queries/JavaScriptKernelEndpointProbe.ql";
pub(crate) const CODEQL_JAVASCRIPT_RAW_DIR: &str = "reports/raw/codeql-javascript";
pub(crate) const CODEQL_JAVASCRIPT_REPORT: &str = "reports/codeql-javascript-kernel.json";
pub(crate) const CODEQL_TYPESCRIPT_QUERY: &str =
    "adapters/codeql/typescript/queries/TypeScriptKernel.ql";
pub(crate) const CODEQL_TYPESCRIPT_ENDPOINT_PROBE: &str =
    "adapters/codeql/typescript/queries/TypeScriptKernelEndpointProbe.ql";
pub(crate) const CODEQL_TYPESCRIPT_RAW_DIR: &str = "reports/raw/codeql-typescript";
pub(crate) const CODEQL_TYPESCRIPT_REPORT: &str = "reports/codeql-typescript-kernel.json";
pub(crate) const CODEQL_PYTHON_QUERY: &str = "adapters/codeql/python/queries/PythonKernel.ql";
pub(crate) const CODEQL_PYTHON_ENDPOINT_PROBE: &str =
    "adapters/codeql/python/queries/PythonKernelEndpointProbe.ql";
pub(crate) const CODEQL_KOTLIN_QUERY: &str = "adapters/codeql/kotlin/queries/KotlinKernel.ql";
pub(crate) const CODEQL_KOTLIN_ENDPOINT_PROBE: &str =
    "adapters/codeql/kotlin/queries/KotlinKernelEndpointProbe.ql";
pub(crate) const CODEQL_KOTLIN_RAW_DIR: &str = "reports/raw/codeql-kotlin-kernel";
pub(crate) const CODEQL_KOTLIN_REPORT: &str = "reports/codeql-kotlin-kernel.json";
pub(crate) const CODEQL_CSHARP_QUERY: &str = "adapters/codeql/csharp/queries/CSharpKernel.ql";
pub(crate) const CODEQL_CSHARP_ENDPOINT_PROBE: &str =
    "adapters/codeql/csharp/queries/CSharpKernelEndpointProbe.ql";
pub(crate) const CODEQL_CSHARP_RAW_DIR: &str = "reports/raw/codeql-csharp-kernel";
pub(crate) const CODEQL_CSHARP_REPORT: &str = "reports/codeql-csharp-kernel.json";
pub(crate) const CODEQL_C_QUERY: &str = "adapters/codeql/cpp/queries/CKernel.ql";
pub(crate) const CODEQL_C_ENDPOINT_PROBE: &str =
    "adapters/codeql/cpp/queries/CKernelEndpointProbe.ql";
pub(crate) const CODEQL_C_RAW_DIR: &str = "reports/raw/codeql-c-kernel";
pub(crate) const CODEQL_C_REPORT: &str = "reports/codeql-c-kernel.json";
pub(crate) const CODEQL_CPP_QUERY: &str = "adapters/codeql/cpp/queries/CppKernel.ql";
pub(crate) const CODEQL_CPP_ENDPOINT_PROBE: &str =
    "adapters/codeql/cpp/queries/CppKernelEndpointProbe.ql";
pub(crate) const CODEQL_CPP_RAW_DIR: &str = "reports/raw/codeql-cpp-kernel";
pub(crate) const CODEQL_CPP_REPORT: &str = "reports/codeql-cpp-kernel.json";
pub(crate) const CODEQL_GO_QUERY: &str = "adapters/codeql/go/queries/GoKernel.ql";
pub(crate) const CODEQL_GO_ENDPOINT_PROBE: &str =
    "adapters/codeql/go/queries/GoKernelEndpointProbe.ql";
pub(crate) const CODEQL_GO_RAW_DIR: &str = "reports/raw/codeql-go-kernel";
pub(crate) const CODEQL_GO_REPORT: &str = "reports/codeql-go-kernel.json";
pub(crate) const CODEQL_RUST_QUERY: &str = "adapters/codeql/rust/queries/RustKernel.ql";
pub(crate) const CODEQL_RUST_ENDPOINT_PROBE: &str =
    "adapters/codeql/rust/queries/RustKernelEndpointProbe.ql";
pub(crate) const CODEQL_RUST_RAW_DIR: &str = "reports/raw/codeql-rust-kernel";
pub(crate) const CODEQL_RUST_REPORT: &str = "reports/codeql-rust-kernel.json";
pub(crate) const CODEQL_RUBY_QUERY: &str = "adapters/codeql/ruby/queries/RubyKernel.ql";
pub(crate) const CODEQL_RUBY_ENDPOINT_PROBE: &str =
    "adapters/codeql/ruby/queries/RubyKernelEndpointProbe.ql";
pub(crate) const CODEQL_RUBY_RAW_DIR: &str = "reports/raw/codeql-ruby-kernel";
pub(crate) const CODEQL_RUBY_REPORT: &str = "reports/codeql-ruby-kernel.json";
/// The module manifest written into every Go CodeQL workspace. The Go
/// extractor has no `none` build mode, so it must observe a real `go build`;
/// supplying the manifest keeps that build hermetic and offline instead of
/// letting autobuild synthesize one and resolve dependencies over the network.
/// The fixtures import nothing, so the language version only has to be old
/// enough that the installed toolchain never fetches another one.
pub(crate) const GO_MODULE_MANIFEST: &str = "module dataflowbench\n\ngo 1.21\n";
/// The pinned CodeQL **query** pack each language's native run resolves its
/// shipped security suite from, verified downloadable against CLI 2.26.3.
///
/// These are query packs, not the library packs the benchmark-controlled
/// adapter pins: each bundles its own `<language>-all` at a version of its own
/// choosing (9.2.4, 2.10.0, and 7.2.4 respectively, against the adapter's
/// 9.2.3, 2.9.0, and 7.2.3). The two profiles therefore run on different
/// library resolutions by construction, which is correct — a native run must
/// measure the shipped product as shipped — and is one more reason the two are
/// never pooled.
pub(crate) const CODEQL_NATIVE_QUERY_PACKS: [(&str, &str); 3] = [
    ("codeql/java-queries", "1.11.9"),
    ("codeql/javascript-queries", "2.4.4"),
    ("codeql/python-queries", "1.8.9"),
];

/// The shipped suite the native profile selects. `security-extended` is the
/// standard taint suite: `code-scanning` is a narrower default and
/// `security-experimental` is explicitly not a product default.
pub(crate) const CODEQL_NATIVE_SUITE_KIND: &str = "security-extended";

/// The documented CLI option that enables the shipped `local` threat-model
/// group, which `codeql/threat-models` defines as containing `environment` and
/// `commandargs`. This configures vendor rows; it does not add rows, so it
/// satisfies the activation rule. Without it, templates 1, 5, and 6 would be
/// decided by the default `remote`-only threat model for a reason that has
/// nothing to do with coverage.
pub(crate) const CODEQL_NATIVE_THREAT_MODEL: &str = "local";

/// The CodeQL JavaScript extractor covers JavaScript and TypeScript alike, so
/// both kernels share one runner. Everything that separates the two
/// populations — the selected case language, the owning pack and query, and
/// the report and raw-evidence roots — hangs off this descriptor, and the
/// selector below refuses the other language's cases outright.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EcmaKernel {
    JavaScript,
    TypeScript,
}

impl EcmaKernel {
    pub(crate) fn language(self) -> &'static str {
        match self {
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
        }
    }

    pub(crate) fn display_name(self) -> &'static str {
        match self {
            Self::JavaScript => "JavaScript",
            Self::TypeScript => "TypeScript",
        }
    }

    pub(crate) fn adapter(self) -> &'static str {
        match self {
            Self::JavaScript => "codeql-javascript",
            Self::TypeScript => "codeql-typescript",
        }
    }

    pub(crate) fn query(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_QUERY,
            Self::TypeScript => CODEQL_TYPESCRIPT_QUERY,
        }
    }

    pub(crate) fn endpoint_probe(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_ENDPOINT_PROBE,
            Self::TypeScript => CODEQL_TYPESCRIPT_ENDPOINT_PROBE,
        }
    }

    pub(crate) fn raw_dir(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_RAW_DIR,
            Self::TypeScript => CODEQL_TYPESCRIPT_RAW_DIR,
        }
    }

    pub(crate) fn report(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_REPORT,
            Self::TypeScript => CODEQL_TYPESCRIPT_REPORT,
        }
    }

    pub(crate) fn qlpack_directory(self) -> &'static str {
        match self {
            Self::JavaScript => "adapters/codeql/javascript",
            Self::TypeScript => "adapters/codeql/typescript",
        }
    }

    /// Whether a selected case may omit its CodeQL query reference.
    ///
    /// The TypeScript direct-propagation pair is shared with the
    /// cross-language direct-flow breadth slice and was frozen in `v0.2.0`
    /// before this pack existed. Freeze manifests bind those case bytes, so
    /// the runner defaults them to the kernel query rather than rewriting
    /// published evidence. A declared query still has to be this kernel's.
    pub(crate) fn allows_implicit_query_reference(self) -> bool {
        matches!(self, Self::TypeScript)
    }
}

/// CodeQL extracts C and C++ with one `cpp` extractor and Bifrost indexes both
/// from one workspace, but DataFlowBench keeps them as two populations with
/// different core denominators: 16 templates for C++, 15 for C, never merged,
/// pooled, or macro-averaged together. Everything that separates them — the
/// selected case language, the scored template set, the policy, the kernel
/// query, and the report and raw-evidence roots — hangs off this descriptor.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CFamilyKernel {
    C,
    Cpp,
}

impl CFamilyKernel {
    pub(crate) fn language(self) -> &'static str {
        match self {
            Self::C => "c",
            Self::Cpp => "cpp",
        }
    }

    pub(crate) fn display_name(self) -> &'static str {
        match self {
            Self::C => "C",
            Self::Cpp => "C++",
        }
    }

    pub(crate) fn policy(self) -> &'static str {
        match self {
            Self::C => BIFROST_C_POLICY,
            Self::Cpp => BIFROST_CPP_POLICY,
        }
    }

    pub(crate) fn query(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_QUERY,
            Self::Cpp => CODEQL_CPP_QUERY,
        }
    }

    pub(crate) fn endpoint_probe(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_ENDPOINT_PROBE,
            Self::Cpp => CODEQL_CPP_ENDPOINT_PROBE,
        }
    }

    pub(crate) fn raw_dir(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_RAW_DIR,
            Self::Cpp => CODEQL_CPP_RAW_DIR,
        }
    }

    pub(crate) fn report(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_REPORT,
            Self::Cpp => CODEQL_CPP_REPORT,
        }
    }

    /// The scored templates of this language's core denominator, read from its
    /// rollout row.
    pub(crate) fn templates(self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }

    /// Whether this language routes its inapplicable cell to
    /// `language-extension` cases that run in the same slice.
    pub(crate) fn has_language_extension_cases(self) -> bool {
        matches!(self, Self::C)
    }
}

/// A case this kernel evaluates: the language's core population, plus — for C —
/// the `language-extension` cases that stand in for the inapplicable
/// exception-catch cell. Extension cases are scored on their own scorecard and
/// never enter the core denominator.
pub(crate) fn c_family_selected_case(case: &Value, kernel: CFamilyKernel) -> bool {
    case["language"].as_str() == Some(kernel.language())
        && case["track"] == "taint"
        && (case["score_tier"] == "core"
            || (kernel.has_language_extension_cases()
                && case["score_tier"] == "language-extension"))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CodeqlLanguage<'a> {
    Java,
    Python,
    /// Kotlin is extracted by CodeQL's `java` extractor, which only sees
    /// Kotlin sources while it traces a real compile. The traced compiler is
    /// carried here because `--build-mode=none` extracts no Kotlin at all.
    Kotlin {
        kotlinc: &'a Path,
    },
    CSharp,
    /// The Go extractor rejects `--build-mode=none` outright; it only sees Go
    /// sources while it traces a real `go build`, so the toolchain is carried
    /// here the way the Kotlin compiler is.
    Go {
        go: &'a Path,
    },
    /// C and C++ share CodeQL's `cpp` extractor. Which of the two populations a
    /// run belongs to is decided by case selection and the kernel query, not by
    /// the extractor.
    CFamily,
    /// Rust support is a public preview in the pinned CLI. The extractor takes
    /// `--build-mode=none`, but it only runs its semantic analyzer when the
    /// source root contains a Cargo manifest, so the runner generates one.
    Rust,
    /// Ruby is buildless: the extractor parses the sources directly under
    /// `--build-mode=none`, with no manifest, project file, or traced compile.
    Ruby,
    /// JavaScript is extracted by the `javascript` extractor with no build mode
    /// at all — the same invocation the ECMA kernels already use.
    Javascript,
}

impl CodeqlLanguage<'_> {
    pub(crate) fn cli_name(self) -> &'static str {
        match self {
            Self::Java | Self::Kotlin { .. } => "java",
            Self::Python => "python",
            Self::CSharp => "csharp",
            Self::Go { .. } => "go",
            Self::CFamily => "cpp",
            Self::Rust => "rust",
            Self::Ruby => "ruby",
            Self::Javascript => "javascript",
        }
    }

    /// True when the extractor is traced through a JVM compile that writes
    /// class files into the workspace.
    pub(crate) fn traces_jvm_compile(self) -> bool {
        matches!(self, Self::Java | Self::Kotlin { .. })
    }
}

pub(crate) fn run_codeql_java_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let raw_dir = Path::new("reports/raw/codeql");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::new();
    let mut query_paths = BTreeSet::new();

    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !selected_codeql_java_case(&case) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = if let Some(reason) =
            model["unsupported_reason"].as_str()
        {
            let raw_path = raw_dir.join(format!("{id}.json"));
            clear_stale_case_timing(raw_dir, id)?;
            fs::write(
                &raw_path,
                serde_json::to_string_pretty(
                    &json!({"adapter": "codeql", "case_id": id, "state": "unsupported", "reason": reason, "evidence_kind": "adapter-capability-declaration"}),
                )? + "\n",
            )?;
            ("unsupported", vec![reason.to_string()], raw_path)
        } else {
            let query = model["query"]
                .as_str()
                .context("CodeQL case lacks query reference")?;
            query_paths.insert(PathBuf::from(query));
            run_codeql_case(binary, packs, &path, &case, Path::new(query), raw_dir)?
        };
        results.push(json!({
            "case_id": id, "outcome": outcome,
            "source_anchors": case["source_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
            "sink_anchors": case["sink_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
            "witness_checkpoints": [], "diagnostics": diagnostics,
            "duration_ms": start.elapsed().as_millis() as u64, "peak_memory_mb": Value::Null,
            "raw_output": raw_path.to_string_lossy()
        }));
    }
    if results.is_empty() {
        bail!("no cases declare a CodeQL model reference");
    }

    let mut configuration_paths = query_paths;
    configuration_paths.insert(PathBuf::from(CODEQL_JAVA_ENDPOINT_PROBE));
    configuration_paths.insert(PathBuf::from("adapters/codeql/qlpack.yml"));
    configuration_paths.insert(PathBuf::from("adapters/codeql/codeql-pack.lock.yml"));
    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new("reports/codeql-java-kernel.json"), &report)?;
    println!("wrote reports/codeql-java-kernel.json");
    Ok(())
}

pub(crate) fn selected_codeql_java_case(case: &Value) -> bool {
    case["language"] == "java"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"].is_object()
}

/// The configuration paths [`run_codeql_java_kernel`] would hash if it ran
/// now: every selected non-unsupported case's declared query, plus the
/// endpoint probe and the pack files the run inserts unconditionally. A drift
/// between this mirror and the runner fails the runner's own end-of-run
/// validation sweep.
pub(crate) fn codeql_java_kernel_configuration_paths(
    cases: &LoadedCases,
) -> Result<BTreeSet<PathBuf>> {
    let mut paths = BTreeSet::new();
    for (_, case) in cases {
        if !selected_codeql_java_case(case) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        if model["unsupported_reason"].is_string() {
            continue;
        }
        paths.insert(PathBuf::from(
            model["query"]
                .as_str()
                .context("CodeQL case lacks query reference")?,
        ));
    }
    paths.insert(PathBuf::from(CODEQL_JAVA_ENDPOINT_PROBE));
    paths.insert(PathBuf::from("adapters/codeql/qlpack.yml"));
    paths.insert(PathBuf::from("adapters/codeql/codeql-pack.lock.yml"));
    Ok(paths)
}

/// The configuration paths [`run_codeql_ecma_kernel`] would hash if it ran
/// now, mirroring its collection: declared (or implicitly defaulted) queries
/// of selected non-unsupported cases, the kernel query, the endpoint probe,
/// and the pack files.
pub(crate) fn codeql_ecma_kernel_configuration_paths(
    kernel: EcmaKernel,
    cases: &LoadedCases,
) -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::new();
    for (_, case) in cases {
        if !ecma_core_case(case, kernel) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        if model["unsupported_reason"].is_string() {
            continue;
        }
        paths.insert(PathBuf::from(
            model["query"].as_str().unwrap_or(kernel.query()),
        ));
    }
    paths.insert(PathBuf::from(kernel.query()));
    paths.insert(PathBuf::from(kernel.endpoint_probe()));
    let qlpack_directory = Path::new(kernel.qlpack_directory());
    paths.insert(qlpack_directory.join("qlpack.yml"));
    let pack_lock = qlpack_directory.join("codeql-pack.lock.yml");
    if pack_lock.is_file() {
        paths.insert(pack_lock);
    }
    paths
}

/// The configuration paths [`run_codeql_python_kernel`] would hash if it ran
/// now: every selected case's declared query folded through
/// [`codeql_python_configuration_paths`].
pub(crate) fn codeql_python_kernel_configuration_paths(
    cases: &LoadedCases,
) -> Result<BTreeSet<PathBuf>> {
    let mut query_paths = BTreeSet::new();
    for (_, case) in cases {
        if !selected_codeql_python_case(case) {
            continue;
        }
        query_paths.insert(PathBuf::from(
            case["tool_model_references"]["codeql"]["query"]
                .as_str()
                .context("Python CodeQL case lacks query reference")?,
        ));
    }
    Ok(codeql_python_configuration_paths(&query_paths))
}

/// Run one of the two ECMAScript-family CodeQL kernels. This deliberately does
/// not reuse the Java selector or its database/raw-output roots: CodeQL has
/// shared standard libraries, but the benchmark adapters must remain
/// language-scoped. The JavaScript and TypeScript populations are likewise
/// disjoint, each with its own pack, query, report, and raw-evidence root.
pub(crate) fn run_codeql_ecma_kernel(
    binary: &Path,
    packs: Option<&Path>,
    kernel: EcmaKernel,
) -> Result<()> {
    validate_cases()?;
    let selected = select_codeql_ecma_cases(kernel)?;
    let raw_dir = Path::new(kernel.raw_dir());
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());
    let mut query_paths = BTreeSet::new();

    for (path, case) in selected {
        let model = &case["tool_model_references"]["codeql"];
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            if let Some(reason) = model["unsupported_reason"].as_str() {
                let raw_path = raw_dir.join(format!("{id}.json"));
                clear_stale_case_timing(raw_dir, id)?;
                fs::write(
                    &raw_path,
                    serde_json::to_string_pretty(&json!({
                        "adapter": kernel.adapter(),
                        "case_id": id,
                        "state": "unsupported",
                        "reason": reason,
                        "evidence_kind": "adapter-capability-declaration"
                    }))? + "\n",
                )?;
                ("unsupported", vec![reason.to_string()], raw_path)
            } else {
                let query = model["query"].as_str().unwrap_or(kernel.query());
                query_paths.insert(PathBuf::from(query));
                run_codeql_ecma_case(
                    binary,
                    packs,
                    &path,
                    &case,
                    Path::new(query),
                    raw_dir,
                    kernel,
                )?
            };
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let mut configuration_paths = query_paths;
    configuration_paths.insert(PathBuf::from(kernel.query()));
    configuration_paths.insert(PathBuf::from(kernel.endpoint_probe()));
    let qlpack_directory = Path::new(kernel.qlpack_directory());
    configuration_paths.insert(qlpack_directory.join("qlpack.yml"));
    let pack_lock = qlpack_directory.join("codeql-pack.lock.yml");
    if pack_lock.is_file() {
        configuration_paths.insert(pack_lock);
    }
    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(kernel.report()), &report)?;
    println!("wrote {}", kernel.report());
    Ok(())
}

pub(crate) fn run_codeql_python_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_python_cases()?;
    let raw_dir = Path::new("reports/raw/codeql-python-kernel");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());
    let mut query_paths = BTreeSet::new();

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let model = &case["tool_model_references"]["codeql"];
        let query = model["query"]
            .as_str()
            .context("Python CodeQL case lacks query reference")?;
        query_paths.insert(PathBuf::from(query));
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(query),
            Some(Path::new(CODEQL_PYTHON_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::Python,
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

    let configuration_paths = codeql_python_configuration_paths(&query_paths);
    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new("reports/codeql-python-kernel.json"), &report)?;
    println!("wrote reports/codeql-python-kernel.json");
    Ok(())
}

/// Run the Kotlin-only CodeQL kernel. Kotlin shares CodeQL's `java` extractor
/// and standard library with the Java kernel, so the selector, query, report,
/// and raw-evidence directory are all deliberately Kotlin-scoped: the two
/// populations must never share a result set.
pub(crate) fn run_codeql_kotlin_kernel(
    binary: &Path,
    packs: Option<&Path>,
    kotlinc: &Path,
) -> Result<()> {
    validate_cases()?;
    let selected = codeql_kotlin_cases()?;
    let raw_dir = Path::new(CODEQL_KOTLIN_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_KOTLIN_QUERY),
            Some(Path::new(CODEQL_KOTLIN_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::Kotlin { kotlinc },
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

    let configuration_hash = hash_paths(&codeql_kotlin_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(CODEQL_KOTLIN_REPORT), &report)?;
    println!("wrote {CODEQL_KOTLIN_REPORT}");
    Ok(())
}

/// Run the C#-only CodeQL kernel. The C# extractor supports
/// `--build-mode=none`, so each fixture is extracted standalone with no project
/// scaffolding, and findings are reconciled against the case's `DFB-SINK:`
/// method callsites.
pub(crate) fn run_codeql_csharp_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_csharp_cases()?;
    let raw_dir = Path::new(CODEQL_CSHARP_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_CSHARP_QUERY),
            Some(Path::new(CODEQL_CSHARP_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::CSharp,
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

    let configuration_hash = hash_paths(&codeql_csharp_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(CODEQL_CSHARP_REPORT), &report)?;
    println!("wrote {CODEQL_CSHARP_REPORT}");
    Ok(())
}

/// Run the Go-only CodeQL kernel. Unlike Python and C#, the Go extractor has
/// no build-free mode, so each cold database is built from the declared fixture
/// plus a synthesized module manifest and a traced `go build`. Findings are
/// reconciled against the case's `DFB-SINK:` function callsites.
pub(crate) fn run_codeql_go_kernel(binary: &Path, packs: Option<&Path>, go: &Path) -> Result<()> {
    validate_cases()?;
    let selected = codeql_go_cases()?;
    let raw_dir = Path::new(CODEQL_GO_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_GO_QUERY),
            Some(Path::new(CODEQL_GO_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::Go { go },
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

    let configuration_hash = hash_paths(&codeql_go_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(CODEQL_GO_REPORT), &report)?;
    println!("wrote {CODEQL_GO_REPORT}");
    Ok(())
}

pub(crate) fn codeql_go_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !go_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Go core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_GO_QUERY
        {
            bail!(
                "Go core case {} references non-Go CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population_with(
        &selected,
        "Go CodeQL kernel",
        &expected_core_templates("go"),
    )?;
    if !Path::new(CODEQL_GO_QUERY).is_file() {
        bail!("Go CodeQL query does not exist: {CODEQL_GO_QUERY}");
    }
    if !Path::new(CODEQL_GO_ENDPOINT_PROBE).is_file() {
        bail!("Go CodeQL endpoint probe does not exist: {CODEQL_GO_ENDPOINT_PROBE}");
    }
    Ok(selected)
}

pub(crate) fn codeql_go_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(CODEQL_GO_QUERY),
        PathBuf::from(CODEQL_GO_ENDPOINT_PROBE),
    ]);
    for candidate in [
        "adapters/codeql/go/qlpack.yml",
        "adapters/codeql/go/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// Run one of the two C-family CodeQL kernels. C and C++ share the `cpp`
/// extractor and one pack, so the population separation is enforced here: each
/// run selects only its own language's cases, analyzes them with its own
/// extension-scoped kernel query, and writes its own report and raw-evidence
/// directory. The two result sets are never merged.
pub(crate) fn run_codeql_c_family_kernel(
    binary: &Path,
    packs: Option<&Path>,
    kernel: CFamilyKernel,
) -> Result<()> {
    validate_cases()?;
    let selected = codeql_c_family_cases(kernel)?;
    let raw_dir = Path::new(kernel.raw_dir());
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(kernel.query()),
            Some(Path::new(kernel.endpoint_probe())),
            raw_dir,
            CodeqlLanguage::CFamily,
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

    let configuration_hash = hash_paths(&codeql_c_family_configuration_paths(kernel))?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(kernel.report()), &report)?;
    println!("wrote {}", kernel.report());
    Ok(())
}

pub(crate) fn codeql_c_family_cases(kernel: CFamilyKernel) -> Result<Vec<(PathBuf, Value)>> {
    let display = kernel.display_name();
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !c_family_selected_case(&case, kernel) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a selected case does carry must name this kernel's query,
        // so the C and C++ populations can never borrow each other's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != kernel.query()
        {
            bail!(
                "{display} case {} references non-{display} CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_c_family_population(&selected, kernel)?;
    if !Path::new(kernel.query()).is_file() {
        bail!("{display} CodeQL query does not exist: {}", kernel.query());
    }
    if !Path::new(kernel.endpoint_probe()).is_file() {
        bail!(
            "{display} CodeQL endpoint probe does not exist: {}",
            kernel.endpoint_probe()
        );
    }
    Ok(selected)
}

/// The core population must be exactly this language's scored templates,
/// balanced one positive to one negative. `language-extension` cases ride
/// along in the same slice, are scored on their own scorecard, and are
/// excluded from that count.
pub(crate) fn validate_c_family_population(
    selected: &[(PathBuf, Value)],
    kernel: CFamilyKernel,
) -> Result<()> {
    let label = format!("{} kernel", kernel.display_name());
    let core = selected
        .iter()
        .filter(|(_, case)| case["score_tier"] == "core")
        .cloned()
        .collect::<Vec<_>>();
    validate_kernel_population_with(&core, &label, &kernel.templates())?;
    if !kernel.has_language_extension_cases() && core.len() != selected.len() {
        bail!("{label} must select core cases only");
    }
    for (path, case) in selected {
        if case["score_tier"] == "language-extension" && case["polarity"] != "positive" {
            bail!(
                "{}: {label} language-extension cases are authored as positives",
                path.display()
            );
        }
    }
    Ok(())
}

/// Run the Rust-only CodeQL kernel. Rust support is a public preview in the
/// pinned CLI 2.26.4 (extractor `rust` 0.1.0, library pack
/// `codeql/rust-all@0.2.19`), and that status is recorded in
/// `docs/rust-kernel.md` alongside the results this run produces. The
/// population is the 30 core assertions of the 15 applicable templates plus the
/// `Result`/`?` `language-extension` pair, which is scored on its own tier.
pub(crate) fn run_codeql_rust_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_rust_cases()?;
    let raw_dir = Path::new(CODEQL_RUST_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_RUST_QUERY),
            Some(Path::new(CODEQL_RUST_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::Rust,
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

    let configuration_hash = hash_paths(&codeql_rust_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(CODEQL_RUST_REPORT), &report)?;
    println!("wrote {CODEQL_RUST_REPORT}");
    Ok(())
}

/// Run the Ruby-only CodeQL kernel. `docs/applicability-matrix.md` gates the
/// Ruby tranche on Bifrost's Ruby indexing and names CodeQL as the primary
/// decisive analyzer, so this is the run the Ruby denominator is decided by.
/// The Ruby extractor is buildless, so each of the 32 core assertions is
/// extracted standalone into its own cold database.
pub(crate) fn run_codeql_ruby_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_ruby_cases()?;
    let raw_dir = Path::new(CODEQL_RUBY_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    write_run_environment(raw_dir, "codeql", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_RUBY_QUERY),
            Some(Path::new(CODEQL_RUBY_ENDPOINT_PROBE)),
            raw_dir,
            CodeqlLanguage::Ruby,
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

    let configuration_hash = hash_paths(&codeql_ruby_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "codeql",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(Path::new(CODEQL_RUBY_REPORT), &report)?;
    println!("wrote {CODEQL_RUBY_REPORT}");
    Ok(())
}

pub(crate) fn codeql_ruby_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !ruby_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Ruby core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_RUBY_QUERY
        {
            bail!(
                "Ruby core case {} references non-Ruby CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population_with(
        &selected,
        "Ruby CodeQL kernel",
        &expected_core_templates("ruby"),
    )?;
    if !Path::new(CODEQL_RUBY_QUERY).is_file() {
        bail!("Ruby CodeQL query does not exist: {CODEQL_RUBY_QUERY}");
    }
    if !Path::new(CODEQL_RUBY_ENDPOINT_PROBE).is_file() {
        bail!("Ruby CodeQL endpoint probe does not exist: {CODEQL_RUBY_ENDPOINT_PROBE}");
    }
    Ok(selected)
}

pub(crate) fn codeql_ruby_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(CODEQL_RUBY_QUERY),
        PathBuf::from(CODEQL_RUBY_ENDPOINT_PROBE),
    ]);
    for candidate in [
        "adapters/codeql/ruby/qlpack.yml",
        "adapters/codeql/ruby/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// A Rust assertion this kernel owns: the 30 `core` assertions of the 15
/// applicable templates, plus the `Result`/`?` `language-extension` pair. The
/// two tiers are selected together so one run produces both, and are kept apart
/// in the scorecards by `score_tier`; the extension never enters the core
/// denominator.
pub(crate) fn rust_kernel_case(case: &Value) -> bool {
    case["language"] == "rust"
        && case["track"] == "taint"
        && (case["score_tier"] == "core" || case["score_tier"] == "language-extension")
}

pub(crate) fn codeql_rust_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !rust_kernel_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Rust case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_RUST_QUERY
        {
            bail!(
                "Rust case {} references non-Rust CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_rust_kernel_population(&selected, "Rust CodeQL kernel")?;
    if !Path::new(CODEQL_RUST_QUERY).is_file() {
        bail!("Rust CodeQL query does not exist: {CODEQL_RUST_QUERY}");
    }
    if !Path::new(CODEQL_RUST_ENDPOINT_PROBE).is_file() {
        bail!("Rust CodeQL endpoint probe does not exist: {CODEQL_RUST_ENDPOINT_PROBE}");
    }
    Ok(selected)
}

/// The Rust core population must be exactly the applicable scored templates
/// the rollout table names — the 15 classic ones, plus Rust's 12 challenge
/// cells now that its row is flipped — balanced one positive to one negative
/// under one model profile. The `Result`/`?` `language-extension` pair rides
/// along in the same slice, is scored on its own scorecard, and is excluded
/// from that count; anything on another tier is a template smuggled back into
/// the core denominator and is rejected here.
pub(crate) fn validate_rust_kernel_population(
    selected: &[(PathBuf, Value)],
    label: &str,
) -> Result<()> {
    for (path, case) in selected {
        let tier = case["score_tier"]
            .as_str()
            .with_context(|| format!("{} lacks score_tier", path.display()))?;
        if tier != "core" && tier != "language-extension" {
            bail!(
                "{label} selected {} with score tier {tier:?}",
                path.display()
            );
        }
    }
    let core = selected
        .iter()
        .filter(|(_, case)| case["score_tier"] == "core")
        .cloned()
        .collect::<Vec<_>>();
    validate_kernel_population_with(&core, label, &expected_core_templates("rust"))
}

pub(crate) fn codeql_rust_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(CODEQL_RUST_QUERY),
        PathBuf::from(CODEQL_RUST_ENDPOINT_PROBE),
    ]);
    for candidate in [
        "adapters/codeql/rust/qlpack.yml",
        "adapters/codeql/rust/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

pub(crate) fn codeql_c_family_configuration_paths(kernel: CFamilyKernel) -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(kernel.query()),
        PathBuf::from(kernel.endpoint_probe()),
    ]);
    for candidate in [
        "adapters/codeql/cpp/qlpack.yml",
        "adapters/codeql/cpp/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

pub(crate) fn codeql_csharp_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !csharp_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a C# core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_CSHARP_QUERY
        {
            bail!(
                "C# core case {} references non-C# CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population_with(
        &selected,
        "C# CodeQL kernel",
        &expected_core_templates("csharp"),
    )?;
    if !Path::new(CODEQL_CSHARP_QUERY).is_file() {
        bail!("C# CodeQL query does not exist: {CODEQL_CSHARP_QUERY}");
    }
    if !Path::new(CODEQL_CSHARP_ENDPOINT_PROBE).is_file() {
        bail!("C# CodeQL endpoint probe does not exist: {CODEQL_CSHARP_ENDPOINT_PROBE}");
    }
    Ok(selected)
}

pub(crate) fn codeql_csharp_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(CODEQL_CSHARP_QUERY),
        PathBuf::from(CODEQL_CSHARP_ENDPOINT_PROBE),
    ]);
    for candidate in [
        "adapters/codeql/csharp/qlpack.yml",
        "adapters/codeql/csharp/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// The exact CLI version and build SHA every normalized CodeQL report records.
pub(crate) fn codeql_version_identity(binary: &Path) -> Result<(String, String)> {
    let version_output = command_output(Command::new(binary).args(["version", "--format=json"]))
        .context("read CodeQL version")?;
    let version_json: Value =
        serde_json::from_str(&version_output).context("parse CodeQL version JSON")?;
    let version = version_json["version"]
        .as_str()
        .context("CodeQL version JSON lacks version")?
        .to_string();
    let build_identity = version_json["sha"]
        .as_str()
        .map(|sha| format!("codeql-cli:{sha}"))
        .context("CodeQL version JSON lacks build sha")?;
    Ok((version, build_identity))
}

pub(crate) fn codeql_kotlin_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !kotlin_core_case(&case) {
            continue;
        }
        // The two direct-propagation cases were frozen in v0.2.0 as part of
        // the cross-language breadth slice and carry no CodeQL reference; any
        // case that does declare one must name the Kotlin kernel query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_KOTLIN_QUERY
        {
            bail!(
                "Kotlin core case {} references non-Kotlin CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population_with(
        &selected,
        "Kotlin CodeQL kernel",
        &expected_core_templates("kotlin"),
    )?;
    if !Path::new(CODEQL_KOTLIN_QUERY).is_file() {
        bail!("Kotlin CodeQL query does not exist: {CODEQL_KOTLIN_QUERY}");
    }
    if !Path::new(CODEQL_KOTLIN_ENDPOINT_PROBE).is_file() {
        bail!("Kotlin CodeQL endpoint probe does not exist: {CODEQL_KOTLIN_ENDPOINT_PROBE}");
    }
    Ok(selected)
}

pub(crate) fn codeql_kotlin_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([
        PathBuf::from(CODEQL_KOTLIN_QUERY),
        PathBuf::from(CODEQL_KOTLIN_ENDPOINT_PROBE),
    ]);
    for candidate in [
        "adapters/codeql/kotlin/qlpack.yml",
        "adapters/codeql/kotlin/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

pub(crate) fn select_codeql_ecma_cases(kernel: EcmaKernel) -> Result<Vec<(PathBuf, Value)>> {
    let display = kernel.display_name();
    let expected_query = kernel.query();
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !ecma_core_case(&case, kernel) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        if !model.is_object() && !kernel.allows_implicit_query_reference() {
            bail!(
                "{display} core case {} lacks a CodeQL model reference",
                case["id"]
            );
        }
        if !model["unsupported_reason"].is_string()
            && model["query"].as_str().is_none()
            && !kernel.allows_implicit_query_reference()
        {
            bail!(
                "{display} core case {} lacks a CodeQL query reference",
                case["id"]
            );
        }
        if let Some(query) = model["query"].as_str()
            && query != expected_query
        {
            bail!(
                "{display} core case {} references non-{display} CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    // The denominator comes from this language's rollout row, so the ECMA
    // CodeQL kernels expand with their fixtures and need no edit here.
    validate_kernel_population_with(
        &selected,
        &format!("{display} CodeQL kernel"),
        &expected_core_templates(kernel.language()),
    )?;
    if !Path::new(kernel.endpoint_probe()).is_file() {
        bail!(
            "{display} CodeQL endpoint probe does not exist: {}",
            kernel.endpoint_probe()
        );
    }
    Ok(selected)
}

pub(crate) fn ecma_core_case(case: &Value, kernel: EcmaKernel) -> bool {
    case["language"] == kernel.language()
        && case["track"] == "taint"
        && case["score_tier"] == "core"
}

pub(crate) fn run_codeql_ecma_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
    kernel: EcmaKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let display = kernel.display_name();
    let workspace = materialize_codeql_ecma_workspace(case_path, case, kernel)?;
    let database_root = std::env::temp_dir().join(format!(
        "dataflowbench-codeql-{}-databases",
        kernel.language()
    ));
    fs::create_dir_all(&database_root)?;
    let database = database_root.join(id);
    if database.exists() {
        fs::remove_dir_all(&database).with_context(|| format!("clear {}", database.display()))?;
    }
    let raw_path = raw_dir.join(format!("{id}.sarif.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let result = (|| {
        let mut phases: Vec<(&str, Duration)> = Vec::new();
        let create_started = Instant::now();
        let create = Command::new(binary)
            .arg("database")
            .arg("create")
            .arg(&database)
            // Both kernels are extracted by CodeQL's `javascript` extractor,
            // which also covers TypeScript syntax. The populations are kept
            // apart by the case selector and by each query's file-extension
            // guard, not by the extractor.
            .arg("--language=javascript")
            .arg(format!("--source-root={}", workspace.display()))
            .arg("--overwrite")
            .output();
        let create = match create {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL {display} database create with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_ecma_spawn_error(
                    raw_dir,
                    id,
                    "database-create",
                    &diagnostic,
                    kernel,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        phases.push(("database-create", create_started.elapsed()));
        write_case_phase_timings(raw_dir, kernel.adapter(), id, &phases)?;
        if !create.status.success() {
            return write_codeql_ecma_error(raw_dir, id, "database-create", &create, None, kernel);
        }

        let mut analyze = Command::new(binary);
        analyze
            .arg("database")
            .arg("analyze")
            .arg(&database)
            .arg(query)
            .arg(kernel.endpoint_probe())
            .arg("--format=sarif-latest")
            .arg(format!("--output={}", raw_path.display()))
            .arg("--rerun");
        if let Some(packs) = packs {
            analyze.arg(format!("--additional-packs={}", packs.display()));
        }
        let analyze_started = Instant::now();
        let analyzed = match analyze.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL {display} database analyze with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_ecma_spawn_error(
                    raw_dir,
                    id,
                    "database-analyze",
                    &diagnostic,
                    kernel,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        phases.push(("database-analyze", analyze_started.elapsed()));
        write_case_phase_timings(raw_dir, kernel.adapter(), id, &phases)?;
        if !analyzed.status.success() {
            return write_codeql_ecma_error(
                raw_dir,
                id,
                "database-analyze",
                &analyzed,
                raw_path.is_file().then_some(raw_path.as_path()),
                kernel,
            );
        }
        if !raw_path.is_file() {
            let diagnostic = format!("CodeQL {display} analysis produced no SARIF output");
            let error_path = write_codeql_ecma_spawn_error(
                raw_dir,
                id,
                "database-analyze",
                &diagnostic,
                kernel,
            )?;
            return Ok(("runner-error", vec![diagnostic], error_path));
        }

        let raw = match fs::read_to_string(&raw_path) {
            Ok(raw) => raw,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!("read CodeQL SARIF {}: {error}", raw_path.display())],
                    raw_path,
                ));
            }
        };
        let sarif: Value = match serde_json::from_str(&raw) {
            Ok(sarif) => sarif,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "parse CodeQL SARIF {}: {error}",
                        raw_path.display()
                    )],
                    raw_path,
                ));
            }
        };
        let execution_errors = sarif_execution_errors(&sarif);
        if !execution_errors.is_empty() {
            return Ok(("runner-error", execution_errors, raw_path));
        }
        if !sarif["runs"]
            .as_array()
            .is_some_and(|runs| !runs.is_empty())
        {
            return Ok((
                "runner-error",
                vec!["CodeQL SARIF contains no analysis runs".to_string()],
                raw_path,
            ));
        }
        let (sarif, observation) = split_codeql_endpoint_probe(&sarif);
        if let Some((outcome, diagnostics)) = unobserved_codeql_endpoint_outcome(observation) {
            return Ok((outcome, diagnostics, raw_path));
        }
        let mut diagnostics = sarif_messages(&sarif);
        let (outcome, anchor_diagnostics) = ecma_sarif_outcome(case_path, case, &sarif);
        diagnostics.extend(anchor_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path))
    })();

    let cleanup = clear_codeql_case_artifacts(&workspace, &database);
    match (result, cleanup) {
        (Ok((outcome, diagnostics, raw_path)), Ok(())) => Ok((outcome, diagnostics, raw_path)),
        (Ok((_, mut diagnostics, raw_path)), Err(error)) => {
            diagnostics.push(format!("CodeQL {display} artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, raw_path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "CodeQL {display} artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

pub(crate) fn materialize_codeql_ecma_workspace(
    case_path: &Path,
    case: &Value,
    kernel: EcmaKernel,
) -> Result<PathBuf> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = std::env::temp_dir()
        .join(format!(
            "dataflowbench-codeql-{}-workspaces",
            kernel.language()
        ))
        .join(id);
    if workspace.exists() {
        fs::remove_dir_all(&workspace).with_context(|| format!("clear {}", workspace.display()))?;
    }
    fs::create_dir_all(&workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }
    Ok(workspace)
}

pub(crate) fn write_codeql_ecma_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    output: &std::process::Output,
    raw_path: Option<&Path>,
    kernel: EcmaKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let diagnostic = format!(
        "CodeQL {} {stage} failed with status {}",
        kernel.display_name(),
        output.status
    );
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": kernel.adapter(),
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "status": output.status.code(),
            "stdout": stdout,
            "stderr": stderr,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok((
        "runner-error",
        vec![diagnostic],
        raw_path.unwrap_or(&error_path).to_path_buf(),
    ))
}

pub(crate) fn write_codeql_ecma_spawn_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    kernel: EcmaKernel,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": kernel.adapter(),
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "diagnostic": diagnostic,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(error_path)
}

pub(crate) fn ecma_sarif_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
) -> (&'static str, Vec<String>) {
    sarif_anchor_outcome(case_path, case, sarif, AnchorDialect::Ecma)
}

pub(crate) fn selected_codeql_python_case(case: &Value) -> bool {
    case["language"] == "python"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .is_some_and(|query| query == CODEQL_PYTHON_QUERY)
}

pub(crate) fn codeql_python_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut all_cases = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if selected_codeql_python_case(&case) {
            all_cases.push((path, case));
        }
    }
    let query = validate_codeql_python_population(&all_cases)?;
    if !query.is_file() {
        bail!("Python CodeQL query does not exist: {}", query.display());
    }
    if !Path::new(CODEQL_PYTHON_ENDPOINT_PROBE).is_file() {
        bail!("Python CodeQL endpoint probe does not exist: {CODEQL_PYTHON_ENDPOINT_PROBE}");
    }
    Ok(all_cases)
}

pub(crate) fn validate_codeql_python_population(cases: &[(PathBuf, Value)]) -> Result<PathBuf> {
    let mut queries = BTreeSet::new();
    for (path, case) in cases {
        if !selected_codeql_python_case(case) {
            bail!(
                "Python CodeQL selection contains a non-core or non-Python case: {}",
                path.display()
            );
        }
        let query = case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .context("Python CodeQL case lacks query reference")?;
        queries.insert(PathBuf::from(query));
    }
    let templates = expected_core_templates("python");
    validate_kernel_population_with(cases, "Python CodeQL kernel", &templates)?;
    if queries.len() != 1 {
        let case_count = 2 * templates.len();
        bail!("Python CodeQL kernel must use one query across all {case_count} cases");
    }
    let query = queries.into_iter().next().expect("one query validated");
    Ok(query)
}

pub(crate) fn codeql_python_configuration_paths(
    query_paths: &BTreeSet<PathBuf>,
) -> BTreeSet<PathBuf> {
    let mut paths = query_paths.clone();
    paths.insert(PathBuf::from(CODEQL_PYTHON_ENDPOINT_PROBE));
    for candidate in [
        "adapters/codeql/python/qlpack.yml",
        "adapters/codeql/python/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

pub(crate) fn run_codeql_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    run_codeql_case_for_language(
        binary,
        packs,
        case_path,
        case,
        query,
        Some(Path::new(CODEQL_JAVA_ENDPOINT_PROBE)),
        raw_dir,
        CodeqlLanguage::Java,
    )
}

/// Run one CodeQL case: build the database, analyze it, and reconcile the
/// SARIF into an outcome.
///
/// The kernel populations pass their language's companion
/// endpoint-observation probe as `endpoint_probe`; it is evaluated in the same
/// `database analyze` invocation as `query`, and a run in which the probe
/// never observed both benchmark-controlled endpoints is `inconclusive` on the
/// same terms as `JoernEndpointRule::BothMustBeObserved`. The modeling matrix
/// passes `None`: an absent *declared* endpoint is frequently the assertion a
/// modeling negative makes, exactly as under Joern's
/// `AbsenceIsTheAssertion` rule.
#[allow(clippy::too_many_arguments)]
pub(crate) fn run_codeql_case_for_language(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    endpoint_probe: Option<&Path>,
    raw_dir: &Path,
    language: CodeqlLanguage,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let mut analysis = vec![query.to_string_lossy().into_owned()];
    if let Some(probe) = endpoint_probe {
        analysis.push(probe.to_string_lossy().into_owned());
    }
    let sarif = match codeql_sarif_for_case(
        binary, packs, case_path, case, raw_dir, language, &analysis,
    )? {
        CodeqlSarif::Failed(outcome) => return Ok(outcome),
        CodeqlSarif::Analyzed { sarif, raw_path } => (sarif, raw_path),
    };
    let (sarif, raw_path) = sarif;
    let sarif = if endpoint_probe.is_some() {
        // A document with no analysis run is malformed evidence, not an
        // unobserved endpoint: it stays `runner-error`, exactly as the ECMA
        // runner and `normalize_anchored_codeql_sarif` already read it.
        if !sarif["runs"]
            .as_array()
            .is_some_and(|runs| !runs.is_empty())
        {
            return Ok((
                "runner-error",
                vec!["CodeQL SARIF contains no analysis runs".to_string()],
                raw_path,
            ));
        }
        let (kernel_sarif, observation) = split_codeql_endpoint_probe(&sarif);
        if let Some((outcome, diagnostics)) = unobserved_codeql_endpoint_outcome(observation) {
            return Ok((outcome, diagnostics, raw_path));
        }
        kernel_sarif
    } else {
        sarif
    };
    let (outcome, diagnostics) = match language {
        CodeqlLanguage::Python => normalize_anchored_codeql_sarif(case, &sarif, "Python"),
        CodeqlLanguage::Kotlin { .. } => normalize_anchored_codeql_sarif(case, &sarif, "Kotlin"),
        // C#, Go, C, C++, and Rust fixtures all declare a `DFB-SINK:` function,
        // so the finding is reconciled against that function's callsites rather
        // than the sink file alone.
        CodeqlLanguage::CSharp => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::CSharp)
        }
        CodeqlLanguage::Go { .. } => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Go)
        }
        CodeqlLanguage::CFamily => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Cpp)
        }
        CodeqlLanguage::Rust => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Rust)
        }
        CodeqlLanguage::Ruby => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Ruby)
        }
        // Only the modeling matrix reaches this arm: the JavaScript kernel runs
        // through `run_codeql_ecma_case`, whose dialect is the plain ECMA one.
        CodeqlLanguage::Javascript => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::EcmaMember)
        }
        CodeqlLanguage::Java => {
            let result_count = sarif_result_count(&sarif);
            let diagnostics = sarif_messages(&sarif);
            let outcome = if result_count == 0 {
                "not-reached"
            } else {
                "reached"
            };
            (outcome, diagnostics)
        }
    };
    Ok((outcome, diagnostics, raw_path))
}

/// The result of driving CodeQL over one case: either a runner-level failure
/// whose evidence is already written, or the parsed SARIF for the caller to
/// reconcile.
pub(crate) enum CodeqlSarif {
    Failed((&'static str, Vec<String>, PathBuf)),
    Analyzed { sarif: Value, raw_path: PathBuf },
}

/// Build one case's database and analyze it, returning the SARIF rather than an
/// outcome.
///
/// Extraction, the traced build, evidence paths, and scratch cleanup are
/// identical for every CodeQL population here; what differs is *what is
/// analyzed* and *how a finding is reconciled*. The `analysis` slice carries
/// the former — a benchmark query path for the kernels and the modeling
/// matrix, a pinned shipped suite plus its threat-model option for the
/// tool-native profile — and the caller supplies the latter.
pub(crate) fn codeql_sarif_for_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
    language: CodeqlLanguage,
    analysis: &[String],
) -> Result<CodeqlSarif> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = materialize_codeql_workspace(case_path, case)?;
    let database_root = std::env::temp_dir().join("dataflowbench-codeql-databases");
    fs::create_dir_all(&database_root)?;
    let database = database_root.join(id);
    if database.exists() {
        fs::remove_dir_all(&database).with_context(|| format!("clear {}", database.display()))?;
    }
    for stale in [
        raw_dir.join(format!("{id}.sarif.json")),
        raw_dir.join(format!("{id}-error.json")),
        case_timing_path(raw_dir, id),
    ] {
        if stale.exists() {
            fs::remove_file(&stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }
    let mut phases: Vec<(&str, Duration)> = Vec::new();
    let mut create_command = Command::new(binary);
    if language.traces_jvm_compile() {
        let classes = workspace.join("classes");
        fs::create_dir_all(&classes)?;
    }
    if matches!(language, CodeqlLanguage::Go { .. }) {
        fs::write(workspace.join("go.mod"), GO_MODULE_MANIFEST)
            .with_context(|| format!("write Go module manifest in {}", workspace.display()))?;
    }
    if matches!(language, CodeqlLanguage::Rust) {
        write_rust_cargo_manifest(&workspace, case)?;
    }
    create_command.args(codeql_database_create_args(
        &database, &workspace, case, language,
    )?);
    let create_started = Instant::now();
    let create = match create_command.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database create: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-create", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(CodeqlSarif::Failed((
                "runner-error",
                vec![diagnostic],
                raw_path,
            )));
        }
    };
    phases.push(("database-create", create_started.elapsed()));
    write_case_phase_timings(raw_dir, "codeql", id, &phases)?;
    if !create.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-create", &create)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(CodeqlSarif::Failed(error));
    }

    let raw_path = raw_dir.join(format!("{id}.sarif.json"));
    let mut analyze = Command::new(binary);
    analyze
        .arg("database")
        .arg("analyze")
        .arg(&database)
        .args(analysis)
        .arg("--format=sarif-latest")
        .arg(format!("--output={}", raw_path.display()))
        .arg("--rerun");
    if let Some(packs) = packs {
        analyze.arg(format!("--additional-packs={}", packs.display()));
    }
    let analyze_started = Instant::now();
    let analyzed = match analyze.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database analyze: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(CodeqlSarif::Failed((
                "runner-error",
                vec![diagnostic],
                raw_path,
            )));
        }
    };
    phases.push(("database-analyze", analyze_started.elapsed()));
    write_case_phase_timings(raw_dir, "codeql", id, &phases)?;
    if !analyzed.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-analyze", &analyzed)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(CodeqlSarif::Failed(error));
    }
    let sarif_text = match fs::read_to_string(&raw_path) {
        Ok(text) => text,
        Err(error) => {
            let (outcome, diagnostics, error_path) =
                codeql_missing_sarif_error(raw_dir, id, &raw_path, &error)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(CodeqlSarif::Failed((outcome, diagnostics, error_path)));
        }
    };
    let sarif: Value = match serde_json::from_str(&sarif_text) {
        Ok(sarif) => sarif,
        Err(error) => {
            let diagnostic = format!("parse CodeQL SARIF {}: {error}", raw_path.display());
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(CodeqlSarif::Failed((
                "runner-error",
                vec![diagnostic],
                raw_path,
            )));
        }
    };
    let execution_errors = sarif_execution_errors(&sarif);
    if !execution_errors.is_empty() {
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(CodeqlSarif::Failed((
            "runner-error",
            execution_errors,
            raw_path,
        )));
    }
    clear_codeql_case_artifacts(&workspace, &database)?;
    Ok(CodeqlSarif::Analyzed { sarif, raw_path })
}

pub(crate) fn clear_codeql_case_artifacts(workspace: &Path, database: &Path) -> Result<()> {
    for path in [database, workspace] {
        if path.exists() {
            fs::remove_dir_all(path).with_context(|| format!("clear {}", path.display()))?;
        }
    }
    Ok(())
}

pub(crate) fn materialize_codeql_workspace(case_path: &Path, case: &Value) -> Result<PathBuf> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = std::env::temp_dir()
        .join("dataflowbench-codeql-workspaces")
        .join(id);
    if workspace.exists() {
        fs::remove_dir_all(&workspace).with_context(|| format!("clear {}", workspace.display()))?;
    }
    fs::create_dir_all(&workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }
    Ok(workspace)
}

/// Give a materialized Rust workspace the Cargo manifest its extractor needs.
///
/// Both Rust analyzers want a crate, not a loose file: CodeQL's extractor and
/// Joern's `rust2cpg` each walk a Cargo manifest. `rust2cpg` given a bare `.rs`
/// file produces an empty CPG — no methods, no calls — so the manifest is the
/// difference between an analyzed case and one that silently looks negative.
/// Pointing the binary target straight at the fixture rather than moving it to
/// `src/main.rs` also keeps every reported location on the case's own anchor
/// filename, so no anchor reconciliation has to map a crate-relative path back.
///
/// The CodeQL extractor accepts `--build-mode=none` and never compiles the fixture,
/// but with no manifest in the source root it logs "semantic analyzer
/// unavailable (no manifest found)" and produces a syntax-only database that
/// resolves no call targets. The manifest is generated rather than checked in
/// so the fixtures stay single-file, exactly like every other language kernel:
/// the case metadata lists only the `.rs` file, and the crate root points
/// straight at it instead of moving it under `src/`, which keeps SARIF
/// locations on the case's own anchor paths. `[workspace]` stops Cargo from
/// walking out of the temporary directory looking for a parent workspace.
pub(crate) fn write_rust_cargo_manifest(workspace: &Path, case: &Value) -> Result<()> {
    let fixtures = codeql_fixture_names(case)?;
    let [fixture] = fixtures[..] else {
        bail!(
            "Rust case {} must declare exactly one fixture file; found {}",
            case["id"],
            fixtures.len()
        );
    };
    let manifest = format!(
        "[package]\n\
         name = \"dataflowbench_case\"\n\
         version = \"0.0.0\"\n\
         edition = \"2021\"\n\
         \n\
         [[bin]]\n\
         name = \"dataflowbench_case\"\n\
         path = \"{fixture}\"\n\
         \n\
         [workspace]\n"
    );
    fs::write(workspace.join("Cargo.toml"), manifest)
        .with_context(|| format!("write Cargo manifest in {}", workspace.display()))?;
    Ok(())
}

pub(crate) fn write_codeql_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    output: &std::process::Output,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let raw_path = raw_dir.join(format!("{id}-error.json"));
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let diagnostic = format!("CodeQL {stage} failed with status {}", output.status);
    fs::write(
        &raw_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "codeql",
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "status": output.status.code(),
            "stdout": stdout,
            "stderr": stderr
        }))? + "\n",
    )?;
    Ok(("runner-error", vec![diagnostic], raw_path))
}

pub(crate) fn write_codeql_spawn_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
) -> Result<PathBuf> {
    let raw_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &raw_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "codeql",
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "diagnostic": diagnostic,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(raw_path)
}

pub(crate) fn codeql_missing_sarif_error(
    raw_dir: &Path,
    id: &str,
    raw_path: &Path,
    error: &std::io::Error,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let diagnostic = format!("read CodeQL SARIF {}: {error}", raw_path.display());
    let error_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
    Ok(("runner-error", vec![diagnostic], error_path))
}

pub(crate) fn codeql_database_create_args(
    database: &Path,
    workspace: &Path,
    case: &Value,
    language: CodeqlLanguage,
) -> Result<Vec<String>> {
    let mut args = vec![
        "database".to_string(),
        "create".to_string(),
        database.to_string_lossy().into_owned(),
        format!("--language={}", language.cli_name()),
        format!("--source-root={}", workspace.display()),
        "--overwrite".to_string(),
    ];
    match language {
        CodeqlLanguage::Java => {
            let fixtures = codeql_fixture_names(case)?;
            args.push(format!("--command=javac -d classes {}", fixtures.join(" ")));
        }
        // CodeQL 2.26.3 extracts no Kotlin at all under `--build-mode=none`;
        // the java extractor only sees Kotlin while it traces a real compile.
        CodeqlLanguage::Kotlin { kotlinc } => {
            let fixtures = codeql_fixture_names(case)?;
            args.push(format!(
                "--command={} -nowarn -d classes {}",
                kotlinc.display(),
                fixtures.join(" ")
            ));
        }
        // The Python, C#, C/C++, and Rust extractors all support
        // `--build-mode=none`, so the fixtures need no project scaffolding, no
        // restore step, and no traced compile. For C/C++ the buildless
        // extractor still discovers a real compiler (clang) to resolve the
        // translation unit; Rust still needs the generated Cargo manifest in
        // the workspace, because without a manifest the extractor reports
        // "semantic analyzer unavailable" and extracts syntax only.
        CodeqlLanguage::Python
        | CodeqlLanguage::CSharp
        | CodeqlLanguage::CFamily
        | CodeqlLanguage::Rust
        | CodeqlLanguage::Ruby => args.push("--build-mode=none".to_string()),
        // The `javascript` extractor takes no build mode; the ECMA kernels
        // invoke it exactly this way.
        CodeqlLanguage::Javascript => {}
        // CodeQL 2.26.3 rejects `--build-mode=none` for Go. The traced build is
        // `go build ./...` over the workspace's synthesized module manifest,
        // which keeps extraction reproducible instead of letting autobuild
        // write its own manifest and resolve dependencies.
        CodeqlLanguage::Go { go } => {
            args.push("--build-mode=manual".to_string());
            args.push(format!("--command={} build ./...", go.display()));
        }
    }
    Ok(args)
}

pub(crate) fn codeql_fixture_names(case: &Value) -> Result<Vec<&str>> {
    case["fixture_files"]
        .as_array()
        .context("CodeQL case lacks fixture_files")?
        .iter()
        .map(|fixture| {
            fixture
                .as_str()
                .context("CodeQL fixture_files must contain strings")
        })
        .collect()
}

/// Reconcile SARIF findings with the case's `DFB-SINK:` anchor file. A finding
/// that lands in an anchored sink file is `reached`; findings that carry no
/// usable location, or that never map onto a canonical sink anchor, are
/// incomplete evidence and stay `inconclusive` rather than becoming a clean
/// negative.
pub(crate) fn normalize_anchored_codeql_sarif(
    case: &Value,
    sarif: &Value,
    language: &str,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = sarif_messages(sarif);
    let Some(runs) = sarif["runs"].as_array() else {
        diagnostics.push("CodeQL SARIF is missing its runs array".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    };
    if runs.is_empty() {
        diagnostics.push("CodeQL SARIF contains no analysis runs".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    }
    if runs.iter().any(|run| run["results"].as_array().is_none()) {
        diagnostics.push("CodeQL SARIF contains a run without a results array".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    }
    let results = runs
        .iter()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
        .collect::<Vec<_>>();
    if results.is_empty() {
        return ("not-reached", diagnostics);
    }

    let mut anchored_findings = 0;
    let mut unmappable_findings = 0;
    for result in results {
        let Some(locations) = result["locations"].as_array() else {
            unmappable_findings += 1;
            continue;
        };
        let mut has_valid_location = false;
        let mut maps_to_sink = false;
        for location in locations {
            let Some(uri) = location["physicalLocation"]["artifactLocation"]["uri"].as_str() else {
                continue;
            };
            let Some(line) = location["physicalLocation"]["region"]["startLine"].as_u64() else {
                continue;
            };
            if line == 0 {
                continue;
            }
            has_valid_location = true;
            if sink_anchor_file_matches(case, uri) {
                maps_to_sink = true;
            }
        }
        if maps_to_sink {
            anchored_findings += 1;
        } else {
            unmappable_findings += 1;
            if !has_valid_location {
                diagnostics
                    .push("CodeQL SARIF finding has no usable physical location".to_string());
            }
        }
    }
    if anchored_findings > 0 {
        if unmappable_findings > 0 {
            diagnostics.push(format!(
                "CodeQL SARIF retained {unmappable_findings} finding(s) that did not map to a canonical {language} sink anchor"
            ));
        }
        diagnostics.sort();
        diagnostics.dedup();
        ("reached", diagnostics)
    } else {
        diagnostics.push(format!(
            "CodeQL SARIF findings could not be mapped to a canonical {language} sink anchor; analysis evidence is incomplete"
        ));
        diagnostics.sort();
        diagnostics.dedup();
        ("inconclusive", diagnostics)
    }
}

/// The `@id` suffix every kernel endpoint-observation probe carries. The probe
/// runs in the same `database analyze` invocation as the kernel query, so its
/// rows land in the same SARIF document; this suffix is how they are told apart
/// from the kernel's own findings.
pub(crate) const CODEQL_ENDPOINT_PROBE_RULE_SUFFIX: &str = "-kernel-endpoint-probe";

/// What a kernel run's companion endpoint-observation probe reported: how many
/// benchmark-controlled source and sink endpoints resolved in the extracted
/// database. The CodeQL counterpart of Joern's `source_node_count` /
/// `sink_node_count` evidence fields.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct CodeqlEndpointObservation {
    pub(crate) sources: usize,
    pub(crate) sinks: usize,
}

pub(crate) fn codeql_endpoint_probe_result(result: &Value) -> bool {
    result["ruleId"].as_str().is_some_and(|id| {
        id.starts_with("dataflowbench/") && id.ends_with(CODEQL_ENDPOINT_PROBE_RULE_SUFFIX)
    })
}

/// Separate a kernel SARIF document into the kernel query's own findings and
/// the endpoint-observation probe's counts. The probe's rows are removed from
/// the returned document so every existing reconciler keeps seeing exactly the
/// kernel's result set; the original SARIF is retained on disk unmodified, so
/// the probe rows stay available as raw evidence.
pub(crate) fn split_codeql_endpoint_probe(sarif: &Value) -> (Value, CodeqlEndpointObservation) {
    let mut kernel = sarif.clone();
    let mut observation = CodeqlEndpointObservation {
        sources: 0,
        sinks: 0,
    };
    for run in kernel["runs"].as_array_mut().into_iter().flatten() {
        let Some(results) = run["results"].as_array_mut() else {
            continue;
        };
        results.retain(|result| {
            if !codeql_endpoint_probe_result(result) {
                return true;
            }
            // CodeQL merges `@kind problem` rows that share a location into
            // one SARIF result whose message joins the rows' texts with
            // newlines. A fixture whose sink argument *is* the source call
            // (`dfb_sink(dfb_source())`) resolves both endpoints to the same
            // expression, so one result can carry both observations; count
            // every line, never just the first.
            let message = result["message"]["text"].as_str().unwrap_or_default();
            for line in message.lines() {
                if line.contains("source endpoint observed") {
                    observation.sources += 1;
                } else if line.contains("sink endpoint observed") {
                    observation.sinks += 1;
                }
            }
            false
        });
    }
    (kernel, observation)
}

/// The CodeQL kernels' mirror of `JoernEndpointRule::BothMustBeObserved`: a
/// kernel fixture always contains both of its own endpoints by construction, so
/// a run whose probe never observed one of them is an incomplete run, never a
/// clean negative. The evidence — the SARIF carrying the probe's rows — is
/// retained as-is; only the interpretation is withheld.
pub(crate) fn unobserved_codeql_endpoint_outcome(
    observation: CodeqlEndpointObservation,
) -> Option<(&'static str, Vec<String>)> {
    (observation.sources == 0 || observation.sinks == 0).then(|| {
        (
            "inconclusive",
            vec![format!(
                "CodeQL endpoint probe resolved {} source endpoint(s) and {} sink endpoint(s); the run never observed both benchmark-controlled endpoints",
                observation.sources, observation.sinks
            )],
        )
    })
}

/// The CodeQL extractor and the Joern frontend a modeling language runs under.
/// Both are the same ones that language's kernel already runs under; a modeling
/// run differs from its sibling only in which artifact it loads.
pub(crate) fn modeling_codeql_language(
    language: ModelingLanguage,
) -> Result<CodeqlLanguage<'static>> {
    match language {
        ModelingLanguage::Python => Ok(CodeqlLanguage::Python),
        ModelingLanguage::Javascript => Ok(CodeqlLanguage::Javascript),
        // Java runs under the same extractor its kernel does, which is what
        // supplies the `--build-mode=none` handling a compiled language needs.
        ModelingLanguage::Java => Ok(CodeqlLanguage::Java),
    }
}

/// The CodeQL extractor a tool-native run uses.
///
/// Extraction is a property of the language, not of the model profile: a native
/// database is built exactly the way the benchmark-controlled one is, and only
/// the *analysis* differs — a shipped suite instead of an adapter query. Sharing
/// the mapping is what keeps the two profiles' databases comparable even though
/// their query resolutions deliberately are not.
pub(crate) fn native_codeql_language(
    language: ModelingLanguage,
) -> Result<CodeqlLanguage<'static>> {
    modeling_codeql_language(language)
}

/// Run one *scored* native cell through CodeQL's shipped security suite.
///
/// There is one CodeQL driver in this file and every population shares it:
/// `codeql_sarif_for_case` builds the database with the language's own
/// extractor and traced build, writes the failure evidence, and cleans up the
/// scratch, exactly as the kernels and the modeling matrix do. Only two things
/// are native here, and both are arguments to that driver rather than a second
/// copy of it: *what is analyzed* — the pinned query pack's own suite plus the
/// `local` threat-model group, passed verbatim in the order `native_activation`
/// pins and `native_configuration_hash` hashes, so the invocation and the
/// retained provenance cannot drift apart — and *how a finding is reconciled*,
/// which is `native_sarif_outcome`.
///
/// The `--codeql-packs` search path is deliberately **not** forwarded. The
/// activation contract in docs/native-profile.md says "no adapter query, no
/// data extension, no `--additional-packs` model of ours", and the runner's
/// gate on that path exists so a stale value fails fast, not so it is used.
/// The shipped suite resolves from the pinned query pack through the CLI's own
/// pack resolution and needs no search path of ours.
pub(crate) fn run_codeql_native_case(
    binary: &Path,
    case_path: &Path,
    case: &Value,
    plan: &NativeRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let sarif = codeql_sarif_for_case(
        binary,
        None,
        case_path,
        case,
        &plan.raw_dir,
        native_codeql_language(plan.language)?,
        &plan.activation.arguments,
    )?;
    Ok(match sarif {
        CodeqlSarif::Failed(outcome) => outcome,
        CodeqlSarif::Analyzed { sarif, raw_path } => {
            let (outcome, diagnostics) = native_sarif_outcome(case_path, case, &sarif);
            (outcome, diagnostics, raw_path)
        }
    })
}

/// CodeQL: both declared subprocesses — `database create`, then
/// `database analyze` with the committed kernel query — timed separately and
/// summed, exactly as the cold whole-invocation figure is.
///
/// The two phases are retained individually as well, because CodeQL's row
/// already declares them: a reader can see how the estimate divides between
/// extraction and evaluation, and compare each against that adapter's own
/// published phase medians.
pub(crate) fn overhead_run_codeql(
    binary: &Path,
    packs: Option<&Path>,
    language: OverheadLanguage,
    run: usize,
) -> Result<OverheadRun> {
    let (codeql_language, query) = match language {
        OverheadLanguage::Ruby => (CodeqlLanguage::Ruby, CODEQL_RUBY_QUERY),
        OverheadLanguage::Python => (CodeqlLanguage::Python, CODEQL_PYTHON_QUERY),
        other => bail!("no CodeQL overhead arm for {}", other.as_str()),
    };
    let (scratch, workspace) = overhead_workspace(OverheadTool::Codeql, language, run)?;
    let database = scratch.join("database");
    let sarif = scratch.join("results.sarif.json");
    let (fixture_name, _) = trivial_fixture(language);
    let case = json!({ "fixture_files": [fixture_name] });

    let load_before = load_average_one_minute();
    let mut create = Command::new(binary);
    create.args(codeql_database_create_args(
        &database,
        &workspace,
        &case,
        codeql_language,
    )?);
    let create_started = Instant::now();
    let created = create
        .output()
        .with_context(|| format!("run CodeQL database create with {}", binary.display()))?;
    let create_ms = create_started.elapsed().as_millis() as u64;
    if !created.status.success() {
        bail!(
            "the CodeQL overhead database create failed with status {}:\n{}",
            created.status,
            String::from_utf8_lossy(&created.stderr)
        );
    }

    let mut analyze = Command::new(binary);
    analyze
        .arg("database")
        .arg("analyze")
        .arg(&database)
        .arg(query)
        .arg("--format=sarif-latest")
        .arg(format!("--output={}", sarif.display()))
        .arg("--rerun");
    if let Some(packs) = packs {
        analyze.arg(format!("--additional-packs={}", packs.display()));
    }
    let analyze_started = Instant::now();
    let analyzed = analyze
        .output()
        .with_context(|| format!("run CodeQL database analyze with {}", binary.display()))?;
    let analyze_ms = analyze_started.elapsed().as_millis() as u64;
    if !analyzed.status.success() {
        bail!(
            "the CodeQL overhead database analyze failed with status {}:\n{}",
            analyzed.status,
            String::from_utf8_lossy(&analyzed.stderr)
        );
    }
    if !sarif.is_file() {
        bail!("the CodeQL overhead invocation produced no SARIF document");
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![
            ("database-create".into(), create_ms),
            ("database-analyze".into(), analyze_ms),
        ],
        wall_ms: create_ms + analyze_ms,
        load_before,
    })
}
