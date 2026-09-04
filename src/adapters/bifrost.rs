//! The Bifrost adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/bifrost/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ModelingTool;
use crate::adapters::codeql::{CFamilyKernel, c_family_selected_case, rust_kernel_case};
use crate::cases::{
    LoadedCases, case_paths, csharp_core_case, fixture_revision, go_core_case, java_core_case,
    javascript_core_case, kotlin_core_case, php_core_case, ruby_core_case, scala_core_case,
    validate_cases,
};
use crate::evidence::{
    AnchorDialect, EvidenceAnchorMatch, SinkAnchorLocation, evidence_path_matches_file,
    sink_anchor_locations,
};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, load_average_one_minute, overhead_workspace,
};
use crate::modeling::{
    ModelingRunPlan, materialize_modeling_workspace, modeling_anchor_dialect, modeling_case_scratch,
};
use crate::report::{ADAPTER_VERSION, hash_paths, write_and_validate_report};
use crate::runtime::{
    clear_stale_case_timing, command_output, now_seconds, write_case_phase_timings,
    write_run_environment,
};
use crate::templates::{challenge_template_case, expected_core_case_count};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Instant};

pub(crate) const BIFROST_C_POLICY: &str = "adapters/bifrost/policies/core-c-kernel.rqlp";
pub(crate) const BIFROST_CPP_POLICY: &str = "adapters/bifrost/policies/core-cpp-kernel.rqlp";
pub(crate) const BIFROST_CSHARP_POLICY: &str = "adapters/bifrost/policies/core-csharp-kernel.rqlp";
pub(crate) const BIFROST_GO_POLICY: &str = "adapters/bifrost/policies/core-go-kernel.rqlp";
pub(crate) const BIFROST_RUST_POLICY: &str = "adapters/bifrost/policies/core-rust-kernel.rqlp";
pub(crate) const BIFROST_RUBY_POLICY: &str = "adapters/bifrost/policies/core-ruby-kernel.rqlp";
/// The language-qualified Bifrost policy for the PHP kernel. PHP has no CodeQL
/// support in the pinned CLI at all, so Bifrost and Joern are its two analyzers;
/// see docs/php-kernel.md.
pub(crate) const BIFROST_PHP_POLICY: &str = "adapters/bifrost/policies/core-php-kernel.rqlp";
/// The cross-language direct-flow breadth policy. The C# and Go
/// direct-propagation pairs predate their kernels and are frozen in the
/// published v0.2.0 evidence, so they keep this policy reference while still
/// belonging to their kernel's 16 balanced templates.
pub(crate) const BIFROST_DIRECT_POLICY: &str = "adapters/bifrost/policies/core-direct.rqlp";
/// The two single-assertion policies the frozen Java direct-propagation pair
/// declares: the positive names `direct-positive.rqlp` and the negative names
/// `explicit-negative.rqlp`. Both predate the Java kernel command and are bound
/// byte-for-byte by the v0.2.0 and v0.3.0 freeze manifests, so the Java kernel
/// accepts them the way the Kotlin, C#, Go, and C-family kernels accept the
/// cross-language breadth policy — by accommodating the frozen reference rather
/// than rewriting published evidence.
pub(crate) const BIFROST_DIRECT_POSITIVE_POLICY: &str =
    "adapters/bifrost/policies/direct-positive.rqlp";
pub(crate) const BIFROST_EXPLICIT_NEGATIVE_POLICY: &str =
    "adapters/bifrost/policies/explicit-negative.rqlp";
/// The language-qualified Bifrost policy declared by ordinary Java kernel
/// assertions. The Java kernel consumes each case's validated declared policy,
/// and its configuration hash covers all selected policy files.
pub(crate) const BIFROST_JAVA_POLICY: &str = "adapters/bifrost/policies/core-java-kernel.rqlp";
/// The language-qualified Bifrost policy every JavaScript kernel assertion is
/// evaluated with. Its frozen direct-propagation pair names the cross-language
/// breadth policy instead, on the same precedent.
pub(crate) const BIFROST_JAVASCRIPT_POLICY: &str =
    "adapters/bifrost/policies/core-javascript-kernel.rqlp";
/// The language-qualified Bifrost policy that every Kotlin kernel assertion is
/// evaluated with. Two of the 32 Kotlin core assertions — the
/// `dfb-template-direct-propagation` pair — were frozen in v0.2.0 as part of
/// the cross-language direct-flow breadth slice, so their case metadata still
/// names the language-neutral breadth policy. The kernel run deliberately
/// evaluates this policy for the whole population so all 32 assertions share
/// one configuration; see docs/kotlin-kernel.md.
pub(crate) const BIFROST_KOTLIN_POLICY: &str = "adapters/bifrost/policies/core-kotlin-kernel.rqlp";
/// The language-qualified Bifrost policy every Scala kernel assertion is
/// evaluated with. Scala has single-analyzer coverage: CodeQL CLI 2.26.4 has no
/// Scala extractor at all, and the pinned Joern 4.0.614 has no Scala *source*
/// frontend. Both absences are analyzer coverage recorded in
/// docs/scala-kernel.md, never negative results. As with Kotlin, the frozen
/// v0.2.0 direct-propagation pair still names the language-neutral breadth
/// policy in its case metadata, so the run pins this policy for the whole
/// population and all 32 assertions share one configuration.
pub(crate) const BIFROST_SCALA_POLICY: &str = "adapters/bifrost/policies/core-scala-kernel.rqlp";
/// The `call-modeling` setting a Bifrost modeling policy must carry. Every
/// committed kernel policy sets `:unmodeled optimistic`, under which an
/// unmodeled call may pass taint through and would decide template 3's
/// positive without the propagator declaration ever being read. A modeling
/// policy that kept that default would not be measuring activation.
pub(crate) const BIFROST_MODELING_CALL_MODELING: &str = "require-model";

