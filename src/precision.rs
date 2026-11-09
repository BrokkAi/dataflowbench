//! Prospective precision fixtures, kept outside every historical population.
//!
//! This inventory registers exact additions to moving main. It is not a release
//! freeze or evidence of analyzer support. Historical closure checks may remove
//! only these exact, digest-verified paths from their filesystem comparison.

use crate::freeze::{repository_path, require_digest, validate_fixture_digests};
use anyhow::{Context, Result, bail};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, sync::OnceLock};

static INVENTORY: OnceLock<Value> = OnceLock::new();

pub(crate) const PREDECESSOR_REVISION: &str = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1";
const PREDECESSOR_FILES: [(&str, &str, &str); 2] = [
    (
        "scripts/swift_population_v2.py",
        "adapters/precision-predecessor-v1/swift_population_v2.py.txt",
        "3ba357b0be10408b3e43b6713b7b161f9fb6676ff8a78f01228191bac64ad899",
    ),
    (
        "src/adapters/joern/swift.rs",
        "adapters/precision-predecessor-v1/joern_swift.rs.txt",
        "14ed6b93580b274b73b450fc82b37be4ea4a49f01edbc9efcdf0315fcc4776d7",
    ),
];

/// Replay the same logical path/byte hash with only two explicitly pinned
/// predecessor inputs. Every other configuration input still uses its actual
/// bytes, so this cannot conceal unrelated query, model or evidence drift.
pub(crate) fn predecessor_configuration_hash(paths: &BTreeSet<PathBuf>) -> Result<Option<String>> {
    let mut hasher = Sha256::new();
    let mut replaced = false;
    for path in paths {
        hasher.update(path.to_string_lossy().as_bytes());
        if let Some((_, snapshot, digest)) = PREDECESSOR_FILES
            .iter()
            .find(|(logical, _, _)| path == Path::new(logical))
        {
            let bytes = fs::read(snapshot)?;
            require_digest(digest, &bytes, snapshot)?;
            hasher.update(bytes);
            replaced = true;
        } else {
            hasher.update(fs::read(path)?);
        }
    }
    Ok(replaced.then(|| format!("{:x}", hasher.finalize())))
}

fn inventory() -> &'static Value {
    INVENTORY.get_or_init(|| {
        serde_json::from_str(include_str!("../populations/precision-gaps-v1.json"))
            .expect("checked-in precision inventory is JSON")
    })
}

pub(crate) fn templates(language: &str) -> Vec<&'static str> {
    inventory()["templates"]
        .as_array()
        .expect("precision templates")
        .iter()
        .filter(|row| {
            row["languages"]
                .as_array()
                .expect("precision languages")
                .iter()
                .any(|item| item == language)
        })
        .map(|row| row["template_id"].as_str().expect("precision template ID"))
        .collect()
}

pub(crate) fn template_case(case: &Value) -> bool {
    case["template_id"].as_str().is_some_and(|template| {
        inventory()["templates"]
            .as_array()
            .expect("precision templates")
            .iter()
            .any(|row| row["template_id"] == template)
    })
}

#[cfg(test)]
pub(crate) fn case_count() -> usize {
    inventory()["cases"]
        .as_array()
        .expect("precision cases")
        .len()
}

fn verify_case(root: &Path, entry: &Value) -> Result<Value> {
    let relative = entry["path"].as_str().context("precision case path")?;
    let bytes = fs::read(repository_path(root, relative)?)?;
    require_digest(
        entry["sha256"].as_str().context("precision case digest")?,
        &bytes,
        relative,
    )?;
    let case: Value = serde_json::from_slice(&bytes)?;
    for key in ["id", "template_id", "language", "polarity"] {
        if entry[key].as_str().is_none() || entry[key] != case[key] {
            bail!("precision case {relative}: {key} mismatch");
        }
    }
    if case["track"] != "taint"
        || case["score_tier"] != "core"
        || case["model_profile"] != "benchmark-controlled"
    {
        bail!("precision case {relative}: track/tier/profile mismatch");
    }
    validate_fixture_digests(root, relative, entry, &case)?;
    Ok(case)
}

