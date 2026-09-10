//! The real-project confirmation slice: a preregistered, seeded draw over a
//! retained frame of security advisories, and the pin records that are its
//! leaves.
//!
//! This is preregistered evidence, not a case population. It has no fixtures
//! and contributes to no denominator, and nothing here reads a case, a report,
//! or any analyzer evidence — at preregistration time none of that exists for
//! these repositories, and once they are run it still must not reach back into
//! selection. See docs/real-project-preregistration.md.

use crate::cases::{schema, validate_value};
use anyhow::{Context, Result, bail};
use jsonschema::JSONSchema;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};
use walkdir::WalkDir;

/// The real-project confirmation slice is preregistered, not curated: the draw
/// record in `corpus/real-project/draw.json` replays a seeded walk over a
/// retained frame, and every pin record is a leaf of that walk. This validator
/// exists because the honesty of the slice is otherwise unfalsifiable. Anyone
/// can assert that analyzer outcomes did not influence selection; recomputing
/// each candidate's draw key from the declared seed, and refusing a walk whose
/// order is not the one the seed produces, is what makes the assertion
/// checkable. A repository swapped in by hand lands at the wrong draw key and
/// the command fails.
///
/// The checks are deliberately structural. Nothing here reads a case, a report,
/// or any analyzer evidence, because at preregistration time none of that
/// exists for these repositories, and after #20 runs them it still must not
/// reach back into selection.
pub(crate) const REAL_PROJECT_DIR: &str = "corpus/real-project";
pub(crate) const REAL_PROJECT_FRAME: &str = "corpus/real-project/frame.json";
pub(crate) const REAL_PROJECT_DRAW: &str = "corpus/real-project/draw.json";
pub(crate) const REAL_PROJECT_PINS_DIR: &str = "corpus/real-project/pins";
pub(crate) const REAL_PROJECT_REVIEW: &str = "corpus/real-project/review.json";
pub(crate) const REAL_PROJECT_REVIEW_SCHEMA: &str = "schemas/real-project-review.schema.json";
pub(crate) const REAL_PROJECT_R2_PROTOCOL: &str = "corpus/real-project/r2/protocol.json";
pub(crate) const REAL_PROJECT_R2_PROTOCOL_SCHEMA: &str =
    "schemas/real-project-r2-protocol.schema.json";
pub(crate) const REAL_PROJECT_R2_SNAPSHOT: &str = "corpus/real-project/r2/snapshot/manifest.json";
pub(crate) const REAL_PROJECT_R2_SNAPSHOT_SCHEMA: &str =
    "schemas/real-project-r2-snapshot.schema.json";
pub(crate) const REAL_PROJECT_R2_FRAME: &str = "corpus/real-project/r2/frame.json";
pub(crate) const REAL_PROJECT_R2_FRAME_SCHEMA: &str = "schemas/real-project-r2-frame.schema.json";
pub(crate) const REAL_PROJECT_R2_E5_INVENTORY: &str = "corpus/real-project/r2/e5-inventory.json";
pub(crate) const REAL_PROJECT_R2_E5_INVENTORY_SCHEMA: &str =
    "schemas/real-project-r2-e5-inventory.schema.json";
pub(crate) const REAL_PROJECT_R2_ELIGIBILITY: &str = "corpus/real-project/r2/eligibility.json";
pub(crate) const REAL_PROJECT_R2_ELIGIBILITY_SCHEMA: &str =
    "schemas/real-project-r2-eligibility.schema.json";
pub(crate) const REAL_PROJECT_R2_DRAW: &str = "corpus/real-project/r2/draw.json";
pub(crate) const REAL_PROJECT_R2_DRAW_SCHEMA: &str = "schemas/real-project-r2-draw.schema.json";
pub(crate) const REAL_PROJECT_R2_EVIDENCE_SCHEMA: &str =
    "schemas/real-project-r2-evidence-manifest.schema.json";

/// The licences a drawn repository may carry, per eligibility criterion E2 of
/// docs/real-project-preregistration.md. The list is OSI-approved identifiers
/// only; `NOASSERTION` and an absent identifier are exclusions, not licences.
pub(crate) const REAL_PROJECT_LICENSES: [&str; 15] = [
    "AGPL-3.0",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSL-1.0",
    "EPL-2.0",
    "GPL-2.0",
    "GPL-3.0",
    "ISC",
    "LGPL-2.1",
    "LGPL-3.0",
    "MIT",
    "MPL-2.0",
    "Unlicense",
    "Zlib",
];

pub(crate) fn real_project_draw_key(seed: &str, ghsa_id: &str) -> String {
    format!(
        "{:x}",
        Sha256::digest(format!("{seed}\n{ghsa_id}").as_bytes())
    )
}

pub(crate) fn real_project_pin_paths() -> Result<Vec<PathBuf>> {
    let mut paths: Vec<_> = fs::read_dir(REAL_PROJECT_PINS_DIR)
        .with_context(|| format!("read {REAL_PROJECT_PINS_DIR}"))?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file() && path.extension().is_some_and(|ext| ext == "json"))
        .collect();
    paths.sort();
    Ok(paths)
}