/// Enforce the load-bearing-model requirement on a Bifrost modeling policy.
///
/// The requirement is the document's, not this runner's: a cell the engine's
/// unmodeled-call default already decides is not a measurement. Wiring the
/// check here means a language PR cannot author a modeling policy that
/// silently inherits the kernel policies' optimistic default.
pub(crate) fn require_bifrost_modeling_load_bearing(policy: &str, path: &str) -> Result<()> {
    if !policy.contains(BIFROST_MODELING_CALL_MODELING) {
        bail!(
            "{path} does not set `:call-modeling (call-modeling :unmodeled {BIFROST_MODELING_CALL_MODELING})`; docs/modeling-matrix.md#the-load-bearing-model-requirement requires the unmodeled-call default to be configured so that the model is load-bearing"
        );
    }
    if policy.contains("optimistic") {
        bail!(
            "{path} still names the kernel policies' `:unmodeled optimistic` default; under it an unmodeled call may pass taint through and would decide a category P or O cell without the declaration being read"
        );
    }
    Ok(())
}

/// Bifrost's native activation surface: built-in policy packs only. A native
/// run may not pass `--policy-file`, which is how every benchmark-controlled
/// Bifrost run supplies its models.
pub(crate) const BIFROST_NATIVE_POLICY_PACK_FLAG: &str = "--policy-pack";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum BifrostRun {
    Smoke,
    JavaKernel,
    JavascriptKernel,
    PythonKernel,
    KotlinKernel,
    ScalaKernel,
    TypescriptKernel,
    CsharpKernel,
    GoKernel,
    CKernel,
    CppKernel,
    RustKernel,
    RubyKernel,
    PhpKernel,
}

impl BifrostRun {
    /// The label a run is named by in diagnostics.
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Smoke => "Bifrost smoke",
            Self::JavaKernel => "Bifrost Java kernel",
            Self::JavascriptKernel => "Bifrost JavaScript kernel",
            Self::PythonKernel => "Bifrost Python kernel",
            Self::KotlinKernel => "Bifrost Kotlin kernel",
            Self::ScalaKernel => "Bifrost Scala kernel",
            Self::TypescriptKernel => "Bifrost TypeScript kernel",
            Self::CsharpKernel => "Bifrost C# kernel",
            Self::GoKernel => "Bifrost Go kernel",
            Self::CKernel => "Bifrost C kernel",
            Self::CppKernel => "Bifrost C++ kernel",
            Self::RustKernel => "Bifrost Rust kernel",
            Self::RubyKernel => "Bifrost Ruby kernel",
            Self::PhpKernel => "Bifrost PHP kernel",
        }
    }

    /// The language whose core denominator this run must cover, or `None` for
    /// the cross-language smoke slice, whose population is the frozen
    /// policy-pinned selection rather than one language's kernel.
    pub(crate) fn language(self) -> Option<&'static str> {
        match self {
            Self::Smoke => None,
            Self::JavaKernel => Some("java"),
            Self::JavascriptKernel => Some("javascript"),
            Self::PythonKernel => Some("python"),
            Self::KotlinKernel => Some("kotlin"),
            Self::ScalaKernel => Some("scala"),
            Self::TypescriptKernel => Some("typescript"),
            Self::CsharpKernel => Some("csharp"),
            Self::GoKernel => Some("go"),
            Self::CKernel => Some("c"),
            Self::CppKernel => Some("cpp"),
            Self::RustKernel => Some("rust"),
            Self::RubyKernel => Some("ruby"),
            Self::PhpKernel => Some("php"),
        }
    }

    /// The core denominator a kernel run must cover exactly, or `None` for a
    /// run whose population is defined some other way. The count comes from the
    /// language's `CHALLENGE_ROLLOUT` row, so a wave PR that flips that row
    /// moves this number with it — 32 for a classic Java kernel, 58 once Java's
    /// challenge fixtures land — without the runner being touched. The C and
    /// Rust `language-extension` cases are selected by the same run but are
    /// counted and scored separately, so they never move this number.
    pub(crate) fn expected_core_cases(self) -> Option<usize> {
        match self {
            // The Python and TypeScript runs select by policy reference as
            // well as by language, so their population is not pinned to the
            // denominator here; it is the selector that defines it.
            Self::Smoke | Self::PythonKernel | Self::TypescriptKernel => None,
            other => other.language().map(expected_core_case_count),
        }
    }
}
pub(crate) fn run_bifrost_smoke(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::Smoke)
}

pub(crate) fn run_bifrost_python_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::PythonKernel)
}

pub(crate) fn run_bifrost_kotlin_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::KotlinKernel)
}

pub(crate) fn run_bifrost_csharp_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::CsharpKernel)
}

