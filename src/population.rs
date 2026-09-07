//! Exact released input populations, independent of moving main's corpus.
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
static ACTIVE: OnceLock<Population> = OnceLock::new();

pub(crate) struct Population {
    cases: BTreeMap<String, (PathBuf, Value)>,
}

pub(crate) fn active() -> Option<&'static Population> {
    ACTIVE.get()
}

pub(crate) fn initialize(name: Option<&str>) -> Result<()> {
    let Some(name) = name else {
        return Ok(());
    };
    if name != "v0.7.0" {
        bail!("unknown population {name:?}; supported: v0.7.0");
    }
    let population = Population::load(Path::new("."))?;
    ACTIVE
        .set(population)
        .map_err(|_| anyhow::anyhow!("population already initialized"))?;
    Ok(())
}

impl Population {
    pub(crate) fn load(root: &Path) -> Result<Self> {
        require_digest(
            BASELINE_SHA256,
            BASELINE.as_bytes(),
            "pinned v0.7.0 population manifest",
        )?;
        let manifest: Value = serde_json::from_str(BASELINE)?;
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
        Ok(Self { cases })
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
                "v0.7.0 population mismatch: missing={:?}, unexpected={:?}",
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
                bail!("selected case {id} is outside or differs from pinned v0.7.0 population");
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
