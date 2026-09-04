//! The preregistered template identities every scored population is built
//! from: the sixteen kernel templates, the reduced set for languages whose
//! exception-catch cell is inapplicable, the thirteen challenge templates,
//! and the per-language rollout rows that decide which of them a language's
//! core denominator contains.

use serde_json::Value;

/// One positive and one negative assertion for each scored template. Runner-side
/// population checks read their denominator from `expected_core_case_count`,
/// which follows the rollout table; this constant is the fixed classic
/// expectation the regression tests pin against.
#[cfg(test)]
pub(crate) const KERNEL_CASE_COUNT: usize = 2 * KERNEL_TEMPLATE_IDS.len();
/// The sixteen scored propagation templates. Every language kernel preserves
/// these identities exactly; see docs/applicability-matrix.md.
pub(crate) const KERNEL_TEMPLATE_IDS: [&str; 16] = [
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
/// The core population of a language whose exception-catch cell is
/// inapplicable: the sixteen scored templates minus
/// `dfb-template-exception-catch`. docs/applicability-matrix.md classifies that
/// cell as **inapplicable** to both C and Rust, for different reasons — no C
/// construct transfers a typed value to a handler, and `setjmp`/`longjmp` does
/// not preserve the template's value-carrying intent; Rust's panics are not the
/// idiomatic recoverable transfer, `std::panic::catch_unwind` is not guaranteed
/// under `panic=abort`, and the payload is type-erased as `Box<dyn Any>`. The
/// two exclusions land on the same template, so the two languages share one
/// template set rather than two identical copies. An inapplicable cell reduces
/// only its own language's denominator, never any other's; the construct each
/// language uses instead (C's error-code return, Rust's `Result`/`?`) is routed
/// to `language-extension` cases scored on their own tier and absent from this
/// set.
pub(crate) const KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH: [&str; 15] = [
    "dfb-template-alias-propagation-separation",
    "dfb-template-argument-position-separation",
    "dfb-template-arithmetic-expression-propagation",
    "dfb-template-array-element-separation",
    "dfb-template-branch-join",
    "dfb-template-call-context-separation",
    "dfb-template-direct-propagation",
    "dfb-template-infeasible-branch",
    "dfb-template-local-multi-step-chain",
    "dfb-template-local-overwrite-kill",
    "dfb-template-loop-carried-kill",
    "dfb-template-object-separation",
    "dfb-template-return-relay-one-hop",
    "dfb-template-return-relay-two-hop",
    "dfb-template-same-object-field-separation",
];
/// One positive and one negative assertion for each template a 15-template
/// kernel scores. Runner-side population checks read their denominator from
/// `expected_core_case_count`, which follows the rollout table; this constant
/// is the fixed classic expectation the regression tests pin against.
#[cfg(test)]
pub(crate) const KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH: usize =
    2 * KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH.len();

/// The `template_id` prefix every challenge-tier template carries. It is load
/// bearing in two places: the smoke population refuses any case that carries it
/// (see `smoke_population_case`), and the preregistered Semgrep CE partition is
/// keyed by template ID rather than by fixture tags.
pub(crate) const CHALLENGE_TEMPLATE_PREFIX: &str = "dfb-template-chal-";

/// The thirteen challenge templates preregistered in docs/challenge-tier.md.
/// The IDs are fixed by that document and are never reused for different
/// semantics; a badly posed template is retired by amendment, not rewritten.
/// They carry `score_tier: "core"` — there is no new score tier — so they fold
/// into each language's core denominator as that language's fixtures land.
pub(crate) const CHALLENGE_TEMPLATE_IDS: [&str; 13] = [
    "dfb-template-chal-anonymous-implementation",
    "dfb-template-chal-callback-registration",
    "dfb-template-chal-closure-capture",
    "dfb-template-chal-computed-property",
    "dfb-template-chal-context-pair-depth2",
    "dfb-template-chal-deep-relay-chain",
    "dfb-template-chal-dispatch-table",
    "dfb-template-chal-element-object",
    "dfb-template-chal-function-field",
    "dfb-template-chal-map-iteration",
    "dfb-template-chal-nested-access-path",
    "dfb-template-chal-recursive-carry",
    "dfb-template-chal-reflective-invocation",
];
/// The challenge set of a language with no run-time reflection at all.
/// docs/challenge-tier.md classifies `dfb-template-chal-reflective-invocation`
/// **inapplicable** to C++ (no standard facility resolves a member function
/// from a string; the nearest construct *is* the dispatch table, and encoding
/// it twice would inflate the denominator without asking a second question) and
/// to Rust (`std::any::Any` downcasts to a known static type and offers no
/// name-based lookup). The two exclusions land on the same template, so the two
/// languages share one set rather than two identical copies.
pub(crate) const CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION: [&str; 12] = [
    "dfb-template-chal-anonymous-implementation",
    "dfb-template-chal-callback-registration",
    "dfb-template-chal-closure-capture",
    "dfb-template-chal-computed-property",
    "dfb-template-chal-context-pair-depth2",
    "dfb-template-chal-deep-relay-chain",
    "dfb-template-chal-dispatch-table",
    "dfb-template-chal-element-object",
    "dfb-template-chal-function-field",
    "dfb-template-chal-map-iteration",
    "dfb-template-chal-nested-access-path",
    "dfb-template-chal-recursive-carry",
];
/// C's challenge set: nine of thirteen. docs/challenge-tier.md excludes
/// reflective invocation (no run-time reflection), computed property (no
/// computed member access and no standard associative container), closure
/// capture (no closures — a function pointer plus a context struct is an
/// ordinary argument the classic core already covers), and anonymous
/// implementation (no anonymous functions and no anonymous types). Every
/// exclusion is a genuine absence of the construct, and it reduces only C's
/// own denominator.
pub(crate) const CHALLENGE_TEMPLATE_IDS_C: [&str; 9] = [
    "dfb-template-chal-callback-registration",
    "dfb-template-chal-context-pair-depth2",
    "dfb-template-chal-deep-relay-chain",
    "dfb-template-chal-dispatch-table",
    "dfb-template-chal-element-object",
    "dfb-template-chal-function-field",
    "dfb-template-chal-map-iteration",
    "dfb-template-chal-nested-access-path",
    "dfb-template-chal-recursive-carry",
];

/// One language's row in the challenge rollout table.
///
/// This is the single authoritative statement of what a language's core
/// denominator is. Every population check — Bifrost, CodeQL, Joern, Semgrep,
/// and the corpus-wide balance validator — reads it, so a wave PR expands a
/// language by editing exactly one row and nothing else.
pub(crate) struct ChallengeRollout {
    /// The `language` field of the case metadata.
    pub(crate) language: &'static str,
    /// The language's name in diagnostics.
    pub(crate) display: &'static str,
    /// The frozen classic core: sixteen templates, or fifteen where
    /// docs/applicability-matrix.md classifies the exception-catch cell
    /// inapplicable.
    pub(crate) classic: &'static [&'static str],
    /// The challenge templates docs/challenge-tier.md classifies applicable to
    /// this language. This is preregistered and never edited by a wave PR.
    pub(crate) challenge: &'static [&'static str],
    /// **The flag a wave PR flips.** `false` means this language's challenge
    /// fixtures do not exist yet and every population check expects its
    /// classic set; the language PR that authors the fixtures flips it to
    /// `true` in the same change, and every check then expects
    /// `classic + challenge` without any other code moving. The rollout is
    /// complete — all thirteen rows are `true` — so the flag now records that
    /// history and guards against a row being un-flipped; it stays because a
    /// future language joins the table at `false`.
    pub(crate) rolled_out: bool,
}