pub(crate) fn validate_real_project_slice() -> Result<usize> {
    if !Path::new(REAL_PROJECT_DIR).is_dir() {
        return Ok(0);
    }
    let frame_bytes =
        fs::read(REAL_PROJECT_FRAME).with_context(|| format!("read {REAL_PROJECT_FRAME}"))?;
    let frame_sha256 = format!("{:x}", Sha256::digest(&frame_bytes));
    let frame: Value = serde_json::from_slice(&frame_bytes)?;
    let candidates = frame["candidates"]
        .as_array()
        .with_context(|| format!("{REAL_PROJECT_FRAME}: candidates must be an array"))?;
    if candidates.is_empty() {
        bail!("{REAL_PROJECT_FRAME}: the retained frame is empty");
    }

    let draw: Value = serde_json::from_str(
        &fs::read_to_string(REAL_PROJECT_DRAW)
            .with_context(|| format!("read {REAL_PROJECT_DRAW}"))?,
    )?;
    let draw_schema = schema("schemas/real-project-draw.schema.json")?;
    validate_value(&draw_schema, &draw, Path::new(REAL_PROJECT_DRAW))?;

    if draw["frame"]["path"] != json!(REAL_PROJECT_FRAME) {
        bail!("{REAL_PROJECT_DRAW}: frame.path must be {REAL_PROJECT_FRAME}");
    }
    if draw["frame"]["sha256"] != json!(frame_sha256) {
        bail!(
            "{REAL_PROJECT_DRAW}: frame digest drifted; the record binds {} and {REAL_PROJECT_FRAME} now hashes to {frame_sha256}",
            draw["frame"]["sha256"]
        );
    }
    let seed = draw["seed"].as_str().expect("schema validated");
    let target = draw["target_per_stratum"]
        .as_u64()
        .expect("schema validated") as usize;
    let criteria = draw["criteria"].as_object().expect("schema validated");

    // Replay the seeded ordering from the frame. This is the check the rest of
    // the slice hangs off: a walk that does not reproduce is a walk that was
    // reordered after the fact.
    let mut selected: BTreeMap<String, (String, String, usize)> = BTreeMap::new();
    for (stratum, rows) in draw["walk"].as_object().expect("schema validated") {
        let mut ordered: Vec<(String, &Value)> = candidates
            .iter()
            .filter(|candidate| candidate["stratum"].as_str() == Some(stratum.as_str()))
            .map(|candidate| {
                let ghsa = candidate["ghsa_id"].as_str().unwrap_or_default();
                (real_project_draw_key(seed, ghsa), candidate)
            })
            .collect();
        ordered.sort_by(|left, right| {
            left.0
                .cmp(&right.0)
                .then_with(|| left.1["ghsa_id"].as_str().cmp(&right.1["ghsa_id"].as_str()))
        });
        if ordered.is_empty() {
            bail!("{REAL_PROJECT_DRAW}: stratum {stratum} has no candidates in the retained frame");
        }
        let rows = rows.as_array().expect("schema validated");
        if rows.len() > ordered.len() {
            bail!(
                "{REAL_PROJECT_DRAW}: stratum {stratum} walks {} candidates but the frame holds {}",
                rows.len(),
                ordered.len()
            );
        }
        let mut chosen = 0usize;
        for (index, row) in rows.iter().enumerate() {
            let (expected_key, candidate) = &ordered[index];
            let ghsa = row["ghsa_id"].as_str().expect("schema validated");
            if row["draw_position"].as_u64() != Some(index as u64 + 1) {
                bail!(
                    "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} declares draw position {} at walk index {}",
                    row["draw_position"],
                    index + 1
                );
            }
            if candidate["ghsa_id"].as_str() != Some(ghsa) {
                bail!(
                    "{REAL_PROJECT_DRAW}: stratum {stratum} position {} is {ghsa}, but the seeded ordering puts {} there",
                    index + 1,
                    candidate["ghsa_id"]
                );
            }
            if row["draw_key"].as_str() != Some(expected_key.as_str()) {
                bail!(
                    "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} declares draw key {} but seed {seed} yields {expected_key}",
                    row["draw_key"]
                );
            }
            if row["repository"].as_str() != candidate["repository"].as_str() {
                bail!(
                    "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} names repository {} but the frame records {}",
                    row["repository"],
                    candidate["repository"]
                );
            }
            let exclusions = row["exclusions"].as_array().expect("schema validated");
            match row["disposition"].as_str().expect("schema validated") {
                "selected" => {
                    if !exclusions.is_empty() {
                        bail!(
                            "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} is selected and still cites {} exclusions",
                            exclusions.len()
                        );
                    }
                    chosen += 1;
                    selected.insert(
                        ghsa.to_string(),
                        (
                            stratum.clone(),
                            row["repository"].as_str().unwrap_or_default().to_string(),
                            index + 1,
                        ),
                    );
                }
                _ => {
                    if exclusions.is_empty() {
                        bail!(
                            "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} is excluded without citing a criterion"
                        );
                    }
                    for exclusion in exclusions {
                        let criterion = exclusion["criterion"].as_str().expect("schema validated");
                        if !criteria.contains_key(criterion) {
                            bail!(
                                "{REAL_PROJECT_DRAW}: stratum {stratum} entry {ghsa} cites undeclared criterion {criterion}"
                            );
                        }
                    }
                }
            }
        }
        // A walk that continues past its last selection would leave candidates
        // dispositioned for no reason, and one that stops short of `target`
        // would be a slice smaller than the preregistered size.
        if rows.last().and_then(|row| row["disposition"].as_str()) != Some("selected") {
            bail!("{REAL_PROJECT_DRAW}: stratum {stratum} must end at its last selected candidate");
        }
        if chosen != target {
            bail!(
                "{REAL_PROJECT_DRAW}: stratum {stratum} selected {chosen} repositories; the preregistered target is {target}"
            );
        }
    }

    let pin_schema = schema("schemas/real-project-pin.schema.json")?;
    let paths = real_project_pin_paths()?;
    if paths.len() != selected.len() {
        bail!(
            "{REAL_PROJECT_PINS_DIR}: holds {} pin records for {} selected repositories",
            paths.len(),
            selected.len()
        );
    }
    let mut pin_ids = BTreeSet::new();
    let mut repositories = BTreeSet::new();
    for path in &paths {
        let pin: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        validate_value(&pin_schema, &pin, path)?;
        let display = path.display();
        let ghsa = pin["advisory"]["ghsa_id"]
            .as_str()
            .expect("schema validated");
        let Some((stratum, repository, position)) = selected.get(ghsa) else {
            bail!("{display}: advisory {ghsa} is not a selected candidate in {REAL_PROJECT_DRAW}");
        };
        if pin["stratum"].as_str() != Some(stratum.as_str()) {
            bail!("{display}: advisory {ghsa} was drawn from stratum {stratum}");
        }
        if pin["language"].as_str() != Some(stratum.as_str()) {
            bail!(
                "{display}: language must equal the stratum {stratum}; eligibility criterion E1 admits no other repository"
            );
        }
        let owner = pin["repository"]["owner"]
            .as_str()
            .expect("schema validated");
        let name = pin["repository"]["name"]
            .as_str()
            .expect("schema validated");
        let slug = format!("{owner}/{name}");
        if slug != *repository {
            bail!("{display}: names {slug}, but the draw selected {repository}");
        }
        if pin["repository"]["url"].as_str() != Some(format!("https://github.com/{slug}").as_str())
        {
            bail!("{display}: repository url must be https://github.com/{slug}");
        }
        if !pin_ids.insert(
            pin["pin_id"]
                .as_str()
                .expect("schema validated")
                .to_string(),
        ) {
            bail!("{display}: duplicate pin_id {}", pin["pin_id"]);
        }
        if !repositories.insert(slug.clone()) {
            bail!(
                "{display}: {slug} already carries a pin; eligibility criterion E8 admits one advisory per repository"
            );
        }
        if pin["selection"]["seed"].as_str() != Some(seed) {
            bail!("{display}: selection.seed must be the draw's seed {seed}");
        }
        let expected_key = real_project_draw_key(seed, ghsa);
        if pin["selection"]["draw_key"].as_str() != Some(expected_key.as_str()) {
            bail!(
                "{display}: draw key {} does not match {expected_key} recomputed from the seed",
                pin["selection"]["draw_key"]
            );
        }
        if pin["selection"]["draw_position"].as_u64() != Some(*position as u64) {
            bail!(
                "{display}: draw position {} contradicts position {position} in {REAL_PROJECT_DRAW}",
                pin["selection"]["draw_position"]
            );
        }
        if pin["selection"]["frame"]["path"] != json!(REAL_PROJECT_FRAME)
            || pin["selection"]["frame"]["sha256"] != json!(frame_sha256)
        {
            bail!("{display}: selection.frame must bind {REAL_PROJECT_FRAME} at {frame_sha256}");
        }

        let candidate = candidates
            .iter()
            .find(|candidate| candidate["ghsa_id"].as_str() == Some(ghsa))
            .expect("selected candidates come from the frame");
        if pin["ecosystem"].as_str() != candidate["ecosystem"].as_str() {
            bail!(
                "{display}: ecosystem {} contradicts the frame's {}",
                pin["ecosystem"],
                candidate["ecosystem"]
            );
        }
        let fix_commits: Vec<&str> = pin["fix_commits"]
            .as_array()
            .expect("schema validated")
            .iter()
            .map(|value| value.as_str().expect("schema validated"))
            .collect();
        let referenced = candidate["fix_commit_references"]
            .as_array()
            .with_context(|| {
                format!("{REAL_PROJECT_FRAME}: {ghsa} has no fix_commit_references")
            })?;
        if referenced.len() != fix_commits.len() {
            bail!(
                "{display}: pins {} fix commits for an advisory that references {}",
                fix_commits.len(),
                referenced.len()
            );
        }
        for reference in referenced {
            let reference = reference.as_str().unwrap_or_default();
            if !fix_commits
                .iter()
                .any(|commit| commit.starts_with(reference))
            {
                bail!("{display}: advisory reference {reference} resolves to no pinned fix commit");
            }
        }

        let selected_fix_commits: Vec<&str> = pin["selected_fix_commits"]
            .as_array()
            .unwrap_or_else(|| pin["fix_commits"].as_array().expect("schema validated"))
            .iter()
            .map(|value| value.as_str().expect("schema validated"))
            .collect();
        if selected_fix_commits
            .iter()
            .any(|selected| !fix_commits.contains(selected))
        {
            bail!("{display}: selected_fix_commits must be a subset of the advisory's fix commits");
        }

        let vulnerable = pin["revisions"]["vulnerable"]["revision"]
            .as_str()
            .expect("schema validated");
        let fixed = pin["revisions"]["fixed"]["revision"]
            .as_str()
            .expect("schema validated");
        if vulnerable == fixed {
            bail!("{display}: the vulnerable and fixed revisions must differ");
        }
        if !selected_fix_commits.contains(&fixed) {
            bail!("{display}: the fixed revision {fixed} is not one of the selected fix commits");
        }
        if fix_commits.contains(&vulnerable) {
            bail!(
                "{display}: the vulnerable revision {vulnerable} is itself a fix commit; it must be the parent of one"
            );
        }
        for kind in ["vulnerable", "fixed"] {
            let revision = pin["revisions"][kind]["revision"]
                .as_str()
                .expect("schema validated");
            let expected = format!("https://codeload.github.com/{slug}/tar.gz/{revision}");
            if pin["revisions"][kind]["source_archive"]["url"].as_str() != Some(expected.as_str()) {
                bail!("{display}: the {kind} source archive url must be {expected}");
            }
        }

        // Invariant 9 of the preregistration: a wave whose ground truth was not
        // independently reviewed has to say so beside its numbers. The
        // disclosure is only worth anything if it cannot drift away from the
        // staffing that produced it, so the record is checked against its own
        // reviewer list rather than trusted to stay in step by hand.
        let reviewers: BTreeSet<&str> = pin["ground_truth"]["reviewers"]
            .as_array()
            .expect("schema validated")
            .iter()
            .filter_map(|value| value.as_str())
            .collect();
        let independence = pin["ground_truth"]["review_independence"]
            .as_str()
            .expect("schema validated");
        if reviewers.len() < 2 && independence != "maintainer-only" {
            bail!(
                "{display}: ground truth names {} reviewer(s) and cannot claim independent review",
                reviewers.len()
            );
        }

        let spdx = pin["license"]["spdx_id"]
            .as_str()
            .expect("schema validated");
        if !REAL_PROJECT_LICENSES.contains(&spdx) {
            bail!(
                "{display}: licence {spdx} is not one of the OSI identifiers eligibility criterion E2 admits"
            );
        }
    }
    validate_real_project_review_at(Path::new("."), false)?;
    Ok(paths.len())
}

