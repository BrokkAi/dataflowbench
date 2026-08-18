use anyhow::{Context, Result, bail};
use clap::{Parser, Subcommand};
use jsonschema::JSONSchema;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::{Instant, SystemTime, UNIX_EPOCH},
};
use walkdir::WalkDir;

const ADAPTER_VERSION: &str = env!("CARGO_PKG_VERSION");
type CorePairKey<'a> = (&'a str, &'a str, &'a str, &'a str);
type CorePairCases<'a> = Vec<(&'a Path, &'a str)>;

const CODEQL_JAVASCRIPT_QUERY: &str = "adapters/codeql/javascript/queries/JavaScriptKernel.ql";
const CODEQL_JAVASCRIPT_RAW_DIR: &str = "reports/raw/codeql-javascript";
const CODEQL_JAVASCRIPT_REPORT: &str = "reports/codeql-javascript-kernel.json";
const CODEQL_JAVASCRIPT_CASE_COUNT: usize = 32;
const CODEQL_JAVASCRIPT_TEMPLATE_COUNT: usize = 16;
const CODEQL_PYTHON_QUERY: &str = "adapters/codeql/python/queries/PythonKernel.ql";
const CODEQL_PYTHON_TEMPLATE_IDS: [&str; 16] = [
    "dfb-template-alias-propagation-separation",
    "dfb-template-argument-position-separation",
    "dfb-template-arithmetic-expression-propagation",
    "dfb-template-array-element-separation",
    "dfb-template-branch-join",
    "dfb-template-call-context-separation",
    "dfb-template-direct-propagation",
    "dfb-template-exception-catch",
    "dfb-template-infeasible-branch",
    "dfb-template-local-multi-step-chain",
    "dfb-template-local-overwrite-kill",
    "dfb-template-loop-carried-kill",
    "dfb-template-object-separation",
    "dfb-template-return-relay-one-hop",
    "dfb-template-return-relay-two-hop",
    "dfb-template-same-object-field-separation",
];

#[derive(Parser)]
#[command(name = "dataflowbench")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Validate,
    ValidateReports,
    /// Validate an immutable benchmark freeze and all referenced evidence.
    ValidateFreeze {
        /// Freeze manifest, relative to the repository root.
        #[arg(default_value = "reports/freeze.json")]
        manifest: PathBuf,
    },
    /// Assemble a freeze/v1 manifest from committed normalized reports.
    CreateFreeze {
        /// Normalized report paths, repository-relative. Repeatable.
        #[arg(long = "report", required = true)]
        reports: Vec<PathBuf>,
        /// Claim scope: development, release, or website.
        #[arg(long, default_value = "development")]
        scope: String,
        /// Release name; release and website scopes require a v-prefixed tag.
        #[arg(long, default_value = "development")]
        release: String,
        /// Frozen evidence revision; defaults to the checkout HEAD.
        #[arg(long)]
        revision: Option<String>,
        /// Manifest destination, relative to the repository root.
        #[arg(long, default_value = "reports/freeze.json")]
        output: PathBuf,
    },
    /// Generate audited result artifacts from a validated freeze manifest.
    GenerateResults {
        /// Freeze manifest, relative to the repository root.
        #[arg(long, default_value = "reports/freeze.json")]
        manifest: PathBuf,
        /// Directory that receives (or holds) the generated artifacts.
        #[arg(long)]
        output_directory: PathBuf,
        /// Verify that checked-in artifacts are current instead of writing.
        #[arg(long)]
        check: bool,
    },
    RunBifrostSmoke {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Python propagation kernel without mixing it with the Java
    /// kernel or the cross-language direct-flow calibration cases.
    RunBifrostPythonKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    RunCodeqlJavaKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    RunCodeqlJavascriptKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Python propagation kernel through the Python CodeQL extractor.
    RunCodeqlPythonKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Commands::Validate => validate_cases(),
        Commands::ValidateReports => validate_reports(),
        Commands::ValidateFreeze { manifest } => validate_freeze(&manifest),
        Commands::CreateFreeze {
            reports,
            scope,
            release,
            revision,
            output,
        } => create_freeze(&reports, &scope, &release, revision.as_deref(), &output),
        Commands::GenerateResults {
            manifest,
            output_directory,
            check,
        } => generate_results(&manifest, &output_directory, check),
        Commands::RunBifrostSmoke { bifrost } => run_bifrost_smoke(&bifrost),
        Commands::RunBifrostPythonKernel { bifrost } => run_bifrost_python_kernel(&bifrost),
        Commands::RunCodeqlJavaKernel {
            codeql,
            codeql_packs,
        } => run_codeql_java_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlJavascriptKernel {
            codeql,
            codeql_packs,
        } => run_codeql_javascript_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlPythonKernel {
            codeql,
            codeql_packs,
        } => run_codeql_python_kernel(&codeql, codeql_packs.as_deref()),
    }
}

fn schema(path: &str) -> Result<JSONSchema> {
    let value: Value =
        serde_json::from_str(&fs::read_to_string(path).with_context(|| format!("read {path}"))?)?;
    // jsonschema 0.18 retains schema references for the compiled validator.
    // These two small, process-lifetime schemas are loaded once per command.
    JSONSchema::compile(Box::leak(Box::new(value))).context("compile schema")
}

fn case_paths() -> Vec<PathBuf> {
    let mut paths: Vec<_> = WalkDir::new("cases")
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file() && entry.file_name() == "case.json")
        .map(|entry| entry.into_path())
        .collect();
    paths.sort();
    paths
}

fn validate_value(compiled: &JSONSchema, value: &Value, path: &Path) -> Result<()> {
    if let Err(errors) = compiled.validate(value) {
        let details = errors
            .map(|error| error.to_string())
            .collect::<Vec<_>>()
            .join("; ");
        bail!("{}: {details}", path.display());
    }
    Ok(())
}

fn validate_cases() -> Result<()> {
    let compiled = schema("schemas/case.schema.json")?;
    let paths = case_paths();
    if paths.is_empty() {
        bail!("no case.json files found beneath cases/");
    }
    let mut cases = Vec::new();
    for path in &paths {
        let value: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        validate_value(&compiled, &value, path)?;
        validate_case_contract(path, &value)?;
        validate_markers(path, &value)?;
        validate_fixture_files(path, &value)?;
        cases.push((path.clone(), value));
    }
    validate_balanced_core_pairs(&cases)?;
    validate_javascript_kernel_balance(&cases)?;
    println!("validated {} cases", paths.len());
    Ok(())
}

fn validate_case_contract(path: &Path, value: &Value) -> Result<()> {
    let expected_flows = value["expected_flows"]
        .as_array()
        .expect("schema validated");
    let expected_nonflows = value["expected_nonflows"]
        .as_array()
        .expect("schema validated");
    match value["polarity"].as_str().expect("schema validated") {
        "positive" if expected_flows.is_empty() || !expected_nonflows.is_empty() => bail!(
            "{}: positive cases require expected_flows and forbid expected_nonflows",
            path.display()
        ),
        "negative" if !expected_flows.is_empty() || expected_nonflows.is_empty() => bail!(
            "{}: negative cases require expected_nonflows and forbid expected_flows",
            path.display()
        ),
        _ => Ok(()),
    }
}

fn validate_balanced_core_pairs(cases: &[(PathBuf, Value)]) -> Result<()> {
    let mut pairs: BTreeMap<CorePairKey<'_>, CorePairCases<'_>> = BTreeMap::new();
    for (path, case) in cases {
        if case["score_tier"] != "core" {
            continue;
        }
        let key = (
            case["track"].as_str().expect("schema validated"),
            case["language"].as_str().expect("schema validated"),
            case["template_id"].as_str().expect("schema validated"),
            case["model_profile"].as_str().expect("schema validated"),
        );
        pairs
            .entry(key)
            .or_default()
            .push((path, case["polarity"].as_str().expect("schema validated")));
    }
    for ((track, language, template, model_profile), cases) in pairs {
        let positives = cases
            .iter()
            .filter(|(_, polarity)| *polarity == "positive")
            .count();
        let negatives = cases.len() - positives;
        if positives != 1 || negatives != 1 {
            bail!(
                "core pair {track}/{language}/{template}/{model_profile} requires exactly one positive and one negative; found {positives} positive and {negatives} negative"
            );
        }
    }
    Ok(())
}

fn validate_javascript_kernel_balance(cases: &[(PathBuf, Value)]) -> Result<()> {
    let java_templates = core_templates_for_language(cases, "java");
    let javascript_templates = core_templates_for_language(cases, "javascript");

    if javascript_templates.is_empty() {
        return Ok(());
    }
    if java_templates.len() != 16 {
        bail!(
            "Java propagation kernel must define exactly 16 core templates; found {}",
            java_templates.len()
        );
    }
    if javascript_templates.len() != 16 {
        bail!(
            "JavaScript propagation kernel must define exactly 16 core templates; found {}",
            javascript_templates.len()
        );
    }
    if javascript_templates != java_templates {
        let missing = java_templates
            .difference(&javascript_templates)
            .cloned()
            .collect::<Vec<_>>();
        let unexpected = javascript_templates
            .difference(&java_templates)
            .cloned()
            .collect::<Vec<_>>();
        bail!(
            "JavaScript propagation kernel must preserve the Java template IDs; missing {missing:?}, unexpected {unexpected:?}"
        );
    }
    Ok(())
}

fn core_templates_for_language<'a>(
    cases: &'a [(PathBuf, Value)],
    language: &str,
) -> BTreeSet<&'a str> {
    cases
        .iter()
        .filter(|(_, case)| {
            case["score_tier"] == "core"
                && case["track"] == "taint"
                && case["language"].as_str() == Some(language)
        })
        .filter_map(|(_, case)| case["template_id"].as_str())
        .collect()
}

fn validate_fixture_files(path: &Path, value: &Value) -> Result<()> {
    let parent = path.parent().expect("case path has parent");
    for fixture in value["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        if !parent.join(fixture).is_file() {
            bail!("{}: fixture {fixture:?} does not exist", path.display());
        }
    }
    Ok(())
}

fn validate_markers(path: &Path, value: &Value) -> Result<()> {
    let parent = path.parent().expect("case path has parent");
    let fixtures = value["fixture_files"].as_array().expect("schema validated");
    for field in ["source_anchors", "sink_anchors"] {
        for anchor in value[field].as_array().expect("schema validated") {
            let file = anchor["file"].as_str().expect("schema validated");
            let marker = anchor["marker"].as_str().expect("schema validated");
            if !fixtures
                .iter()
                .any(|fixture| fixture.as_str() == Some(file))
            {
                bail!(
                    "{}: anchor file {file:?} is not listed in fixture_files",
                    path.display()
                );
            }
            let body = fs::read_to_string(parent.join(file))
                .with_context(|| format!("read fixture {file}"))?;
            if !body.contains(marker) {
                bail!(
                    "{}: marker {marker:?} is absent from {file}",
                    path.display()
                );
            }
            if let Some(line_hint) = anchor["line_hint"].as_u64() {
                let hinted_line = body.lines().nth(line_hint as usize - 1);
                if !hinted_line.is_some_and(|line| line.contains(marker)) {
                    bail!(
                        "{}: marker {marker:?} is not on hinted line {line_hint} in {file}",
                        path.display()
                    );
                }
            }
        }
    }
    for checkpoint in value["witness_checkpoints"]
        .as_array()
        .into_iter()
        .flatten()
    {
        let checkpoint = checkpoint.as_str().expect("schema validated");
        let mut occurrences = 0;
        for fixture in fixtures {
            let fixture = fixture.as_str().expect("schema validated");
            let body = fs::read_to_string(parent.join(fixture))
                .with_context(|| format!("read fixture {fixture}"))?;
            occurrences += body.matches(checkpoint).count();
        }
        if occurrences != 1 {
            bail!(
                "{}: witness checkpoint {checkpoint:?} must occur exactly once across fixture_files; found {occurrences}",
                path.display()
            );
        }
    }
    Ok(())
}

fn validate_reports() -> Result<()> {
    let compiled = schema("schemas/result.schema.json")?;
    let mut paths: Vec<_> = fs::read_dir("reports")
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file() && path.extension().is_some_and(|ext| ext == "json"))
        .collect();
    paths.sort();
    let mut validated = 0usize;
    for path in &paths {
        let report: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        // Freeze manifests live beside normalized reports but follow their
        // own contract; validate-freeze owns them.
        if report.get("benchmark").is_some() && report.get("claim").is_some() {
            continue;
        }
        validated += 1;
        validate_value(&compiled, &report, path)?;
        for result in report["results"].as_array().expect("schema validated") {
            let raw = result["raw_output"].as_str().expect("schema validated");
            if !Path::new(raw).is_file() {
                bail!("{}: retained raw output {raw:?} is absent", path.display());
            }
        }
    }
    println!("validated {validated} reports");
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum BifrostRun {
    Smoke,
    PythonKernel,
}
fn validate_freeze(manifest: &Path) -> Result<()> {
    let root = repository_root()?;
    let manifest = if manifest.is_absolute() {
        manifest.to_path_buf()
    } else {
        root.join(manifest)
    };
    validate_freeze_at(&root, &manifest, true)?;
    println!("validated immutable freeze {}", manifest.display());
    Ok(())
}

/// Validate a freeze against a repository checkout. The `check_git` switch is
/// intentionally only used by unit tests that construct an isolated fixture;
/// the CLI always checks the checkout's exact HEAD and clean worktree.
fn validate_freeze_at(root: &Path, manifest_path: &Path, check_git: bool) -> Result<()> {
    let freeze_schema = compile_schema(&root.join("schemas/freeze.schema.json"))?;
    let manifest_bytes = fs::read(manifest_path)
        .with_context(|| format!("read freeze manifest {}", manifest_path.display()))?;
    let manifest: Value = serde_json::from_slice(&manifest_bytes)
        .with_context(|| format!("parse freeze manifest {}", manifest_path.display()))?;
    validate_value(&freeze_schema, &manifest, manifest_path)?;

    let benchmark = &manifest["benchmark"];
    let revision = required_string(benchmark, "revision", "benchmark")?;
    let release = required_string(benchmark, "release", "benchmark")?;
    let claim = &manifest["claim"];
    let claim_scope = required_string(claim, "scope", "claim")?;
    if check_git {
        validate_freeze_git_state(root, revision, release, claim_scope)?;
    }

    let case_schema = compile_schema(&root.join("schemas/case.schema.json"))?;
    let result_schema = compile_schema(&root.join("schemas/result.schema.json"))?;
    let case_schema_version = benchmark["case_schema_version"]
        .as_u64()
        .expect("freeze schema validated");
    let result_schema_version = benchmark["result_schema_version"]
        .as_u64()
        .expect("freeze schema validated");
    let mut cases = BTreeMap::new();
    let mut case_paths = Vec::new();
    let mut actual_tracks = BTreeSet::new();
    let mut actual_tiers = BTreeSet::new();
    let mut actual_profiles = BTreeSet::new();

    for selected in manifest["cases"]
        .as_array()
        .expect("freeze schema validated")
    {
        let id = required_string(selected, "id", "selected case")?;
        let relative_path = required_string(selected, "path", id)?;
        let path = repository_path(root, relative_path)?;
        if cases.insert(id.to_string(), path.clone()).is_some() {
            bail!("freeze selects case {id} more than once");
        }
        if case_paths.iter().any(|(name, _)| name == relative_path) {
            bail!("freeze selects path {relative_path:?} more than once");
        }
        let bytes = fs::read(&path).with_context(|| format!("read case {}", path.display()))?;
        require_digest(
            selected["sha256"]
                .as_str()
                .expect("freeze schema validated"),
            &bytes,
            &format!("case {id}"),
        )?;
        let case: Value = serde_json::from_slice(&bytes)
            .with_context(|| format!("parse selected case {}", path.display()))?;
        validate_value(&case_schema, &case, &path)?;
        if case["schema_version"] != case_schema_version {
            bail!(
                "case {id} uses schema {}, expected {}",
                case["schema_version"],
                case_schema_version
            );
        }
        if case["id"].as_str() != Some(id) {
            bail!("selected case {id} does not match its case file ID");
        }
        for field in [
            "track",
            "score_tier",
            "model_profile",
            "template_id",
            "polarity",
        ] {
            if selected[field] != case[field] {
                bail!("selected case {id} has stale {field} metadata");
            }
        }
        validate_fixture_digests(root, relative_path, selected, &case)?;
        actual_tracks.insert(
            case["track"]
                .as_str()
                .expect("case schema validated")
                .to_string(),
        );
        actual_tiers.insert(
            case["score_tier"]
                .as_str()
                .expect("case schema validated")
                .to_string(),
        );
        actual_profiles.insert(
            case["model_profile"]
                .as_str()
                .expect("case schema validated")
                .to_string(),
        );
        case_paths.push((relative_path.to_string(), path));
    }
    if cases.is_empty() {
        bail!("freeze must select at least one case");
    }
    let computed_fixture_revision = fixture_revision_for_manifest_cases(root, &case_paths)?;
    if benchmark["fixture_revision"].as_str() != Some(computed_fixture_revision.as_str()) {
        bail!("freeze fixture revision does not match selected case and fixture bytes");
    }
    require_set_matches(&claim["tracks"], &actual_tracks, "claim tracks")?;
    require_set_matches(&claim["score_tiers"], &actual_tiers, "claim score tiers")?;
    require_set_matches(
        &claim["model_profiles"],
        &actual_profiles,
        "claim model profiles",
    )?;
    validate_exclusions(claim, &cases)?;

    let actual_dimensions = manifest["reports"]
        .as_array()
        .expect("freeze schema validated")
        .iter()
        .map(|report| required_string(report, "dimension", "frozen report").map(str::to_string))
        .collect::<Result<BTreeSet<_>>>()?;
    require_set_matches(&claim["dimensions"], &actual_dimensions, "claim dimensions")?;

    let mut adapters = BTreeMap::new();
    for adapter in manifest["adapters"]
        .as_array()
        .expect("freeze schema validated")
    {
        let id = required_string(adapter, "id", "adapter")?;
        if adapters.insert(id.to_string(), adapter).is_some() {
            bail!("freeze declares adapter {id} more than once");
        }
    }
    if adapters.is_empty() {
        bail!("freeze must bind at least one adapter");
    }
    validate_adapter_identities(claim_scope, &adapters)?;

    let mut report_paths = BTreeSet::new();
    let mut report_context = FreezeReportValidation {
        root,
        adapters: &adapters,
        cases: &cases,
        result_schema: &result_schema,
        result_schema_version,
        fixture_revision: benchmark["fixture_revision"]
            .as_str()
            .expect("freeze schema validated"),
        report_paths: &mut report_paths,
    };
    for frozen_report in manifest["reports"]
        .as_array()
        .expect("freeze schema validated")
    {
        validate_frozen_report(&mut report_context, frozen_report)?;
    }
    if report_paths.is_empty() {
        bail!("freeze must bind at least one normalized report");
    }
    Ok(())
}