/// Historical validators still require their complete original file set.
/// Additional files qualify only at their registered paths with exact bytes.
/// A historical-only test checkout need not contain prospective additions.
pub(crate) fn historical_paths(
    root: &Path,
    mut paths: BTreeSet<PathBuf>,
) -> Result<BTreeSet<PathBuf>> {
    for entry in inventory()["cases"].as_array().context("precision cases")? {
        let relative = PathBuf::from(entry["path"].as_str().context("precision path")?);
        if paths.contains(&relative) {
            verify_case(root, entry)?;
            paths.remove(&relative);
        }
    }
    Ok(paths)
}

/// Require the entire prospective addition, including every registered pair.
pub(crate) fn validate(root: &Path) -> Result<()> {
    if inventory()["schema_version"] != 1 || inventory()["status"] != "prospective" {
        bail!("precision inventory identity mismatch");
    }
    let mut expected = BTreeSet::new();
    for row in inventory()["templates"]
        .as_array()
        .context("precision templates")?
    {
        let template = row["template_id"].as_str().context("precision template")?;
        for language in row["languages"].as_array().context("precision languages")? {
            let language = language.as_str().context("precision language")?;
            if crate::templates::challenge_rollout(language).is_none() {
                bail!("unknown precision language {language}");
            }
            for polarity in ["positive", "negative"] {
                if !expected.insert((template, language, polarity)) {
                    bail!("duplicate precision registration {template}/{language}/{polarity}");
                }
            }
        }
    }
    let mut actual = BTreeSet::new();
    let mut paths = BTreeSet::new();
    let mut ids = BTreeSet::new();
    for entry in inventory()["cases"].as_array().context("precision cases")? {
        verify_case(root, entry)?;
        let text = |key| entry[key].as_str().context("precision case field");
        if !paths.insert(text("path")?) || !ids.insert(text("id")?) {
            bail!("duplicate precision case path or ID");
        }
        if !actual.insert((text("template_id")?, text("language")?, text("polarity")?)) {
            bail!("duplicate precision pair member");
        }
    }
    if actual != expected {
        bail!("precision inventory does not contain its exact registered pairs");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn predecessor_snapshots_are_exact_git_source_bytes() {
        for (logical, snapshot, digest) in PREDECESSOR_FILES {
            let result = std::process::Command::new("git")
                .args(["show", &format!("{PREDECESSOR_REVISION}:{logical}")])
                .output()
                .unwrap();
            assert!(result.status.success(), "{logical}");
            require_digest(digest, &result.stdout, logical).unwrap();
            assert_eq!(fs::read(snapshot).unwrap(), result.stdout);
        }
    }

    #[test]
    fn predecessor_hash_keeps_every_other_input_live() {
        let path =
            std::env::temp_dir().join(format!("dfb-precision-config-{}", std::process::id()));
        fs::write(&path, b"original query").unwrap();
        let paths = BTreeSet::from([PathBuf::from(PREDECESSOR_FILES[0].0), path.clone()]);
        let original = predecessor_configuration_hash(&paths).unwrap().unwrap();
        fs::write(&path, b"changed query").unwrap();
        assert_ne!(
            original,
            predecessor_configuration_hash(&paths).unwrap().unwrap()
        );
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn additions_are_complete_and_historical_inputs_stay_separate() {
        validate(Path::new(".")).unwrap();
        let paths = crate::cases::all_case_paths().into_iter().collect();
        let historical = historical_paths(Path::new("."), paths).unwrap();
        assert_eq!(historical.len(), 1108);
        assert_eq!(crate::cases::all_case_paths().len(), 1108 + case_count());
    }

    #[test]
    fn a_registered_path_cannot_hide_changed_case_bytes() {
        let entry = &inventory()["cases"][0];
        let relative = PathBuf::from(entry["path"].as_str().unwrap());
        let root =
            std::env::temp_dir().join(format!("dfb-precision-digest-{}", std::process::id()));
        let path = root.join(&relative);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, b"{}").unwrap();
        let error = historical_paths(&root, BTreeSet::from([relative])).unwrap_err();
        assert!(error.to_string().contains("digest mismatch"));
        fs::remove_dir_all(root).unwrap();
    }
}