/// Validate the prospective R2 contract without consulting or creating the
/// mutable population. R2 is intentionally a separate protocol artifact: the
/// R1 packet digest-binds the legacy documents and must remain byte-for-byte
/// intact as an inconclusive historical audit.
pub(crate) fn validate_real_project_r2_protocol_at(root: &Path) -> Result<()> {
    let protocol_path = root.join(REAL_PROJECT_R2_PROTOCOL);
    let protocol: Value = serde_json::from_slice(
        &fs::read(&protocol_path).with_context(|| format!("read {}", protocol_path.display()))?,
    )
    .with_context(|| format!("parse {}", protocol_path.display()))?;
    let schema_path = root.join(REAL_PROJECT_R2_PROTOCOL_SCHEMA);
    let schema_value: Value = serde_json::from_slice(
        &fs::read(&schema_path).with_context(|| format!("read {}", schema_path.display()))?,
    )?;
    let compiled = jsonschema::JSONSchema::compile(Box::leak(Box::new(schema_value)))
        .context("compile real-project R2 protocol schema")?;
    validate_value(&compiled, &protocol, &protocol_path)?;

    if protocol["wave"] != "R2" || protocol["seed"] != "dataflowbench-real-project-wave-r2" {
        bail!("{REAL_PROJECT_R2_PROTOCOL}: wave and seed must identify the fresh R2 draw");
    }
    if protocol["analyzer_evidence_consulted"] != false {
        bail!("{REAL_PROJECT_R2_PROTOCOL}: analyzer evidence must not influence R2");
    }
    let superseded = &protocol["superseded_review"];
    if superseded["path"] != REAL_PROJECT_REVIEW || superseded["outcome"] != "inconclusive" {
        bail!("{REAL_PROJECT_R2_PROTOCOL}: R2 must retain the inconclusive R1 review identity");
    }
    validate_review_artifact(root, superseded)?;
    let criteria = protocol["eligibility"]["criteria"]
        .as_object()
        .context("R2 protocol eligibility.criteria must be an object")?;
    let expected = (1..=8)
        .map(|index| format!("E{index}"))
        .collect::<BTreeSet<_>>();
    let actual = criteria.keys().cloned().collect::<BTreeSet<_>>();
    if actual != expected {
        bail!("{REAL_PROJECT_R2_PROTOCOL}: eligibility must declare exactly E1-E8");
    }
    Ok(())
}

