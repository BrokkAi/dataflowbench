//! The `freeze/v1` immutable evidence manifest: building one, and validating
//! a checkout against one. See docs/freeze.md — a correction is a new freeze,
//! never a rewrite.

use crate::adapters::bifrost::bifrost_runner_error_reason;
use crate::cases::validate_value;
use crate::evidence::sarif_execution_errors;
use anyhow::{Context, Result, bail};
use jsonschema::JSONSchema;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command,
};
use walkdir::WalkDir;

pub(crate) fn validate_freeze(manifest: &Path) -> Result<()> {
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
pub(crate) fn validate_freeze_at(root: &Path, manifest_path: &Path, check_git: bool) -> Result<()> {
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

pub(crate) fn compile_schema(path: &Path) -> Result<JSONSchema> {
    let value: Value = serde_json::from_str(
        &fs::read_to_string(path).with_context(|| format!("read schema {}", path.display()))?,
    )?;
    JSONSchema::compile(Box::leak(Box::new(value))).context("compile schema")
}

pub(crate) fn required_string<'a>(
    object: &'a Value,
    field: &str,
    context: &str,
) -> Result<&'a str> {
    object[field]
        .as_str()
        .filter(|value| !value.is_empty())
        .with_context(|| format!("{context} requires non-empty {field}"))
}

