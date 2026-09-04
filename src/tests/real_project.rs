//! Regression tests for `crate::real_project`: the seeded draw replays, every
//! exclusion cites a declared criterion, and every pin binds two revisions.

use crate::real_project::{
    REAL_PROJECT_DRAW, real_project_draw_key, real_project_pin_paths, validate_real_project_slice,
};
use serde_json::{Value, json};
use std::fs;

/// The draw key is the whole integrity claim of the real-project slice, so
/// it is pinned to a literal here rather than recomputed by the same
/// expression the production code uses. If the seed, the separator, or the
/// hash ever changes, every committed pin record stops validating and this
/// test says why.
#[test]
pub(crate) fn the_real_project_draw_key_is_stable() {
    assert_eq!(
        real_project_draw_key("dataflowbench-real-project-wave-r1", "GHSA-vj76-c3g6-qr5v"),
        "0d4260b164eb9f1eb560508d963d434d7a12b3a5418b7285ce07fc42a4388099"
    );
    assert_ne!(
        real_project_draw_key("dataflowbench-real-project-wave-r1", "GHSA-vj76-c3g6-qr5v"),
        real_project_draw_key("dataflowbench-real-project-wave-r2", "GHSA-vj76-c3g6-qr5v")
    );
}

/// The committed slice replays: `validate` recomputes every draw key from
/// the retained frame and accepts the walk and the six pin records as they
/// stand.
#[test]
pub(crate) fn the_committed_real_project_slice_replays() {
    assert_eq!(validate_real_project_slice().unwrap(), 6);
}

/// Every eligibility criterion an exclusion cites must be declared by the
/// draw record, and every stratum must stop at its last selection. These
/// are the two properties that keep the walk from becoming a place to
/// record a decision without naming its reason.
#[test]
pub(crate) fn every_real_project_exclusion_cites_a_declared_criterion() {
    let draw: Value =
        serde_json::from_str(&fs::read_to_string(REAL_PROJECT_DRAW).unwrap()).unwrap();
    let criteria = draw["criteria"].as_object().unwrap();
    assert!(!criteria.is_empty());
    for (stratum, rows) in draw["walk"].as_object().unwrap() {
        let rows = rows.as_array().unwrap();
        assert_eq!(
            rows.last().unwrap()["disposition"],
            json!("selected"),
            "stratum {stratum} must end at a selection"
        );
        for row in rows {
            let exclusions = row["exclusions"].as_array().unwrap();
            assert_eq!(
                row["disposition"] == json!("excluded"),
                !exclusions.is_empty(),
                "stratum {stratum} entry {} disagrees with its exclusions",
                row["ghsa_id"]
            );
            for exclusion in exclusions {
                assert!(
                    criteria.contains_key(exclusion["criterion"].as_str().unwrap()),
                    "undeclared criterion {}",
                    exclusion["criterion"]
                );
            }
        }
    }
}

/// A pin record pins two *different* revisions of the same repository and
/// binds an archive URL that names the revision it claims. Nothing about
/// the slice works if a digest can drift away from the revision it is
/// supposed to witness.
#[test]
pub(crate) fn every_real_project_pin_binds_two_revisions_and_their_archives() {
    let paths = real_project_pin_paths().unwrap();
    assert_eq!(paths.len(), 6);
    for path in paths {
        let pin: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        let slug = format!(
            "{}/{}",
            pin["repository"]["owner"].as_str().unwrap(),
            pin["repository"]["name"].as_str().unwrap()
        );
        let vulnerable = pin["revisions"]["vulnerable"]["revision"].as_str().unwrap();
        let fixed = pin["revisions"]["fixed"]["revision"].as_str().unwrap();
        assert_ne!(vulnerable, fixed, "{}", path.display());
        for (kind, revision) in [("vulnerable", vulnerable), ("fixed", fixed)] {
            assert_eq!(
                pin["revisions"][kind]["source_archive"]["url"],
                json!(format!(
                    "https://codeload.github.com/{slug}/tar.gz/{revision}"
                )),
                "{}",
                path.display()
            );
            assert_ne!(
                pin["revisions"][kind]["source_archive"]["sha256"],
                Value::Null
            );
        }
        assert_eq!(pin["ground_truth"]["status"], json!("proposed"));
        assert_eq!(pin["ground_truth"]["adjudication"], json!("pending"));
        // Wave R1's review is maintainer-only by an explicit, recorded
        // waiver. A pin that ever claims independent review has to name the
        // reviewers who back the claim.
        assert_eq!(
            pin["ground_truth"]["review_independence"],
            json!("maintainer-only"),
            "{}",
            path.display()
        );
    }
}