impl ChallengeRollout {
    /// This language's current core denominator: the classic set until its
    /// fixtures land, the expanded set afterwards.
    pub(crate) fn expected_templates(&self) -> Vec<&'static str> {
        let mut templates = self.classic.to_vec();
        if self.rolled_out {
            templates.extend_from_slice(self.challenge);
        }
        templates
    }
}

/// The rollout table. Ordered by docs/challenge-tier.md's wave plan: wave 1
/// (the saturated kernels), wave 2 (near-parity), wave 3 (adapted-construct),
/// wave 4 (analyzer-coverage-gated). The applicable challenge sets are fixed by
/// the preregistration's applicability matrix and are not a wave's to change;
/// only `rolled_out` moves.
pub(crate) const CHALLENGE_ROLLOUT: [ChallengeRollout; 13] = [
    ChallengeRollout {
        language: "java",
        display: "Java",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "javascript",
        display: "JavaScript",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "python",
        display: "Python",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "typescript",
        display: "TypeScript",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "kotlin",
        display: "Kotlin",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "csharp",
        display: "C#",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "scala",
        display: "Scala",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "go",
        display: "Go",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "cpp",
        display: "C++",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "rust",
        display: "Rust",
        classic: &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH,
        challenge: &CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "c",
        display: "C",
        classic: &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH,
        challenge: &CHALLENGE_TEMPLATE_IDS_C,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "php",
        display: "PHP",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
    ChallengeRollout {
        language: "ruby",
        display: "Ruby",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: true,
    },
];

/// This language's row, or `None` for a language the benchmark does not cover.
pub(crate) fn challenge_rollout(language: &str) -> Option<&'static ChallengeRollout> {
    CHALLENGE_ROLLOUT
        .iter()
        .find(|row| row.language == language)
}

/// Whether this language's challenge fixtures have landed. A wave PR flips the
/// row; nothing else in the tree needs to know.
#[cfg(test)]
pub(crate) fn challenge_rolled_out(language: &str) -> bool {
    challenge_rollout(language).is_some_and(|row| row.rolled_out)
}

/// The core denominator every population check for this language uses. A
/// language with no row keeps the sixteen-template classic core, which is what
/// a new language starts from.
pub(crate) fn expected_core_templates(language: &str) -> Vec<&'static str> {
    challenge_rollout(language)
        .map(ChallengeRollout::expected_templates)
        .unwrap_or_else(|| KERNEL_TEMPLATE_IDS.to_vec())
}

/// The core assertion count of this language: one positive and one negative per
/// template in its current denominator.
pub(crate) fn expected_core_case_count(language: &str) -> usize {
    2 * expected_core_templates(language).len()
}

/// Whether a case is a challenge-tier assertion, decided from its
/// `template_id` alone.
pub(crate) fn challenge_template_case(case: &Value) -> bool {
    case["template_id"]
        .as_str()
        .is_some_and(|template| template.starts_with(CHALLENGE_TEMPLATE_PREFIX))
}
