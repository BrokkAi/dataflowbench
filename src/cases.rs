//! Canonical case loading and the case contract: schema validation, the
//! balanced-core-pair rule, marker placement, and the shared population
//! checks every adapter's selection is revalidated against.

use crate::modeling::validate_modeling_cases;
use crate::native::{validate_native_cases, validate_profile_disjoint_populations};
use crate::real_project::validate_real_project_slice;
use crate::templates::CHALLENGE_ROLLOUT;
use anyhow::{Context, Result, bail};
use jsonschema::JSONSchema;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf};
use walkdir::WalkDir;

pub(crate) type CorePairKey<'a> = (&'a str, &'a str, &'a str, &'a str);
pub(crate) type CorePairCases<'a> = Vec<(&'a Path, &'a str)>;

pub(crate) fn schema(path: &str) -> Result<JSONSchema> {
    let value: Value =
        serde_json::from_str(&fs::read_to_string(path).with_context(|| format!("read {path}"))?)?;
    // jsonschema 0.18 retains schema references for the compiled validator.
    // These two small, process-lifetime schemas are loaded once per command.
    JSONSchema::compile(Box::leak(Box::new(value))).context("compile schema")
}

pub(crate) fn case_paths() -> Vec<PathBuf> {
    let mut paths: Vec<_> = WalkDir::new("cases")
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file() && entry.file_name() == "case.json")
        .map(|entry| entry.into_path())
        .collect();
    paths.sort();
    paths
}

pub(crate) fn validate_value(compiled: &JSONSchema, value: &Value, path: &Path) -> Result<()> {
    if let Err(errors) = compiled.validate(value) {
        let details = errors
            .map(|error| error.to_string())
            .collect::<Vec<_>>()
            .join("; ");
        bail!("{}: {details}", path.display());
    }
    Ok(())
}

pub(crate) fn validate_cases() -> Result<()> {
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
    // Every language is checked against its own row in the challenge rollout
    // table, which is the one place a denominator is stated. Before this table
    // existed the ECMA kernels were checked against Java's template set
    // directly; that comparison would have made a wave PR's correctness depend
    // on which of the three wave-1 languages happened to land first, so each
    // language now answers to the preregistered set instead of to a sibling.
    for row in &CHALLENGE_ROLLOUT {
        validate_scored_kernel_balance(
            &cases,
            row.language,
            row.display,
            &row.expected_templates(),
        )?;
    }
    // The modeling matrix is its own tier and its own denominator: every
    // language with a modeling row is checked against its required set, and a
    // language without one contributes nothing.
    validate_modeling_cases(&cases)?;
    // The tool-native profile shares that tier and is separated from it by
    // profile alone, so the population check and the disjointness check are two
    // obligations rather than one; both run over the shipped native rows.
    validate_native_cases(&cases)?;
    validate_profile_disjoint_populations(&cases)?;
    // The real-project slice is preregistered evidence, not a case population:
    // it has no fixtures yet and contributes to no denominator. It is checked
    // here because this is the command CI already runs over every committed
    // JSON fixture, and a seeded draw that stops being reproducible should fail
    // the same build that a malformed case fails.
    let pins = validate_real_project_slice()?;
    println!("validated {} cases", paths.len());
    println!("validated {pins} real-project pin records");
    Ok(())
}

pub(crate) fn validate_case_contract(path: &Path, value: &Value) -> Result<()> {
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

pub(crate) fn validate_balanced_core_pairs(cases: &[(PathBuf, Value)]) -> Result<()> {
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

/// A ported kernel must carry its scored template identities unchanged, with no
/// template renamed, split, or silently dropped because the language spells a
/// construct differently. The expected set is the language's core denominator
/// from its `CHALLENGE_ROLLOUT` row: the classic set from
/// docs/applicability-matrix.md — sixteen templates for most languages, fifteen
/// for C and Rust, whose inapplicable exception-catch cell reduces only their
/// own denominators — plus that language's applicable challenge templates once
/// its row is rolled out. A language with no core cases yet is simply not a
/// kernel population.
pub(crate) fn validate_scored_kernel_balance(
    cases: &[(PathBuf, Value)],
    language: &str,
    display: &str,
    expected_templates: &[&str],
) -> Result<()> {
    let kernel_templates = core_templates_for_language(cases, language);
    if kernel_templates.is_empty() {
        return Ok(());
    }
    let expected = expected_templates.iter().copied().collect::<BTreeSet<_>>();
    if kernel_templates != expected {
        let missing = expected
            .difference(&kernel_templates)
            .copied()
            .collect::<Vec<_>>();
        let unexpected = kernel_templates
            .difference(&expected)
            .copied()
            .collect::<Vec<_>>();
        bail!(
            "{display} propagation kernel must preserve the scored template IDs; missing {missing:?}, unexpected {unexpected:?}"
        );
    }
    Ok(())
}

pub(crate) fn core_templates_for_language<'a>(
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

pub(crate) fn validate_fixture_files(path: &Path, value: &Value) -> Result<()> {
    let parent = path.parent().expect("case path has parent");
    for fixture in value["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        if !parent.join(fixture).is_file() {
            bail!("{}: fixture {fixture:?} does not exist", path.display());
        }
    }
    Ok(())
}

pub(crate) fn validate_markers(path: &Path, value: &Value) -> Result<()> {
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

/// Every case file in the repository, parsed once and shared across the
/// per-report configuration derivations that select from it.
pub(crate) type LoadedCases = Vec<(PathBuf, Value)>;

pub(crate) fn cached_case_scan(case_scan: &mut Option<LoadedCases>) -> Result<&LoadedCases> {
    if case_scan.is_none() {
        let mut cases = Vec::new();
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)
                .with_context(|| format!("parse case {}", path.display()))?;
            cases.push((path, case));
        }
        *case_scan = Some(cases);
    }
    Ok(case_scan.as_ref().expect("filled above"))
}

