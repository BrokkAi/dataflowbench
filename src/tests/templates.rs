//! Regression tests for `crate::templates`.

use crate::cases::{case_paths, core_templates_for_language};
use crate::templates::{
    CHALLENGE_ROLLOUT, CHALLENGE_TEMPLATE_IDS, CHALLENGE_TEMPLATE_PREFIX, KERNEL_TEMPLATE_IDS,
    KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH, challenge_rolled_out, challenge_rollout,
    challenge_template_case, expected_core_case_count, expected_core_templates,
};
use serde_json::Value;
use std::{collections::BTreeMap, collections::BTreeSet, fs};

/// The C denominator is the sixteen scored templates minus the
/// inapplicable exception-catch cell, and nothing else.
#[test]
pub(crate) fn the_reduced_template_set_is_the_scored_set_without_exception_catch() {
    let scored = KERNEL_TEMPLATE_IDS.iter().copied().collect::<BTreeSet<_>>();
    let c = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    assert_eq!(
        scored.difference(&c).copied().collect::<Vec<_>>(),
        vec!["dfb-template-exception-catch"]
    );
    assert!(c.difference(&scored).next().is_none());
}

/// C and Rust exclude the same classic template for different reasons, so
/// they share one 15-template constant instead of two identical copies.
/// Both challenge rows are now flipped, so each language's corpus core is
/// that shared classic set plus its own challenge cells -- nine for C,
/// twelve for Rust. Their language-extension cases stay distinct and never
/// enter either core denominator.
#[test]
pub(crate) fn c_and_rust_share_the_scored_set_without_exception_catch() {
    let cases = case_paths()
        .into_iter()
        .map(|path| {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            (path, case)
        })
        .collect::<Vec<_>>();
    let classic = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    for language in ["c", "rust"] {
        let core = core_templates_for_language(&cases, language);
        // Both languages start from the same 15-template classic
        // constant and both have since expanded past it, so the constant
        // is a subset of either core rather than equal to it, and the
        // shared exclusion is what the two still have in common.
        assert!(classic.is_subset(&core), "{language} classic set");
        assert!(!core.contains("dfb-template-exception-catch"));
        // Each language's corpus is exactly its rollout row.
        assert_eq!(
            core,
            expected_core_templates(language)
                .into_iter()
                .collect::<BTreeSet<_>>()
        );
        assert_eq!(
            challenge_rolled_out(language),
            core.len() > classic.len(),
            "{language} corpus does not match its rollout state"
        );
    }
    assert_eq!(core_templates_for_language(&cases, "rust").len(), 27);
    assert_eq!(core_templates_for_language(&cases, "c").len(), 24);
    assert!(
        !core_templates_for_language(&cases, "rust")
            .contains("dfb-template-result-error-propagation")
    );
    let extension = cases
        .iter()
        .filter(|(_, case)| {
            case["language"] == "rust" && case["score_tier"] == "language-extension"
        })
        .collect::<Vec<_>>();
    assert_eq!(extension.len(), 2);
    for (_, case) in extension {
        assert_eq!(case["template_id"], "dfb-template-result-error-propagation");
    }
}

/// Every challenge case that exists in the corpus belongs to a language
/// whose row is rolled out, and lands in that language's core population
/// with a preregistered template ID.
#[test]
pub(crate) fn challenge_cases_exist_only_for_rolled_out_languages() {
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        if !challenge_template_case(&case) {
            continue;
        }
        let template = case["template_id"].as_str().unwrap();
        assert!(
            CHALLENGE_TEMPLATE_IDS.contains(&template),
            "{} carries an unpreregistered challenge template",
            path.display()
        );
        let language = case["language"].as_str().unwrap();
        assert!(
            challenge_rolled_out(language),
            "{} carries a challenge template while {language} is not rolled out",
            path.display()
        );
        assert_eq!(case["score_tier"], "core", "{}", path.display());
        assert!(
            expected_core_templates(language).contains(&template),
            "{} is not in {language}'s expanded core",
            path.display()
        );
    }
}

/// The rollout table is the one authoritative statement of each language's
/// denominator, and it must reproduce docs/challenge-tier.md's expanded
/// core table exactly.
#[test]
pub(crate) fn the_rollout_table_matches_the_preregistered_denominators() {
    let expanded: BTreeMap<&str, (usize, usize)> = BTreeMap::from([
        // language => (classic templates, applicable challenge templates)
        ("java", (16, 14)),
        ("javascript", (16, 14)),
        ("python", (16, 14)),
        ("typescript", (16, 14)),
        ("kotlin", (16, 14)),
        ("scala", (16, 14)),
        ("csharp", (16, 14)),
        ("go", (16, 14)),
        ("php", (16, 14)),
        ("ruby", (16, 14)),
        ("cpp", (16, 13)),
        ("c", (15, 9)),
        ("rust", (15, 12)),
    ]);
    assert_eq!(CHALLENGE_ROLLOUT.len(), expanded.len());
    for row in &CHALLENGE_ROLLOUT {
        let (classic, challenge) = expanded[row.language];
        assert_eq!(row.classic.len(), classic, "{} classic", row.language);
        assert_eq!(row.challenge.len(), challenge, "{} challenge", row.language);
        // Every challenge cell is one of the fourteen preregistered
        // templates; a language can narrow the set, never invent one.
        for template in row.challenge {
            assert!(
                CHALLENGE_TEMPLATE_IDS.contains(template),
                "{} claims unpreregistered template {template}",
                row.language
            );
            assert!(template.starts_with(CHALLENGE_TEMPLATE_PREFIX));
        }
        // The rollout is complete: Ruby was the last wave, so every one of
        // the thirteen rows is flipped and no language validates against
        // its classic set alone any more. This is the assertion that would
        // catch a row being silently un-flipped.
        assert!(row.rolled_out, "{} rollout state", row.language);
        assert!(
            challenge_rolled_out(row.language),
            "{} rollout state",
            row.language
        );
        // Every language's denominator is therefore its expanded core:
        // the classic templates plus its applicable challenge templates.
        let expected = classic + challenge;
        assert_eq!(row.expected_templates().len(), expected);
        assert_eq!(expected_core_case_count(row.language), 2 * expected);
    }
    // The exclusions docs/challenge-tier.md states, by name.
    let cpp = challenge_rollout("cpp").unwrap().challenge;
    let rust = challenge_rollout("rust").unwrap().challenge;
    let c = challenge_rollout("c").unwrap().challenge;
    for set in [cpp, rust, c] {
        assert!(!set.contains(&"dfb-template-chal-reflective-invocation"));
    }
    for set in [rust, c] {
        assert!(!set.contains(&"dfb-template-chal-interprocedural-exception-persistence"));
    }
    for excluded in [
        "dfb-template-chal-computed-property",
        "dfb-template-chal-closure-capture",
        "dfb-template-chal-anonymous-implementation",
    ] {
        assert!(!c.contains(&excluded), "C must exclude {excluded}");
    }
}