/// Validate R2's immutable source-only advisory snapshot when it exists. The
/// preregistration commit deliberately has no snapshot; after capture lands,
/// every response body must be uniquely manifest-bound and pagination must be
/// complete and contiguous.
pub(crate) fn validate_real_project_r2_snapshot_at(root: &Path) -> Result<()> {
    let manifest_path = root.join(REAL_PROJECT_R2_SNAPSHOT);
    if !manifest_path.exists() {
        return Ok(());
    }
    let manifest: Value = serde_json::from_slice(
        &fs::read(&manifest_path).with_context(|| format!("read {}", manifest_path.display()))?,
    )
    .with_context(|| format!("parse {}", manifest_path.display()))?;
    let schema_path = root.join(REAL_PROJECT_R2_SNAPSHOT_SCHEMA);
    let schema_value: Value = serde_json::from_slice(
        &fs::read(&schema_path).with_context(|| format!("read {}", schema_path.display()))?,
    )?;
    let compiled = jsonschema::JSONSchema::compile(Box::leak(Box::new(schema_value)))
        .context("compile real-project R2 snapshot schema")?;
    validate_value(&compiled, &manifest, &manifest_path)?;

    validate_review_artifact(root, &manifest["protocol"])?;
    let protocol: Value = serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_PROTOCOL))?)?;
    let protocol_queries = protocol["population"]["queries"]
        .as_array()
        .expect("protocol schema validated");
    let mut expected_strata =
        BTreeMap::from([("java", "maven"), ("javascript", "npm"), ("python", "pip")]);
    let mut manifested_paths = BTreeSet::new();
    for query in manifest["queries"]
        .as_array()
        .expect("snapshot schema validated")
    {
        let stratum = query["stratum"]
            .as_str()
            .expect("snapshot schema validated");
        let ecosystem = query["ecosystem"]
            .as_str()
            .expect("snapshot schema validated");
        if expected_strata.remove(stratum) != Some(ecosystem) {
            bail!(
                "{REAL_PROJECT_R2_SNAPSHOT}: duplicate or mismatched {stratum}/{ecosystem} query"
            );
        }
        let expected_query = protocol_queries
            .iter()
            .find(|expected| expected["stratum"] == stratum)
            .expect("protocol declares every stratum");
        let actual_parameters = query["parameters"]
            .as_object()
            .expect("snapshot schema validated");
        let expected_parameters = expected_query["parameters"]
            .as_object()
            .expect("protocol schema validated");
        let render_parameter = |value: &Value| {
            value
                .as_str()
                .map(str::to_string)
                .unwrap_or_else(|| value.to_string())
        };
        if actual_parameters.len() != expected_parameters.len()
            || expected_parameters.iter().any(|(key, expected)| {
                actual_parameters.get(key).map_or(true, |actual| {
                    render_parameter(actual) != render_parameter(expected)
                })
            })
        {
            bail!(
                "{REAL_PROJECT_R2_SNAPSHOT}: {stratum} parameters differ from the preregistration"
            );
        }
        let pages = query["pages"]
            .as_array()
            .expect("snapshot schema validated");
        for (index, page) in pages.iter().enumerate() {
            if page["page"].as_u64() != Some(index as u64 + 1) {
                bail!("{REAL_PROJECT_R2_SNAPSHOT}: {ecosystem} pages must be contiguous from one");
            }
            let url = page["request_url"]
                .as_str()
                .expect("snapshot schema validated");
            if !url.starts_with("https://api.github.com/advisories?") {
                bail!(
                    "{REAL_PROJECT_R2_SNAPSHOT}: {stratum} page leaves the preregistered endpoint"
                );
            }
            for (key, value) in actual_parameters {
                let rendered = render_parameter(value);
                let needle = format!("{key}={}", rendered.replace(',', "%2C"));
                if !url.contains(&needle) {
                    bail!("{REAL_PROJECT_R2_SNAPSHOT}: {stratum} request URL omits {key}");
                }
            }
            let relative = page["response_path"]
                .as_str()
                .expect("snapshot schema validated")
                .to_string();
            validate_review_artifact(root, &json!({ "path": relative, "sha256": page["sha256"] }))?;
            if !manifested_paths.insert(relative.clone()) {
                bail!("{REAL_PROJECT_R2_SNAPSHOT}: duplicate response path {relative}");
            }
            let body: Value = serde_json::from_slice(&fs::read(root.join(&relative))?)?;
            let item_count = body
                .as_array()
                .with_context(|| format!("{relative}: response body must be a JSON array"))?
                .len() as u64;
            if page["item_count"].as_u64() != Some(item_count) {
                bail!("{REAL_PROJECT_R2_SNAPSHOT}: {relative} item count does not match its body");
            }
            let next = page["next_url"].as_str();
            if index + 1 < pages.len() {
                if next != pages[index + 1]["request_url"].as_str() {
                    bail!(
                        "{REAL_PROJECT_R2_SNAPSHOT}: {ecosystem} pagination link is discontinuous"
                    );
                }
            } else if next.is_some() {
                bail!(
                    "{REAL_PROJECT_R2_SNAPSHOT}: final {ecosystem} page still declares a next URL"
                );
            }
        }
    }
    if !expected_strata.is_empty() {
        bail!("{REAL_PROJECT_R2_SNAPSHOT}: missing preregistered stratum query");
    }

    let response_root = root.join("corpus/real-project/r2/snapshot/advisories");
    let actual_paths = WalkDir::new(&response_root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| {
            entry
                .path()
                .strip_prefix(root)
                .unwrap_or(entry.path())
                .to_string_lossy()
                .replace('\\', "/")
        })
        .collect::<BTreeSet<_>>();
    if actual_paths != manifested_paths {
        bail!("{REAL_PROJECT_R2_SNAPSHOT}: response files and manifest entries differ");
    }
    Ok(())
}

pub(crate) fn validate_real_project_r2_frame_at(root: &Path) -> Result<usize> {
    let frame_path = root.join(REAL_PROJECT_R2_FRAME);
    if !frame_path.exists() {
        return Ok(0);
    }
    let frame: Value = serde_json::from_slice(
        &fs::read(&frame_path).with_context(|| format!("read {}", frame_path.display()))?,
    )?;
    let schema_value: Value =
        serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_FRAME_SCHEMA))?)?;
    let compiled = jsonschema::JSONSchema::compile(Box::leak(Box::new(schema_value)))
        .context("compile real-project R2 frame schema")?;
    validate_value(&compiled, &frame, &frame_path)?;
    validate_review_artifact(root, &frame["derived_from"])?;

    let manifest: Value = serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_SNAPSHOT))?)?;
    let mut derived = Vec::new();
    let mut raw_counts = BTreeMap::new();
    let repository_re = regex::Regex::new(r"^https://github\.com/([^/]+)/([^/#?]+)/?$")?;
    let commit_re =
        regex::Regex::new(r"^https://github\.com/([^/]+)/([^/]+)/commit/([0-9a-f]{7,40})")?;
    for query in manifest["queries"]
        .as_array()
        .expect("snapshot schema validated")
    {
        let stratum = query["stratum"]
            .as_str()
            .expect("snapshot schema validated");
        let ecosystem = query["ecosystem"]
            .as_str()
            .expect("snapshot schema validated");
        let mut raw = 0u64;
        for page in query["pages"]
            .as_array()
            .expect("snapshot schema validated")
        {
            let relative = page["response_path"]
                .as_str()
                .expect("snapshot schema validated");
            let advisories: Value = serde_json::from_slice(&fs::read(root.join(relative))?)?;
            for (array_index, advisory) in advisories
                .as_array()
                .expect("snapshot body validated")
                .iter()
                .enumerate()
            {
                raw += 1;
                if !advisory["withdrawn_at"].is_null() {
                    continue;
                }
                let Some(location) = advisory["source_code_location"].as_str() else {
                    continue;
                };
                let Some(repository) = repository_re.captures(location) else {
                    continue;
                };
                let owner = repository.get(1).expect("capture").as_str();
                let name = repository.get(2).expect("capture").as_str();
                let mut fixes = Vec::new();
                for reference in advisory["references"]
                    .as_array()
                    .into_iter()
                    .flatten()
                    .filter_map(Value::as_str)
                {
                    let Some(commit) = commit_re.captures(reference) else {
                        continue;
                    };
                    if commit
                        .get(1)
                        .expect("capture")
                        .as_str()
                        .eq_ignore_ascii_case(owner)
                        && commit
                            .get(2)
                            .expect("capture")
                            .as_str()
                            .eq_ignore_ascii_case(name)
                    {
                        let revision = commit.get(3).expect("capture").as_str().to_string();
                        if !fixes.contains(&revision) {
                            fixes.push(revision);
                        }
                    }
                }
                if fixes.is_empty() {
                    continue;
                }
                let mut packages = advisory["vulnerabilities"]
                    .as_array()
                    .into_iter()
                    .flatten()
                    .filter_map(|item| item["package"]["name"].as_str().map(str::to_string))
                    .collect::<BTreeSet<_>>()
                    .into_iter()
                    .collect::<Vec<_>>();
                packages.sort();
                derived.push(json!({
                    "stratum": stratum, "ecosystem": ecosystem,
                    "ghsa_id": advisory["ghsa_id"], "cve_id": advisory["cve_id"],
                    "cwes": advisory["cwes"].as_array().into_iter().flatten().map(|cwe| cwe["cwe_id"].clone()).collect::<Vec<_>>(),
                    "severity": advisory["severity"], "published_at": advisory["published_at"],
                    "repository": format!("{owner}/{name}"), "source_code_location": location,
                    "packages": packages, "fix_commit_references": fixes,
                    "advisory_evidence": { "path": relative, "sha256": page["sha256"], "array_index": array_index }
                }));
            }
        }
        raw_counts.insert(stratum.to_string(), raw);
    }
    derived.sort_by(|left, right| {
        left["stratum"]
            .as_str()
            .cmp(&right["stratum"].as_str())
            .then_with(|| left["ghsa_id"].as_str().cmp(&right["ghsa_id"].as_str()))
    });
    if frame["candidates"] != json!(derived) {
        bail!("{REAL_PROJECT_R2_FRAME}: candidates do not re-derive from the immutable snapshot");
    }
    for stratum in ["java", "javascript", "python"] {
        let admitted = derived
            .iter()
            .filter(|row| row["stratum"] == stratum)
            .count() as u64;
        let raw = raw_counts[stratum];
        if frame["counts"]["raw"][stratum].as_u64() != Some(raw)
            || frame["counts"]["admitted"][stratum].as_u64() != Some(admitted)
            || frame["counts"]["rejected"][stratum].as_u64() != Some(raw - admitted)
        {
            bail!("{REAL_PROJECT_R2_FRAME}: {stratum} counts do not match the snapshot");
        }
    }
    Ok(derived.len())
}