fn compile_schema(path: &Path) -> Result<JSONSchema> {
    let value: Value = serde_json::from_str(
        &fs::read_to_string(path).with_context(|| format!("read schema {}", path.display()))?,
    )?;
    JSONSchema::compile(Box::leak(Box::new(value))).context("compile schema")
}

fn required_string<'a>(object: &'a Value, field: &str, context: &str) -> Result<&'a str> {
    object[field]
        .as_str()
        .filter(|value| !value.is_empty())
        .with_context(|| format!("{context} requires non-empty {field}"))
}

fn repository_root() -> Result<PathBuf> {
    let output = Command::new("git")
        .args(["rev-parse", "--show-toplevel"])
        .output()
        .context("locate repository root")?;
    if !output.status.success() {
        bail!("freeze validation must run inside a Git checkout");
    }
    Ok(PathBuf::from(
        String::from_utf8_lossy(&output.stdout).trim(),
    ))
}

fn validate_freeze_git_state(
    root: &Path,
    revision: &str,
    release: &str,
    scope: &str,
) -> Result<()> {
    let head = git_output(root, ["rev-parse", "HEAD"])?;
    // A commit cannot contain its own hash, so the manifest commit (and any
    // later commit adding generated artifacts) validates against the frozen
    // evidence commit as an ancestor. Byte immutability of every referenced
    // artifact is enforced separately through the manifest digests.
    if head != revision && !git_is_ancestor(root, revision, &head)? {
        bail!("freeze revision {revision} is not checkout HEAD {head} or one of its ancestors");
    }
    let status = git_output(root, ["status", "--porcelain", "--untracked-files=all"])?;
    if !status.is_empty() {
        bail!("cannot validate a freeze from a dirty checkout");
    }
    if matches!(scope, "release" | "website") {
        if !release.starts_with('v') {
            bail!("{scope} claims require a versioned release tag");
        }
        let tag_revision = git_output(
            root,
            ["rev-parse", &format!("refs/tags/{release}^{{commit}}")],
        )?;
        if tag_revision != revision && !git_is_ancestor(root, revision, &tag_revision)? {
            bail!("release {release} does not contain freeze revision {revision}");
        }
    }
    Ok(())
}

fn git_is_ancestor(root: &Path, ancestor: &str, descendant: &str) -> Result<bool> {
    let output = Command::new("git")
        .current_dir(root)
        .args(["merge-base", "--is-ancestor", ancestor, descendant])
        .output()
        .context("run git merge-base --is-ancestor")?;
    match output.status.code() {
        Some(0) => Ok(true),
        Some(1) => Ok(false),
        _ => bail!("cannot resolve freeze revision {ancestor} in this checkout"),
    }
}

fn git_output<const N: usize>(root: &Path, args: [&str; N]) -> Result<String> {
    let output = Command::new("git")
        .current_dir(root)
        .args(args)
        .output()
        .with_context(|| format!("run git {}", args.join(" ")))?;
    if !output.status.success() {
        bail!("git {} failed", args.join(" "));
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn repository_path(root: &Path, relative: &str) -> Result<PathBuf> {
    let path = Path::new(relative);
    if path.is_absolute()
        || path
            .components()
            .any(|component| component == std::path::Component::ParentDir)
    {
        bail!("freeze artifact path must be repository-relative: {relative:?}");
    }
    let path = root.join(path);
    if !path.is_file() {
        bail!("freeze artifact is missing: {relative:?}");
    }
    let root = fs::canonicalize(root).context("canonicalize repository root")?;
    let canonical = fs::canonicalize(&path)
        .with_context(|| format!("canonicalize freeze artifact {relative:?}"))?;
    if !canonical.starts_with(root) {
        bail!("freeze artifact resolves outside the repository: {relative:?}");
    }
    Ok(canonical)
}

fn require_digest(expected: &str, bytes: &[u8], context: &str) -> Result<()> {
    let actual = format!("{:x}", Sha256::digest(bytes));
    if expected != actual {
        bail!("{context} SHA-256 digest mismatch: expected {expected}, got {actual}");
    }
    Ok(())
}

fn validate_fixture_digests(
    root: &Path,
    case_path: &str,
    selected: &Value,
    case: &Value,
) -> Result<()> {
    let mut expected = BTreeMap::new();
    for fixture in case["fixture_files"]
        .as_array()
        .expect("case schema validated")
    {
        let fixture = fixture.as_str().expect("case schema validated");
        let path = Path::new(case_path)
            .parent()
            .expect("case path has parent")
            .join(fixture);
        let path = path.to_string_lossy().replace('\\', "/");
        expected.insert(path, fixture);
    }
    let mut actual = BTreeMap::new();
    for digest in selected["fixture_digests"]
        .as_array()
        .expect("freeze schema validated")
    {
        let path = required_string(digest, "path", "fixture digest")?;
        if actual.insert(path.to_string(), digest).is_some() {
            bail!("case {} lists fixture {path:?} more than once", case["id"]);
        }
    }
    if expected.keys().collect::<Vec<_>>() != actual.keys().collect::<Vec<_>>() {
        bail!(
            "case {} fixture selection does not match case fixture_files",
            case["id"]
        );
    }
    for (path, digest) in actual {
        let bytes = fs::read(repository_path(root, &path)?)?;
        require_digest(
            digest["sha256"].as_str().expect("freeze schema validated"),
            &bytes,
            &format!("fixture {path}"),
        )?;
    }
    Ok(())
}

fn fixture_revision_for_manifest_cases(root: &Path, cases: &[(String, PathBuf)]) -> Result<String> {
    let mut hasher = Sha256::new();
    let mut cases = cases.to_vec();
    cases.sort_by(|left, right| left.0.cmp(&right.0));
    for (relative, path) in &cases {
        hasher.update(relative.as_bytes());
        let bytes = fs::read(path)?;
        hasher.update(&bytes);
        let case: Value = serde_json::from_slice(&bytes)?;
        let parent = Path::new(relative).parent().expect("case path has parent");
        for fixture in case["fixture_files"]
            .as_array()
            .expect("case schema validated")
        {
            let fixture = fixture.as_str().expect("case schema validated");
            let fixture_path = parent.join(fixture);
            // Keep this revision compatible with the result runners' existing
            // fixture_revision() contract: the case path identifies the case,
            // while each case-local fixture is bound by its declared filename.
            hasher.update(fixture.as_bytes());
            hasher.update(fs::read(root.join(&fixture_path))?);
        }
    }
    Ok(format!("sha256:{:x}", hasher.finalize()))
}

fn require_set_matches(value: &Value, expected: &BTreeSet<String>, label: &str) -> Result<()> {
    let actual = value
        .as_array()
        .expect("freeze schema validated")
        .iter()
        .map(|item| item.as_str().expect("freeze schema validated"))
        .map(str::to_string)
        .collect::<BTreeSet<_>>();
    if actual != *expected {
        bail!("{label} do not match selected cases: expected {expected:?}, got {actual:?}");
    }
    Ok(())
}

fn validate_exclusions(claim: &Value, cases: &BTreeMap<String, PathBuf>) -> Result<()> {
    for exclusion in claim["exclusions"]
        .as_array()
        .expect("freeze schema validated")
    {
        let id = required_string(exclusion, "id", "claim exclusion")?;
        if cases.contains_key(id) {
            bail!("claim exclusion {id} is also selected in the freeze");
        }
    }
    Ok(())
}

fn validate_adapter_identities(scope: &str, adapters: &BTreeMap<String, &Value>) -> Result<()> {
    if scope == "development" {
        return Ok(());
    }
    for (id, adapter) in adapters {
        for field in ["tool_version", "build_identity", "adapter_version"] {
            let value = adapter[field]
                .as_str()
                .expect("freeze schema validated")
                .trim()
                .to_ascii_lowercase();
            if matches!(
                value.as_str(),
                "unknown" | "unspecified" | "unresolved" | "not reported" | "n/a" | "na"
            ) {
                bail!("{scope} freeze adapter {id} must bind a concrete {field}, not {value:?}");
            }
        }
    }
    Ok(())
}

struct FreezeReportValidation<'a> {
    root: &'a Path,
    adapters: &'a BTreeMap<String, &'a Value>,
    cases: &'a BTreeMap<String, PathBuf>,
    result_schema: &'a JSONSchema,
    result_schema_version: u64,
    fixture_revision: &'a str,
    report_paths: &'a mut BTreeSet<String>,
}

fn validate_frozen_report(context: &mut FreezeReportValidation<'_>, frozen: &Value) -> Result<()> {
    let adapter_id = required_string(frozen, "adapter", "frozen report")?;
    let adapter = context
        .adapters
        .get(adapter_id)
        .with_context(|| format!("frozen report references unknown adapter {adapter_id}"))?;
    let relative_path = required_string(frozen, "path", "frozen report")?;
    if !context.report_paths.insert(relative_path.to_string()) {
        bail!("freeze includes normalized report {relative_path:?} more than once");
    }
    let path = repository_path(context.root, relative_path)?;
    let report_bytes = fs::read(&path)?;
    require_digest(
        frozen["sha256"].as_str().expect("freeze schema validated"),
        &report_bytes,
        &format!("normalized report {relative_path}"),
    )?;
    if frozen["normalized_report_sha256"] != frozen["sha256"] {
        bail!("frozen report {relative_path} has inconsistent normalized report digests");
    }
    let report: Value = serde_json::from_slice(&report_bytes)
        .with_context(|| format!("parse normalized report {relative_path}"))?;
    validate_value(context.result_schema, &report, &path)?;
    if report["schema_version"] != context.result_schema_version {
        bail!("normalized report {relative_path} has a mixed result schema version");
    }
    if report["fixture_revision"].as_str() != Some(context.fixture_revision) {
        bail!("normalized report {relative_path} has a mixed fixture revision");
    }
    for (report_field, adapter_field) in [
        ("tool", "tool"),
        ("tool_version", "tool_version"),
        ("tool_build_identity", "build_identity"),
        ("adapter_version", "adapter_version"),
        ("configuration_hash", "configuration_hash"),
    ] {
        if report[report_field] != adapter[adapter_field] {
            bail!(
                "normalized report {relative_path} does not match adapter {adapter_id} {adapter_field}"
            );
        }
    }
    if frozen["track"] != adapter["track"] || frozen["model_profile"] != adapter["model_profile"] {
        bail!("frozen report {relative_path} does not match its adapter partition");
    }
    if frozen["dimension"] != adapter["dimension"] {
        bail!("frozen report {relative_path} does not match its adapter dimension");
    }
    if frozen["dimension"] != "witness" && frozen["dimension"] != frozen["track"] {
        bail!("frozen report {relative_path} pools independent score dimensions");
    }

    let mut expected_ids = BTreeSet::new();
    for case_id in frozen["case_ids"]
        .as_array()
        .expect("freeze schema validated")
    {
        let case_id = case_id.as_str().expect("freeze schema validated");
        if !expected_ids.insert(case_id) {
            bail!("frozen report {relative_path} lists case {case_id} more than once");
        }
        let case_path = context.cases.get(case_id).with_context(|| {
            format!("frozen report {relative_path} references unselected case {case_id}")
        })?;
        let case: Value = serde_json::from_slice(&fs::read(case_path)?)?;
        if case["track"] != frozen["track"] || case["model_profile"] != frozen["model_profile"] {
            bail!("frozen report {relative_path} pools tracks or model profiles");
        }
    }
    let results = report["results"]
        .as_array()
        .expect("result schema validated");
    let mut actual_ids = BTreeSet::new();
    for result in results {
        let id = result["case_id"].as_str().expect("result schema validated");
        if !actual_ids.insert(id) {
            bail!("normalized report {relative_path} contains case {id} more than once");
        }
    }
    if expected_ids != actual_ids {
        bail!("normalized report {relative_path} case IDs differ from freeze selection");
    }
    validate_frozen_outcomes(frozen, results, relative_path)?;
    validate_raw_evidence(context.root, frozen, results, relative_path)?;
    Ok(())
}

fn validate_frozen_outcomes(frozen: &Value, results: &[Value], report_path: &str) -> Result<()> {
    let mut frozen_outcomes = BTreeMap::new();
    for item in frozen["outcomes"]
        .as_array()
        .expect("freeze schema validated")
    {
        let id = required_string(item, "case_id", "frozen outcome")?;
        if frozen_outcomes
            .insert(
                id,
                item["outcome"].as_str().expect("freeze schema validated"),
            )
            .is_some()
        {
            bail!("frozen report {report_path} lists outcome for {id} more than once");
        }
    }
    for result in results {
        let id = result["case_id"].as_str().expect("result schema validated");
        let actual = result["outcome"].as_str().expect("result schema validated");
        if frozen_outcomes.get(id).copied() != Some(actual) {
            bail!("frozen report {report_path} has stale normalized outcome for {id}");
        }
    }
    if frozen_outcomes.len() != results.len() {
        bail!("frozen report {report_path} outcomes do not cover exactly its results");
    }
    Ok(())
}

fn validate_raw_evidence(
    root: &Path,
    frozen: &Value,
    results: &[Value],
    report_path: &str,
) -> Result<()> {
    let mut evidence = BTreeMap::new();
    for item in frozen["raw_evidence"]
        .as_array()
        .expect("freeze schema validated")
    {
        let id = required_string(item, "case_id", "raw evidence")?;
        let path = required_string(item, "path", "raw evidence")?;
        if evidence.insert(id.to_string(), item).is_some() {
            bail!("frozen report {report_path} lists raw evidence for {id} more than once");
        }
        let path_on_disk = repository_path(root, path)?;
        let bytes = fs::read(&path_on_disk)?;
        require_digest(
            item["sha256"].as_str().expect("freeze schema validated"),
            &bytes,
            &format!("raw evidence {path}"),
        )?;
    }
    for result in results {
        let id = result["case_id"].as_str().expect("result schema validated");
        let raw_path = result["raw_output"]
            .as_str()
            .expect("result schema validated");
        let item = evidence
            .get(id)
            .with_context(|| format!("frozen report {report_path} lacks raw evidence for {id}"))?;
        if item["path"].as_str() != Some(raw_path) {
            bail!("frozen report {report_path} raw evidence path differs for {id}");
        }
        let raw_bytes = fs::read(repository_path(root, raw_path)?)?;
        let raw: Value = serde_json::from_slice(&raw_bytes)
            .with_context(|| format!("parse raw evidence {raw_path}"))?;
        let outcome = result["outcome"].as_str().expect("result schema validated");
        if let Some(declared) = raw_special_outcome(&raw)
            && declared != outcome
        {
            bail!(
                "raw evidence for {id} declares {declared}, but normalized report claims {outcome}"
            );
        }
    }
    if evidence.len() != results.len() {
        bail!("frozen report {report_path} raw evidence does not cover exactly its results");
    }
    Ok(())
}

fn raw_special_outcome(raw: &Value) -> Option<&'static str> {
    if raw["_dataflowbench_runner"]["outcome"] == "runner-error" {
        return Some("runner-error");
    }
    match raw["state"].as_str() {
        Some("unsupported") => return Some("unsupported"),
        Some("runner-error") => return Some("runner-error"),
        Some("inconclusive") => return Some("inconclusive"),
        _ => {}
    }
    if raw["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|run| run["completion"]["type"] == "inconclusive")
    {
        return Some("inconclusive");
    }
    if bifrost_runner_error_reason(raw).is_some() {
        return Some("runner-error");
    }
    if !sarif_execution_errors(raw).is_empty() {
        return Some("runner-error");
    }
    None
}

fn create_freeze(
    reports: &[PathBuf],
    scope: &str,
    release: &str,
    revision: Option<&str>,
    output: &PathBuf,
) -> Result<()> {
    let root = repository_root()?;
    let output_path = if output.is_absolute() {
        output.clone()
    } else {
        root.join(output)
    };
    let revision = git_output(
        root.as_path(),
        [
            "rev-parse",
            &format!("{}^{{commit}}", revision.unwrap_or("HEAD")),
        ],
    )
    .context("resolve freeze revision")?;
    let manifest = build_freeze_manifest(&root, reports, scope, release, &revision)?;
    let mut bytes = serde_json::to_vec_pretty(&manifest)?;
    bytes.push(b'\n');
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("create manifest directory {}", parent.display()))?;
    }
    fs::write(&output_path, bytes)
        .with_context(|| format!("write freeze manifest {}", output_path.display()))?;
    // Full evidence validation; the git state check runs once the manifest is
    // committed, because writing the manifest itself dirties the checkout.
    validate_freeze_at(&root, &output_path, false)?;
    println!(
        "wrote freeze manifest {}; commit it, then run validate-freeze to bind the checkout",
        output_path.display()
    );
    Ok(())
}

