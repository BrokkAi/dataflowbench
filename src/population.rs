//! Exact released and prospective input populations, independent of moving main.
use crate::freeze::{
    fixture_revision_for_manifest_cases, repository_path, require_digest, validate_fixture_digests,
};
use anyhow::{Context, Result, bail};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::OnceLock,
};

const BASELINE: &str = include_str!("../populations/v0.7.0.json");
const BASELINE_SHA256: &str = "6323c36ef5790e447b8f0990ac5670a619165ea40fd56adda20d3fff3bd54519";
const SWIFT: &str = include_str!("../populations/swift-synthetic-v1.json");
const SWIFT_SHA256: &str = "95e3075b26ebd55cff6dc5fa0fc413ed15733c2ae9d8e21014f80395ca24c4f5";
const SWIFT_V2: &str = include_str!("../populations/swift-synthetic-v2.json");
const SWIFT_V2_SHA256: &str = "b6c29ff47942c73c34bd479c7ce1137b5bf97d0fbede1204f8eae16aa32007bb";
static ACTIVE: OnceLock<Population> = OnceLock::new();

pub(crate) struct Population {
    name: &'static str,
    cases: BTreeMap<String, (PathBuf, Value)>,
}

pub(crate) fn active() -> Option<&'static Population> {
    ACTIVE.get()
}

pub(crate) fn initialize(name: Option<&str>) -> Result<()> {
    let Some(name) = name else {
        return Ok(());
    };
    let population = match name {
        "v0.7.0" => Population::load(Path::new("."))?,
        "swift-synthetic-v1" => Population::load_swift(Path::new("."))?,
        "swift-synthetic-v2" => Population::load_swift_v2(Path::new("."))?,
        _ => bail!(
            "unknown population {name:?}; supported: v0.7.0, swift-synthetic-v1, swift-synthetic-v2"
        ),
    };
    ACTIVE
        .set(population)
        .map_err(|_| anyhow::anyhow!("population already initialized"))?;
    Ok(())
}

impl Population {
    pub(crate) fn load(root: &Path) -> Result<Self> {
        Self::load_manifest(root, "v0.7.0", BASELINE, BASELINE_SHA256)
    }

    fn load_swift(root: &Path) -> Result<Self> {
        Self::load_manifest(root, "swift-synthetic-v1", SWIFT, SWIFT_SHA256)
    }

    fn load_swift_v2(root: &Path) -> Result<Self> {
        Self::load_manifest(root, "swift-synthetic-v2", SWIFT_V2, SWIFT_V2_SHA256)
    }

    fn load_manifest(root: &Path, name: &'static str, bytes: &str, digest: &str) -> Result<Self> {
        require_digest(
            digest,
            bytes.as_bytes(),
            &format!("pinned {name} population manifest"),
        )?;
        let manifest: Value = serde_json::from_str(bytes)?;
        let mut cases = BTreeMap::new();
        let mut paths = BTreeSet::new();
        let mut revision_paths = Vec::new();
        for selected in manifest["cases"].as_array().context("population cases")? {
            let id = selected["id"].as_str().context("population case id")?;
            let relative = selected["path"].as_str().context("population case path")?;
            let path = repository_path(root, relative)?;
            let bytes = fs::read(&path)?;
            require_digest(
                selected["sha256"].as_str().context("case digest")?,
                &bytes,
                id,
            )?;
            let case: Value = serde_json::from_slice(&bytes)?;
            if case["id"].as_str() != Some(id) {
                bail!("population case ID mismatch: {id}");
            }
            for field in [
                "template_id",
                "polarity",
                "score_tier",
                "track",
                "model_profile",
            ] {
                if selected[field] != case[field] {
                    bail!("population case {id} has mismatched {field}");
                }
            }
            validate_fixture_digests(root, relative, selected, &case)?;
            if !paths.insert(relative.to_string())
                || cases
                    .insert(id.to_string(), (PathBuf::from(relative), case))
                    .is_some()
            {
                bail!("duplicate population case {id}");
            }
            revision_paths.push((relative.to_string(), path));
        }
        let revision = fixture_revision_for_manifest_cases(root, &revision_paths)?;
        if Some(revision.as_str()) != manifest["fixture_revision"].as_str() {
            bail!("population fixture revision mismatch");
        }
        Ok(Self { name, cases })
    }

    pub(crate) fn paths(&self) -> Vec<PathBuf> {
        let mut paths: Vec<_> = self.cases.values().map(|(path, _)| path.clone()).collect();
        paths.sort();
        paths
    }

    pub(crate) fn core_templates(&self, language: &str) -> Vec<&str> {
        self.cases
            .values()
            .filter(|(_, case)| {
                case["language"] == language
                    && case["score_tier"] == "core"
                    && case["track"] == "taint"
            })
            .map(|(_, case)| case["template_id"].as_str().expect("pinned case template"))
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect()
    }