pub(crate) fn java_core_case(case: &Value) -> bool {
    case["language"] == "java" && case["track"] == "taint" && case["score_tier"] == "core"
}

pub(crate) fn javascript_core_case(case: &Value) -> bool {
    case["language"] == "javascript" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A PHP core assertion. As with the Kotlin, C#, Go, and C-family kernels, the
/// direct-propagation pair predates this kernel and is frozen in the published
/// v0.2.0 and v0.3.0 evidence naming the cross-language breadth policy, so that
/// policy reference is accepted alongside the language-qualified one.
pub(crate) fn php_core_case(case: &Value) -> bool {
    case["language"] == "php" && case["track"] == "taint" && case["score_tier"] == "core"
}

pub(crate) fn go_core_case(case: &Value) -> bool {
    case["language"] == "go" && case["track"] == "taint" && case["score_tier"] == "core"
}

pub(crate) fn ruby_core_case(case: &Value) -> bool {
    case["language"] == "ruby" && case["track"] == "taint" && case["score_tier"] == "core"
}

pub(crate) fn csharp_core_case(case: &Value) -> bool {
    case["language"] == "csharp" && case["track"] == "taint" && case["score_tier"] == "core"
}

pub(crate) fn kotlin_core_case(case: &Value) -> bool {
    case["language"] == "kotlin" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A Scala assertion the Bifrost kernel run owns. Scala is selected the way
/// Kotlin is — by language, track, and score tier — because its
/// direct-propagation pair is frozen in the v0.2.0 evidence naming the
/// cross-language breadth policy, and the run pins the language-qualified
/// policy for the whole population instead of reading it from each case. No
/// CodeQL or Joern counterpart exists: neither pinned tool can extract Scala
/// source, which is coverage recorded in docs/scala-kernel.md, not a negative.
pub(crate) fn scala_core_case(case: &Value) -> bool {
    case["language"] == "scala" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// Assert that a selected language kernel is exactly that language's core
/// denominator under one model profile, balanced one positive to one negative.
/// The denominator is a parameter rather than a constant because
/// docs/applicability-matrix.md reduces C and Rust to fifteen classic
/// templates, and docs/challenge-tier.md expands a language's set as its
/// challenge wave lands; an inapplicable cell reduces only its own language's
/// denominator.
pub(crate) fn validate_kernel_population_with(
    cases: &[(PathBuf, Value)],
    label: &str,
    expected_templates: &[&str],
) -> Result<()> {
    let expected_case_count = 2 * expected_templates.len();
    if cases.len() != expected_case_count {
        bail!(
            "{label} must select exactly {expected_case_count} assertions; found {}",
            cases.len()
        );
    }
    let mut pairs: BTreeMap<&str, (usize, usize)> = BTreeMap::new();
    let mut model_profiles = BTreeSet::new();
    for (path, case) in cases {
        let template = case["template_id"]
            .as_str()
            .with_context(|| format!("{} lacks template_id", path.display()))?;
        model_profiles.insert(
            case["model_profile"]
                .as_str()
                .with_context(|| format!("{} lacks model_profile", path.display()))?,
        );
        let entry = pairs.entry(template).or_default();
        match case["polarity"].as_str() {
            Some("positive") => entry.0 += 1,
            Some("negative") => entry.1 += 1,
            Some(other) => bail!("{} has unsupported polarity {other:?}", path.display()),
            None => bail!("{} lacks polarity", path.display()),
        }
    }
    let expected = expected_templates.iter().copied().collect::<BTreeSet<_>>();
    let actual = pairs.keys().copied().collect::<BTreeSet<_>>();
    if actual != expected {
        let missing = expected.difference(&actual).copied().collect::<Vec<_>>();
        let unexpected = actual.difference(&expected).copied().collect::<Vec<_>>();
        bail!("{label} template set mismatch (missing={missing:?}, unexpected={unexpected:?})");
    }
    if pairs
        .values()
        .any(|(positive, negative)| *positive != 1 || *negative != 1)
    {
        bail!("{label} requires one positive and one negative per template");
    }
    if model_profiles.len() != 1 {
        bail!("{label} must use one model profile across all {expected_case_count} cases");
    }
    Ok(())
}

pub(crate) fn fixture_revision() -> Result<String> {
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