/// Assemble a freeze/v1 manifest from committed normalized reports. Every
/// digest is computed from current bytes; validation of the result against
/// the full contract is the caller's responsibility.
fn build_freeze_manifest(
    root: &Path,
    reports: &[PathBuf],
    scope: &str,
    release: &str,
    revision: &str,
) -> Result<Value> {
    if reports.is_empty() {
        bail!("create-freeze requires at least one --report");
    }

    // Index every case in the repository by ID, with repository-relative paths.
    let mut case_index = BTreeMap::new();
    for entry in WalkDir::new(root.join("cases")) {
        let entry = entry.context("walk cases directory")?;
        if !entry.file_type().is_file() || entry.file_name() != "case.json" {
            continue;
        }
        let bytes = fs::read(entry.path())
            .with_context(|| format!("read case {}", entry.path().display()))?;
        let case: Value = serde_json::from_slice(&bytes)
            .with_context(|| format!("parse case {}", entry.path().display()))?;
        let relative = entry
            .path()
            .strip_prefix(root)
            .expect("walked under repository root")
            .to_string_lossy()
            .replace('\\', "/");
        let id = required_string(&case, "id", &relative)?.to_string();
        if case_index.insert(id.clone(), (relative, case)).is_some() {
            bail!("case ID {id} appears in more than one case file");
        }
    }

    let digest_file = |relative: &str| -> Result<String> {
        let bytes = fs::read(root.join(relative))
            .with_context(|| format!("read freeze artifact {relative}"))?;
        Ok(format!("{:x}", Sha256::digest(&bytes)))
    };

    let mut selected_case_ids = BTreeSet::new();
    let mut frozen_reports = Vec::new();
    let mut adapter_values = Vec::new();
    let mut declared_fixture_revisions = BTreeSet::new();
    for report_path in reports {
        if report_path.is_absolute() {
            bail!(
                "report paths must be repository-relative: {}",
                report_path.display()
            );
        }
        let relative = report_path.to_string_lossy().replace('\\', "/");
        let bytes = fs::read(root.join(&relative))
            .with_context(|| format!("read normalized report {relative}"))?;
        let report: Value = serde_json::from_slice(&bytes)
            .with_context(|| format!("parse normalized report {relative}"))?;
        let report_sha256 = format!("{:x}", Sha256::digest(&bytes));
        declared_fixture_revisions
            .insert(required_string(&report, "fixture_revision", &relative)?.to_string());

        let adapter_id = Path::new(&relative)
            .file_stem()
            .map(|stem| stem.to_string_lossy().to_string())
            .filter(|stem| !stem.is_empty())
            .with_context(|| format!("derive adapter ID from report path {relative}"))?;

        let mut case_ids = BTreeSet::new();
        let mut outcomes = BTreeMap::new();
        let mut raw_evidence = BTreeMap::new();
        let mut tracks = BTreeSet::new();
        let mut profiles = BTreeSet::new();
        for result in report["results"].as_array().into_iter().flatten() {
            let case_id = required_string(result, "case_id", &relative)?;
            if !case_ids.insert(case_id.to_string()) {
                bail!("normalized report {relative} lists case {case_id} more than once");
            }
            let (_, case) = case_index
                .get(case_id)
                .with_context(|| format!("report {relative} references unknown case {case_id}"))?;
            tracks.insert(required_string(case, "track", case_id)?.to_string());
            profiles.insert(required_string(case, "model_profile", case_id)?.to_string());
            outcomes.insert(
                case_id.to_string(),
                required_string(result, "outcome", case_id)?.to_string(),
            );
            let raw_path = required_string(result, "raw_output", case_id)?;
            raw_evidence.insert(
                case_id.to_string(),
                json!({
                    "case_id": case_id,
                    "path": raw_path,
                    "sha256": digest_file(raw_path)?,
                }),
            );
            selected_case_ids.insert(case_id.to_string());
        }
        if case_ids.is_empty() {
            bail!("normalized report {relative} contains no results");
        }
        let (track, profile) = match (tracks.len(), profiles.len()) {
            (1, 1) => (
                tracks.first().expect("one track").clone(),
                profiles.first().expect("one profile").clone(),
            ),
            _ => bail!(
                "normalized report {relative} pools tracks {tracks:?} or model profiles {profiles:?}; a freeze binds one partition per report"
            ),
        };

        adapter_values.push(json!({
            "id": adapter_id,
            "tool": required_string(&report, "tool", &relative)?,
            "tool_version": required_string(&report, "tool_version", &relative)?,
            "build_identity": required_string(&report, "tool_build_identity", &relative)?,
            "adapter_version": required_string(&report, "adapter_version", &relative)?,
            "configuration_hash": required_string(&report, "configuration_hash", &relative)?,
            "track": track,
            "dimension": track,
            "model_profile": profile,
        }));
        frozen_reports.push(json!({
            "path": relative,
            "sha256": report_sha256,
            "normalized_report_sha256": report_sha256,
            "adapter": adapter_id,
            "track": track,
            "dimension": track,
            "model_profile": profile,
            "case_ids": case_ids.iter().collect::<Vec<_>>(),
            "outcomes": outcomes
                .iter()
                .map(|(case_id, outcome)| json!({"case_id": case_id, "outcome": outcome}))
                .collect::<Vec<_>>(),
            "raw_evidence": raw_evidence.values().collect::<Vec<_>>(),
        }));
    }

    let mut case_values = Vec::new();
    let mut selected_paths = Vec::new();
    let mut tracks = BTreeSet::new();
    let mut tiers = BTreeSet::new();
    let mut profiles = BTreeSet::new();
    for case_id in &selected_case_ids {
        let (relative, case) = &case_index[case_id];
        let mut fixture_digests = Vec::new();
        for fixture in case["fixture_files"].as_array().into_iter().flatten() {
            let fixture = fixture
                .as_str()
                .with_context(|| format!("case {case_id} fixture file must be a string"))?;
            let fixture_path = Path::new(relative)
                .parent()
                .with_context(|| format!("case path {relative} has no parent"))?
                .join(fixture)
                .to_string_lossy()
                .replace('\\', "/");
            fixture_digests.push(json!({
                "path": fixture_path,
                "sha256": digest_file(&fixture_path)?,
            }));
        }
        tracks.insert(required_string(case, "track", case_id)?.to_string());
        tiers.insert(required_string(case, "score_tier", case_id)?.to_string());
        profiles.insert(required_string(case, "model_profile", case_id)?.to_string());
        case_values.push(json!({
            "id": case_id,
            "path": relative,
            "sha256": digest_file(relative)?,
            "fixture_digests": fixture_digests,
            "track": case["track"],
            "score_tier": case["score_tier"],
            "model_profile": case["model_profile"],
            "template_id": case["template_id"],
            "polarity": case["polarity"],
        }));
        selected_paths.push((relative.clone(), root.join(relative)));
    }
    let fixture_revision = fixture_revision_for_manifest_cases(root, &selected_paths)?;
    if declared_fixture_revisions != BTreeSet::from([fixture_revision.clone()]) {
        bail!(
            "normalized reports declare fixture revisions {declared_fixture_revisions:?}, but the selected cases hash to {fixture_revision}; re-run the adapters against the current fixtures"
        );
    }

    let dimensions = frozen_reports
        .iter()
        .map(|report| {
            report["dimension"]
                .as_str()
                .expect("dimension set above")
                .to_string()
        })
        .collect::<BTreeSet<_>>();
    Ok(json!({
        "schema_version": 1,
        "benchmark": {
            "revision": revision,
            "release": release,
            "case_schema_version": 2,
            "result_schema_version": 1,
            "fixture_revision": fixture_revision,
            "dirty": false,
        },
        "claim": {
            "scope": scope,
            "tracks": tracks.iter().collect::<Vec<_>>(),
            "dimensions": dimensions.iter().collect::<Vec<_>>(),
            "exclusions": [],
            "score_tiers": tiers.iter().collect::<Vec<_>>(),
            "model_profiles": profiles.iter().collect::<Vec<_>>(),
        },
        "cases": case_values,
        "adapters": adapter_values,
        "reports": frozen_reports,
    }))
}

const RESULT_OUTCOME_ORDER: [&str; 5] = [
    "reached",
    "not-reached",
    "inconclusive",
    "unsupported",
    "runner-error",
];
const SCORE_TIER_ORDER: [&str; 4] = ["calibration", "core", "language-extension", "real-project"];

/// Case metadata a result view needs beyond what the freeze manifest binds.
/// Language and semantic dimensions live in the case file, whose bytes the
/// freeze validator has already verified against the manifest digest.
struct GeneratedCaseMeta {
    language: String,
    semantic_dimensions: Vec<String>,
    template_id: String,
    polarity: String,
    score_tier: String,
}

fn generate_results(manifest: &Path, output_directory: &Path, check: bool) -> Result<()> {
    let root = repository_root()?;
    let manifest = if manifest.is_absolute() {
        manifest.to_path_buf()
    } else {
        root.join(manifest)
    };
    generate_results_at(&root, &manifest, output_directory, true, check)?;
    if check {
        println!(
            "result artifacts in {} are current",
            output_directory.display()
        );
    } else {
        println!("wrote result artifacts to {}", output_directory.display());
    }
    Ok(())
}

/// Generate (or, with `check`, verify) result artifacts from a freeze that
/// must first pass full validation. `check_git` mirrors `validate_freeze_at`:
/// only isolated test fixtures may skip the checkout comparison.
fn generate_results_at(
    root: &Path,
    manifest_path: &Path,
    output_directory: &Path,
    check_git: bool,
    check: bool,
) -> Result<()> {
    validate_freeze_at(root, manifest_path, check_git)?;
    let artifacts = build_result_artifacts(root, manifest_path)?;
    if check {
        check_result_artifacts(output_directory, &artifacts)
    } else {
        write_result_artifacts(output_directory, &artifacts)
    }
}

fn build_result_artifacts(root: &Path, manifest_path: &Path) -> Result<BTreeMap<String, Vec<u8>>> {
    let manifest_bytes = fs::read(manifest_path)
        .with_context(|| format!("read freeze manifest {}", manifest_path.display()))?;
    let manifest_sha256 = format!("{:x}", Sha256::digest(&manifest_bytes));
    let manifest: Value = serde_json::from_slice(&manifest_bytes)
        .with_context(|| format!("parse freeze manifest {}", manifest_path.display()))?;
    let manifest_relative = manifest_display_path(root, manifest_path);

    let mut case_meta = BTreeMap::new();
    for selected in manifest["cases"].as_array().expect("freeze validated") {
        let id = required_string(selected, "id", "selected case")?;
        let relative_path = required_string(selected, "path", id)?;
        let case_bytes = fs::read(root.join(relative_path))
            .with_context(|| format!("read case {relative_path}"))?;
        let case: Value = serde_json::from_slice(&case_bytes)
            .with_context(|| format!("parse case {relative_path}"))?;
        let semantic_dimensions = case["semantic_dimensions"]
            .as_array()
            .expect("case schema validated")
            .iter()
            .map(|dimension| {
                dimension
                    .as_str()
                    .expect("case schema validated")
                    .to_string()
            })
            .collect();
        case_meta.insert(
            id.to_string(),
            GeneratedCaseMeta {
                language: required_string(&case, "language", id)?.to_string(),
                semantic_dimensions,
                template_id: required_string(selected, "template_id", id)?.to_string(),
                polarity: required_string(selected, "polarity", id)?.to_string(),
                score_tier: required_string(selected, "score_tier", id)?.to_string(),
            },
        );
    }

    let mut adapters = BTreeMap::new();
    for adapter in manifest["adapters"].as_array().expect("freeze validated") {
        adapters.insert(
            required_string(adapter, "id", "adapter")?.to_string(),
            adapter,
        );
    }

    let mut used_identifiers: BTreeMap<String, usize> = BTreeMap::new();
    let mut scorecard_values = Vec::new();
    let mut scorecard_pages = Vec::new();
    for report in manifest["reports"].as_array().expect("freeze validated") {
        let adapter_id = required_string(report, "adapter", "frozen report")?;
        let adapter = adapters
            .get(adapter_id)
            .with_context(|| format!("frozen report binds unknown adapter {adapter_id}"))?;
        let identifier = scorecard_identifier(&mut used_identifiers, adapter_id, report)?;
        let (value, page) = build_scorecard(
            &identifier,
            adapter,
            report,
            &case_meta,
            &manifest_relative,
            &manifest_sha256,
        )?;
        scorecard_values.push(value);
        scorecard_pages.push((identifier, page));
    }

    let results = json!({
        "schema_version": 1,
        "manifest": {"path": manifest_relative, "sha256": manifest_sha256},
        "benchmark": manifest["benchmark"],
        "claim": manifest["claim"],
        "scorecards": scorecard_values,
    });
    let mut results_bytes = serde_json::to_vec_pretty(&results)?;
    results_bytes.push(b'\n');

    let mut artifacts = BTreeMap::new();
    artifacts.insert("results.json".to_string(), results_bytes);
    artifacts.insert(
        "index.md".to_string(),
        build_index_page(
            &manifest,
            &manifest_relative,
            &manifest_sha256,
            &scorecard_pages,
        )
        .into_bytes(),
    );
    for (identifier, page) in scorecard_pages {
        artifacts.insert(format!("scorecards/{identifier}.md"), page.into_bytes());
    }
    Ok(artifacts)
}