pub(crate) fn repository_root() -> Result<PathBuf> {
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

pub(crate) fn validate_freeze_git_state(
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

pub(crate) fn git_is_ancestor(root: &Path, ancestor: &str, descendant: &str) -> Result<bool> {
    let output = Command::new("git")
        .current_dir(root)
        .args(["merge-base", "--is-ancestor", ancestor, descendant])
        .output()
        .context("run git merge-base --is-ancestor")?;
    match output.status.code() {
        Some(0) => Ok(true),
        Some(1) => Ok(false),
        // A revision that resolves nowhere is almost always one that lived
        // only on a pull-request branch: `main` is squash-merged, so the
        // branch commit is discarded and the manifest is left naming a commit
        // no checkout of `main` can resolve. `create-freeze` refuses to record
        // such a revision, so reaching here means the manifest was written by
        // an older build or edited by hand.
        _ => bail!(
            "cannot resolve freeze revision {ancestor} in this checkout; \
             a revision recorded from a pull-request branch does not survive \
             the squash merge, so re-create the freeze from a checkout of \
             `main` as docs/freeze.md describes"
        ),
    }
}

/// A freeze records the commit its evidence lives at, and every later
/// validation resolves that commit from the checkout. `main` is squash-merged,
/// which replaces a pull-request branch with a single new commit and discards
/// the branch's own commits, so a revision taken from a branch stops resolving
/// the moment the pull request lands. The revision must therefore already be
/// reachable from `main` when the freeze is created: the evidence merges
/// first, and the freeze is assembled from a clean checkout of the merged
/// `main`. Refusing at creation time is what makes this catchable — on the
/// pull request itself the branch commit still resolves, so validation only
/// discovers the loss after the merge, on `main`.
pub(crate) fn require_merged_freeze_revision(root: &Path, revision: &str) -> Result<()> {
    // No integration branch to compare against (a mirror without `main`, or a
    // repository whose first commits predate it): the ancestry rule still
    // holds at validation, so record the revision rather than block the freeze.
    let Some(main) = resolve_integration_branch(root)? else {
        return Ok(());
    };
    if main != revision && !git_is_ancestor(root, revision, &main)? {
        bail!(
            "freeze revision {revision} is not reachable from main ({main}); \
             `main` is squash-merged, so a commit that exists only on a \
             pull-request branch is discarded at merge time and the recorded \
             revision becomes unresolvable. Merge the evidence first, then run \
             create-freeze from a clean checkout of the merged `main`; never \
             bundle the evidence and the manifest into one pull request. See \
             docs/freeze.md."
        );
    }
    Ok(())
}

/// Resolve the integration branch a freeze revision must be reachable from,
/// preferring the local `main` so an out-of-date remote ref cannot reject a
/// revision that is genuinely merged.
pub(crate) fn resolve_integration_branch(root: &Path) -> Result<Option<String>> {
    for reference in ["refs/heads/main", "refs/remotes/origin/main"] {
        let output = Command::new("git")
            .current_dir(root)
            .args([
                "rev-parse",
                "--verify",
                "--quiet",
                &format!("{reference}^{{commit}}"),
            ])
            .output()
            .context("resolve integration branch")?;
        if output.status.success() {
            return Ok(Some(
                String::from_utf8_lossy(&output.stdout).trim().to_string(),
            ));
        }
    }
    Ok(None)
}

pub(crate) fn git_output<const N: usize>(root: &Path, args: [&str; N]) -> Result<String> {
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

pub(crate) fn repository_path(root: &Path, relative: &str) -> Result<PathBuf> {
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

pub(crate) fn require_digest(expected: &str, bytes: &[u8], context: &str) -> Result<()> {
    let actual = format!("{:x}", Sha256::digest(bytes));
    if expected != actual {
        bail!("{context} SHA-256 digest mismatch: expected {expected}, got {actual}");
    }
    Ok(())
}

pub(crate) fn validate_fixture_digests(
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

pub(crate) fn fixture_revision_for_manifest_cases(
    root: &Path,
    cases: &[(String, PathBuf)],
) -> Result<String> {
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

pub(crate) fn require_set_matches(
    value: &Value,
    expected: &BTreeSet<String>,
    label: &str,
) -> Result<()> {
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

pub(crate) fn validate_exclusions(claim: &Value, cases: &BTreeMap<String, PathBuf>) -> Result<()> {
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

pub(crate) fn validate_adapter_identities(
    scope: &str,
    adapters: &BTreeMap<String, &Value>,
) -> Result<()> {
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

pub(crate) struct FreezeReportValidation<'a> {
    pub(crate) root: &'a Path,
    pub(crate) adapters: &'a BTreeMap<String, &'a Value>,
    pub(crate) cases: &'a BTreeMap<String, PathBuf>,
    pub(crate) result_schema: &'a JSONSchema,
    pub(crate) result_schema_version: u64,
    pub(crate) fixture_revision: &'a str,
    pub(crate) report_paths: &'a mut BTreeSet<String>,
}

pub(crate) fn validate_frozen_report(
    context: &mut FreezeReportValidation<'_>,
    frozen: &Value,
) -> Result<()> {
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

pub(crate) fn validate_frozen_outcomes(
    frozen: &Value,
    results: &[Value],
    report_path: &str,
) -> Result<()> {
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

pub(crate) fn validate_raw_evidence(
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
        let documents = parse_raw_evidence_documents(&raw_bytes)
            .with_context(|| format!("parse raw evidence {raw_path}"))?;
        let outcome = result["outcome"].as_str().expect("result schema validated");
        if let Some(declared) = documents.iter().find_map(raw_special_outcome)
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

/// Raw evidence is the analyzer's own output retained verbatim, and not every
/// analyzer emits a single JSON document: Pysa's taint output is JSON Lines,
/// one record per line. The special-outcome audit must read whichever shape
/// the file has, so a file that is not one document is decoded as a stream of
/// documents; content that is neither is still an error.
pub(crate) fn parse_raw_evidence_documents(raw_bytes: &[u8]) -> Result<Vec<Value>> {
    if let Ok(single) = serde_json::from_slice::<Value>(raw_bytes) {
        return Ok(vec![single]);
    }
    let documents = serde_json::Deserializer::from_slice(raw_bytes)
        .into_iter::<Value>()
        .collect::<std::result::Result<Vec<_>, _>>()?;
    if documents.is_empty() {
        bail!("raw evidence holds no JSON documents");
    }
    Ok(documents)
}

pub(crate) fn raw_special_outcome(raw: &Value) -> Option<&'static str> {
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
    // Semgrep's own `--json` document carries engine, rule, and parse failures
    // in a top-level `errors` array beside a `results` array that a failed scan
    // still emits empty. No frozen result may read that empty list as a clean
    // negative.
    if raw["results"].is_array()
        && raw["errors"]
            .as_array()
            .is_some_and(|errors| !errors.is_empty())
    {
        return Some("runner-error");
    }
    if bifrost_runner_error_reason(raw).is_some() {
        return Some("runner-error");
    }
    if !sarif_execution_errors(raw).is_empty() {
        return Some("runner-error");
    }
    None
}

pub(crate) fn create_freeze(
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
    require_merged_freeze_revision(root.as_path(), &revision)?;
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
pub(crate) fn build_freeze_manifest(
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
