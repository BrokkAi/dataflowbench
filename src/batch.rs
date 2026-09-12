//! Resumable multi-kernel execution for one analyzer.
//!
//! The manifest is execution evidence: it says which benchmark, binary,
//! configurations, and environment produced each completed normalized report.
//! It is not a freeze or publication artifact. Completed reports remain
//! individually validated and atomically published by their ordinary adapters;
//! the manifest only records when it is safe to reuse them.
//!
//! The implementation currently supports Bifrost because it is the only
//! analyzer with a single `Result`-returning adapter command spanning all 13
//! language kernels. The executor is injected, so future analyzers can join
//! without changing the resume contract.

use crate::adapters::bifrost::BifrostRun;
use crate::adapters::{ModelingTool, ToolIdentity, witness_tool_identity};
use crate::batch::SliceState::{Completed, Incomplete, Pending};
use crate::cases::fixture_revision;
use crate::report::{current_configuration_paths, hash_paths, validate_reports_in};
use crate::runtime::now_seconds;
use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    process::Command,
};

pub(crate) const MANIFEST_SCHEMA_VERSION: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, clap::ValueEnum)]
pub(crate) enum BatchAnalyzer {
    Bifrost,
}

impl BatchAnalyzer {
    pub(crate) fn key(self) -> &'static str {
        match self {
            Self::Bifrost => "bifrost",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, clap::ValueEnum)]
pub(crate) enum BatchKernel {
    Java,
    Javascript,
    Python,
    Kotlin,
    Scala,
    Typescript,
    Csharp,
    Go,
    C,
    Cpp,
    Rust,
    Ruby,
    Php,
}

impl BatchKernel {
    pub(crate) const ALL: [Self; 13] = [
        Self::Java,
        Self::Javascript,
        Self::Python,
        Self::Kotlin,
        Self::Scala,
        Self::Typescript,
        Self::Csharp,
        Self::Go,
        Self::C,
        Self::Cpp,
        Self::Rust,
        Self::Ruby,
        Self::Php,
    ];