pub(crate) fn run_bifrost(binary: &Path, run: BifrostRun) -> Result<()> {
    validate_cases()?;
    let (raw_dir, report_path) = match run {
        BifrostRun::Smoke => (
            Path::new("reports/raw/bifrost"),
            Path::new("reports/bifrost-smoke.json"),
        ),
        BifrostRun::JavaKernel => (
            Path::new("reports/raw/bifrost-java-kernel"),
            Path::new("reports/bifrost-java-kernel.json"),
        ),
        BifrostRun::JavascriptKernel => (
            Path::new("reports/raw/bifrost-javascript-kernel"),
            Path::new("reports/bifrost-javascript-kernel.json"),
        ),
        BifrostRun::PythonKernel => (
            Path::new("reports/raw/bifrost-python-kernel"),
            Path::new("reports/bifrost-python-kernel.json"),
        ),
        BifrostRun::KotlinKernel => (
            Path::new("reports/raw/bifrost-kotlin-kernel"),
            Path::new("reports/bifrost-kotlin-kernel.json"),
        ),
        BifrostRun::ScalaKernel => (
            Path::new("reports/raw/bifrost-scala-kernel"),
            Path::new("reports/bifrost-scala-kernel.json"),
        ),
        BifrostRun::TypescriptKernel => (
            Path::new("reports/raw/bifrost-typescript-kernel"),
            Path::new("reports/bifrost-typescript-kernel.json"),
        ),
        BifrostRun::CsharpKernel => (
            Path::new("reports/raw/bifrost-csharp-kernel"),
            Path::new("reports/bifrost-csharp-kernel.json"),
        ),
        BifrostRun::GoKernel => (
            Path::new("reports/raw/bifrost-go-kernel"),
            Path::new("reports/bifrost-go-kernel.json"),
        ),
        BifrostRun::CKernel => (
            Path::new("reports/raw/bifrost-c-kernel"),
            Path::new("reports/bifrost-c-kernel.json"),
        ),
        BifrostRun::CppKernel => (
            Path::new("reports/raw/bifrost-cpp-kernel"),
            Path::new("reports/bifrost-cpp-kernel.json"),
        ),
        BifrostRun::RustKernel => (
            Path::new("reports/raw/bifrost-rust-kernel"),
            Path::new("reports/bifrost-rust-kernel.json"),
        ),
        BifrostRun::RubyKernel => (
            Path::new("reports/raw/bifrost-ruby-kernel"),
            Path::new("reports/bifrost-ruby-kernel.json"),
        ),
        BifrostRun::PhpKernel => (
            Path::new("reports/raw/bifrost-php-kernel"),
            Path::new("reports/bifrost-php-kernel.json"),
        ),
    };
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let version =
        command_output(Command::new(binary).arg("--version")).unwrap_or_else(|_| "unknown".into());
    let build_identity = command_output(Command::new(binary).arg("--build-identity"))
        .unwrap_or_else(|_| "unknown".into());
    write_run_environment(raw_dir, "bifrost", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::new();
    let mut policy_paths = BTreeSet::new();
    let mut selected_cases = 0;
    let mut selected_core_cases = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !selected_bifrost_case(&case, run) {
            continue;
        }
        selected_cases += 1;
        if case["score_tier"] == "core" {
            selected_core_cases += 1;
        }
        let id = case["id"].as_str().expect("schema validated");
        let model = &case["tool_model_references"]["bifrost"];
        let raw_path = raw_dir.join(format!("{id}.json"));
        if raw_path.exists() {
            fs::remove_file(&raw_path)
                .with_context(|| format!("clear stale raw output {}", raw_path.display()))?;
        }
        clear_stale_case_timing(raw_dir, id)?;
        let start = Instant::now();
        let (outcome, diagnostics, checkpoints) = if let Some(reason) =
            model["unsupported_reason"].as_str()
        {
            fs::write(
                &raw_path,
                serde_json::to_string_pretty(
                    &json!({"adapter": "bifrost", "case_id": id, "state": "unsupported", "reason": reason, "evidence_kind": "adapter-capability-declaration"}),
                )? + "\n",
            )?;
            ("unsupported", vec![reason.to_string()], Vec::new())
        } else {
            let policy = bifrost_policy_for(&case, run)?;
            policy_paths.insert(PathBuf::from(policy));
            let workspace = materialize_bifrost_workspace(&path, &case, policy)?;
            let mut command = Command::new(binary);
            command
                .arg("--root")
                .arg(&workspace)
                .arg("--policy-file")
                .arg("policy.rqlp")
                .args([
                    "--evaluation-date",
                    "2026-08-11",
                    "--format",
                    "json",
                    "--fail-on",
                    "never",
                    "--output",
                ])
                .arg(&raw_path);
            // One CLI invocation is indivisible from the adapter's vantage:
            // `total`, per #89. Any phase timings Bifrost emits itself ride in
            // the JSON report it writes to `raw_path` and are retained
            // verbatim.
            let invoked = Instant::now();
            let output = match command.output() {
                Ok(output) => output,
                Err(error) => {
                    let diagnostic = format!("failed to run {}: {error}", binary.display());
                    write_bifrost_error(&raw_path, id, None, "spawn", "", &diagnostic)?;
                    results.push(bifrost_result(
                        &case,
                        id,
                        "runner-error",
                        vec![diagnostic],
                        Vec::new(),
                        start.elapsed(),
                        &raw_path,
                    ));
                    continue;
                }
            };
            write_case_phase_timings(raw_dir, "bifrost", id, &[("total", invoked.elapsed())])?;
            let status_code = output.status.code();
            if !raw_path.is_file() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let diagnostic = format!(
                    "Bifrost policy execution produced no JSON report (status {})",
                    output.status
                );
                write_bifrost_error(
                    &raw_path,
                    id,
                    status_code,
                    "evaluate",
                    stdout.trim(),
                    &format!("{}\n{}", diagnostic, stderr.trim()),
                )?;
                ("runner-error", vec![diagnostic], Vec::new())
            } else {
                let raw = fs::read_to_string(&raw_path)
                    .with_context(|| format!("read {}", raw_path.display()))?;
                match serde_json::from_str::<Value>(&raw) {
                    Ok(mut report) => {
                        if status_code.is_none()
                            || status_code.is_some_and(|code| !matches!(code, 0..=2))
                        {
                            report["_dataflowbench_runner"] = json!({
                                "outcome": "runner-error",
                                "exit_status": status_code
                            });
                            fs::write(&raw_path, serde_json::to_string_pretty(&report)? + "\n")?;
                        }
                        let dialect = bifrost_anchor_dialect(
                            case["language"].as_str().expect("schema validated"),
                        )?;
                        normalize_bifrost(&path, &case, &report, status_code, dialect)?
                    }
                    Err(error) => {
                        let diagnostic =
                            format!("parse Bifrost JSON report {}: {error}", raw_path.display());
                        ("runner-error", vec![diagnostic], Vec::new())
                    }
                }
            }
        };
        results.push(bifrost_result(
            &case,
            id,
            outcome,
            diagnostics,
            checkpoints,
            start.elapsed(),
            &raw_path,
        ));
    }
    if selected_cases == 0 {
        bail!("no cases selected for {}", run.label());
    }
    if let Some(expected) = run.expected_core_cases()
        && selected_core_cases != expected
    {
        bail!(
            "{} must select exactly {expected} core assertions; found {selected_core_cases}",
            run.label()
        );
    }
    let configuration_hash = hash_paths(&policy_paths)?;
    let report = json!({
        "schema_version": 1,
        "tool": "bifrost",
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
    write_and_validate_report(report_path, &report)?;
    println!("wrote {}", report_path.display());
    Ok(())
}

/// The Bifrost policy a run evaluates for one case.
///
/// Kernel runs normally pin the language-qualified policy for the population.
/// Java instead evaluates each case with its validated declared policy, so the
/// direct-propagation pair and future compatible policy variants retain the
/// selector contract recorded in their case metadata. The report configuration
/// hash covers every policy actually selected by the run.
pub(crate) fn bifrost_policy_for(case: &Value, run: BifrostRun) -> Result<&str> {
    let declared_policy = case["tool_model_references"]["bifrost"]["policy"]
        .as_str()
        .context("Bifrost case lacks policy reference")?;
    match run {
        BifrostRun::JavaKernel => Ok(declared_policy),
        BifrostRun::JavascriptKernel => Ok(BIFROST_JAVASCRIPT_POLICY),
        BifrostRun::KotlinKernel => Ok(BIFROST_KOTLIN_POLICY),
        BifrostRun::ScalaKernel => Ok(BIFROST_SCALA_POLICY),
        _ => Ok(declared_policy),
    }
}

/// The policy files a Bifrost run would hash into its `configuration_hash`
/// if it ran now: every policy [`bifrost_policy_for`] selects for a case the
/// run admits, minus preregistered-unsupported cases, which never reach a
/// policy. This mirrors the collection the run loop in [`run_bifrost`]
/// performs; a drift between the two fails the runner's own end-of-run
/// validation sweep.
pub(crate) fn bifrost_policy_paths(
    run: BifrostRun,
    cases: &LoadedCases,
) -> Result<BTreeSet<PathBuf>> {
    let mut paths = BTreeSet::new();
    for (_, case) in cases {
        if !selected_bifrost_case(case, run)
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string()
        {
            continue;
        }
        paths.insert(PathBuf::from(bifrost_policy_for(case, run)?));
    }
    Ok(paths)
}

pub(crate) fn selected_bifrost_case(case: &Value, run: BifrostRun) -> bool {
    match run {
        BifrostRun::Smoke => has_bifrost_model_reference(case) && smoke_population_case(case),
        BifrostRun::JavaKernel => java_kernel_bifrost_case(case),
        BifrostRun::JavascriptKernel => javascript_kernel_bifrost_case(case),
        BifrostRun::KotlinKernel => kotlin_core_case(case),
        BifrostRun::ScalaKernel => scala_core_case(case),
        BifrostRun::PythonKernel => {
            case["language"] == "python"
                && case["track"] == "taint"
                && case["score_tier"] == "core"
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| policy.ends_with("core-python-kernel.rqlp"))
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::TypescriptKernel => {
            case["language"] == "typescript"
                && case["track"] == "taint"
                && case["score_tier"] == "core"
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(typescript_kernel_policy)
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::CsharpKernel => {
            csharp_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_CSHARP_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::GoKernel => {
            go_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_GO_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::CKernel => c_family_bifrost_case(case, CFamilyKernel::C),
        BifrostRun::CppKernel => c_family_bifrost_case(case, CFamilyKernel::Cpp),
        BifrostRun::RubyKernel => {
            ruby_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_RUBY_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::RustKernel => {
            rust_kernel_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_RUST_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::PhpKernel => {
            php_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_PHP_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
    }
}

/// A Java assertion the dedicated Bifrost Java kernel run owns: the language's
/// whole core population, classic and — once java's `CHALLENGE_ROLLOUT` row is
/// flipped — challenge alike.
///
/// Most assertions use `BIFROST_JAVA_POLICY`. The direct-propagation pair
/// predates the kernel and names
/// `direct-positive.rqlp` and `explicit-negative.rqlp`, which the v0.2.0 and
/// v0.3.0 freezes bind byte-for-byte; those two policies remain authoritative
/// because their endpoint names match their frozen fixtures. Challenge cases
/// name the Java kernel policy, so they need no further accommodation.
pub(crate) fn java_kernel_bifrost_case(case: &Value) -> bool {
    java_core_case(case)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| {
                policy == BIFROST_JAVA_POLICY
                    || policy == BIFROST_DIRECT_POLICY
                    || policy == BIFROST_DIRECT_POSITIVE_POLICY
                    || policy == BIFROST_EXPLICIT_NEGATIVE_POLICY
            })
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

/// A JavaScript assertion the dedicated Bifrost JavaScript kernel run owns.
/// Same shape as the Java kernel; the frozen direct-propagation pair here names
/// the cross-language breadth policy rather than the single-assertion pair.
pub(crate) fn javascript_kernel_bifrost_case(case: &Value) -> bool {
    javascript_core_case(case)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| {
                policy == BIFROST_JAVASCRIPT_POLICY || policy == BIFROST_DIRECT_POLICY
            })
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

/// A C or C++ case this kernel run evaluates. As with the Kotlin and C#
/// kernels, the direct-propagation pair predates the kernel and is frozen in
/// the published v0.2.0 evidence naming the cross-language breadth policy, so
/// that policy reference is accepted alongside the language-qualified one.
pub(crate) fn c_family_bifrost_case(case: &Value, kernel: CFamilyKernel) -> bool {
    c_family_selected_case(case, kernel)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| policy == kernel.policy() || policy == BIFROST_DIRECT_POLICY)
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

/// Policies that carry a TypeScript kernel assertion.
///
/// The direct-propagation pair belongs to both the TypeScript kernel and the
/// cross-language direct-flow breadth slice, and was frozen in `v0.2.0` while
/// still declaring the language-agnostic `core-direct` policy. Freeze manifests
/// bind those case bytes, so the kernel accepts that policy instead of
/// rewriting published evidence; the two policies differ only by the
/// `(language typescript ...)` selector qualifier, which is redundant for a
/// single-fixture TypeScript workspace.
pub(crate) fn typescript_kernel_policy(policy: &str) -> bool {
    policy.ends_with("core-typescript-kernel.rqlp") || policy.ends_with("core-direct.rqlp")
}

pub(crate) fn has_bifrost_model_reference(case: &Value) -> bool {
    let model = &case["tool_model_references"]["bifrost"];
    model.is_object() && (model["policy"].is_string() || model["unsupported_reason"].is_string())
}

/// The smoke population is frozen by contract: the 13-language direct-flow
/// breadth pairs, the Java and JavaScript propagation kernels, the Python
/// parity kernel, and the calibration cases — 118 cases in total. Every later
/// language kernel has its own dedicated `run-bifrost-<language>-kernel`
/// population, so its policy must never leak into the smoke selection even
/// though its cases also carry Bifrost model references.
///
/// Pinning by policy alone stopped being sufficient once the challenge tier was
/// preregistered: a Java, JavaScript, or Python challenge case names the *same*
/// language kernel policy its classic siblings do, so it would have been swept
/// into the frozen 118 and silently changed what that population means. The
/// exclusion is therefore by template identity, which is the property that
/// actually distinguishes the tiers — any case whose `template_id` starts with
/// `dfb-template-chal-` is never smoke-selected, whatever policy it names and
/// whether or not it declares an `unsupported_reason`. The expanded core is
/// evaluated by the dedicated per-language kernel runs instead.
pub(crate) fn smoke_population_case(case: &Value) -> bool {
    if challenge_template_case(case) {
        return false;
    }
    // Same reasoning, one tier later: a Java, JavaScript, or Python modeling
    // case will name that language's Bifrost artifact, and the frozen 118 must
    // not absorb it. Modeling is a separate tier with a separate scorecard and
    // is never pooled with a kernel or calibration population.
    if case["score_tier"] == "modeling" {
        return false;
    }
    let model = &case["tool_model_references"]["bifrost"];
    if model["unsupported_reason"].is_string() {
        return true;
    }
    const SMOKE_POLICIES: [&str; 7] = [
        BIFROST_DIRECT_POLICY,
        BIFROST_DIRECT_POSITIVE_POLICY,
        BIFROST_EXPLICIT_NEGATIVE_POLICY,
        "adapters/bifrost/policies/one-hop-positive.rqlp",
        BIFROST_JAVA_POLICY,
        BIFROST_JAVASCRIPT_POLICY,
        "adapters/bifrost/policies/core-python-kernel.rqlp",
    ];
    model["policy"]
        .as_str()
        .is_some_and(|policy| SMOKE_POLICIES.contains(&policy))
}

pub(crate) fn bifrost_result(
    case: &Value,
    id: &str,
    outcome: &str,
    diagnostics: Vec<String>,
    checkpoints: Vec<Value>,
    duration: std::time::Duration,
    raw_path: &Path,
) -> Value {
    json!({
        "case_id": id,
        "outcome": outcome,
        "source_anchors": case["source_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "sink_anchors": case["sink_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "witness_checkpoints": checkpoints,
        "diagnostics": diagnostics,
        "duration_ms": duration.as_millis() as u64,
        "peak_memory_mb": Value::Null,
        "raw_output": raw_path.to_string_lossy()
    })
}

pub(crate) fn write_bifrost_error(
    raw_path: &Path,
    id: &str,
    status: Option<i32>,
    stage: &str,
    stdout: &str,
    stderr: &str,
) -> Result<()> {
    fs::write(
        raw_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "bifrost",
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(())
}

pub(crate) fn materialize_bifrost_workspace(
    case_path: &Path,
    case: &Value,
    policy: &str,
) -> Result<PathBuf> {
    let id = case["id"].as_str().expect("schema validated");
    // Keep generated workspaces outside this repository. Bifrost honors the
    // repository's ignore rules, so placing fixtures below ignored `target/`
    // would make an otherwise valid run index zero source files.
    let workspace = std::env::temp_dir()
        .join("dataflowbench-bifrost-smoke")
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
    fs::copy(policy, workspace.join("policy.rqlp"))?;
    Ok(workspace)
}

pub(crate) fn normalize_bifrost(
    case_path: &Path,
    case: &Value,
    report: &Value,
    status: Option<i32>,
    dialect: AnchorDialect,
) -> Result<(&'static str, Vec<String>, Vec<Value>)> {
    let mut report_diagnostics = diagnostics(report);
    let incompleteness = incompleteness_reasons(report);
    report_diagnostics.extend(incompleteness.iter().cloned());
    report_diagnostics.sort();
    report_diagnostics.dedup();
    match status {
        Some(0..=2) => {}
        Some(status) => {
            report_diagnostics.push(format!(
                "Bifrost exited with unexpected policy status {status}"
            ));
            report_diagnostics.sort();
            report_diagnostics.dedup();
            return Ok(("runner-error", report_diagnostics, Vec::new()));
        }
        None => {
            report_diagnostics.push(
                "Bifrost process exited without a status code (likely terminated by a signal)"
                    .to_string(),
            );
            report_diagnostics.sort();
            report_diagnostics.dedup();
            return Ok(("runner-error", report_diagnostics, Vec::new()));
        }
    }
    // A run that Bifrost itself reports as failed is an execution error, even
    // when the process exits with the inconclusive status 2. This mirrors the
    // freeze validator's `raw_special_outcome` precedence exactly: an
    // explicitly inconclusive completion still outranks a failed sibling run,
    // but a failure never normalizes to `inconclusive`.
    let has_inconclusive_completion = report["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|run| run["completion"]["type"] == "inconclusive");
    if !has_inconclusive_completion && let Some(reason) = bifrost_runner_error_reason(report) {
        report_diagnostics.push(reason);
        report_diagnostics.sort();
        report_diagnostics.dedup();
        return Ok(("runner-error", report_diagnostics, Vec::new()));
    }
    // Bifrost reserves exit status 2 for an unreliable/inconclusive run. It
    // takes precedence over finding absence, even if the report is sparse.
    if status == Some(2) {
        if incompleteness.is_empty() {
            report_diagnostics.push("Bifrost exited with inconclusive status 2".to_string());
        }
        return Ok(("inconclusive", report_diagnostics, Vec::new()));
    }
    if let Some(reason) = bifrost_runner_error_reason(report) {
        report_diagnostics.push(reason);
        report_diagnostics.sort();
        report_diagnostics.dedup();
        return Ok(("runner-error", report_diagnostics, Vec::new()));
    }
    if !report["runs"]
        .as_array()
        .is_some_and(|runs| !runs.is_empty())
    {
        report_diagnostics.push("Bifrost report contains no evaluation runs".to_string());
        report_diagnostics.sort();
        report_diagnostics.dedup();
        return Ok(("runner-error", report_diagnostics, Vec::new()));
    }
    if !incompleteness.is_empty() {
        return Ok(("inconclusive", report_diagnostics, Vec::new()));
    }
    if has_bifrost_empty_selection(report) {
        return Ok(("inconclusive", report_diagnostics, Vec::new()));
    }
    let findings = collect_bifrost_findings(report);
    if findings.is_empty() {
        return Ok(("not-reached", report_diagnostics, Vec::new()));
    }
    // A finding counts as `reached` only when it lands on a callsite of the
    // case's own anchored sink function, in the anchored file — the same
    // reconciliation every external adapter passes through (CodeQL's SARIF
    // anchor match, the Joern flow-anchor match, Semgrep's finding match).
    // A finding the case's sink anchor cannot vouch for is `inconclusive`,
    // never a clean `reached`. The raw report retains witnesses, but expected
    // checkpoints from the case are still never turned into observed result
    // evidence.
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            report_diagnostics.push(format!(
                "cannot prove a Bifrost finding against the sink anchor: {reason}"
            ));
            report_diagnostics.sort();
            report_diagnostics.dedup();
            return Ok(("inconclusive", report_diagnostics, Vec::new()));
        }
    };
    let mut matched = 0usize;
    let mut unmatched = 0usize;
    let mut ambiguous = 0usize;
    for finding in findings {
        match bifrost_finding_anchor_match(finding, &sink_locations) {
            EvidenceAnchorMatch::Matched => matched += 1,
            EvidenceAnchorMatch::Unmatched => unmatched += 1,
            EvidenceAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        report_diagnostics.push(format!(
            "{ambiguous} Bifrost finding(s) carry no usable or an ambiguous sink-anchor location"
        ));
        report_diagnostics.sort();
        report_diagnostics.dedup();
        return Ok(("inconclusive", report_diagnostics, Vec::new()));
    }
    if matched > 0 {
        return Ok(("reached", report_diagnostics, Vec::new()));
    }
    report_diagnostics.push(format!(
        "{unmatched} Bifrost finding(s) did not match the case sink anchor"
    ));
    report_diagnostics.sort();
    report_diagnostics.dedup();
    Ok(("inconclusive", report_diagnostics, Vec::new()))
}

/// The AnchorDialect a Bifrost run reconciles a case's sink anchor with,
/// selected from the case's own language. Kotlin and Scala declare their
/// sinks with the same identifier-before-parameter-list shape Java does, so
/// they share Java's dialect exactly as the Joern Kotlin kernel does.
pub(crate) fn bifrost_anchor_dialect(language: &str) -> Result<AnchorDialect> {
    match language {
        "java" | "kotlin" | "scala" => Ok(AnchorDialect::Java),
        "javascript" | "typescript" => Ok(AnchorDialect::Ecma),
        "python" => Ok(AnchorDialect::Python),
        "csharp" => Ok(AnchorDialect::CSharp),
        "go" => Ok(AnchorDialect::Go),
        "c" | "cpp" => Ok(AnchorDialect::Cpp),
        "rust" => Ok(AnchorDialect::Rust),
        "ruby" => Ok(AnchorDialect::Ruby),
        "php" => Ok(AnchorDialect::Php),
        other => bail!("no Bifrost sink-anchor dialect is wired for language {other:?}"),
    }
}

/// A Bifrost finding carries a single primary location, so reconciliation is
/// the one-location form of the Joern flow match, exactly as Semgrep's: the
/// finding's own file and line must land on a callsite of the case's anchored
/// sink.
pub(crate) fn bifrost_finding_anchor_match(
    finding: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> EvidenceAnchorMatch {
    let (Some(file), Some(line)) = (
        finding["primary"]["path"].as_str(),
        finding["primary"]["region"]["start_line"].as_u64(),
    ) else {
        return EvidenceAnchorMatch::Ambiguous;
    };
    if line == 0 {
        return EvidenceAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    for (index, anchor) in sink_locations.iter().enumerate() {
        if evidence_path_matches_file(file, &anchor.file) && anchor.callsite_lines.contains(&line) {
            matches.insert(index);
        }
    }
    if matches.len() > 1 {
        EvidenceAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        EvidenceAnchorMatch::Matched
    } else {
        EvidenceAnchorMatch::Unmatched
    }
}

/// An empty endpoint selection makes a taint verdict vacuous. Bifrost retains
/// it as a structured advisory because an embedding may intentionally ask an
/// empty question; DataFlowBench never does, since every scored case declares
/// anchored source and sink endpoints. Preserve that distinction by refusing
/// to grade the adapter result as a decisive miss.
pub(crate) fn has_bifrost_empty_selection(value: &Value) -> bool {
    value["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["diagnostics"].as_array().into_iter().flatten())
        .any(|diagnostic| {
            diagnostic["code"]["type"] == "empty_selection"
                || diagnostic["family"] == "empty_selection"
        })
}

pub(crate) fn incompleteness_reasons(value: &Value) -> Vec<String> {
    let mut reasons = Vec::new();
    for run in value["runs"].as_array().into_iter().flatten() {
        let Some(completion_type) = run["completion"]["type"].as_str() else {
            continue;
        };
        if completion_type == "complete" {
            continue;
        }
        let mut run_reasons = run["completion"]["reasons"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(str::to_string)
            .collect::<Vec<_>>();
        if run_reasons.is_empty() {
            run_reasons.push(format!("completion_type={completion_type}"));
        }
        reasons.extend(
            run_reasons
                .into_iter()
                .map(|reason| format!("Bifrost reported incomplete analysis: {reason}")),
        );
    }
    reasons.sort();
    reasons.dedup();
    reasons
}

pub(crate) fn bifrost_runner_error_reason(value: &Value) -> Option<String> {
    let failed_completion = value["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .find_map(|run| {
            run["completion"]["type"].as_str().and_then(|kind| {
                matches!(kind, "error" | "failed" | "runner-error")
                    .then(|| format!("Bifrost reported runner failure: {kind}"))
            })
        });
    if failed_completion.is_some() {
        return failed_completion;
    }
    for field in ["type", "state"] {
        if let Some(kind) = value["execution"]["termination"][field].as_str()
            && matches!(kind, "error" | "failed" | "runner-error")
        {
            return Some(format!("Bifrost execution terminated with {kind}"));
        }
    }
    None
}

/// Every entry of every `findings` array anywhere in the raw document, in
/// document order — the same recursive sweep the former finding counter
/// performed, retained so a structural change in the report cannot silently
/// hide findings from reconciliation.
pub(crate) fn collect_bifrost_findings(value: &Value) -> Vec<&Value> {
    let mut findings = Vec::new();
    collect_bifrost_findings_into(value, &mut findings);
    findings
}

pub(crate) fn collect_bifrost_findings_into<'a>(value: &'a Value, out: &mut Vec<&'a Value>) {
    match value {
        Value::Object(map) => {
            for (key, item) in map {
                if key == "findings" {
                    out.extend(item.as_array().into_iter().flatten());
                } else {
                    collect_bifrost_findings_into(item, out);
                }
            }
        }
        Value::Array(items) => {
            for item in items {
                collect_bifrost_findings_into(item, out);
            }
        }
        _ => {}
    }
}

pub(crate) fn diagnostics(value: &Value) -> Vec<String> {
    let mut out = Vec::new();
    collect_diagnostics(value, &mut out);
    out.sort();
    out.dedup();
    out
}

pub(crate) fn collect_diagnostics(value: &Value, out: &mut Vec<String>) {
    match value {
        Value::Object(map) => {
            for (key, item) in map {
                if key == "message" && item.is_string() {
                    out.push(item.as_str().unwrap().to_string());
                } else {
                    collect_diagnostics(item, out);
                }
            }
        }
        Value::Array(items) => {
            for item in items {
                collect_diagnostics(item, out);
            }
        }
        _ => {}
    }
}

/// Run one *scored* modeling cell through Bifrost's policy CLI, under the
/// language's modeling policy rather than its kernel policy.
pub(crate) fn run_bifrost_modeling_case(
    binary: &Path,
    case_path: &Path,
    case: &Value,
    plan: &ModelingRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    if raw_path.exists() {
        fs::remove_file(&raw_path).with_context(|| format!("clear {}", raw_path.display()))?;
    }
    clear_stale_case_timing(&plan.raw_dir, id)?;
    let policy = plan
        .language
        .artifact(ModelingTool::Bifrost)
        .expect("every wave-M1 language has a Bifrost modeling policy");
    let scratch = modeling_case_scratch(ModelingTool::Bifrost, plan.language, id)?;
    materialize_modeling_workspace(case_path, case, &scratch)?;
    fs::copy(policy, scratch.join("policy.rqlp"))?;

    let mut command = Command::new(binary);
    command
        .arg("--root")
        .arg(&scratch)
        .arg("--policy-file")
        .arg("policy.rqlp")
        .args([
            "--evaluation-date",
            "2026-08-11",
            "--format",
            "json",
            "--fail-on",
            "never",
            "--output",
        ])
        .arg(&raw_path)
        .stdin(std::process::Stdio::null());
    let invoked = Instant::now();
    let output = match command.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run {}: {error}", binary.display());
            write_bifrost_error(&raw_path, id, None, "spawn", "", &diagnostic)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    write_case_phase_timings(
        &plan.raw_dir,
        "bifrost",
        id,
        &[("total", invoked.elapsed())],
    )?;
    let status_code = output.status.code();
    let normalized = if !raw_path.is_file() {
        let diagnostic = format!(
            "Bifrost modeling policy execution produced no JSON report (status {})",
            output.status
        );
        write_bifrost_error(
            &raw_path,
            id,
            status_code,
            "evaluate",
            String::from_utf8_lossy(&output.stdout).trim(),
            &format!(
                "{diagnostic}\n{}",
                String::from_utf8_lossy(&output.stderr).trim()
            ),
        )?;
        ("runner-error", vec![diagnostic], raw_path.clone())
    } else {
        let raw = fs::read_to_string(&raw_path)
            .with_context(|| format!("read {}", raw_path.display()))?;
        match serde_json::from_str::<Value>(&raw) {
            Ok(mut report) => {
                if status_code.is_none() || status_code.is_some_and(|code| !matches!(code, 0..=2)) {
                    report["_dataflowbench_runner"] =
                        json!({"outcome": "runner-error", "exit_status": status_code});
                    fs::write(&raw_path, serde_json::to_string_pretty(&report)? + "\n")?;
                }
                let (outcome, diagnostics, _) = normalize_bifrost(
                    case_path,
                    case,
                    &report,
                    status_code,
                    modeling_anchor_dialect(plan.language)?,
                )?;
                (outcome, diagnostics, raw_path.clone())
            }
            Err(error) => (
                "runner-error",
                vec![format!(
                    "parse Bifrost JSON report {}: {error}",
                    raw_path.display()
                )],
                raw_path.clone(),
            ),
        }
    };
    fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    Ok(normalized)
}

/// Bifrost: the committed kernel policy for the language, copied into the
/// workspace as `policy.rqlp` exactly as the cold runner does, and the same
/// policy-CLI flags.
pub(crate) fn overhead_run_bifrost(
    binary: &Path,
    language: OverheadLanguage,
    run: usize,
) -> Result<OverheadRun> {
    let policy = match language {
        // The Python kernel resolves its policy per case from the frozen
        // `tool_model_references`; every one of its core cases names this
        // file, which is what the cold Python run evaluates.
        OverheadLanguage::Python => "adapters/bifrost/policies/core-python-kernel.rqlp",
        OverheadLanguage::Java => BIFROST_JAVA_POLICY,
        other => bail!("no Bifrost overhead arm for {}", other.as_str()),
    };
    let (scratch, workspace) = overhead_workspace(OverheadTool::Bifrost, language, run)?;
    fs::copy(policy, workspace.join("policy.rqlp"))?;
    let report = scratch.join("report.json");

    let mut command = Command::new(binary);
    command
        .arg("--root")
        .arg(&workspace)
        .arg("--policy-file")
        .arg("policy.rqlp")
        .args([
            "--evaluation-date",
            "2026-08-11",
            "--format",
            "json",
            "--fail-on",
            "never",
            "--output",
        ])
        .arg(&report);
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Bifrost policy CLI with {}", binary.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !report.is_file() {
        bail!(
            "the Bifrost overhead invocation produced no JSON report (status {}):\n{}",
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