fn manifest_display_path(root: &Path, manifest_path: &Path) -> String {
    let canonical_root = fs::canonicalize(root).unwrap_or_else(|_| root.to_path_buf());
    let canonical_manifest =
        fs::canonicalize(manifest_path).unwrap_or_else(|_| manifest_path.to_path_buf());
    canonical_manifest
        .strip_prefix(&canonical_root)
        .unwrap_or(&canonical_manifest)
        .to_string_lossy()
        .replace('\\', "/")
}

/// A stable page identifier per frozen report. Reports that share an adapter,
/// track, dimension, and profile are distinct result populations, so later
/// occurrences receive an ordinal suffix in manifest order.
fn scorecard_identifier(
    used: &mut BTreeMap<String, usize>,
    adapter_id: &str,
    report: &Value,
) -> Result<String> {
    let mut base = String::new();
    for part in [
        adapter_id,
        required_string(report, "track", "frozen report")?,
        required_string(report, "dimension", "frozen report")?,
        required_string(report, "model_profile", "frozen report")?,
    ] {
        if !base.is_empty() {
            base.push('-');
        }
        for character in part.chars() {
            base.push(match character.to_ascii_lowercase() {
                lower @ ('a'..='z' | '0'..='9') => lower,
                _ => '-',
            });
        }
    }
    let ordinal = used.entry(base.clone()).or_insert(0);
    *ordinal += 1;
    if *ordinal == 1 {
        Ok(base)
    } else {
        Ok(format!("{base}-{ordinal}"))
    }
}

fn classify_outcome(polarity: &str, outcome: &str) -> &'static str {
    match (polarity, outcome) {
        ("positive", "reached") => "true-positive",
        ("positive", "not-reached") => "false-negative",
        ("negative", "reached") => "false-positive",
        ("negative", "not-reached") => "true-negative",
        (_, "inconclusive") => "inconclusive",
        (_, "unsupported") => "unsupported",
        _ => "runner-error",
    }
}

fn rate_fraction(numerator: usize, denominator: usize) -> Value {
    if denominator == 0 {
        Value::Null
    } else {
        json!({
            "numerator": numerator,
            "denominator": denominator,
            "percent": percent_string(numerator as f64 / denominator as f64),
        })
    }
}

fn percent_string(rate: f64) -> String {
    format!("{:.1}", rate * 100.0)
}

fn mean_percent(rates: &[f64]) -> Option<String> {
    if rates.is_empty() {
        None
    } else {
        Some(percent_string(
            rates.iter().sum::<f64>() / rates.len() as f64,
        ))
    }
}

fn build_scorecard(
    identifier: &str,
    adapter: &Value,
    report: &Value,
    case_meta: &BTreeMap<String, GeneratedCaseMeta>,
    manifest_relative: &str,
    manifest_sha256: &str,
) -> Result<(Value, String)> {
    let mut outcomes = BTreeMap::new();
    for record in report["outcomes"].as_array().expect("freeze validated") {
        outcomes.insert(
            required_string(record, "case_id", "outcome record")?,
            required_string(record, "outcome", "outcome record")?,
        );
    }
    let mut raw_evidence = BTreeMap::new();
    for evidence in report["raw_evidence"].as_array().expect("freeze validated") {
        raw_evidence.insert(
            required_string(evidence, "case_id", "raw evidence")?,
            (
                required_string(evidence, "path", "raw evidence")?,
                required_string(evidence, "sha256", "raw evidence")?,
            ),
        );
    }

    // language -> score tier -> case IDs, in deterministic order.
    let mut populations: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
    for case_id in report["case_ids"].as_array().expect("freeze validated") {
        let case_id = case_id.as_str().expect("freeze validated");
        let meta = case_meta
            .get(case_id)
            .with_context(|| format!("frozen report selects unknown case {case_id}"))?;
        populations
            .entry(meta.language.as_str())
            .or_default()
            .entry(meta.score_tier.as_str())
            .or_default()
            .push(case_id);
    }

    let track = required_string(report, "track", "frozen report")?;
    let dimension = required_string(report, "dimension", "frozen report")?;
    let model_profile = required_string(report, "model_profile", "frozen report")?;
    let report_path = required_string(report, "path", "frozen report")?;
    let report_sha256 = required_string(report, "sha256", "frozen report")?;
    let normalized_sha256 = required_string(report, "normalized_report_sha256", "frozen report")?;

    let mut page = String::new();
    page.push_str(&format!("# Scorecard `{identifier}`\n\n"));
    page.push_str(&format!(
        "Adapter `{}`: `{}` `{}` (build `{}`, adapter version `{}`, configuration `{}`).\n\n",
        required_string(adapter, "id", "adapter")?,
        required_string(adapter, "tool", "adapter")?,
        required_string(adapter, "tool_version", "adapter")?,
        required_string(adapter, "build_identity", "adapter")?,
        required_string(adapter, "adapter_version", "adapter")?,
        required_string(adapter, "configuration_hash", "adapter")?,
    ));
    page.push_str(&format!(
        "Track `{track}`, score dimension `{dimension}`, model profile `{model_profile}`. \
         This scorecard is a single result population; it is never pooled with \
         other tracks, dimensions, or model profiles.\n\n"
    ));
    page.push_str(&format!(
        "Normalized report: `{report_path}` (`sha256:{report_sha256}`, normalized \
         `sha256:{normalized_sha256}`). Generated from freeze manifest \
         `{manifest_relative}` (`sha256:{manifest_sha256}`).\n"
    ));

    let mut language_values = Vec::new();
    for (language, tiers) in &populations {
        let mut tier_values = Vec::new();
        for tier in SCORE_TIER_ORDER {
            let Some(case_ids) = tiers.get(tier) else {
                continue;
            };
            let scored = tier != "calibration";
            page.push_str(&format!("\n## Language `{language}`, tier `{tier}`\n\n"));

            let mut coverage: BTreeMap<&str, usize> = BTreeMap::new();
            for case_id in case_ids {
                *coverage.entry(outcomes[case_id]).or_default() += 1;
            }
            let coverage_value: Value = RESULT_OUTCOME_ORDER
                .iter()
                .map(|outcome| {
                    (
                        outcome.to_string(),
                        json!(coverage.get(outcome).copied().unwrap_or(0)),
                    )
                })
                .chain([("total".to_string(), json!(case_ids.len()))])
                .collect::<serde_json::Map<_, _>>()
                .into();
            page.push_str("Outcome coverage: ");
            for outcome in RESULT_OUTCOME_ORDER {
                page.push_str(&format!(
                    "`{outcome}` {}, ",
                    coverage.get(outcome).copied().unwrap_or(0)
                ));
            }
            page.push_str(&format!(
                "total {}. `inconclusive`, `unsupported`, and `runner-error` are \
                 capability and execution coverage; they are never counted as \
                 clean negatives.\n",
                case_ids.len()
            ));
            if !scored {
                page.push_str(
                    "\nCalibration cases exercise schemas and adapters; they do not \
                     contribute to a correctness score.\n",
                );
            }

            // semantic dimension -> template -> case IDs.
            let mut by_dimension: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
            for case_id in case_ids {
                let meta = &case_meta[*case_id];
                for semantic_dimension in &meta.semantic_dimensions {
                    by_dimension
                        .entry(semantic_dimension.as_str())
                        .or_default()
                        .entry(meta.template_id.as_str())
                        .or_default()
                        .push(case_id);
                }
            }

            let mut dimension_values = Vec::new();
            let mut dimension_tprs = Vec::new();
            let mut dimension_fprs = Vec::new();
            if scored {
                page.push_str("\n### Semantic dimension rates\n\n");
                page.push_str(
                    "| Semantic dimension | TP | FN | FP | TN | Inconclusive | \
                     Unsupported | Runner error | TPR (template macro) | \
                     FPR (template macro) |\n",
                );
                page.push_str("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n");
            }
            for (semantic_dimension, templates) in &by_dimension {
                let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
                let mut template_tprs = Vec::new();
                let mut template_fprs = Vec::new();
                for template_cases in templates.values() {
                    let mut template_counts: BTreeMap<&str, usize> = BTreeMap::new();
                    for case_id in template_cases {
                        let classification =
                            classify_outcome(&case_meta[*case_id].polarity, outcomes[case_id]);
                        *template_counts.entry(classification).or_default() += 1;
                        *counts.entry(classification).or_default() += 1;
                    }
                    let true_positives = template_counts.get("true-positive").copied().unwrap_or(0);
                    let false_negatives =
                        template_counts.get("false-negative").copied().unwrap_or(0);
                    let false_positives =
                        template_counts.get("false-positive").copied().unwrap_or(0);
                    let true_negatives = template_counts.get("true-negative").copied().unwrap_or(0);
                    if true_positives + false_negatives > 0 {
                        template_tprs.push(
                            true_positives as f64 / (true_positives + false_negatives) as f64,
                        );
                    }
                    if false_positives + true_negatives > 0 {
                        template_fprs.push(
                            false_positives as f64 / (false_positives + true_negatives) as f64,
                        );
                    }
                }
                let count = |classification: &str| counts.get(classification).copied().unwrap_or(0);
                let tpr = mean_percent(&template_tprs);
                let fpr = mean_percent(&template_fprs);
                if scored {
                    page.push_str(&format!(
                        "| `{semantic_dimension}` | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n",
                        count("true-positive"),
                        count("false-negative"),
                        count("false-positive"),
                        count("true-negative"),
                        count("inconclusive"),
                        count("unsupported"),
                        count("runner-error"),
                        percent_cell(&tpr),
                        percent_cell(&fpr),
                    ));
                }
                if let Some(tpr) = &tpr {
                    dimension_tprs.push(tpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                if let Some(fpr) = &fpr {
                    dimension_fprs.push(fpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                dimension_values.push(json!({
                    "name": semantic_dimension,
                    "counts": {
                        "true_positives": count("true-positive"),
                        "false_negatives": count("false-negative"),
                        "false_positives": count("false-positive"),
                        "true_negatives": count("true-negative"),
                        "inconclusive": count("inconclusive"),
                        "unsupported": count("unsupported"),
                        "runner_errors": count("runner-error"),
                    },
                    "true_positive_rate": rate_fraction(
                        count("true-positive"),
                        count("true-positive") + count("false-negative"),
                    ),
                    "false_positive_rate": rate_fraction(
                        count("false-positive"),
                        count("false-positive") + count("true-negative"),
                    ),
                    "template_macro": {
                        "true_positive_rate_percent": tpr,
                        "false_positive_rate_percent": fpr,
                        "scored_positive_templates": template_tprs.len(),
                        "scored_negative_templates": template_fprs.len(),
                    },
                }));
            }
            let macro_tpr = mean_percent(&dimension_tprs);
            let macro_fpr = mean_percent(&dimension_fprs);
            if scored {
                page.push_str(&format!(
                    "\nMacro-average over semantic dimensions: TPR {}, FPR {}. \
                     Macro-averages pool templates first, then semantic dimensions; \
                     raw case counts are shown for audit only.\n",
                    percent_cell(&macro_tpr),
                    percent_cell(&macro_fpr),
                ));
            }

            page.push_str("\n### Cases\n\n");
            page.push_str(
                "| Template | Case | Polarity | Outcome | Classification | \
                 Raw evidence | Raw SHA-256 |\n",
            );
            page.push_str("| --- | --- | --- | --- | --- | --- | --- |\n");
            let mut case_values = Vec::new();
            let mut ordered_cases: Vec<&&str> = case_ids.iter().collect();
            ordered_cases
                .sort_by_key(|case_id| (case_meta[**case_id].template_id.as_str(), **case_id));
            for case_id in ordered_cases {
                let meta = &case_meta[*case_id];
                let outcome = outcomes[case_id];
                let classification = classify_outcome(&meta.polarity, outcome);
                let (raw_path, raw_sha256) = raw_evidence[case_id];
                page.push_str(&format!(
                    "| `{}` | `{case_id}` | {} | `{outcome}` | {classification} | \
                     `{raw_path}` | `{raw_sha256}` |\n",
                    meta.template_id, meta.polarity,
                ));
                case_values.push(json!({
                    "case_id": case_id,
                    "template_id": meta.template_id,
                    "polarity": meta.polarity,
                    "semantic_dimensions": meta.semantic_dimensions,
                    "outcome": outcome,
                    "classification": classification,
                    "raw_evidence": {"path": raw_path, "sha256": raw_sha256},
                }));
            }

            tier_values.push(json!({
                "score_tier": tier,
                "scored": scored,
                "outcome_coverage": coverage_value,
                "semantic_dimensions": dimension_values,
                "dimension_macro": {
                    "true_positive_rate_percent": macro_tpr,
                    "false_positive_rate_percent": macro_fpr,
                },
                "cases": case_values,
            }));
        }
        language_values.push(json!({
            "language": language,
            "score_tiers": tier_values,
        }));
    }

    let value = json!({
        "id": identifier,
        "adapter": adapter,
        "track": track,
        "dimension": dimension,
        "model_profile": model_profile,
        "report": {
            "path": report_path,
            "sha256": report_sha256,
            "normalized_report_sha256": normalized_sha256,
        },
        "languages": language_values,
    });
    Ok((value, page))
}

fn percent_cell(percent: &Option<String>) -> String {
    match percent {
        Some(percent) => format!("{percent}%"),
        None => "n/a".to_string(),
    }
}

fn build_index_page(
    manifest: &Value,
    manifest_relative: &str,
    manifest_sha256: &str,
    scorecard_pages: &[(String, String)],
) -> String {
    let benchmark = &manifest["benchmark"];
    let claim = &manifest["claim"];
    let mut page = String::new();
    page.push_str("# DataFlowBench frozen results\n\n");
    page.push_str(&format!(
        "Generated from freeze manifest `{manifest_relative}` \
         (`sha256:{manifest_sha256}`), benchmark release `{}` at revision \
         `{}`, fixture revision `{}`.\n\n",
        benchmark["release"].as_str().unwrap_or_default(),
        benchmark["revision"].as_str().unwrap_or_default(),
        benchmark["fixture_revision"].as_str().unwrap_or_default(),
    ));
    page.push_str(&format!(
        "Claim scope `{}`. Every number on these pages is derived from the \
         immutable freeze evidence above; none are maintained by hand. Tracks, \
         score dimensions, score tiers, and model profiles are separate result \
         populations and are never combined into one leaderboard.\n\n",
        claim["scope"].as_str().unwrap_or_default(),
    ));
    for (label, field) in [
        ("Tracks", "tracks"),
        ("Score dimensions", "dimensions"),
        ("Score tiers", "score_tiers"),
        ("Model profiles", "model_profiles"),
    ] {
        let names = claim[field]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(|name| format!("`{name}`"))
            .collect::<Vec<_>>()
            .join(", ");
        page.push_str(&format!("- {label}: {names}\n"));
    }

    page.push_str("\n## Exclusions\n\n");
    let exclusions = claim["exclusions"].as_array().cloned().unwrap_or_default();
    if exclusions.is_empty() {
        page.push_str("None.\n");
    } else {
        page.push_str("| Case | Reason |\n| --- | --- |\n");
        for exclusion in &exclusions {
            page.push_str(&format!(
                "| `{}` | {} |\n",
                exclusion["id"].as_str().unwrap_or_default(),
                exclusion["reason"].as_str().unwrap_or_default(),
            ));
        }
    }

    page.push_str("\n## Scorecards\n\n");
    for (identifier, _) in scorecard_pages {
        page.push_str(&format!("- [`{identifier}`](scorecards/{identifier}.md)\n"));
    }
    page
}

fn write_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    for (relative, bytes) in artifacts {
        let path = output_directory.join(relative);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("create output directory {}", parent.display()))?;
        }
        fs::write(&path, bytes)
            .with_context(|| format!("write result artifact {}", path.display()))?;
    }
    Ok(())
}

/// Prove the checked-in artifacts are byte-identical to a fresh generation.
/// Missing, stale, and unexpected files each fail the check so a stale page
/// cannot survive behind a regenerated sibling.
fn check_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    let mut problems = Vec::new();
    for (relative, expected) in artifacts {
        let path = output_directory.join(relative);
        match fs::read(&path) {
            Ok(actual) if &actual == expected => {}
            Ok(_) => problems.push(format!("stale artifact: {relative}")),
            Err(_) => problems.push(format!("missing artifact: {relative}")),
        }
    }
    if output_directory.is_dir() {
        for entry in WalkDir::new(output_directory) {
            let entry = entry.context("walk output directory")?;
            if !entry.file_type().is_file() {
                continue;
            }
            let relative = entry
                .path()
                .strip_prefix(output_directory)
                .expect("walked under output directory")
                .to_string_lossy()
                .replace('\\', "/");
            if !artifacts.contains_key(&relative) {
                problems.push(format!("unexpected artifact: {relative}"));
            }
        }
    }
    if !problems.is_empty() {
        bail!("result artifacts are not current:\n{}", problems.join("\n"));
    }
    Ok(())
}