    fn key(self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::Javascript => "javascript",
            Self::Python => "python",
            Self::Kotlin => "kotlin",
            Self::Scala => "scala",
            Self::Typescript => "typescript",
            Self::Csharp => "csharp",
            Self::Go => "go",
            Self::C => "c",
            Self::Cpp => "cpp",
            Self::Rust => "rust",
            Self::Ruby => "ruby",
            Self::Php => "php",
        }
    }

    fn bifrost_run(self) -> BifrostRun {
        match self {
            Self::Java => BifrostRun::JavaKernel,
            Self::Javascript => BifrostRun::JavascriptKernel,
            Self::Python => BifrostRun::PythonKernel,
            Self::Kotlin => BifrostRun::KotlinKernel,
            Self::Scala => BifrostRun::ScalaKernel,
            Self::Typescript => BifrostRun::TypescriptKernel,
            Self::Csharp => BifrostRun::CsharpKernel,
            Self::Go => BifrostRun::GoKernel,
            Self::C => BifrostRun::CKernel,
            Self::Cpp => BifrostRun::CppKernel,
            Self::Rust => BifrostRun::RustKernel,
            Self::Ruby => BifrostRun::RubyKernel,
            Self::Php => BifrostRun::PhpKernel,
        }
    }

    fn report_path(self, analyzer: BatchAnalyzer) -> PathBuf {
        PathBuf::from(format!(
            "reports/{}-{}-kernel.json",
            analyzer.key(),
            self.key()
        ))
    }

    fn population_stem(self, analyzer: BatchAnalyzer) -> String {
        format!("{}-{}-kernel", analyzer.key(), self.key())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum BatchState {
    Requested,
    Running,
    Complete,
    Failed,
    Validated,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum SliceState {
    Pending,
    Running,
    Completed,
    Incomplete,
    Failed,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct BinaryIdentity {
    path: String,
    sha256: String,
    version: String,
    build_identity: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct BenchmarkIdentity {
    revision: String,
    dirty: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct EnvironmentIdentity {
    family: String,
    os: String,
    arch: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct SliceRecord {
    pub(crate) state: SliceState,
    pub(crate) report: String,
    pub(crate) raw_dir: String,
    pub(crate) attempts: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    failure: Option<FailureRecord>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub(crate) outcomes: Option<BTreeMap<String, usize>>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct FailureRecord {
    kind: String,
    diagnostic: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct ValidationRecord {
    pub(crate) state: String,
    diagnostic: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct BatchManifest {
    pub(crate) schema_version: u32,
    analyzer: String,
    command_line: Vec<String>,
    created_at_unix_seconds: u64,
    updated_at_unix_seconds: u64,
    benchmark: BenchmarkIdentity,
    analyzer_identity: BinaryIdentity,
    environment: EnvironmentIdentity,
    adapter_version: String,
    fixture_revision: String,
    configuration_hashes: BTreeMap<String, String>,
    requested_kernels: Vec<String>,
    pub(crate) state: BatchState,
    pub(crate) kernels: BTreeMap<String, SliceRecord>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub(crate) validation: Option<ValidationRecord>,
}

#[derive(Clone)]
struct RunIdentity {
    benchmark: BenchmarkIdentity,
    analyzer_identity: BinaryIdentity,
    fixture_revision: String,
    configuration_hashes: BTreeMap<String, String>,
}

fn digest_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn git_output<const N: usize>(root: &Path, args: [&str; N]) -> Result<String> {
    let output = Command::new("git").args(args).current_dir(root).output()?;
    if !output.status.success() {
        bail!(
            "git {} failed: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        );
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn benchmark_identity(root: &Path) -> Result<BenchmarkIdentity> {
    let revision = git_output(root, ["rev-parse", "HEAD"])?;
    let output = Command::new("git")
        .args([
            "status",
            "--porcelain",
            "--untracked-files=no",
            "--",
            ".",
            ":(exclude)reports",
        ])
        .current_dir(root)
        .output()?;
    if !output.status.success() {
        bail!(
            "git status failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        );
    }
    let status = String::from_utf8_lossy(&output.stdout);
    Ok(BenchmarkIdentity {
        revision,
        dirty: !status.is_empty(),
    })
}

fn binary_digest(binary: &Path) -> Result<String> {
    Ok(digest_bytes(&fs::read(binary).with_context(|| {
        format!("read analyzer binary {}", binary.display())
    })?))
}

fn witness_binary_identity(analyzer: BatchAnalyzer, binary: &Path) -> Result<BinaryIdentity> {
    let identity: ToolIdentity = match analyzer {
        BatchAnalyzer::Bifrost => {
            witness_tool_identity(ModelingTool::Bifrost, binary)?.version_line_only()
        }
    };
    Ok(BinaryIdentity {
        path: binary.to_string_lossy().into_owned(),
        sha256: binary_digest(binary)?,
        version: identity.version,
        build_identity: identity.build_identity,
    })
}

fn environment_identity() -> EnvironmentIdentity {
    EnvironmentIdentity {
        family: std::env::consts::FAMILY.to_string(),
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
    }
}

fn configuration_hashes(
    analyzer: BatchAnalyzer,
    kernels: &[BatchKernel],
) -> Result<BTreeMap<String, String>> {
    let mut hashes = BTreeMap::new();
    let mut case_scan = None;
    for kernel in kernels {
        let paths = current_configuration_paths(&kernel.population_stem(analyzer), &mut case_scan)?
            .with_context(|| {
                format!(
                    "derive configuration identity for {} {}",
                    analyzer.key(),
                    kernel.key()
                )
            })?;
        hashes.insert(kernel.key().to_string(), hash_paths(&paths)?);
    }
    Ok(hashes)
}

fn measure_identity(
    root: &Path,
    analyzer: BatchAnalyzer,
    binary: &Path,
    kernels: &[BatchKernel],
) -> Result<RunIdentity> {
    let binary = if binary.is_absolute() {
        binary.to_path_buf()
    } else {
        root.join(binary)
    };
    Ok(RunIdentity {
        benchmark: benchmark_identity(root)?,
        analyzer_identity: witness_binary_identity(analyzer, &binary)?,
        fixture_revision: fixture_revision()?,
        configuration_hashes: configuration_hashes(analyzer, kernels)?,
    })
}

fn slice_record(kernel: BatchKernel, analyzer: BatchAnalyzer) -> SliceRecord {
    SliceRecord {
        state: Pending,
        report: kernel.report_path(analyzer).to_string_lossy().into_owned(),
        raw_dir: format!("reports/raw/{}-{}-kernel", analyzer.key(), kernel.key()),
        attempts: 0,
        failure: None,
        outcomes: None,
    }
}

fn new_manifest(
    analyzer: BatchAnalyzer,
    kernels: &[BatchKernel],
    identity: RunIdentity,
) -> Result<BatchManifest> {
    let now = now_seconds()?;
    let mut records = BTreeMap::new();
    let mut requested = Vec::new();
    for kernel in kernels {
        records.insert(kernel.key().to_string(), slice_record(*kernel, analyzer));
        requested.push(kernel.key().to_string());
    }
    Ok(BatchManifest {
        schema_version: MANIFEST_SCHEMA_VERSION,
        analyzer: analyzer.key().to_string(),
        command_line: std::env::args().collect(),
        created_at_unix_seconds: now,
        updated_at_unix_seconds: now,
        benchmark: identity.benchmark,
        analyzer_identity: identity.analyzer_identity,
        environment: environment_identity(),
        adapter_version: env!("CARGO_PKG_VERSION").to_string(),
        fixture_revision: identity.fixture_revision,
        configuration_hashes: identity.configuration_hashes,
        requested_kernels: requested,
        state: BatchState::Requested,
        kernels: records,
        validation: None,
    })
}

fn write_manifest_atomic(root: &Path, path: &Path, manifest: &BatchManifest) -> Result<()> {
    let destination = root.join(path);
    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent)?;
    }
    let staged = destination.with_extension("json.tmp");
    fs::write(&staged, serde_json::to_string_pretty(manifest)? + "\n")?;
    fs::rename(&staged, &destination)
        .with_context(|| format!("publish manifest {}", destination.display()))?;
    Ok(())
}

fn load_manifest(root: &Path, path: &Path) -> Result<BatchManifest> {
    let bytes = fs::read(root.join(path))
        .with_context(|| format!("read batch manifest {}", root.join(path).display()))?;
    serde_json::from_slice(&bytes)
        .with_context(|| format!("parse batch manifest {}", root.join(path).display()))
}

fn identity_mismatch(manifest: &BatchManifest, current: &RunIdentity) -> Vec<String> {
    let mut differences = Vec::new();
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION {
        differences.push(format!(
            "manifest schema {:?} is not supported (expected {MANIFEST_SCHEMA_VERSION})",
            manifest.schema_version
        ));
    }
    if manifest.benchmark != current.benchmark {
        differences.push("benchmark revision or dirty state changed".to_string());
    }
    if manifest.analyzer_identity.sha256 != current.analyzer_identity.sha256 {
        differences.push("analyzer binary digest changed".to_string());
    }
    if manifest.analyzer_identity.version != current.analyzer_identity.version
        || manifest.analyzer_identity.build_identity != current.analyzer_identity.build_identity
    {
        differences.push("witnessed analyzer identity changed".to_string());
    }
    if manifest.fixture_revision != current.fixture_revision {
        differences.push("fixture/configuration revision changed".to_string());
    }
    if manifest.configuration_hashes != current.configuration_hashes {
        differences.push("adapter configuration hashes changed".to_string());
    }
    if manifest.environment != environment_identity() {
        differences.push("execution environment changed".to_string());
    }
    differences
}

fn read_report(root: &Path, relative: &str) -> Result<serde_json::Value> {
    let bytes = fs::read(root.join(relative))
        .with_context(|| format!("read completed report {relative}"))?;
    serde_json::from_slice(&bytes).with_context(|| format!("parse completed report {relative}"))
}

fn outcome_counts(report: &serde_json::Value) -> BTreeMap<String, usize> {
    let mut counts = BTreeMap::new();
    for outcome in report["results"].as_array().into_iter().flatten() {
        *counts
            .entry(outcome["outcome"].as_str().unwrap_or("missing").to_string())
            .or_default() += 1;
    }
    counts
}

fn verify_completed_report(
    root: &Path,
    manifest: &BatchManifest,
    key: &str,
    record: &SliceRecord,
) -> Result<BTreeMap<String, usize>> {
    let report = read_report(root, &record.report)?;
    if report["tool"].as_str() != Some(manifest.analyzer.as_str()) {
        bail!("{} records the wrong tool", record.report);
    }
    if report["tool_version"].as_str() != Some(manifest.analyzer_identity.version.as_str())
        || report["tool_build_identity"].as_str()
            != Some(manifest.analyzer_identity.build_identity.as_str())
        || report["adapter_version"].as_str() != Some(manifest.adapter_version.as_str())
        || report["fixture_revision"].as_str() != Some(manifest.fixture_revision.as_str())
    {
        bail!("{} does not match the manifest identity", record.report);
    }
    let stamped = report["configuration_hash"]
        .as_str()
        .with_context(|| format!("{} lacks configuration_hash", record.report))?;
    let expected = manifest
        .configuration_hashes
        .get(key)
        .with_context(|| format!("manifest lacks a configuration hash for {key}"))?;
    if stamped != expected {
        bail!(
            "{} configuration hash does not match the manifest",
            record.report
        );
    }
    validate_reports_in(root, Some(&PathBuf::from(&record.report)))?;
    Ok(outcome_counts(&report))
}

fn set_overall_state(manifest: &mut BatchManifest, state: BatchState) -> Result<()> {
    manifest.state = state;
    manifest.updated_at_unix_seconds = now_seconds()?;
    Ok(())
}

fn summarize(manifest: &BatchManifest) {
    let counts = manifest.kernels.values().fold(
        BTreeMap::new(),
        |mut counts: BTreeMap<String, usize>, record| {
            let state = serde_json::to_value(record.state)
                .ok()
                .and_then(|value| value.as_str().map(str::to_string))
                .unwrap_or_else(|| "unknown".to_string());
            *counts.entry(state).or_default() += 1;
            counts
        },
    );
    let overall = serde_json::to_value(manifest.state)
        .ok()
        .and_then(|value| value.as_str().map(str::to_string))
        .unwrap_or_else(|| "unknown".to_string());
    println!(
        "batch state={overall} {}",
        counts
            .iter()
            .map(|(state, count)| format!("{state}={count}"))
            .collect::<Vec<_>>()
            .join(" ")
    );
    for (key, record) in &manifest.kernels {
        println!(
            "kernel {key} state={:?} report={}",
            record.state, record.report
        );
    }
}

pub(crate) fn run_batch<R>(
    root: &Path,
    analyzer: BatchAnalyzer,
    binary: &Path,
    requested: &[BatchKernel],
    manifest_path: &Path,
    runner: R,
) -> Result<BatchManifest>
where
    R: Fn(&Path, BatchKernel) -> Result<()>,
{
    if requested.is_empty() {
        bail!("select at least one language kernel");
    }
    if requested.iter().collect::<BTreeSet<_>>().len() != requested.len() {
        bail!("language kernels must be unique");
    }
    let current = measure_identity(root, analyzer, binary, requested)?;
    let (mut manifest, created) = if root.join(manifest_path).exists() {
        (load_manifest(root, manifest_path)?, false)
    } else {
        (new_manifest(analyzer, requested, current.clone())?, true)
    };
    if manifest.analyzer != analyzer.key() {
        bail!(
            "manifest belongs to analyzer {:?}, not {:?}; create a new manifest",
            manifest.analyzer,
            analyzer.key()
        );
    }
    let requested_keys: BTreeSet<_> = requested.iter().map(|kernel| kernel.key()).collect();
    let manifest_keys: BTreeSet<_> = manifest
        .requested_kernels
        .iter()
        .map(String::as_str)
        .collect();
    if manifest_keys != requested_keys {
        bail!(
            "requested language set differs from the manifest; create a new manifest for a different population"
        );
    }
    let differences = identity_mismatch(&manifest, &current);
    if !differences.is_empty() {
        bail!(
            "batch manifest is stale; create a new manifest: {}",
            differences.join("; ")
        );
    }
    if created {
        write_manifest_atomic(root, manifest_path, &manifest)?;
    }

    set_overall_state(&mut manifest, BatchState::Running)?;
    write_manifest_atomic(root, manifest_path, &manifest)?;
    let mut ran_any = false;
    for (key, record) in manifest.kernels.clone() {
        let kernel = BatchKernel::ALL
            .into_iter()
            .find(|kernel| kernel.key() == key)
            .with_context(|| format!("manifest names unknown kernel {key}"))?;
        let mut record = record;
        match record.state {
            Completed => {}
            Pending | SliceState::Running => {
                // A report can already be published if the previous process was
                // interrupted after atomic report publication but before the
                // manifest was updated. Reuse only a report that still
                // validates against the pinned identity.
                match verify_completed_report(root, &manifest, &key, &record) {
                    Ok(outcomes) => {
                        record.state = Completed;
                        record.outcomes = Some(outcomes);
                        record.failure = None;
                        manifest.kernels.insert(key.clone(), record.clone());
                    }
                    Err(_) => {
                        record.state = SliceState::Running;
                        record.attempts += 1;
                        manifest.kernels.insert(key.clone(), record.clone());
                        write_manifest_atomic(root, manifest_path, &manifest)?;
                        ran_any = true;
                        match runner(binary, kernel) {
                            Ok(()) => {
                                let outcomes =
                                    verify_completed_report(root, &manifest, &key, &record)?;
                                record.state = Completed;
                                record.outcomes = Some(outcomes);
                                record.failure = None;
                                manifest.kernels.insert(key, record);
                            }
                            Err(error) => {
                                record.state = SliceState::Failed;
                                record.failure = Some(FailureRecord {
                                    kind: "execution".to_string(),
                                    diagnostic: format!("{error:#}"),
                                });
                                manifest.kernels.insert(key, record);
                            }
                        }
                        write_manifest_atomic(root, manifest_path, &manifest)?;
                    }
                }
            }
            Incomplete | SliceState::Failed => {
                record.attempts += 1;
                record.state = SliceState::Running;
                manifest.kernels.insert(key.clone(), record.clone());
                write_manifest_atomic(root, manifest_path, &manifest)?;
                ran_any = true;
                match runner(binary, kernel) {
                    Ok(()) => {
                        let outcomes = verify_completed_report(root, &manifest, &key, &record)?;
                        record.state = Completed;
                        record.outcomes = Some(outcomes);
                        record.failure = None;
                        manifest.kernels.insert(key, record);
                    }
                    Err(error) => {
                        record.state = SliceState::Failed;
                        record.failure = Some(FailureRecord {
                            kind: "execution".to_string(),
                            diagnostic: format!("{error:#}"),
                        });
                        manifest.kernels.insert(key, record);
                    }
                }
                write_manifest_atomic(root, manifest_path, &manifest)?;
            }
        }
    }

    let all_completed = manifest
        .kernels
        .values()
        .all(|record| record.state == Completed);
    if all_completed {
        match validate_reports_in(root, None) {
            Ok(()) => {
                manifest.validation = Some(ValidationRecord {
                    state: "passed".to_string(),
                    diagnostic: None,
                });
                set_overall_state(&mut manifest, BatchState::Validated)?;
            }
            Err(error) => {
                manifest.validation = Some(ValidationRecord {
                    state: "failed".to_string(),
                    diagnostic: Some(format!("{error:#}")),
                });
                set_overall_state(&mut manifest, BatchState::Failed)?;
            }
        }
    } else {
        manifest.validation = None;
        let state = if ran_any {
            BatchState::Failed
        } else {
            BatchState::Running
        };
        set_overall_state(&mut manifest, state)?;
    }
    write_manifest_atomic(root, manifest_path, &manifest)?;
    summarize(&manifest);
    Ok(manifest)
}

pub(crate) fn run_batch_cli(
    root: &Path,
    analyzer: BatchAnalyzer,
    binary: &Path,
    requested: &[BatchKernel],
    manifest_path: &Path,
) -> Result<BatchManifest> {
    run_batch(
        root,
        analyzer,
        binary,
        requested,
        manifest_path,
        |binary, kernel| crate::adapters::bifrost::run_bifrost(binary, kernel.bifrost_run()),
    )
}