/// Validate the committed R2 E5 inventory and, once captured, replay every
/// eligibility decision and draw step from the immutable frame and evidence.
pub(crate) fn validate_real_project_r2_selection_at(root: &Path) -> Result<Option<usize>> {
    let inventory_path = root.join(REAL_PROJECT_R2_E5_INVENTORY);
    let inventory: Value = serde_json::from_slice(&fs::read(&inventory_path)?)?;
    let inventory_schema: Value =
        serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_E5_INVENTORY_SCHEMA))?)?;
    let compiled = JSONSchema::compile(Box::leak(Box::new(inventory_schema)))
        .context("compile real-project R2 E5 inventory schema")?;
    validate_value(&compiled, &inventory, &inventory_path)?;
    for key in ["r1_frame", "r1_draw"] {
        validate_review_artifact(root, &inventory[key])?;
    }
    for source in inventory["source_lists"]
        .as_array()
        .expect("schema validated")
    {
        validate_review_artifact(root, source)?;
    }
    let r1_draw: Value = serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_DRAW))?)?;
    let r1_selected = r1_draw["walk"]
        .as_object()
        .expect("R1 draw schema validated")
        .values()
        .flat_map(|rows| rows.as_array().expect("R1 draw schema validated"))
        .filter(|row| row["disposition"] == "selected")
        .map(|row| {
            row["repository"]
                .as_str()
                .expect("R1 draw schema validated")
                .to_ascii_lowercase()
        })
        .collect::<BTreeSet<_>>();
    let inventoried = inventory["r1_selected_repositories"]
        .as_array()
        .expect("schema validated")
        .iter()
        .map(|value| {
            value
                .as_str()
                .expect("schema validated")
                .to_ascii_lowercase()
        })
        .collect::<BTreeSet<_>>();
    if inventoried != r1_selected {
        bail!("{REAL_PROJECT_R2_E5_INVENTORY}: R1 selected repositories do not replay");
    }
    let e5_excluded = [
        "r1_selected_repositories",
        "named_donor_or_corpus_repositories",
        "evaluated_analyzer_or_dependency_repositories",
    ]
    .into_iter()
    .flat_map(|field| inventory[field].as_array().expect("schema validated"))
    .map(|value| {
        value
            .as_str()
            .expect("schema validated")
            .to_ascii_lowercase()
    })
    .collect::<BTreeSet<_>>();

    let eligibility_path = root.join(REAL_PROJECT_R2_ELIGIBILITY);
    let draw_path = root.join(REAL_PROJECT_R2_DRAW);
    if !eligibility_path.exists() && !draw_path.exists() {
        return Ok(None);
    }
    if !eligibility_path.exists() || !draw_path.exists() {
        bail!("R2 eligibility and draw must be committed together");
    }
    let eligibility_bytes = fs::read(&eligibility_path)?;
    let eligibility: Value = serde_json::from_slice(&eligibility_bytes)?;
    let draw: Value = serde_json::from_slice(&fs::read(&draw_path)?)?;
    for (schema_path, value, path, label) in [
        (
            REAL_PROJECT_R2_ELIGIBILITY_SCHEMA,
            &eligibility,
            &eligibility_path,
            "eligibility",
        ),
        (REAL_PROJECT_R2_DRAW_SCHEMA, &draw, &draw_path, "draw"),
    ] {
        let schema_value: Value = serde_json::from_slice(&fs::read(root.join(schema_path))?)?;
        let compiled = JSONSchema::compile(Box::leak(Box::new(schema_value)))
            .with_context(|| format!("compile real-project R2 {label} schema"))?;
        validate_value(&compiled, value, path)?;
    }
    validate_review_artifact(root, &eligibility["frame"])?;
    validate_review_artifact(root, &draw["frame"])?;
    validate_review_artifact(root, &draw["eligibility"])?;

    let frame: Value = serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_FRAME))?)?;
    let candidates = frame["candidates"]
        .as_array()
        .expect("frame schema validated");
    let records = eligibility["candidates"]
        .as_array()
        .expect("eligibility schema validated");
    let seed = draw["seed"].as_str().expect("draw schema validated");
    let mut selected_before = Vec::<String>::new();
    let mut consumed = 0usize;
    let evidence_schema: Value =
        serde_json::from_slice(&fs::read(root.join(REAL_PROJECT_R2_EVIDENCE_SCHEMA))?)?;
    let evidence_compiled = JSONSchema::compile(Box::leak(Box::new(evidence_schema)))
        .context("compile real-project R2 evidence schema")?;
    for stratum in ["java", "javascript", "python"] {
        let mut ordered = candidates
            .iter()
            .filter(|candidate| candidate["stratum"] == stratum)
            .collect::<Vec<_>>();
        ordered.sort_by_key(|candidate| {
            let ghsa = candidate["ghsa_id"]
                .as_str()
                .expect("frame schema validated");
            (real_project_draw_key(seed, ghsa), ghsa.to_string())
        });
        let rows = draw["walk"][stratum]
            .as_array()
            .expect("draw schema validated");
        let mut selected = 0usize;
        for (index, row) in rows.iter().enumerate() {
            let candidate = ordered
                .get(index)
                .with_context(|| format!("{REAL_PROJECT_R2_DRAW}: {stratum} walk exceeds frame"))?;
            let record_index = row["eligibility_index"]
                .as_u64()
                .expect("draw schema validated") as usize;
            let record = records.get(record_index).with_context(|| {
                format!("{REAL_PROJECT_R2_DRAW}: eligibility index {record_index} is out of range")
            })?;
            for key in ["ghsa_id", "repository"] {
                if row[key] != candidate[key] || record[key] != candidate[key] {
                    bail!(
                        "{REAL_PROJECT_R2_DRAW}: {stratum} position {} does not match the frame",
                        index + 1
                    );
                }
            }
            if row["draw_position"].as_u64() != Some((index + 1) as u64)
                || record["draw_position"] != row["draw_position"]
            {
                bail!("{REAL_PROJECT_R2_DRAW}: {stratum} positions are not contiguous");
            }
            let ghsa = row["ghsa_id"].as_str().expect("draw schema validated");
            if row["draw_key"] != real_project_draw_key(seed, ghsa) {
                bail!("{REAL_PROJECT_R2_DRAW}: {ghsa} draw key does not replay");
            }
            let decisions = record["decisions"]
                .as_object()
                .expect("eligibility schema validated");
            for decision in decisions.values() {
                for evidence in decision["evidence"]
                    .as_array()
                    .expect("eligibility schema validated")
                {
                    validate_review_artifact(root, evidence)?;
                }
            }
            let e8_state = decisions["E8"]["selected_repositories_before"]
                .as_array()
                .expect("eligibility schema validated")
                .iter()
                .map(|value| value.as_str().expect("schema validated").to_string())
                .collect::<Vec<_>>();
            if e8_state != selected_before {
                bail!("{REAL_PROJECT_R2_ELIGIBILITY}: {ghsa} E8 state does not replay");
            }
            let manifest_relative = format!("corpus/real-project/r2/evidence/{ghsa}/manifest.json");
            let manifest_path = root.join(&manifest_relative);
            let manifest: Value = serde_json::from_slice(&fs::read(&manifest_path)?)?;
            validate_value(&evidence_compiled, &manifest, &manifest_path)?;
            if manifest["ghsa_id"] != row["ghsa_id"] || manifest["repository"] != row["repository"]
            {
                bail!("{manifest_relative}: identity differs from the draw");
            }
            let mut response_bodies = BTreeMap::new();
            for response in manifest["responses"].as_array().expect("schema validated") {
                validate_review_artifact(root, response)?;
                let response_path = response["path"].as_str().expect("schema validated");
                if !response_path.starts_with(&format!("corpus/real-project/r2/evidence/{ghsa}/")) {
                    bail!("{manifest_relative}: response path belongs to another candidate");
                }
                let body = fs::read(root.join(response_path))?;
                if response["bytes"].as_u64() != Some(body.len() as u64) {
                    bail!("{manifest_relative}: response byte length drifted");
                }
                let purpose = response["purpose"]
                    .as_str()
                    .expect("schema validated")
                    .to_string();
                let parsed: Value = serde_json::from_slice(&body)?;
                if response_bodies.insert(purpose.clone(), parsed).is_some() {
                    bail!("{manifest_relative}: duplicate response purpose {purpose}");
                }
            }
            for required in [
                "repository",
                "languages",
                "commit-00",
                "license-vulnerable",
                "license-fixed",
                "readme-vulnerable",
            ] {
                if !response_bodies.contains_key(required) {
                    bail!("{manifest_relative}: missing {required} response");
                }
            }
            let repository = &response_bodies["repository"];
            let languages = &response_bodies["languages"];
            let license = &response_bodies["license-vulnerable"];
            let expected_language = match stratum {
                "java" => "Java",
                "javascript" => "JavaScript",
                "python" => "Python",
                _ => unreachable!(),
            };
            let e1 = repository["language"].as_str() == Some(expected_language);
            let spdx = license["license"]["spdx_id"].as_str().unwrap_or_default();
            let e2 = REAL_PROJECT_LICENSES.contains(&spdx)
                && license["content"]
                    .as_str()
                    .is_some_and(|value| !value.is_empty());
            let e3 = repository["archived"] == false && repository["fork"] == false;
            let e4 = repository["size"]
                .as_u64()
                .is_some_and(|size| size <= 256_000);
            let slug = row["repository"].as_str().expect("draw schema validated");
            let e5 = !e5_excluded.contains(&slug.to_ascii_lowercase());
            let mut commit_responses = response_bodies
                .iter()
                .filter(|(purpose, _)| purpose.starts_with("commit-"))
                .map(|(_, body)| body)
                .collect::<Vec<_>>();
            commit_responses.sort_by_key(|body| {
                (
                    body["commit"]["committer"]["date"]
                        .as_str()
                        .unwrap_or_default()
                        .to_string(),
                    body["sha"].as_str().unwrap_or_default().to_string(),
                )
            });
            let compare_responses = response_bodies
                .iter()
                .filter(|(purpose, _)| purpose.starts_with("compare-"))
                .map(|(_, body)| body)
                .collect::<Vec<_>>();
            let e6 = !commit_responses.is_empty()
                && commit_responses[0]["parents"]
                    .as_array()
                    .is_some_and(|parents| parents.len() == 1)
                && compare_responses.len() + 1 == commit_responses.len()
                && compare_responses
                    .iter()
                    .all(|body| body["status"] == "ahead");
            let e7 = languages[expected_language]
                .as_u64()
                .is_some_and(|bytes| bytes >= 20_000);
            let e8 = !selected_before
                .iter()
                .any(|selected| selected.eq_ignore_ascii_case(slug));
            for (criterion, expected) in [
                ("E1", e1),
                ("E2", e2),
                ("E3", e3),
                ("E4", e4),
                ("E5", e5),
                ("E6", e6),
                ("E7", e7),
                ("E8", e8),
            ] {
                let expected_outcome = if expected { "pass" } else { "fail" };
                if decisions[criterion]["outcome"] != expected_outcome {
                    bail!(
                        "{REAL_PROJECT_R2_ELIGIBILITY}: {ghsa} {criterion} does not re-derive from evidence"
                    );
                }
            }
            let passes = decisions
                .values()
                .all(|decision| decision["outcome"] == "pass");
            let disposition = if passes { "selected" } else { "excluded" };
            if row["disposition"] != disposition {
                bail!("{REAL_PROJECT_R2_DRAW}: {ghsa} disposition contradicts E1-E8");
            }
            if passes {
                let repository = row["repository"]
                    .as_str()
                    .expect("draw schema validated")
                    .to_string();
                if r1_selected.contains(&repository.to_ascii_lowercase()) {
                    bail!("{REAL_PROJECT_R2_DRAW}: R2 reuses R1 repository {repository}");
                }
                selected_before.push(repository);
                selected += 1;
            }
            consumed += 1;
        }
        if selected != 2
            || rows
                .last()
                .map_or(true, |row| row["disposition"] != "selected")
        {
            bail!("{REAL_PROJECT_R2_DRAW}: {stratum} must stop at its second selection");
        }
    }
    if consumed != records.len() {
        bail!("{REAL_PROJECT_R2_ELIGIBILITY}: contains unreferenced candidate records");
    }
    Ok(Some(selected_before.len()))
}

