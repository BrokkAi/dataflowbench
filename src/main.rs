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
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Commands::Validate => validate_cases(),
        Commands::ValidateReports => validate_reports(),
        Commands::ValidateFreeze { manifest } => validate_freeze(&manifest),
        Commands::RunBifrostSmoke { bifrost } => run_bifrost_smoke(&bifrost),
        Commands::RunBifrostPythonKernel { bifrost } => run_bifrost_python_kernel(&bifrost),
        Commands::RunCodeqlJavaKernel {
            codeql,
            codeql_packs,
        } => run_codeql_java_kernel(&codeql, codeql_packs.as_deref()),
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
    for path in &paths {
        let report: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        validate_value(&compiled, &report, path)?;
        for result in report["results"].as_array().expect("schema validated") {
            let raw = result["raw_output"].as_str().expect("schema validated");
            if !Path::new(raw).is_file() {
                bail!("{}: retained raw output {raw:?} is absent", path.display());
            }
        }
    }
    println!("validated {} reports", paths.len());
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
    if head != revision {
        bail!("freeze revision {revision} does not match checkout HEAD {head}");
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
        if tag_revision != revision {
            bail!("release {release} does not point at freeze revision {revision}");
        }
    }
    Ok(())
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
        let model = &case["tool_model_references"]["codeql"];
        if !model.is_object() {
            continue;
        }
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

fn run_codeql_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
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
    let classes = workspace.join("classes");
    fs::create_dir_all(&classes)?;
    let fixture_names = case["fixture_files"]
        .as_array()
        .expect("schema validated")
        .iter()
        .map(|fixture| fixture.as_str().expect("schema validated"))
        .collect::<Vec<_>>();
    let build_command = format!("javac -d classes {}", fixture_names.join(" "));
    let create = Command::new(binary)
        .arg("database")
        .arg("create")
        .arg(&database)
        .arg("--language=java")
        .arg(format!("--source-root={}", workspace.display()))
        .arg(format!("--command={build_command}"))
        .arg("--overwrite")
        .output()
        .context("create CodeQL database")?;
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
    let analyzed = analyze.output().context("analyze CodeQL database")?;
    if !analyzed.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-analyze", &analyzed)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(error);
    }
    let sarif: Value = serde_json::from_str(&fs::read_to_string(&raw_path)?)?;
    let execution_errors = sarif_execution_errors(&sarif);
    if !execution_errors.is_empty() {
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(("runner-error", execution_errors, raw_path));
    }
    let result_count = sarif_result_count(&sarif);
    let diagnostics = sarif_messages(&sarif);
    let outcome = if result_count == 0 {
        "not-reached"
    } else {
        "reached"
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
    fn checked_reports_keep_separate_fixture_revisions() {
        let bifrost: Value =
            serde_json::from_str(&fs::read_to_string("reports/bifrost-smoke.json").unwrap())
                .unwrap();
        let python: Value = serde_json::from_str(
            &fs::read_to_string("reports/bifrost-python-kernel.json").unwrap(),
        )
        .unwrap();
        let codeql: Value =
            serde_json::from_str(&fs::read_to_string("reports/codeql-java-kernel.json").unwrap())
                .unwrap();
        let revisions = [
            &bifrost["fixture_revision"],
            &python["fixture_revision"],
            &codeql["fixture_revision"],
        ]
        .into_iter()
        .map(|revision| revision.as_str().unwrap())
        .collect::<BTreeSet<_>>();
        assert_eq!(revisions.len(), 3);
        assert!(revisions.iter().all(|revision| {
            revision
                .strip_prefix("sha256:")
                .is_some_and(|digest| digest.len() == 64)
        }));
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
}