fn run_bifrost_smoke(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::Smoke)
}

fn run_bifrost_python_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::PythonKernel)
}

fn run_bifrost(binary: &Path, run: BifrostRun) -> Result<()> {
    validate_cases()?;
    let (raw_dir, report_path) = match run {
        BifrostRun::Smoke => (
            Path::new("reports/raw/bifrost"),
            Path::new("reports/bifrost-smoke.json"),
        ),
        BifrostRun::PythonKernel => (
            Path::new("reports/raw/bifrost-python-kernel"),
            Path::new("reports/bifrost-python-kernel.json"),
        ),
    };
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let version =
        command_output(Command::new(binary).arg("--version")).unwrap_or_else(|_| "unknown".into());
    let build_identity = command_output(Command::new(binary).arg("--build-identity"))
        .unwrap_or_else(|_| "unknown".into());
    let revision = fixture_revision()?;
    let mut results = Vec::new();
    let mut policy_paths = BTreeSet::new();
    let mut selected_cases = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !selected_bifrost_case(&case, run) {
            continue;
        }
        selected_cases += 1;
        let id = case["id"].as_str().expect("schema validated");
        let model = &case["tool_model_references"]["bifrost"];
        let raw_path = raw_dir.join(format!("{id}.json"));
        if raw_path.exists() {
            fs::remove_file(&raw_path)
                .with_context(|| format!("clear stale raw output {}", raw_path.display()))?;
        }
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
            let policy = model["policy"]
                .as_str()
                .context("Bifrost case lacks policy reference")?;
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
                        normalize_bifrost(&case, &report, status_code)?
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
        let selection = match run {
            BifrostRun::Smoke => "Bifrost smoke",
            BifrostRun::PythonKernel => "Bifrost Python kernel",
        };
        bail!("no cases selected for {selection}");
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
    fs::write(report_path, serde_json::to_string_pretty(&report)? + "\n")?;
    validate_reports()?;
    println!("wrote {}", report_path.display());
    Ok(())
}

fn selected_bifrost_case(case: &Value, run: BifrostRun) -> bool {
    match run {
        BifrostRun::Smoke => has_bifrost_model_reference(case),
        BifrostRun::PythonKernel => {
            case["language"] == "python"
                && case["track"] == "taint"
                && case["score_tier"] == "core"
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| policy.ends_with("core-python-kernel.rqlp"))
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
    }
}

fn has_bifrost_model_reference(case: &Value) -> bool {
    let model = &case["tool_model_references"]["bifrost"];
    model.is_object() && (model["policy"].is_string() || model["unsupported_reason"].is_string())
}

fn bifrost_result(
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

fn write_bifrost_error(
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

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CodeqlLanguage {
    Java,
    Python,
}

impl CodeqlLanguage {
    fn cli_name(self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::Python => "python",
        }
    }
}

fn run_codeql_java_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let raw_dir = Path::new("reports/raw/codeql");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
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
    fs::write(
        "reports/codeql-java-kernel.json",
        serde_json::to_string_pretty(&report)? + "\n",
    )?;
    validate_reports()?;
    println!("wrote reports/codeql-java-kernel.json");
    Ok(())
}

fn selected_codeql_java_case(case: &Value) -> bool {
    case["language"] == "java"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"].is_object()
}