/// Validate the provenance-bound independent-review record. Pending and
/// inconclusive records are valid preregistration evidence, but callers that
/// can execute analyzers or freeze real-project results pass `require_ready`
/// and fail closed until both independent labs and disagreement handling have
/// completed.
pub(crate) fn validate_real_project_review_at(root: &Path, require_ready: bool) -> Result<()> {
    let review_path = root.join(REAL_PROJECT_REVIEW);
    let review_bytes =
        fs::read(&review_path).with_context(|| format!("read {}", review_path.display()))?;
    let review: Value = serde_json::from_slice(&review_bytes)
        .with_context(|| format!("parse {}", review_path.display()))?;
    let schema_path = root.join(REAL_PROJECT_REVIEW_SCHEMA);
    let schema_value: Value = serde_json::from_slice(
        &fs::read(&schema_path).with_context(|| format!("read {}", schema_path.display()))?,
    )?;
    let compiled = jsonschema::JSONSchema::compile(Box::leak(Box::new(schema_value)))
        .context("compile real-project review schema")?;
    validate_value(&compiled, &review, &review_path)?;

    let scoped_artifacts = review["scope"]
        .as_object()
        .expect("review schema validated");
    for key in ["preregistration", "review_contract", "draw", "frame"] {
        validate_review_artifact(root, &scoped_artifacts[key])?;
    }
    for artifact in scoped_artifacts["schemas"]
        .as_array()
        .expect("review schema validated")
    {
        validate_review_artifact(root, artifact)?;
    }
    let scoped_pins = scoped_artifacts["pins"]
        .as_array()
        .expect("review schema validated");
    let mut scoped_paths = BTreeSet::new();
    for artifact in scoped_pins {
        let path = validate_review_artifact(root, artifact)?;
        if !scoped_paths.insert(path) {
            bail!("{REAL_PROJECT_REVIEW}: duplicate scoped pin artifact");
        }
    }
    let actual_pin_paths = real_project_pin_paths_at(root)?
        .into_iter()
        .map(|path| {
            path.strip_prefix(root)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/")
        })
        .collect::<BTreeSet<_>>();
    if scoped_paths != actual_pin_paths {
        bail!("{REAL_PROJECT_REVIEW}: scoped pins do not match the selected pin set");
    }
    for artifact in scoped_artifacts["measurement_tools"]
        .as_array()
        .expect("review schema validated")
    {
        validate_review_artifact(root, artifact)?;
    }
    for prior in review["prior_reviews"]
        .as_array()
        .expect("review schema validated")
    {
        validate_review_artifact(root, &prior["report"])?;
    }

    let canonical_packet = review_packet_artifacts(&review)?;
    for role in ["reviewer_a", "reviewer_b"] {
        let reviewer = &review["reviewers"][role];
        let packet = reviewer["packet"]["artifacts"]
            .as_array()
            .expect("review schema validated")
            .iter()
            .map(review_artifact_identity)
            .collect::<Result<BTreeSet<_>>>()?;
        if packet != canonical_packet {
            bail!("{REAL_PROJECT_REVIEW}: {role} packet differs from the canonical digest set");
        }
        match (
            reviewer["report"]["path"].as_str(),
            reviewer["report"]["sha256"].as_str(),
        ) {
            (Some(_), Some(_)) => {
                let report_path = validate_review_artifact(root, &reviewer["report"])?;
                if !report_path.starts_with("corpus/real-project/reviews/") {
                    bail!(
                        "{REAL_PROJECT_REVIEW}: reviewer reports must be retained under corpus/real-project/reviews/"
                    );
                }
            }
            (None, None) => {}
            _ => bail!(
                "{REAL_PROJECT_REVIEW}: {role} report path and digest must both be present or both be null"
            ),
        }
    }

    let reviewed_pins = review["per_pin_ground_truth"]
        .as_array()
        .expect("review schema validated");
    let mut reviewed_paths = BTreeSet::new();
    for pin in reviewed_pins {
        let path = validate_review_artifact(root, &pin["pin_artifact"])?;
        if !reviewed_paths.insert(path) {
            bail!("{REAL_PROJECT_REVIEW}: duplicate per-pin ground-truth review");
        }
    }
    if reviewed_paths != actual_pin_paths {
        bail!("{REAL_PROJECT_REVIEW}: per-pin reviews do not cover the selected pin set");
    }

    validate_review_state(root, &review, require_ready)?;
    Ok(())
}