    pub(crate) fn validate_case_ids(&self, actual: &BTreeSet<String>) -> Result<()> {
        let expected: BTreeSet<_> = self.cases.keys().cloned().collect();
        if &expected != actual {
            bail!(
                "{} population mismatch: missing={:?}, unexpected={:?}",
                self.name,
                expected.difference(actual).collect::<Vec<_>>(),
                actual.difference(&expected).collect::<Vec<_>>()
            );
        }
        Ok(())
    }

    pub(crate) fn validate_members(&self, cases: &[(PathBuf, Value)]) -> Result<()> {
        for (path, case) in cases {
            let id = case["id"].as_str().context("selected case id")?;
            if self.cases.get(id) != Some(&(path.clone(), case.clone())) {
                bail!(
                    "selected case {id} is outside or differs from pinned {} population",
                    self.name
                );
            }
        }
        Ok(())
    }
}

/// Validate the prospective Swift fixture inventory, without activating any analyzer.
pub(crate) fn validate_swift_population(root: &Path) -> Result<()> {
    let previous = Population::load_swift(root)?;
    let population = Population::load_swift_v2(root)?;
    for (id, original) in &previous.cases {
        if population.cases.get(id) != Some(original) {
            bail!("Swift v2 changed immutable v1 member {id}");
        }
    }
    let actual: BTreeSet<_> = walkdir::WalkDir::new(root.join("cases/taint/swift"))
        .into_iter()
        .collect::<std::result::Result<Vec<_>, _>>()?
        .into_iter()
        .filter(|entry| entry.file_type().is_file() && entry.file_name() == "case.json")
        .map(|entry| entry.path().strip_prefix(root).map(Path::to_path_buf))
        .collect::<std::result::Result<_, _>>()?;
    let expected: BTreeSet<_> = population.paths().into_iter().collect();
    if actual != expected {
        bail!("Swift prospective population file set differs from manifest");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn swift_prospective_population_is_separate_and_complete() {
        let swift = Population::load_swift(Path::new(".")).unwrap();
        let baseline = Population::load(Path::new(".")).unwrap();
        assert_eq!(swift.paths().len(), 90);
        assert_eq!(swift.core_templates("swift").len(), 33);
        assert!(swift.core_templates("java").is_empty());
        assert!(
            swift
                .cases
                .keys()
                .all(|id| !baseline.cases.contains_key(id))
        );
        let mut tiers = BTreeMap::new();
        for (_, case) in swift.cases.values() {
            assert_eq!(case["language"], "swift");
            assert_eq!(case["model_profile"], "benchmark-controlled");
            *tiers
                .entry(case["score_tier"].as_str().unwrap())
                .or_insert(0) += 1;
        }
        assert_eq!(
            tiers,
            BTreeMap::from([("calibration", 4), ("core", 66), ("modeling", 20)])
        );
        validate_swift_population(Path::new(".")).unwrap();
    }

    #[test]
    fn swift_v2_extends_v1_without_profile_or_byte_drift() {
        let v1 = Population::load_swift(Path::new(".")).unwrap();
        let v2 = Population::load_swift_v2(Path::new(".")).unwrap();
        assert_eq!(v2.cases.len(), 104);
        for (id, entry) in &v1.cases {
            assert_eq!(v2.cases.get(id), Some(entry));
        }
        let additions: Vec<_> = v2
            .cases
            .iter()
            .filter(|(id, _)| !v1.cases.contains_key(*id))
            .collect();
        assert_eq!(additions.len(), 14);
        assert_eq!(
            additions
                .iter()
                .filter(|(_, (_, c))| c["model_profile"] == "tool-native")
                .count(),
            12
        );
        assert_eq!(
            additions
                .iter()
                .filter(|(_, (_, c))| c["score_tier"] == "language-extension")
                .count(),
            2
        );
        assert!(v1.validate_members(&[additions[0].1.clone()]).is_err());
        assert_eq!(v2.core_templates("swift"), v1.core_templates("swift"));
    }

    #[test]
    fn swift_manifest_rejects_missing_extra_and_changed_inputs() {
        let root = std::env::temp_dir().join(format!(
            "dfb-swift-population-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let manifest: Value = serde_json::from_str(SWIFT_V2).unwrap();
        for case in manifest["cases"].as_array().unwrap() {
            for relative in std::iter::once(case["path"].as_str().unwrap()).chain(
                case["fixture_digests"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|f| f["path"].as_str().unwrap()),
            ) {
                let dest = root.join(relative);
                fs::create_dir_all(dest.parent().unwrap()).unwrap();
                fs::copy(relative, dest).unwrap();
            }
        }
        validate_swift_population(&root).unwrap();
        let first = &manifest["cases"][0];
        for relative in [
            first["path"].as_str().unwrap(),
            first["fixture_digests"][0]["path"].as_str().unwrap(),
        ] {
            let path = root.join(relative);
            let original = fs::read(&path).unwrap();
            let mut changed = original.clone();
            changed.push(b' ');
            fs::write(&path, changed).unwrap();
            assert!(validate_swift_population(&root).is_err());
            fs::remove_file(&path).unwrap();
            assert!(validate_swift_population(&root).is_err());
            fs::write(&path, original).unwrap();
        }
        let extra = root.join("cases/taint/swift/unregistered-positive/case.json");
        fs::create_dir_all(extra.parent().unwrap()).unwrap();
        fs::copy(root.join(first["path"].as_str().unwrap()), &extra).unwrap();
        assert!(
            validate_swift_population(&root)
                .unwrap_err()
                .to_string()
                .contains("file set")
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn baseline_exact_bytes_and_new_kernels_are_separate() {
        let population = Population::load(Path::new(".")).unwrap();
        assert_eq!(population.paths().len(), 852);
        let selected: BTreeSet<_> = population.paths().into_iter().collect();
        let current: BTreeSet<_> = crate::cases::all_case_paths().into_iter().collect();
        assert!(selected.is_subset(&current));
        assert!(!current.difference(&selected).collect::<Vec<_>>().is_empty());
        let mut ids: BTreeSet<_> = population.cases.keys().cloned().collect();
        population.validate_case_ids(&ids).unwrap();
        ids.pop_first();
        assert!(
            population
                .validate_case_ids(&ids)
                .unwrap_err()
                .to_string()
                .contains("missing=")
        );
        ids = population.cases.keys().cloned().collect();
        let new_path = current.difference(&selected).next().unwrap();
        let new_case: Value = serde_json::from_slice(&fs::read(new_path).unwrap()).unwrap();
        ids.insert(new_case["id"].as_str().unwrap().to_string());
        assert!(
            population
                .validate_case_ids(&ids)
                .unwrap_err()
                .to_string()
                .contains("unexpected=")
        );
        assert!(
            population
                .validate_members(&[(new_path.clone(), new_case)])
                .is_err()
        );
    }

    #[test]
    fn baseline_rejects_changed_and_missing_case_and_fixture_bytes() {
        let root = std::env::temp_dir().join(format!(
            "dfb-population-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let manifest: Value = serde_json::from_str(BASELINE).unwrap();
        for case in manifest["cases"].as_array().unwrap() {
            let paths = std::iter::once(case["path"].as_str().unwrap()).chain(
                case["fixture_digests"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|f| f["path"].as_str().unwrap()),
            );
            for relative in paths {
                let dest = root.join(relative);
                fs::create_dir_all(dest.parent().unwrap()).unwrap();
                fs::copy(relative, dest).unwrap();
            }
        }
        Population::load(&root).unwrap();
        let first = &manifest["cases"][0];
        for relative in [
            first["path"].as_str().unwrap(),
            first["fixture_digests"][0]["path"].as_str().unwrap(),
        ] {
            let path = root.join(relative);
            let original = fs::read(&path).unwrap();
            let mut changed = original.clone();
            changed.push(b' ');
            fs::write(&path, changed).unwrap();
            assert!(
                Population::load(&root)
                    .err()
                    .unwrap()
                    .to_string()
                    .contains("digest mismatch")
            );
            fs::remove_file(&path).unwrap();
            assert!(
                Population::load(&root)
                    .err()
                    .unwrap()
                    .to_string()
                    .contains("missing")
            );
            fs::write(&path, original).unwrap();
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn active_selection_reaches_warm_runners_without_changing_full_validation() {
        const CHILD: &str = "DFB_POPULATION_TEST_CHILD";
        if std::env::var_os(CHILD).is_none() {
            let status = std::process::Command::new(std::env::current_exe().unwrap())
                .args(["--exact", "population::tests::active_selection_reaches_warm_runners_without_changing_full_validation"])
                .env(CHILD, "1").status().unwrap();
            assert!(status.success());
            return;
        }
        initialize(Some("v0.7.0")).unwrap();
        assert_eq!(crate::cases::case_paths().len(), 852);
        assert_eq!(
            crate::cases::fixture_revision().unwrap(),
            "sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151"
        );
        crate::cases::validate_cases().unwrap();
        for tool in [
            crate::latency::WarmTool::Joern,
            crate::latency::WarmTool::Semgrep,
        ] {
            let warm =
                crate::latency::warm_population(tool, crate::latency::WarmLanguage::Java).unwrap();
            assert!(!warm.cases.is_empty());
            active().unwrap().validate_members(&warm.cases).unwrap();
        }
    }

    #[test]
    fn active_swift_selection_preserves_full_validation_and_rejects_other_inputs() {
        const CHILD: &str = "DFB_SWIFT_POPULATION_TEST_CHILD";
        if std::env::var_os(CHILD).is_none() {
            let status = std::process::Command::new(std::env::current_exe().unwrap())
                .args(["--exact", "population::tests::active_swift_selection_preserves_full_validation_and_rejects_other_inputs"])
                .env(CHILD, "1").status().unwrap();
            assert!(status.success());
            return;
        }
        initialize(Some("swift-synthetic-v1")).unwrap();
        assert_eq!(crate::cases::case_paths().len(), 90);
        crate::cases::validate_cases().unwrap();
        // A selected execution population must not narrow the retained-report
        // sweep's configuration derivation for older language populations.
        for stem in [
            "bifrost-java-kernel",
            "codeql-java-kernel",
            "codeql-python-kernel",
        ] {
            let report: Value =
                serde_json::from_str(&fs::read_to_string(format!("reports/{stem}.json")).unwrap())
                    .unwrap();
            assert_eq!(
                crate::report::configuration_hash_state(
                    stem,
                    report["configuration_hash"].as_str().unwrap(),
                    &mut None,
                )
                .unwrap(),
                crate::report::ConfigurationHashState::Current,
            );
        }
        let baseline = Population::load(Path::new(".")).unwrap();
        let outside = baseline.cases.values().next().unwrap().clone();
        assert!(active().unwrap().validate_members(&[outside]).is_err());
    }

    #[test]
    fn active_swift_v2_selection_keeps_v1_modeling_disjoint() {
        const CHILD: &str = "DFB_SWIFT_V2_POPULATION_TEST_CHILD";
        if std::env::var_os(CHILD).is_none() {
            let status = std::process::Command::new(std::env::current_exe().unwrap())
                .args([
                    "--exact",
                    "population::tests::active_swift_v2_selection_keeps_v1_modeling_disjoint",
                ])
                .env(CHILD, "1")
                .status()
                .unwrap();
            assert!(status.success());
            return;
        }
        initialize(Some("swift-synthetic-v2")).unwrap();
        assert_eq!(crate::cases::case_paths().len(), 104);
        crate::cases::validate_cases().unwrap();
        let cases = &active().unwrap().cases;
        assert_eq!(
            cases
                .values()
                .filter(|(_, c)| c["model_profile"] == "tool-native")
                .count(),
            12
        );
        assert_eq!(
            cases
                .values()
                .filter(|(_, c)| c["score_tier"] == "modeling"
                    && c["model_profile"] == "benchmark-controlled")
                .count(),
            20
        );
        let manifest: Value = serde_json::from_str(SWIFT_V2).unwrap();
        assert_eq!(
            crate::cases::fixture_revision().unwrap(),
            manifest["fixture_revision"].as_str().unwrap()
        );
        for (_, case) in cases
            .values()
            .filter(|(_, c)| c["model_profile"] == "tool-native")
        {
            for language in [
                crate::adapters::ModelingLanguage::Java,
                crate::adapters::ModelingLanguage::Javascript,
                crate::adapters::ModelingLanguage::Python,
            ] {
                assert!(!crate::native::native_case(case, language));
            }
        }
        let mut native = cases
            .values()
            .filter(|(_, c)| c["model_profile"] == "tool-native")
            .cloned()
            .collect::<Vec<_>>();
        native[0].1["tool_model_references"] = serde_json::json!({"codeql":"unqualified"});
        assert!(
            crate::native::validate_native_cases(&native)
                .unwrap_err()
                .to_string()
                .contains("cannot activate")
        );
    }

    #[test]
    fn baseline_template_denominators_remain_balanced() {
        let population = Population::load(Path::new(".")).unwrap();
        let languages: BTreeSet<_> = population
            .cases
            .values()
            .filter(|(_, c)| c["score_tier"] == "core")
            .map(|(_, c)| c["language"].as_str().unwrap())
            .collect();
        for language in languages {
            let cases: Vec<_> = population
                .cases
                .values()
                .filter(|(_, c)| c["score_tier"] == "core" && c["language"] == language)
                .cloned()
                .collect();
            crate::cases::validate_kernel_population_with(
                &cases,
                language,
                &population.core_templates(language),
            )
            .unwrap();
            let mut missing = cases.clone();
            missing.pop();
            assert!(
                crate::cases::validate_kernel_population_with(
                    &missing,
                    language,
                    &population.core_templates(language)
                )
                .is_err()
            );
        }
    }
}