/// Run the JavaScript-only CodeQL kernel. This deliberately does not reuse the
/// Java selector or its database/raw-output roots: CodeQL has shared standard
/// libraries, but the benchmark adapters must remain language-scoped.
fn run_codeql_javascript_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = select_codeql_javascript_cases()?;
    let raw_dir = Path::new(CODEQL_JAVASCRIPT_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
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
                fs::write(
                    &raw_path,
                    serde_json::to_string_pretty(&json!({
                        "adapter": "codeql-javascript",
                        "case_id": id,
                        "state": "unsupported",
                        "reason": reason,
                        "evidence_kind": "adapter-capability-declaration"
                    }))? + "\n",
                )?;
                ("unsupported", vec![reason.to_string()], raw_path)
            } else {
                let query = model["query"]
                    .as_str()
                    .context("JavaScript CodeQL case lacks query reference")?;
                query_paths.insert(PathBuf::from(query));
                run_codeql_javascript_case(binary, packs, &path, &case, Path::new(query), raw_dir)?
            };
        results.push(codeql_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let mut configuration_paths = query_paths;
    configuration_paths.insert(PathBuf::from(CODEQL_JAVASCRIPT_QUERY));
    configuration_paths.insert(PathBuf::from("adapters/codeql/javascript/qlpack.yml"));
    let javascript_lock = PathBuf::from("adapters/codeql/javascript/codeql-pack.lock.yml");
    if javascript_lock.is_file() {
        configuration_paths.insert(javascript_lock);
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
    fs::write(
        CODEQL_JAVASCRIPT_REPORT,
        serde_json::to_string_pretty(&report)? + "\n",
    )?;
    validate_reports()?;
    println!("wrote {CODEQL_JAVASCRIPT_REPORT}");
    Ok(())
}

fn run_codeql_python_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_python_cases()?;
    let raw_dir = Path::new("reports/raw/codeql-python-kernel");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
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
            raw_dir,
            CodeqlLanguage::Python,
        )?;
        results.push(codeql_result(
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
    fs::write(
        "reports/codeql-python-kernel.json",
        serde_json::to_string_pretty(&report)? + "\n",
    )?;
    validate_reports()?;
    println!("wrote reports/codeql-python-kernel.json");
    Ok(())
}

fn codeql_result(
    case: &Value,
    id: &str,
    outcome: &str,
    diagnostics: Vec<String>,
    duration: std::time::Duration,
    raw_path: &Path,
) -> Value {
    json!({
        "case_id": id,
        "outcome": outcome,
        "source_anchors": case["source_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "sink_anchors": case["sink_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "witness_checkpoints": [],
        "diagnostics": diagnostics,
        "duration_ms": duration.as_millis() as u64,
        "peak_memory_mb": Value::Null,
        "raw_output": raw_path.to_string_lossy()
    })
}

fn select_codeql_javascript_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !javascript_core_case(&case) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        if !model.is_object() {
            bail!(
                "JavaScript core case {} lacks a CodeQL model reference",
                case["id"]
            );
        }
        if !model["unsupported_reason"].is_string() {
            let query = model["query"].as_str().with_context(|| {
                format!(
                    "JavaScript core case {} lacks a CodeQL query reference",
                    case["id"]
                )
            })?;
            if query != CODEQL_JAVASCRIPT_QUERY {
                bail!(
                    "JavaScript core case {} references non-JavaScript CodeQL query {query:?}",
                    case["id"]
                );
            }
        } else if let Some(query) = model["query"].as_str()
            && query != CODEQL_JAVASCRIPT_QUERY
        {
            bail!(
                "JavaScript core case {} references non-JavaScript CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    if selected.len() != CODEQL_JAVASCRIPT_CASE_COUNT {
        bail!(
            "JavaScript CodeQL kernel must select exactly {} core assertions; found {}",
            CODEQL_JAVASCRIPT_CASE_COUNT,
            selected.len()
        );
    }
    let mut templates = BTreeMap::<&str, (usize, usize)>::new();
    for (_, case) in &selected {
        let template = case["template_id"].as_str().expect("schema validated");
        let counts = templates.entry(template).or_default();
        if case["polarity"] == "positive" {
            counts.0 += 1;
        } else {
            counts.1 += 1;
        }
    }
    if templates.len() != CODEQL_JAVASCRIPT_TEMPLATE_COUNT
        || templates
            .values()
            .any(|(positive, negative)| *positive != 1 || *negative != 1)
    {
        bail!(
            "JavaScript CodeQL kernel must contain {} balanced templates; found {templates:?}",
            CODEQL_JAVASCRIPT_TEMPLATE_COUNT
        );
    }
    Ok(selected)
}

fn javascript_core_case(case: &Value) -> bool {
    case["language"] == "javascript" && case["track"] == "taint" && case["score_tier"] == "core"
}

fn run_codeql_javascript_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = materialize_codeql_javascript_workspace(case_path, case)?;
    let database_root = std::env::temp_dir().join("dataflowbench-codeql-javascript-databases");
    fs::create_dir_all(&database_root)?;
    let database = database_root.join(id);
    if database.exists() {
        fs::remove_dir_all(&database).with_context(|| format!("clear {}", database.display()))?;
    }
    let raw_path = raw_dir.join(format!("{id}.sarif.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    for stale in [&raw_path, &error_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let result = (|| {
        let create = Command::new(binary)
            .arg("database")
            .arg("create")
            .arg(&database)
            .arg("--language=javascript")
            .arg(format!("--source-root={}", workspace.display()))
            .arg("--overwrite")
            .output();
        let create = match create {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL JavaScript database create with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_javascript_spawn_error(
                    raw_dir,
                    id,
                    "database-create",
                    &diagnostic,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        if !create.status.success() {
            return write_codeql_javascript_error(raw_dir, id, "database-create", &create, None);
        }

        let mut analyze = Command::new(binary);
        analyze
            .arg("database")
            .arg("analyze")
            .arg(&database)
            .arg(query)
            .arg("--format=sarif-latest")
            .arg(format!("--output={}", raw_path.display()))
            .arg("--rerun");
        if let Some(packs) = packs {
            analyze.arg(format!("--additional-packs={}", packs.display()));
        }
        let analyzed = match analyze.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL JavaScript database analyze with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_javascript_spawn_error(
                    raw_dir,
                    id,
                    "database-analyze",
                    &diagnostic,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        if !analyzed.status.success() {
            return write_codeql_javascript_error(
                raw_dir,
                id,
                "database-analyze",
                &analyzed,
                raw_path.is_file().then_some(raw_path.as_path()),
            );
        }
        if !raw_path.is_file() {
            let diagnostic = "CodeQL JavaScript analysis produced no SARIF output".to_string();
            let error_path =
                write_codeql_javascript_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
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
        let mut diagnostics = sarif_messages(&sarif);
        let (outcome, anchor_diagnostics) = javascript_sarif_outcome(case_path, case, &sarif);
        diagnostics.extend(anchor_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path))
    })();

    let cleanup = clear_codeql_case_artifacts(&workspace, &database);
    match (result, cleanup) {
        (Ok((outcome, diagnostics, raw_path)), Ok(())) => Ok((outcome, diagnostics, raw_path)),
        (Ok((_, mut diagnostics, raw_path)), Err(error)) => {
            diagnostics.push(format!(
                "CodeQL JavaScript artifact cleanup failed: {error}"
            ));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, raw_path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "CodeQL JavaScript artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

fn materialize_codeql_javascript_workspace(case_path: &Path, case: &Value) -> Result<PathBuf> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = std::env::temp_dir()
        .join("dataflowbench-codeql-javascript-workspaces")
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

fn write_codeql_javascript_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    output: &std::process::Output,
    raw_path: Option<&Path>,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let diagnostic = format!(
        "CodeQL JavaScript {stage} failed with status {}",
        output.status
    );
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "codeql-javascript",
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

fn write_codeql_javascript_spawn_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "codeql-javascript",
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "diagnostic": diagnostic,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(error_path)
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct JavascriptSinkAnchor {
    file: String,
    marker_line: u64,
    function_name: String,
    callsite_lines: BTreeSet<u64>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SarifAnchorMatch {
    Matched,
    Unmatched,
    Ambiguous,
}

fn javascript_sarif_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
) -> (&'static str, Vec<String>) {
    if sarif_result_count(sarif) == 0 {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match javascript_sink_locations(case_path, case) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove SARIF finding against sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for result in sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
    {
        match javascript_sarif_result_match(result, &sink_locations) {
            SarifAnchorMatch::Matched => matched += 1,
            SarifAnchorMatch::Unmatched => unmatched += 1,
            SarifAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} SARIF finding(s) have ambiguous sink-anchor locations"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} SARIF finding(s) did not match the case sink anchor"
        )],
    )
}

fn javascript_sink_locations(
    case_path: &Path,
    case: &Value,
) -> std::result::Result<Vec<JavascriptSinkAnchor>, String> {
    let fixture_root = case_path
        .parent()
        .ok_or_else(|| "case path has no parent".to_string())?;
    let mut locations = Vec::new();
    for anchor in case["sink_anchors"]
        .as_array()
        .ok_or_else(|| "case has no sink anchors".to_string())?
    {
        let file = anchor["file"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks file".to_string())?;
        let marker = anchor["marker"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks marker".to_string())?;
        let body = fs::read_to_string(fixture_root.join(file))
            .map_err(|error| format!("read sink fixture {file}: {error}"))?;
        let hinted_line = anchor["line_hint"].as_u64();
        let lines = body
            .lines()
            .enumerate()
            .filter_map(|(index, line)| line.contains(marker).then_some(index as u64 + 1))
            .collect::<Vec<_>>();
        let line = if let Some(line) = hinted_line {
            if !lines.contains(&line) {
                return Err(format!("marker {marker:?} is not on hinted line {line}"));
            }
            line
        } else if lines.len() == 1 {
            lines[0]
        } else {
            return Err(format!(
                "marker {marker:?} has {} possible lines",
                lines.len()
            ));
        };
        let declaration = body
            .lines()
            .nth(line as usize - 1)
            .ok_or_else(|| format!("sink anchor line {line} is outside {file}"))?;
        let function_name = javascript_function_name(declaration, marker)
            .ok_or_else(|| format!("sink marker {marker:?} is not on a function declaration"))?;
        let callsite_lines = body
            .lines()
            .enumerate()
            .filter_map(|(index, candidate)| {
                let candidate_line = index as u64 + 1;
                (candidate_line != line && javascript_function_call(candidate, &function_name))
                    .then_some(candidate_line)
            })
            .collect::<BTreeSet<_>>();
        if callsite_lines.is_empty() {
            return Err(format!(
                "sink function {function_name} has no callsites in {file}"
            ));
        }
        locations.push(JavascriptSinkAnchor {
            file: file.to_string(),
            marker_line: line,
            function_name,
            callsite_lines,
        });
    }
    if locations.is_empty() {
        return Err("case has no resolvable sink locations".to_string());
    }
    if locations
        .iter()
        .map(|location| (&location.file, location.marker_line))
        .collect::<BTreeSet<_>>()
        .len()
        != locations.len()
    {
        return Err("case contains duplicate sink anchors".to_string());
    }
    Ok(locations)
}

fn javascript_function_name(line: &str, marker: &str) -> Option<String> {
    let marker_start = line.find(marker)?;
    let declaration = &line[..marker_start];
    let function_start = declaration
        .match_indices("function")
        .filter(|(start, _)| {
            let before = declaration[..*start].chars().next_back();
            let after = declaration[*start + "function".len()..].chars().next();
            !before.is_some_and(javascript_identifier_char)
                && !after.is_some_and(javascript_identifier_char)
        })
        .map(|(start, _)| start)
        .last()?;
    let mut name = declaration[function_start + "function".len()..].trim_start();
    if let Some(rest) = name.strip_prefix('*') {
        name = rest.trim_start();
    }
    let end = name
        .char_indices()
        .find_map(|(index, character)| (!javascript_identifier_char(character)).then_some(index))
        .unwrap_or(name.len());
    (end > 0).then(|| name[..end].to_string())
}

fn javascript_identifier_char(character: char) -> bool {
    character == '_' || character == '$' || character.is_ascii_alphanumeric()
}

fn javascript_function_call(line: &str, function_name: &str) -> bool {
    let line = javascript_code_without_literals(line);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        let preceded_by_member = before == Some('.') || before == Some('?');
        if !before.is_some_and(javascript_identifier_char)
            && !preceded_by_member
            && after == Some('(')
        {
            let prefix = line[..start].trim_end();
            if !prefix.ends_with("function") {
                return true;
            }
        }
        search_from = end;
    }
    false
}

fn javascript_code_without_literals(line: &str) -> String {
    let mut output = String::with_capacity(line.len());
    let mut quote = None;
    let mut escaped = false;
    let mut characters = line.chars().peekable();
    while let Some(character) = characters.next() {
        if let Some(active_quote) = quote {
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == active_quote {
                quote = None;
            }
            output.push(' ');
            continue;
        }
        if character == '/' && characters.peek() == Some(&'/') {
            break;
        }
        if matches!(character, '\'' | '"' | '`') {
            quote = Some(character);
            output.push(' ');
        } else {
            output.push(character);
        }
    }
    output
}

fn javascript_sarif_result_match(
    result: &Value,
    sink_locations: &[JavascriptSinkAnchor],
) -> SarifAnchorMatch {
    let Some(locations) = result["locations"].as_array() else {
        return SarifAnchorMatch::Ambiguous;
    };
    if locations.is_empty() {
        return SarifAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    let mut malformed = false;
    for location in locations {
        let Some(uri) = location["physicalLocation"]["artifactLocation"]["uri"].as_str() else {
            malformed = true;
            continue;
        };
        let Some(line) = location["physicalLocation"]["region"]["startLine"].as_u64() else {
            malformed = true;
            continue;
        };
        for (index, anchor) in sink_locations.iter().enumerate() {
            if sarif_uri_matches_file(uri, &anchor.file) && anchor.callsite_lines.contains(&line) {
                matches.insert(index);
            }
        }
    }
    if malformed || matches.len() > 1 {
        SarifAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        SarifAnchorMatch::Matched
    } else {
        SarifAnchorMatch::Unmatched
    }
}

fn sarif_uri_matches_file(uri: &str, file: &str) -> bool {
    let uri = uri.replace('\\', "/");
    let uri = uri.split(['?', '#']).next().unwrap_or(&uri);
    let uri = uri.strip_prefix("file://").unwrap_or(uri);
    let uri = uri.trim_start_matches('/');
    let normalize = |path: &str| path.trim_start_matches("./").replace('\\', "/");
    let uri = normalize(uri);
    let file = normalize(file);
    uri == file
        || uri.ends_with(&format!("/{file}"))
        || Path::new(&uri).file_name().and_then(|name| name.to_str())
            == Path::new(&file).file_name().and_then(|name| name.to_str())
}

fn selected_codeql_python_case(case: &Value) -> bool {
    case["language"] == "python"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .is_some_and(|query| query == CODEQL_PYTHON_QUERY)
}

fn codeql_python_cases() -> Result<Vec<(PathBuf, Value)>> {
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
    Ok(all_cases)
}

fn validate_codeql_python_population(cases: &[(PathBuf, Value)]) -> Result<PathBuf> {
    if cases.len() != 32 {
        bail!(
            "Python CodeQL kernel must select exactly 32 core assertions; found {}",
            cases.len()
        );
    }
    let mut pairs: BTreeMap<(&str, &str), (usize, usize)> = BTreeMap::new();
    let mut model_profiles = BTreeSet::new();
    let mut queries = BTreeSet::new();
    for (path, case) in cases {
        if !selected_codeql_python_case(case) {
            bail!(
                "Python CodeQL selection contains a non-core or non-Python case: {}",
                path.display()
            );
        }
        let template = case["template_id"]
            .as_str()
            .context("Python CodeQL case lacks template_id")?;
        let profile = case["model_profile"]
            .as_str()
            .context("Python CodeQL case lacks model_profile")?;
        model_profiles.insert(profile);
        let query = case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .context("Python CodeQL case lacks query reference")?;
        queries.insert(PathBuf::from(query));
        let entry = pairs.entry((template, profile)).or_default();
        match case["polarity"].as_str() {
            Some("positive") => entry.0 += 1,
            Some("negative") => entry.1 += 1,
            Some(other) => bail!("{} has unsupported polarity {other:?}", path.display()),
            None => bail!("{} lacks polarity", path.display()),
        }
    }
    let expected_templates = CODEQL_PYTHON_TEMPLATE_IDS
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let actual_templates = pairs
        .keys()
        .map(|(template, _)| *template)
        .collect::<BTreeSet<_>>();
    if actual_templates != expected_templates {
        let missing = expected_templates
            .difference(&actual_templates)
            .copied()
            .collect::<Vec<_>>();
        let unexpected = actual_templates
            .difference(&expected_templates)
            .copied()
            .collect::<Vec<_>>();
        bail!(
            "Python CodeQL kernel template set mismatch (missing={missing:?}, unexpected={unexpected:?})"
        );
    }
    if pairs.len() != 16 {
        bail!(
            "Python CodeQL kernel must contain exactly 16 balanced templates; found {}",
            pairs.len()
        );
    }
    if pairs
        .values()
        .any(|(positive, negative)| *positive != 1 || *negative != 1)
    {
        bail!("Python CodeQL kernel requires one positive and one negative per template");
    }
    if model_profiles.len() != 1 {
        bail!("Python CodeQL kernel must use one model profile across all 32 cases");
    }
    if queries.len() != 1 {
        bail!("Python CodeQL kernel must use one query across all 32 cases");
    }
    let query = queries.into_iter().next().expect("one query validated");
    Ok(query)
}

fn codeql_python_configuration_paths(query_paths: &BTreeSet<PathBuf>) -> BTreeSet<PathBuf> {
    let mut paths = query_paths.clone();
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

fn run_codeql_case(
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
        raw_dir,
        CodeqlLanguage::Java,
    )
}

fn run_codeql_case_for_language(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
    language: CodeqlLanguage,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
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
    ] {
        if stale.exists() {
            fs::remove_file(&stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }
    let mut create_command = Command::new(binary);
    if language == CodeqlLanguage::Java {
        let classes = workspace.join("classes");
        fs::create_dir_all(&classes)?;
    }
    create_command.args(codeql_database_create_args(
        &database, &workspace, case, language,
    )?);
    let create = match create_command.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database create: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-create", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    if !create.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-create", &create)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(error);
    }

    let raw_path = raw_dir.join(format!("{id}.sarif.json"));
    let mut analyze = Command::new(binary);
    analyze
        .arg("database")
        .arg("analyze")
        .arg(&database)
        .arg(query)
        .arg("--format=sarif-latest")
        .arg(format!("--output={}", raw_path.display()))
        .arg("--rerun");
    if let Some(packs) = packs {
        analyze.arg(format!("--additional-packs={}", packs.display()));
    }
    let analyzed = match analyze.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database analyze: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    if !analyzed.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-analyze", &analyzed)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(error);
    }
    let sarif_text = match fs::read_to_string(&raw_path) {
        Ok(text) => text,
        Err(error) => {
            let (outcome, diagnostics, error_path) =
                codeql_missing_sarif_error(raw_dir, id, &raw_path, &error)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok((outcome, diagnostics, error_path));
        }
    };
    let sarif: Value = match serde_json::from_str(&sarif_text) {
        Ok(sarif) => sarif,
        Err(error) => {
            let diagnostic = format!("parse CodeQL SARIF {}: {error}", raw_path.display());
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    let execution_errors = sarif_execution_errors(&sarif);
    if !execution_errors.is_empty() {
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(("runner-error", execution_errors, raw_path));
    }
    let (outcome, diagnostics) = if language == CodeqlLanguage::Python {
        normalize_python_codeql_sarif(case, &sarif)
    } else {
        let result_count = sarif_result_count(&sarif);
        let diagnostics = sarif_messages(&sarif);
        let outcome = if result_count == 0 {
            "not-reached"
        } else {
            "reached"
        };
        (outcome, diagnostics)
    };
    clear_codeql_case_artifacts(&workspace, &database)?;
    Ok((outcome, diagnostics, raw_path))
}

fn clear_codeql_case_artifacts(workspace: &Path, database: &Path) -> Result<()> {
    for path in [database, workspace] {
        if path.exists() {
            fs::remove_dir_all(path).with_context(|| format!("clear {}", path.display()))?;
        }
    }
    Ok(())
}

fn materialize_codeql_workspace(case_path: &Path, case: &Value) -> Result<PathBuf> {
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

fn write_codeql_error(
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

fn write_codeql_spawn_error(
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

fn codeql_missing_sarif_error(
    raw_dir: &Path,
    id: &str,
    raw_path: &Path,
    error: &std::io::Error,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let diagnostic = format!("read CodeQL SARIF {}: {error}", raw_path.display());
    let error_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
    Ok(("runner-error", vec![diagnostic], error_path))
}

fn codeql_database_create_args(
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
            let fixture_names = case["fixture_files"]
                .as_array()
                .context("CodeQL case lacks fixture_files")?
                .iter()
                .map(|fixture| {
                    fixture
                        .as_str()
                        .context("CodeQL fixture_files must contain strings")
                })
                .collect::<Result<Vec<_>>>()?;
            let build_command = format!("javac -d classes {}", fixture_names.join(" "));
            args.push(format!("--command={build_command}"));
        }
        CodeqlLanguage::Python => args.push("--build-mode=none".to_string()),
    }
    Ok(args)
}

fn normalize_python_codeql_sarif(case: &Value, sarif: &Value) -> (&'static str, Vec<String>) {
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
            if python_sink_anchor_matches(case, uri) {
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
                "CodeQL SARIF retained {unmappable_findings} finding(s) that did not map to a canonical Python sink anchor"
            ));
        }
        diagnostics.sort();
        diagnostics.dedup();
        ("reached", diagnostics)
    } else {
        diagnostics.push(
            "CodeQL SARIF findings could not be mapped to a canonical Python sink anchor; analysis evidence is incomplete"
                .to_string(),
        );
        diagnostics.sort();
        diagnostics.dedup();
        ("inconclusive", diagnostics)
    }
}

fn python_sink_anchor_matches(case: &Value, uri: &str) -> bool {
    case["sink_anchors"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|anchor| {
            let Some(file) = anchor["file"].as_str() else {
                return false;
            };
            sarif_uri_matches_file(uri, file)
        })
}

fn sarif_result_count(sarif: &Value) -> usize {
    sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|run| run["results"].as_array().map_or(0, Vec::len))
        .sum()
}

fn sarif_messages(sarif: &Value) -> Vec<String> {
    let mut messages = sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
        .filter_map(|result| result["message"]["text"].as_str())
        .map(str::to_string)
        .collect::<Vec<_>>();
    messages.sort();
    messages.dedup();
    messages
}

fn sarif_execution_errors(sarif: &Value) -> Vec<String> {
    let mut errors = Vec::new();
    for invocation in sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["invocations"].as_array().into_iter().flatten())
    {
        if invocation["executionSuccessful"] == false {
            errors.push("CodeQL SARIF reports unsuccessful execution".to_string());
        }
        for notification in invocation["toolExecutionNotifications"]
            .as_array()
            .into_iter()
            .flatten()
        {
            if notification["level"] == "error" {
                errors.push(
                    notification["message"]["text"]
                        .as_str()
                        .unwrap_or("CodeQL SARIF contains an execution error")
                        .to_string(),
                );
            }
        }
    }
    errors.sort();
    errors.dedup();
    errors
}

fn hash_paths(paths: &BTreeSet<PathBuf>) -> Result<String> {
    let mut hasher = Sha256::new();
    for path in paths {
        hasher.update(path.to_string_lossy().as_bytes());
        hasher.update(fs::read(path).with_context(|| format!("read {}", path.display()))?);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn fixture_revision() -> Result<String> {
    let mut hasher = Sha256::new();
    for path in case_paths() {
        hasher.update(path.to_string_lossy().as_bytes());
        let case_bytes = fs::read(&path)?;
        hasher.update(&case_bytes);
        let case: Value = serde_json::from_slice(&case_bytes)?;
        let root = path.parent().expect("case path has parent");
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            hasher.update(fixture.as_bytes());
            hasher.update(fs::read(root.join(fixture))?);
        }
    }
    Ok(format!("sha256:{:x}", hasher.finalize()))
}

fn materialize_bifrost_workspace(case_path: &Path, case: &Value, policy: &str) -> Result<PathBuf> {
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

fn normalize_bifrost(
    case: &Value,
    report: &Value,
    status: Option<i32>,
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
    let finding_count = count_findings(report);
    let expects_flow = !case["expected_flows"]
        .as_array()
        .expect("schema validated")
        .is_empty();
    let outcome = match (expects_flow, finding_count) {
        (true, 0) => "not-reached",
        (true, _) => "reached",
        (false, 0) => "not-reached",
        (false, _) => "reached",
    };
    // The raw Bifrost report retains witnesses, but the adapter does not yet
    // prove their locations against canonical DFB markers. Do not turn
    // expected checkpoints from the case into observed result evidence.
    Ok((outcome, report_diagnostics, Vec::new()))
}

fn incompleteness_reasons(value: &Value) -> Vec<String> {
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

fn bifrost_runner_error_reason(value: &Value) -> Option<String> {
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

fn count_findings(value: &Value) -> usize {
    match value {
        Value::Object(map) => map
            .iter()
            .map(|(key, item)| {
                if key == "findings" {
                    item.as_array().map_or(0, Vec::len)
                } else {
                    count_findings(item)
                }
            })
            .sum(),
        Value::Array(items) => items.iter().map(count_findings).sum(),
        _ => 0,
    }
}

fn diagnostics(value: &Value) -> Vec<String> {
    let mut out = Vec::new();
    collect_diagnostics(value, &mut out);
    out.sort();
    out.dedup();
    out
}

fn collect_diagnostics(value: &Value, out: &mut Vec<String>) {
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

fn command_output(command: &mut Command) -> Result<String> {
    let output = command.output()?;
    if !output.status.success() {
        bail!("command failed");
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn now_seconds() -> Result<u64> {
    Ok(SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs())
}

#[cfg(test)]
mod tests {
    use super::*;

    struct FreezeFixture {
        root: PathBuf,
        manifest: PathBuf,
        report: PathBuf,
        raw: PathBuf,
    }

    impl FreezeFixture {
        fn new(outcome: &str, raw: Value) -> Self {
            let unique = format!(
                "dataflowbench-freeze-test-{}-{}",
                std::process::id(),
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            );
            let root = std::env::temp_dir().join(unique);
            fs::create_dir_all(root.join("schemas")).unwrap();
            fs::create_dir_all(root.join("cases/taint/test")).unwrap();
            fs::create_dir_all(root.join("reports/raw")).unwrap();
            for schema in [
                "case.schema.json",
                "result.schema.json",
                "freeze.schema.json",
            ] {
                fs::copy(
                    Path::new("schemas").join(schema),
                    root.join("schemas").join(schema),
                )
                .unwrap();
            }

            let case_relative = "cases/taint/test/case.json";
            let fixture_relative = "cases/taint/test/flow.c";
            let case_path = root.join(case_relative);
            fs::write(
                &case_path,
                serde_json::to_vec_pretty(&json!({
                    "schema_version": 2,
                    "id": "dfb-taint-test",
                    "template_id": "dfb-template-test",
                    "polarity": "positive",
                    "score_tier": "core",
                    "track": "taint",
                    "language": "c",
                    "semantic_dimensions": ["local-flow"],
                    "feature_tags": ["intraprocedural"],
                    "model_profile": "benchmark-controlled",
                    "fixture_files": ["flow.c"],
                    "source_anchors": [{"marker": "DFB-SOURCE: input", "file": "flow.c"}],
                    "sink_anchors": [{"marker": "DFB-SINK: sink", "file": "flow.c"}],
                    "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}],
                    "expected_nonflows": [],
                    "expected_analysis_capability": {"kind": "intraprocedural-taint"},
                    "execution_budget": {"wall_clock_seconds": 1},
                    "fixture_provenance": {
                        "kind": "authored", "origin": "test", "revision": "test", "license": "MIT"
                    },
                    "tool_model_references": {}
                }))
                .unwrap(),
            )
            .unwrap();
            fs::write(
                root.join(fixture_relative),
                "/* DFB-SOURCE: input DFB-SINK: sink */\n",
            )
            .unwrap();

            let selected_case = (case_relative.to_string(), case_path.clone());
            let fixture_revision =
                fixture_revision_for_manifest_cases(&root, std::slice::from_ref(&selected_case))
                    .unwrap();
            let raw_relative = "reports/raw/test.json";
            let raw_path = root.join(raw_relative);
            fs::write(&raw_path, serde_json::to_vec_pretty(&raw).unwrap()).unwrap();
            let report_relative = "reports/test.json";
            let report_path = root.join(report_relative);
            let report = json!({
                "schema_version": 1,
                "tool": "test-tool",
                "tool_version": "1.0.0",
                "tool_build_identity": "test-build-1",
                "adapter_version": "1.0.0",
                "configuration_hash": "0000000000000000000000000000000000000000000000000000000000000000",
                "fixture_revision": fixture_revision,
                "started_at_unix_seconds": 1,
                "ended_at_unix_seconds": 2,
                "cold_or_warm": "cold",
                "results": [{
                    "case_id": "dfb-taint-test",
                    "outcome": outcome,
                    "source_anchors": ["DFB-SOURCE: input"],
                    "sink_anchors": ["DFB-SINK: sink"],
                    "witness_checkpoints": [],
                    "diagnostics": [],
                    "duration_ms": 1,
                    "peak_memory_mb": null,
                    "raw_output": raw_relative
                }]
            });
            fs::write(&report_path, serde_json::to_vec_pretty(&report).unwrap()).unwrap();

            let case_bytes = fs::read(&case_path).unwrap();
            let fixture_bytes = fs::read(root.join(fixture_relative)).unwrap();
            let report_bytes = fs::read(&report_path).unwrap();
            let raw_bytes = fs::read(&raw_path).unwrap();
            let digest = |bytes: &[u8]| format!("{:x}", Sha256::digest(bytes));
            let manifest = json!({
                "schema_version": 1,
                "benchmark": {
                    "revision": "a".repeat(40),
                    "release": "development",
                    "case_schema_version": 2,
                    "result_schema_version": 1,
                    "fixture_revision": fixture_revision,
                    "dirty": false
                },
                "claim": {
                    "scope": "development",
                    "tracks": ["taint"],
                    "dimensions": ["taint"],
                    "exclusions": [],
                    "score_tiers": ["core"],
                    "model_profiles": ["benchmark-controlled"]
                },
                "cases": [{
                    "id": "dfb-taint-test", "path": case_relative, "sha256": digest(&case_bytes),
                    "fixture_digests": [{"path": fixture_relative, "sha256": digest(&fixture_bytes)}],
                    "track": "taint", "score_tier": "core", "model_profile": "benchmark-controlled",
                    "template_id": "dfb-template-test", "polarity": "positive"
                }],
                "adapters": [{
                    "id": "test", "tool": "test-tool", "tool_version": "1.0.0",
                    "build_identity": "test-build-1", "adapter_version": "1.0.0",
                    "configuration_hash": "0000000000000000000000000000000000000000000000000000000000000000",
                    "track": "taint", "dimension": "taint", "model_profile": "benchmark-controlled"
                }],
                "reports": [{
                    "path": report_relative, "sha256": digest(&report_bytes),
                    "normalized_report_sha256": digest(&report_bytes), "adapter": "test",
                    "track": "taint", "dimension": "taint", "model_profile": "benchmark-controlled",
                    "case_ids": ["dfb-taint-test"], "outcomes": [{"case_id": "dfb-taint-test", "outcome": outcome}],
                    "raw_evidence": [{"case_id": "dfb-taint-test", "path": raw_relative, "sha256": digest(&raw_bytes)}]
                }]
            });
            let manifest_path = root.join("reports/freeze.json");
            fs::write(
                &manifest_path,
                serde_json::to_vec_pretty(&manifest).unwrap(),
            )
            .unwrap();
            Self {
                root,
                manifest: manifest_path,
                report: report_path,
                raw: raw_path,
            }
        }

        fn read_manifest(&self) -> Value {
            serde_json::from_slice(&fs::read(&self.manifest).unwrap()).unwrap()
        }

        fn write_manifest(&self, manifest: &Value) {
            fs::write(&self.manifest, serde_json::to_vec_pretty(manifest).unwrap()).unwrap();
        }

        fn refresh_report_digest(&self, manifest: &mut Value) {
            let digest = format!("{:x}", Sha256::digest(fs::read(&self.report).unwrap()));
            manifest["reports"][0]["sha256"] = json!(digest);
            manifest["reports"][0]["normalized_report_sha256"] = json!(digest);
        }
    }

    impl Drop for FreezeFixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.root);
        }
    }
    #[test]
    fn checked_in_cases_validate() {
        validate_cases().unwrap();
    }
    #[test]
    fn report_directory_validates() {
        validate_reports().unwrap();
    }
    #[test]
    fn normalizer_keeps_negative_and_unsupported_distinct() {
        let negative = json!({"expected_flows": []});
        assert_eq!(
            normalize_bifrost(
                &negative,
                &json!({
                    "runs": [{"completion": {"type": "complete"}, "findings": []}]
                }),
                Some(0)
            )
            .unwrap()
            .0,
            "not-reached"
        );
        assert_eq!(
            normalize_bifrost(
                &negative,
                &json!({
                    "runs": [{"completion": {"type": "complete"}, "findings": [{}]}]
                }),
                Some(0)
            )
            .unwrap()
            .0,
            "reached"
        );
        assert_eq!(
            normalize_bifrost(&negative, &json!({}), Some(2)).unwrap().0,
            "inconclusive"
        );
        assert!(normalize_bifrost(
            &negative,
            &json!({"runs": [{"completion": {"type": "inconclusive", "reasons": ["partial_discovery"]}}]}),
            Some(2)
        )
        .unwrap()
        .1
            .contains(&"Bifrost reported incomplete analysis: partial_discovery".to_string()));
    }

    #[test]
    fn normalizer_does_not_synthesize_witness_checkpoints() {
        let case = json!({
            "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}],
            "witness_checkpoints": ["DFB-WITNESS: relay"]
        });
        let normalized = normalize_bifrost(
            &case,
            &json!({
                "runs": [{"completion": {"type": "complete"}, "findings": [{}]}]
            }),
            Some(0),
        )
        .unwrap();
        assert_eq!(normalized.0, "reached");
        assert!(normalized.2.is_empty());
    }

    #[test]
    fn incomplete_or_unexpected_bifrost_status_never_becomes_clean_negative() {
        let negative = json!({"expected_flows": []});
        let incomplete = json!({
            "runs": [{
                "completion": {"type": "inconclusive", "reasons": ["partial_discovery"]},
                "findings": []
            }]
        });
        assert_eq!(
            normalize_bifrost(&negative, &incomplete, Some(0))
                .unwrap()
                .0,
            "inconclusive"
        );
        assert_eq!(
            normalize_bifrost(
                &negative,
                &json!({"runs": [{"completion": {"type": "complete"}, "findings": []}]}),
                Some(9)
            )
            .unwrap()
            .0,
            "runner-error"
        );
        assert_eq!(
            normalize_bifrost(&negative, &json!({"findings": []}), Some(0))
                .unwrap()
                .0,
            "runner-error"
        );
    }

    #[test]
    fn python_kernel_selection_is_separate_from_direct_and_java() {
        let python_kernel = json!({
            "language": "python",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-python-kernel.rqlp"}
            }
        });
        let python_direct = json!({
            "language": "python",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
            }
        });
        let java_kernel = json!({
            "language": "java",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-python-kernel.rqlp"}
            }
        });
        let python_unsupported = json!({
            "language": "python",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"unsupported_reason": "requires an external model catalog"}
            }
        });
        assert!(selected_bifrost_case(
            &python_kernel,
            BifrostRun::PythonKernel
        ));
        assert!(!selected_bifrost_case(
            &python_direct,
            BifrostRun::PythonKernel
        ));
        assert!(!selected_bifrost_case(
            &java_kernel,
            BifrostRun::PythonKernel
        ));
        assert!(selected_bifrost_case(
            &python_unsupported,
            BifrostRun::PythonKernel
        ));
        assert!(selected_bifrost_case(&python_direct, BifrostRun::Smoke));
    }

    #[test]
    fn core_templates_require_one_positive_and_one_negative() {
        let case = |polarity| {
            json!({
                "track": "taint",
                "language": "java",
                "template_id": "dfb-template-direct-propagation",
                "model_profile": "benchmark-controlled",
                "score_tier": "core",
                "polarity": polarity
            })
        };
        let balanced = vec![
            (PathBuf::from("positive.json"), case("positive")),
            (PathBuf::from("negative.json"), case("negative")),
        ];
        assert!(validate_balanced_core_pairs(&balanced).is_ok());

        let unbalanced = vec![(PathBuf::from("positive.json"), case("positive"))];
        assert!(validate_balanced_core_pairs(&unbalanced).is_err());
    }

    #[test]
    fn marker_validation_rejects_stale_metadata() {
        let path = Path::new("cases/taint/java/direct-positive/case.json");
        let mut case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();

        case["source_anchors"][0]["line_hint"] = json!(1);
        assert!(validate_markers(path, &case).is_err());

        case["source_anchors"][0]["line_hint"] = json!(4);
        case["witness_checkpoints"] = json!(["DFB-WITNESS: absent"]);
        assert!(validate_markers(path, &case).is_err());
    }

    #[test]
    fn sarif_normalization_counts_results_and_deduplicates_messages() {
        let sarif = json!({
            "runs": [
                {"results": [
                    {"message": {"text": "flow found"}},
                    {"message": {"text": "flow found"}}
                ]},
                {"results": []}
            ]
        });
        assert_eq!(sarif_result_count(&sarif), 2);
        assert_eq!(sarif_messages(&sarif), vec!["flow found"]);
    }

    #[test]
    fn sarif_execution_errors_prevent_clean_negative_interpretation() {
        let sarif = json!({
            "runs": [{
                "results": [],
                "invocations": [{
                    "executionSuccessful": false,
                    "toolExecutionNotifications": [{
                        "level": "error",
                        "message": {"text": "query evaluation failed"}
                    }]
                }]
            }]
        });
        assert_eq!(sarif_result_count(&sarif), 0);
        assert_eq!(
            sarif_execution_errors(&sarif),
            vec![
                "CodeQL SARIF reports unsuccessful execution",
                "query evaluation failed"
            ]
        );
    }

    #[test]
    fn javascript_core_selection_is_exactly_32_balanced_assertions() {
        let mut selected = Vec::new();
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if javascript_core_case(&case) {
                selected.push(case);
            }
        }
        assert_eq!(selected.len(), CODEQL_JAVASCRIPT_CASE_COUNT);
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for case in selected {
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(templates.len(), CODEQL_JAVASCRIPT_TEMPLATE_COUNT);
        assert!(
            templates
                .values()
                .all(|(positive, negative)| *positive == 1 && *negative == 1)
        );
    }

    #[test]
    fn java_and_javascript_codeql_selectors_are_language_disjoint() {
        let mut java = 0;
        let mut javascript = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_codeql_java_case(&case) {
                java += 1;
                assert_eq!(case["language"], "java");
            }
            if javascript_core_case(&case) {
                javascript += 1;
                assert_eq!(case["language"], "javascript");
            }
        }
        assert_eq!(java, 32);
        assert_eq!(javascript, CODEQL_JAVASCRIPT_CASE_COUNT);
    }

    #[test]
    fn javascript_core_selection_is_language_and_track_scoped() {
        let javascript = json!({
            "language": "javascript",
            "track": "taint",
            "score_tier": "core"
        });
        assert!(javascript_core_case(&javascript));
        for language in ["typescript", "java", "python"] {
            let mut other = javascript.clone();
            other["language"] = json!(language);
            assert!(!javascript_core_case(&other));
        }
        let mut other = javascript.clone();
        other["track"] = json!("value-flow");
        assert!(!javascript_core_case(&other));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!javascript_core_case(&other));
    }

    #[test]
    fn javascript_sarif_mapping_requires_the_sink_file_and_line() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-javascript-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.js"),
            "function sink(value) {} // DFB-SINK: sink\nfunction other(value) {}\nother(input);\nsink(input);\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.js",
                "line_hint": 1
            }]
        });
        let matching = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "file:///tmp/work/fixture.js"},
                "region": {"startLine": 4}
            }}]}]}]
        });
        assert_eq!(
            javascript_sarif_outcome(&case_path, &case, &matching).0,
            "reached"
        );
        let wrong_line = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.js"},
                "region": {"startLine": 3}
            }}]}]}]
        });
        assert_eq!(
            javascript_sarif_outcome(&case_path, &case, &wrong_line).0,
            "inconclusive"
        );
        let missing_location = json!({
            "runs": [{"results": [{"message": {"text": "flow"}}]}]
        });
        assert_eq!(
            javascript_sarif_outcome(&case_path, &case, &missing_location).0,
            "inconclusive"
        );
        let no_results = json!({"runs": [{"results": []}]});
        assert_eq!(
            javascript_sarif_outcome(&case_path, &case, &no_results).0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn javascript_sarif_ambiguous_locations_stay_inconclusive() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-javascript-ambiguous-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.js"),
            "// DFB-SINK: duplicate\n// DFB-SINK: duplicate\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{"marker": "DFB-SINK: duplicate", "file": "fixture.js"}]
        });
        let sarif = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.js"},
                "region": {"startLine": 1}
            }}]}]}]
        });
        assert_eq!(
            javascript_sarif_outcome(&case_path, &case, &sarif).0,
            "inconclusive"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn javascript_codeql_report_paths_are_dedicated() {
        assert_eq!(CODEQL_JAVASCRIPT_RAW_DIR, "reports/raw/codeql-javascript");
        assert_eq!(
            CODEQL_JAVASCRIPT_REPORT,
            "reports/codeql-javascript-kernel.json"
        );
        assert_eq!(
            CODEQL_JAVASCRIPT_QUERY,
            "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
        );
    }

    #[test]
    fn python_codeql_population_requires_exact_balanced_32() {
        let mut cases = Vec::new();
        for index in 0..16 {
            for polarity in ["positive", "negative"] {
                cases.push((
                    PathBuf::from(format!("case-{index}-{polarity}.json")),
                    json!({
                        "id": format!("dfb-taint-python-template-{index}-{polarity}"),
                        "template_id": CODEQL_PYTHON_TEMPLATE_IDS[index],
                        "polarity": polarity,
                        "score_tier": "core",
                        "track": "taint",
                        "language": "python",
                        "model_profile": "benchmark-controlled",
                        "tool_model_references": {
                            "codeql": {"query": CODEQL_PYTHON_QUERY}
                        }
                    }),
                ));
            }
        }
        // Population validation is metadata-only; the checked-in query path
        // is verified by the command-facing selection helper.
        assert_eq!(
            validate_codeql_python_population(&cases).unwrap(),
            PathBuf::from("adapters/codeql/python/queries/PythonKernel.ql")
        );
        let mut drifted = cases.clone();
        drifted[0].1["template_id"] = json!("dfb-template-unapproved-drift");
        assert!(validate_codeql_python_population(&drifted).is_err());
        cases.pop();
        assert!(validate_codeql_python_population(&cases).is_err());
    }

    #[test]
    fn python_codeql_selection_requires_canonical_query() {
        let mut case = json!({
            "language": "python",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {"codeql": {"query": CODEQL_PYTHON_QUERY}}
        });
        assert!(selected_codeql_python_case(&case));
        case["tool_model_references"]["codeql"]["query"] =
            json!("adapters/codeql/python/queries/OtherKernel.ql");
        assert!(!selected_codeql_python_case(&case));
    }

    #[test]
    fn codeql_database_creation_uses_language_specific_build_modes() {
        let case = json!({"fixture_files": ["direct_flow.py"]});
        let python_args = codeql_database_create_args(
            Path::new("/tmp/python-db"),
            Path::new("/tmp/python-workspace"),
            &case,
            CodeqlLanguage::Python,
        )
        .unwrap();
        assert!(python_args.iter().any(|arg| arg == "--language=python"));
        assert!(python_args.iter().any(|arg| arg == "--build-mode=none"));
        assert!(!python_args.iter().any(|arg| arg.starts_with("--command=")));

        let java_args = codeql_database_create_args(
            Path::new("/tmp/java-db"),
            Path::new("/tmp/java-workspace"),
            &case,
            CodeqlLanguage::Java,
        )
        .unwrap();
        assert!(java_args.iter().any(|arg| arg == "--language=java"));
        assert!(
            java_args
                .iter()
                .any(|arg| arg == "--command=javac -d classes direct_flow.py")
        );
        assert!(!java_args.iter().any(|arg| arg == "--build-mode=none"));
    }

    #[test]
    fn codeql_missing_sarif_keeps_runner_error_evidence() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-codeql-missing-sarif-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let raw_path = root.join("case.sarif.json");
        let read_error = fs::read_to_string(&raw_path).unwrap_err();
        let (outcome, diagnostics, evidence_path) =
            codeql_missing_sarif_error(&root, "case", &raw_path, &read_error).unwrap();

        assert_eq!(outcome, "runner-error");
        assert!(diagnostics[0].contains("read CodeQL SARIF"));
        assert_eq!(evidence_path, root.join("case-error.json"));
        let evidence: Value =
            serde_json::from_str(&fs::read_to_string(&evidence_path).unwrap()).unwrap();
        assert_eq!(evidence["state"], "runner-error");
        assert_eq!(evidence["stage"], "database-analyze");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn python_codeql_sarif_requires_a_canonical_sink_anchor() {
        let case = json!({
            "sink_anchors": [{"file": "direct_flow.py", "line_hint": 5}]
        });
        let reached = json!({
            "runs": [{"results": [{
                "message": {"text": "flow"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "file:///tmp/codeql/direct_flow.py"},
                    "region": {"startLine": 11}
                }}]
            }]}]
        });
        assert_eq!(normalize_python_codeql_sarif(&case, &reached).0, "reached");

        let wrong_file = json!({
            "runs": [{"results": [{
                "message": {"text": "unrelated finding"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "other_fixture.py"},
                    "region": {"startLine": 4}
                }}]
            }]}]
        });
        assert_eq!(
            normalize_python_codeql_sarif(&case, &wrong_file).0,
            "inconclusive"
        );

        let clean = json!({"runs": [{"results": []}]});
        assert_eq!(
            normalize_python_codeql_sarif(&case, &clean).0,
            "not-reached"
        );

        let malformed = json!({"runs": [{"results": [{}]}]});
        assert_eq!(
            normalize_python_codeql_sarif(&case, &malformed).0,
            "inconclusive"
        );
        assert_eq!(
            normalize_python_codeql_sarif(&case, &json!({"runs": []})).0,
            "runner-error"
        );
    }

    #[test]
    fn freeze_schema_is_versioned_and_compiles() {
        let schema = compile_schema(Path::new("schemas/freeze.schema.json")).unwrap();
        let invalid = json!({"schema_version": 2});
        assert!(schema.validate(&invalid).is_err());
    }

    #[test]
    fn freeze_fixture_revision_is_order_independent() {
        let paths = case_paths();
        let selected = paths
            .iter()
            .take(2)
            .map(|path| (path.to_string_lossy().to_string(), path.clone()))
            .collect::<Vec<_>>();
        let mut reversed = selected.clone();
        reversed.reverse();
        assert_eq!(
            fixture_revision_for_manifest_cases(Path::new("."), &selected).unwrap(),
            fixture_revision_for_manifest_cases(Path::new("."), &reversed).unwrap()
        );
    }

    #[test]
    fn checked_reports_match_declared_fixture_revisions() {
        let bifrost: Value =
            serde_json::from_str(&fs::read_to_string("reports/bifrost-smoke.json").unwrap())
                .unwrap();
        let python: Value = serde_json::from_str(
            &fs::read_to_string("reports/bifrost-python-kernel.json").unwrap(),
        )
        .unwrap();
        let current_revision = fixture_revision().unwrap();
        assert_eq!(bifrost["fixture_revision"], current_revision);
        assert_eq!(python["fixture_revision"], current_revision);

        for report in [&bifrost, &python] {
            let revision = report["fixture_revision"].as_str().unwrap();
            assert!(
                revision
                    .strip_prefix("sha256:")
                    .is_some_and(|digest| digest.len() == 64)
            );
        }
        for path in [
            "reports/codeql-java-kernel.json",
            "reports/codeql-javascript-kernel.json",
            "reports/codeql-python-kernel.json",
        ] {
            let report: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            let revision = report["fixture_revision"].as_str().unwrap();
            assert!(
                revision
                    .strip_prefix("sha256:")
                    .is_some_and(|digest| digest.len() == 64)
            );
        }
    }

    #[test]
    fn raw_special_outcomes_cannot_be_downgraded_to_clean_negatives() {
        assert_eq!(
            raw_special_outcome(&json!({"state": "unsupported"})),
            Some("unsupported")
        );
        assert_eq!(
            raw_special_outcome(&json!({"state": "runner-error"})),
            Some("runner-error")
        );
        assert_eq!(
            raw_special_outcome(&json!({"runs": [{"completion": {"type": "inconclusive"}}]})),
            Some("inconclusive")
        );
        assert_eq!(raw_special_outcome(&json!({"findings": []})), None);
    }

    #[test]
    fn representative_bifrost_incomplete_evidence_stays_inconclusive() {
        let raw = json!({
            "schema_version": 4,
            "execution": {
                "termination": null,
                "terminal_stage": null,
                "pending_policy_ids": ["dataflowbench.taint.core-direct"]
            },
            "runs": [{
                "policy_id": "dataflowbench.taint.core-direct",
                "completion": {
                    "type": "inconclusive",
                    "reasons": ["partial_discovery", "budget_exhausted"]
                },
                "findings": []
            }]
        });
        assert_eq!(raw_special_outcome(&raw), Some("inconclusive"));
    }

    #[test]
    fn bifrost_runner_failures_are_not_clean_negatives() {
        let case = json!({"expected_flows": []});
        let raw = json!({
            "execution": {"termination": {"type": "error"}},
            "runs": []
        });
        assert_eq!(
            normalize_bifrost(&case, &raw, Some(0)).unwrap().0,
            "runner-error"
        );
        assert_eq!(raw_special_outcome(&raw), Some("runner-error"));
        assert_eq!(
            raw_special_outcome(&json!({
                "_dataflowbench_runner": {"outcome": "runner-error", "exit_status": 127}
            })),
            Some("runner-error")
        );
    }

    #[test]
    fn freeze_rejects_missing_raw_evidence() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::remove_file(&fixture.raw).unwrap();
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
    }

    #[test]
    fn freeze_rejects_altered_fixture_bytes() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
    }

    #[test]
    fn freeze_rejects_mixed_fixture_revision() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let mut report: Value =
            serde_json::from_slice(&fs::read(&fixture.report).unwrap()).unwrap();
        report["fixture_revision"] =
            json!("sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
        fs::write(&fixture.report, serde_json::to_vec_pretty(&report).unwrap()).unwrap();
        let mut manifest = fixture.read_manifest();
        fixture.refresh_report_digest(&mut manifest);
        fixture.write_manifest(&manifest);
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
    }

    #[test]
    fn freeze_rejects_profile_or_track_pooling() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let mut manifest = fixture.read_manifest();
        manifest["adapters"][0]["model_profile"] = json!("tool-native");
        manifest["reports"][0]["model_profile"] = json!("tool-native");
        fixture.write_manifest(&manifest);
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());

        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let mut manifest = fixture.read_manifest();
        manifest["adapters"][0]["track"] = json!("value-flow");
        manifest["reports"][0]["track"] = json!("value-flow");
        fixture.write_manifest(&manifest);
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
    }

    #[test]
    fn freeze_rejects_special_outcome_downgrade() {
        let fixture = FreezeFixture::new("unsupported", json!({"state": "unsupported"}));
        let mut report: Value =
            serde_json::from_slice(&fs::read(&fixture.report).unwrap()).unwrap();
        report["results"][0]["outcome"] = json!("not-reached");
        fs::write(&fixture.report, serde_json::to_vec_pretty(&report).unwrap()).unwrap();
        let mut manifest = fixture.read_manifest();
        manifest["reports"][0]["outcomes"][0]["outcome"] = json!("not-reached");
        fixture.refresh_report_digest(&mut manifest);
        fixture.write_manifest(&manifest);
        assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
    }

    #[test]
    fn release_freeze_rejects_placeholder_analyzer_identity() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let manifest = fixture.read_manifest();
        let mut adapters = BTreeMap::new();
        adapters.insert("test".to_string(), &manifest["adapters"][0]);
        let mut release = manifest["adapters"][0].clone();
        release["tool_version"] = json!("unknown");
        let mut release_adapters = BTreeMap::new();
        release_adapters.insert("test".to_string(), &release);
        assert!(validate_adapter_identities("release", &release_adapters).is_err());
        assert!(validate_adapter_identities("development", &adapters).is_ok());
    }

    #[test]
    fn freeze_rejects_dirty_checkout_state() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        assert!(
            Command::new("git")
                .args(["init", "-q"])
                .current_dir(&fixture.root)
                .status()
                .unwrap()
                .success()
        );
        assert!(
            Command::new("git")
                .args(["add", "."])
                .current_dir(&fixture.root)
                .status()
                .unwrap()
                .success()
        );
        assert!(
            Command::new("git")
                .args([
                    "-c",
                    "user.email=dataflowbench-test@example.invalid",
                    "-c",
                    "user.name=DataFlowBench Test",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "-qm",
                    "fixture"
                ])
                .current_dir(&fixture.root)
                .status()
                .unwrap()
                .success()
        );
        let revision = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();
        assert!(
            validate_freeze_git_state(&fixture.root, &revision, "development", "development")
                .is_ok()
        );
        fs::write(fixture.root.join("dirty.txt"), "dirty\n").unwrap();
        assert!(
            validate_freeze_git_state(&fixture.root, &revision, "development", "development")
                .is_err()
        );
    }

    #[test]
    fn create_freeze_manifest_matches_validated_fixture() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let manifest = build_freeze_manifest(
            &fixture.root,
            &[PathBuf::from("reports/test.json")],
            "development",
            "development",
            &"a".repeat(40),
        )
        .unwrap();
        // The assembler reconstructs the hand-built fixture manifest exactly.
        assert_eq!(manifest, fixture.read_manifest());
        let assembled = fixture.root.join("reports/assembled.json");
        fs::write(&assembled, serde_json::to_vec_pretty(&manifest).unwrap()).unwrap();
        validate_freeze_at(&fixture.root, &assembled, false).unwrap();
    }

    #[test]
    fn create_freeze_rejects_stale_fixture_bytes() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
        let error = build_freeze_manifest(
            &fixture.root,
            &[PathBuf::from("reports/test.json")],
            "development",
            "development",
            &"a".repeat(40),
        )
        .unwrap_err()
        .to_string();
        assert!(error.contains("re-run the adapters"), "{error}");
    }

    #[test]
    fn freeze_git_state_accepts_ancestor_revisions_and_containing_tags() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let run_git = |args: &[&str]| {
            assert!(
                Command::new("git")
                    .args([
                        "-c",
                        "user.email=dataflowbench-test@example.invalid",
                        "-c",
                        "user.name=DataFlowBench Test",
                        "-c",
                        "commit.gpgsign=false",
                        "-c",
                        "tag.gpgsign=false",
                    ])
                    .args(args)
                    .current_dir(&fixture.root)
                    .status()
                    .unwrap()
                    .success()
            );
        };
        run_git(&["init", "-q"]);
        run_git(&["add", "."]);
        run_git(&["commit", "-qm", "evidence"]);
        let evidence = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();
        fs::write(fixture.root.join("later.txt"), "later\n").unwrap();
        run_git(&["add", "."]);
        run_git(&["commit", "-qm", "manifest"]);
        let head = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();

        // The evidence commit validates as an ancestor of HEAD.
        validate_freeze_git_state(&fixture.root, &evidence, "development", "development").unwrap();
        assert!(
            validate_freeze_git_state(&fixture.root, &"b".repeat(40), "development", "development")
                .is_err()
        );

        // A release tag must contain the frozen evidence revision.
        run_git(&["tag", "v0.1.0"]);
        validate_freeze_git_state(&fixture.root, &evidence, "v0.1.0", "release").unwrap();
        run_git(&["tag", "v0.0.1", &evidence]);
        assert!(validate_freeze_git_state(&fixture.root, &head, "v0.0.1", "release").is_err());
    }

    #[test]
    fn generate_results_writes_deterministic_artifacts() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let output = fixture.root.join("generated");
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();

        let results: Value =
            serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
        assert_eq!(results["schema_version"], 1);
        let manifest_bytes = fs::read(&fixture.manifest).unwrap();
        assert_eq!(
            results["manifest"]["sha256"],
            json!(format!("{:x}", Sha256::digest(&manifest_bytes)))
        );
        let scorecard = &results["scorecards"][0];
        assert_eq!(
            scorecard["id"],
            json!("test-taint-taint-benchmark-controlled")
        );
        let tier = &scorecard["languages"][0]["score_tiers"][0];
        assert_eq!(scorecard["languages"][0]["language"], json!("c"));
        assert_eq!(tier["score_tier"], json!("core"));
        assert_eq!(tier["outcome_coverage"]["reached"], json!(1));
        assert_eq!(tier["outcome_coverage"]["total"], json!(1));
        assert_eq!(tier["cases"][0]["classification"], json!("true-positive"));
        let dimension = &tier["semantic_dimensions"][0];
        assert_eq!(dimension["name"], json!("local-flow"));
        assert_eq!(dimension["true_positive_rate"]["numerator"], json!(1));
        assert_eq!(dimension["true_positive_rate"]["percent"], json!("100.0"));
        assert_eq!(dimension["false_positive_rate"], Value::Null);
        assert_eq!(
            dimension["template_macro"]["true_positive_rate_percent"],
            json!("100.0")
        );
        assert_eq!(
            tier["dimension_macro"]["false_positive_rate_percent"],
            Value::Null
        );

        let index = fs::read_to_string(output.join("index.md")).unwrap();
        assert!(index.contains("test-taint-taint-benchmark-controlled"));
        let page =
            fs::read_to_string(output.join("scorecards/test-taint-taint-benchmark-controlled.md"))
                .unwrap();
        assert!(page.contains("`dfb-taint-test`"));
        assert!(page.contains("true-positive"));
        assert!(page.contains("reports/raw/test.json"));

        // Repeated generation from identical evidence is byte-stable.
        let before = fs::read(output.join("results.json")).unwrap();
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        assert_eq!(before, fs::read(output.join("results.json")).unwrap());
    }

    #[test]
    fn generate_results_classifies_incomplete_outcomes_separately() {
        let fixture = FreezeFixture::new("inconclusive", json!({"state": "inconclusive"}));
        let output = fixture.root.join("generated");
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        let results: Value =
            serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
        let tier = &results["scorecards"][0]["languages"][0]["score_tiers"][0];
        assert_eq!(tier["cases"][0]["classification"], json!("inconclusive"));
        let dimension = &tier["semantic_dimensions"][0];
        assert_eq!(dimension["counts"]["inconclusive"], json!(1));
        assert_eq!(dimension["counts"]["false_negatives"], json!(0));
        // No definitive positive result: the rate stays null, never zero.
        assert_eq!(dimension["true_positive_rate"], Value::Null);
        assert_eq!(
            dimension["template_macro"]["true_positive_rate_percent"],
            Value::Null
        );
    }

    #[test]
    fn generate_results_check_detects_current_stale_missing_and_extra() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let output = fixture.root.join("generated");
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("missing artifact")
        );
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, true).unwrap();

        fs::write(output.join("index.md"), "stale\n").unwrap();
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("stale artifact: index.md")
        );

        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        fs::write(output.join("extra.md"), "extra\n").unwrap();
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("unexpected artifact: extra.md")
        );
    }

    #[test]
    fn generate_results_requires_a_valid_freeze() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
        let output = fixture.root.join("generated");
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).is_err()
        );
        assert!(!output.exists());
    }

    #[test]
    fn scorecard_identifiers_disambiguate_repeated_populations() {
        let mut used = BTreeMap::new();
        let report = json!({
            "track": "taint",
            "dimension": "taint",
            "model_profile": "benchmark-controlled"
        });
        assert_eq!(
            scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
            "test-adapter-taint-taint-benchmark-controlled"
        );
        assert_eq!(
            scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
            "test-adapter-taint-taint-benchmark-controlled-2"
        );
    }
}