pub(crate) fn validate_frozen_real_project_review(root: &Path, artifact: &Value) -> Result<()> {
    if artifact["path"] != REAL_PROJECT_REVIEW {
        bail!("real-project freeze must bind {REAL_PROJECT_REVIEW}");
    }
    validate_review_artifact(root, artifact)?;
    validate_real_project_review_at(root, true)
}

fn real_project_pin_paths_at(root: &Path) -> Result<Vec<PathBuf>> {
    let directory = root.join(REAL_PROJECT_PINS_DIR);
    let mut paths = fs::read_dir(&directory)
        .with_context(|| format!("read {}", directory.display()))?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file() && path.extension().is_some_and(|ext| ext == "json"))
        .collect::<Vec<_>>();
    paths.sort();
    Ok(paths)
}

fn review_artifact_identity(artifact: &Value) -> Result<(String, String)> {
    let path = artifact["path"]
        .as_str()
        .context("review artifact requires path")?;
    let digest = artifact["sha256"]
        .as_str()
        .context("review artifact requires sha256")?;
    Ok((path.to_string(), digest.to_string()))
}

fn review_packet_artifacts(review: &Value) -> Result<BTreeSet<(String, String)>> {
    let scope = review["scope"]
        .as_object()
        .expect("review schema validated");
    let mut artifacts = BTreeSet::new();
    for key in ["preregistration", "review_contract", "draw", "frame"] {
        artifacts.insert(review_artifact_identity(&scope[key])?);
    }
    for schema in scope["schemas"]
        .as_array()
        .expect("review schema validated")
    {
        artifacts.insert(review_artifact_identity(schema)?);
    }
    for pin in scope["pins"].as_array().expect("review schema validated") {
        artifacts.insert(review_artifact_identity(pin)?);
    }
    for tool in scope["measurement_tools"]
        .as_array()
        .expect("review schema validated")
    {
        artifacts.insert(review_artifact_identity(tool)?);
    }
    Ok(artifacts)
}

fn validate_review_artifact(root: &Path, artifact: &Value) -> Result<String> {
    let (relative, expected) = review_artifact_identity(artifact)?;
    let relative_path = Path::new(&relative);
    if relative_path.is_absolute()
        || relative_path
            .components()
            .any(|component| component == std::path::Component::ParentDir)
    {
        bail!("review artifact path must be repository-relative: {relative:?}");
    }
    let path = root.join(relative_path);
    let canonical_root = root
        .canonicalize()
        .with_context(|| format!("canonicalize repository root {}", root.display()))?;
    let canonical_path = path
        .canonicalize()
        .with_context(|| format!("canonicalize review artifact {relative}"))?;
    if !canonical_path.starts_with(&canonical_root) {
        bail!("review artifact path escapes the repository: {relative:?}");
    }
    let bytes = fs::read(&path).with_context(|| format!("read review artifact {relative}"))?;
    let actual = format!("{:x}", Sha256::digest(&bytes));
    if actual != expected {
        bail!(
            "review artifact {relative} SHA-256 digest mismatch: expected {expected}, got {actual}"
        );
    }
    Ok(relative.replace('\\', "/"))
}

pub(crate) fn validate_review_state(
    root: &Path,
    review: &Value,
    require_ready: bool,
) -> Result<()> {
    let readiness = &review["readiness"];
    let execution_ready = readiness["execution_ready"] == true;
    let freeze_ready = readiness["freeze_ready"] == true;
    let ready = readiness["outcome"] == "ready" && execution_ready && freeze_ready;
    if !ready {
        if execution_ready || freeze_ready || readiness["outcome"] == "ready" {
            bail!(
                "{REAL_PROJECT_REVIEW}: a non-ready review must keep both execution_ready and freeze_ready false"
            );
        }
        if review["status"] == "complete" {
            bail!("{REAL_PROJECT_REVIEW}: a complete review must be execution- and freeze-ready");
        }
        let coherent = match review["status"].as_str().expect("review schema validated") {
            "pending" => readiness["outcome"] == "pending",
            "inconclusive" => {
                readiness["outcome"] == "inconclusive" || readiness["outcome"] == "blocked"
            }
            _ => false,
        };
        if !coherent {
            bail!("{REAL_PROJECT_REVIEW}: review status and readiness outcome disagree");
        }
        if readiness["blocking_reasons"]
            .as_array()
            .expect("review schema validated")
            .is_empty()
        {
            bail!("{REAL_PROJECT_REVIEW}: a non-ready review requires a blocking reason");
        }
        if require_ready {
            bail!(
                "{REAL_PROJECT_REVIEW}: independent review is not ready; analyzer execution and real-project freeze are blocked"
            );
        }
        return Ok(());
    }
    if review["status"] != "complete" {
        bail!("{REAL_PROJECT_REVIEW}: readiness cannot be true before the review is complete");
    }
    if !readiness["blocking_reasons"]
        .as_array()
        .expect("review schema validated")
        .is_empty()
    {
        bail!("{REAL_PROJECT_REVIEW}: a ready review cannot retain blocking reasons");
    }
    if review["disagreement"]["status"] == "pending"
        || review["disagreement"]["status"] == "unresolved"
        || review["disagreement"]["outcome"] == "pending"
        || review["disagreement"]["outcome"] == "inconclusive"
    {
        bail!("{REAL_PROJECT_REVIEW}: unresolved disagreement blocks readiness");
    }

    let mut checkout_paths = BTreeSet::new();
    let mut checkout_revisions = BTreeSet::new();
    let mut evidence_paths = BTreeSet::new();
    let mut report_paths = BTreeSet::new();
    let mut has_rejection = false;
    for role in ["reviewer_a", "reviewer_b"] {
        let reviewer = &review["reviewers"][role];
        let plan = &review["protocol"][role];
        for field in ["provider", "model", "reasoning_effort", "role"] {
            if reviewer[field] != plan[field] {
                bail!(
                    "{REAL_PROJECT_REVIEW}: {role} provenance differs from its preregistered plan"
                );
            }
        }
        if reviewer["status"] != "submitted"
            || reviewer["blind_independence"]["status"] != "verified"
            || reviewer["blind_independence"]["independent_checkout"] != true
            || reviewer["blind_independence"]["independent_evidence_path"] != true
            || reviewer["checkout"]["clean"] != true
        {
            bail!(
                "{REAL_PROJECT_REVIEW}: {role} has no completed independent clean-checkout review"
            );
        }
        for field in ["run_id", "started_at", "completed_at"] {
            if reviewer[field].as_str().map_or(true, str::is_empty) {
                bail!("{REAL_PROJECT_REVIEW}: {role} requires {field}");
            }
        }
        if reviewer["checkout"]["observed_at"]
            .as_str()
            .map_or(true, str::is_empty)
        {
            bail!("{REAL_PROJECT_REVIEW}: {role} requires checkout.observed_at");
        }
        let checkout_path = reviewer["checkout"]["path"]
            .as_str()
            .filter(|value| !value.is_empty())
            .with_context(|| format!("{REAL_PROJECT_REVIEW}: {role} requires checkout.path"))?;
        if !checkout_paths.insert(checkout_path) {
            bail!("{REAL_PROJECT_REVIEW}: reviewers must use separate clean checkouts");
        }
        let checkout_revision = reviewer["checkout"]["revision"]
            .as_str()
            .filter(|value| value.len() == 40)
            .with_context(|| format!("{REAL_PROJECT_REVIEW}: {role} requires checkout.revision"))?;
        checkout_revisions.insert(checkout_revision);
        let evidence_path = reviewer["packet"]["evidence_path"]
            .as_str()
            .filter(|value| !value.is_empty())
            .with_context(|| {
                format!("{REAL_PROJECT_REVIEW}: {role} requires packet.evidence_path")
            })?;
        if !evidence_paths.insert(evidence_path) {
            bail!("{REAL_PROJECT_REVIEW}: reviewers must use separate evidence paths");
        }
        let report_path = validate_review_artifact(root, &reviewer["report"])?;
        if !report_path.starts_with("corpus/real-project/reviews/")
            || !report_paths.insert(report_path)
        {
            bail!(
                "{REAL_PROJECT_REVIEW}: reviewer reports must be distinct retained review artifacts"
            );
        }
        for verdict in reviewer["subject_verdicts"]
            .as_object()
            .expect("review schema validated")
            .values()
        {
            match verdict.as_str().expect("review schema validated") {
                "accept" => {}
                "reject" => has_rejection = true,
                _ => bail!("{REAL_PROJECT_REVIEW}: {role} has an unresolved subject verdict"),
            }
        }
    }
    if checkout_revisions.len() != 1 {
        bail!("{REAL_PROJECT_REVIEW}: reviewers must inspect the same checkout revision");
    }
    if review["reviewers"]["reviewer_a"]["provider"]
        == review["reviewers"]["reviewer_b"]["provider"]
        || review["reviewers"]["reviewer_a"]["model"] == review["reviewers"]["reviewer_b"]["model"]
    {
        bail!("{REAL_PROJECT_REVIEW}: reviewer labs must have distinct providers and models");
    }
    let reviewer_a = &review["reviewers"]["reviewer_a"];
    if reviewer_a["provider"] != "openai"
        || !matches!(
            reviewer_a["model"].as_str(),
            Some("gpt-6-astra-light" | "gpt-5.6-sol")
        )
        || (reviewer_a["model"] == "gpt-5.6-sol" && reviewer_a["reasoning_effort"] != "medium")
    {
        bail!("{REAL_PROJECT_REVIEW}: reviewer A must be Astra Light or Sol medium");
    }
    let reviewer_b = &review["reviewers"]["reviewer_b"];
    if reviewer_b["provider"] != "z.ai" || reviewer_b["model"] != "glm-5.3" {
        bail!("{REAL_PROJECT_REVIEW}: reviewer B must be the independent GLM 5.3 lab");
    }
    for pin in review["per_pin_ground_truth"]
        .as_array()
        .expect("review schema validated")
    {
        for role in ["reviewer_a", "reviewer_b"] {
            for field in [
                "status",
                "vulnerable_revision",
                "fixed_revision",
                "remediation",
            ] {
                match pin[role][field].as_str().expect("review schema validated") {
                    "accept" => {}
                    "reject" => has_rejection = true,
                    _ => bail!("{REAL_PROJECT_REVIEW}: per-pin review has an unresolved verdict"),
                }
            }
        }
        if pin["consensus"] != "accept" || pin["remediation_location"]["status"] != "accept" {
            bail!("{REAL_PROJECT_REVIEW}: every selected pin requires accepted ground truth");
        }
        let pin_path = pin["pin_artifact"]["path"]
            .as_str()
            .expect("review schema validated");
        let pinned: Value = serde_json::from_slice(&fs::read(root.join(pin_path))?)?;
        if pin["pin_id"] != pinned["pin_id"]
            || pin["remediation_location"]["vulnerable_revision"]
                != pinned["revisions"]["vulnerable"]["revision"]
            || pin["remediation_location"]["fixed_revision"]
                != pinned["revisions"]["fixed"]["revision"]
        {
            bail!("{REAL_PROJECT_REVIEW}: per-pin ground truth contradicts its pinned revisions");
        }
    }
    if has_rejection && review["disagreement"]["outcome"] != "adjudicated" {
        bail!("{REAL_PROJECT_REVIEW}: a rejected review position requires adjudication");
    }
    match review["disagreement"]["outcome"]
        .as_str()
        .expect("review schema validated")
    {
        "agreed" => {
            if review["disagreement"]["status"] != "none"
                || !review["disagreement"]["items"]
                    .as_array()
                    .expect("review schema validated")
                    .is_empty()
                || review["disagreement"]["adjudicator"]["type"] != "none"
            {
                bail!(
                    "{REAL_PROJECT_REVIEW}: an agreed review must record no disagreement or adjudicator"
                );
            }
        }
        "adjudicated" => {
            let adjudicator = &review["disagreement"]["adjudicator"];
            if review["disagreement"]["status"] != "resolved"
                || review["disagreement"]["items"]
                    .as_array()
                    .expect("review schema validated")
                    .is_empty()
                || adjudicator["type"] == "none"
                || ["id", "run_id", "started_at", "completed_at"]
                    .iter()
                    .any(|field| adjudicator[*field].as_str().map_or(true, str::is_empty))
            {
                bail!(
                    "{REAL_PROJECT_REVIEW}: adjudication requires a resolved item and complete adjudicator provenance"
                );
            }
        }
        _ => bail!("{REAL_PROJECT_REVIEW}: a ready review must be agreed or adjudicated"),
    }
    if review["disagreement"]["items"]
        .as_array()
        .expect("review schema validated")
        .iter()
        .any(|item| item["status"] != "resolved" || item["resolution"].as_str().is_none())
    {
        bail!("{REAL_PROJECT_REVIEW}: every disagreement requires a retained resolution");
    }
    if review["claims"]["subject_verdict"] != "accept" {
        bail!("{REAL_PROJECT_REVIEW}: bounded claims have not been accepted");
    }
    Ok(())
}
