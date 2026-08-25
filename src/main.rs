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

const CODEQL_JAVASCRIPT_QUERY: &str = "adapters/codeql/javascript/queries/JavaScriptKernel.ql";
const CODEQL_JAVASCRIPT_RAW_DIR: &str = "reports/raw/codeql-javascript";
const CODEQL_JAVASCRIPT_REPORT: &str = "reports/codeql-javascript-kernel.json";
const CODEQL_TYPESCRIPT_QUERY: &str = "adapters/codeql/typescript/queries/TypeScriptKernel.ql";
const CODEQL_TYPESCRIPT_RAW_DIR: &str = "reports/raw/codeql-typescript";
const CODEQL_TYPESCRIPT_REPORT: &str = "reports/codeql-typescript-kernel.json";
const CODEQL_PYTHON_QUERY: &str = "adapters/codeql/python/queries/PythonKernel.ql";
const CODEQL_KOTLIN_QUERY: &str = "adapters/codeql/kotlin/queries/KotlinKernel.ql";
const CODEQL_KOTLIN_RAW_DIR: &str = "reports/raw/codeql-kotlin-kernel";
const CODEQL_KOTLIN_REPORT: &str = "reports/codeql-kotlin-kernel.json";
const CODEQL_CSHARP_QUERY: &str = "adapters/codeql/csharp/queries/CSharpKernel.ql";
const CODEQL_CSHARP_RAW_DIR: &str = "reports/raw/codeql-csharp-kernel";
const CODEQL_CSHARP_REPORT: &str = "reports/codeql-csharp-kernel.json";
const CODEQL_C_QUERY: &str = "adapters/codeql/cpp/queries/CKernel.ql";
const CODEQL_C_RAW_DIR: &str = "reports/raw/codeql-c-kernel";
const CODEQL_C_REPORT: &str = "reports/codeql-c-kernel.json";
const CODEQL_CPP_QUERY: &str = "adapters/codeql/cpp/queries/CppKernel.ql";
const CODEQL_CPP_RAW_DIR: &str = "reports/raw/codeql-cpp-kernel";
const CODEQL_CPP_REPORT: &str = "reports/codeql-cpp-kernel.json";
const BIFROST_C_POLICY: &str = "adapters/bifrost/policies/core-c-kernel.rqlp";
const BIFROST_CPP_POLICY: &str = "adapters/bifrost/policies/core-cpp-kernel.rqlp";
const BIFROST_CSHARP_POLICY: &str = "adapters/bifrost/policies/core-csharp-kernel.rqlp";
const CODEQL_GO_QUERY: &str = "adapters/codeql/go/queries/GoKernel.ql";
const CODEQL_GO_RAW_DIR: &str = "reports/raw/codeql-go-kernel";
const CODEQL_GO_REPORT: &str = "reports/codeql-go-kernel.json";
const BIFROST_GO_POLICY: &str = "adapters/bifrost/policies/core-go-kernel.rqlp";
const CODEQL_RUST_QUERY: &str = "adapters/codeql/rust/queries/RustKernel.ql";
const CODEQL_RUST_RAW_DIR: &str = "reports/raw/codeql-rust-kernel";
const CODEQL_RUST_REPORT: &str = "reports/codeql-rust-kernel.json";
const BIFROST_RUST_POLICY: &str = "adapters/bifrost/policies/core-rust-kernel.rqlp";
const CODEQL_RUBY_QUERY: &str = "adapters/codeql/ruby/queries/RubyKernel.ql";
const CODEQL_RUBY_RAW_DIR: &str = "reports/raw/codeql-ruby-kernel";
const CODEQL_RUBY_REPORT: &str = "reports/codeql-ruby-kernel.json";
const BIFROST_RUBY_POLICY: &str = "adapters/bifrost/policies/core-ruby-kernel.rqlp";
/// The language-qualified Bifrost policy for the PHP kernel. PHP has no CodeQL
/// support in the pinned CLI at all, so Bifrost and Joern are its two analyzers;
/// see docs/php-kernel.md.
const BIFROST_PHP_POLICY: &str = "adapters/bifrost/policies/core-php-kernel.rqlp";
/// The single Joern query script. One script serves every Joern kernel:
/// the benchmark-controlled endpoints are passed in per case, so nothing in it
/// is language-, template-, or polarity-specific.
const JOERN_KERNEL_SCRIPT: &str = "adapters/joern/queries/kernel.sc";
const JOERN_JAVA_RAW_DIR: &str = "reports/raw/joern-java-kernel";
const JOERN_JAVA_REPORT: &str = "reports/joern-java-kernel.json";
const JOERN_JAVASCRIPT_RAW_DIR: &str = "reports/raw/joern-javascript-kernel";
const JOERN_JAVASCRIPT_REPORT: &str = "reports/joern-javascript-kernel.json";
const JOERN_PYTHON_RAW_DIR: &str = "reports/raw/joern-python-kernel";
const JOERN_PYTHON_REPORT: &str = "reports/joern-python-kernel.json";
const JOERN_RUBY_RAW_DIR: &str = "reports/raw/joern-ruby-kernel";
const JOERN_RUBY_REPORT: &str = "reports/joern-ruby-kernel.json";
const JOERN_PHP_RAW_DIR: &str = "reports/raw/joern-php-kernel";
const JOERN_PHP_REPORT: &str = "reports/joern-php-kernel.json";
const JOERN_RUST_RAW_DIR: &str = "reports/raw/joern-rust-kernel";
const JOERN_RUST_REPORT: &str = "reports/joern-rust-kernel.json";
/// The committed, benchmark-controlled Semgrep CE taint rules. One rule file
/// per covered language; each carries the two `__DFB_SOURCE__`/`__DFB_SINK__`
/// placeholders the runner resolves from the case's own marker lines. Every
/// Semgrep report hashes this whole directory, so no report can cite a
/// configuration hash that any committed rule no longer has.
const SEMGREP_RULES_DIR: &str = "adapters/semgrep/rules";
/// The placeholder tokens in a committed rule file. Nothing else is templated.
const SEMGREP_SOURCE_PLACEHOLDER: &str = "__DFB_SOURCE__";
const SEMGREP_SINK_PLACEHOLDER: &str = "__DFB_SINK__";
/// The module manifest written into every Go CodeQL workspace. The Go
/// extractor has no `none` build mode, so it must observe a real `go build`;
/// supplying the manifest keeps that build hermetic and offline instead of
/// letting autobuild synthesize one and resolve dependencies over the network.
/// The fixtures import nothing, so the language version only has to be old
/// enough that the installed toolchain never fetches another one.
const GO_MODULE_MANIFEST: &str = "module dataflowbench\n\ngo 1.21\n";
/// The cross-language direct-flow breadth policy. The C# and Go
/// direct-propagation pairs predate their kernels and are frozen in the
/// published v0.2.0 evidence, so they keep this policy reference while still
/// belonging to their kernel's 16 balanced templates.
const BIFROST_DIRECT_POLICY: &str = "adapters/bifrost/policies/core-direct.rqlp";
/// The two single-assertion policies the frozen Java direct-propagation pair
/// declares: the positive names `direct-positive.rqlp` and the negative names
/// `explicit-negative.rqlp`. Both predate the Java kernel command and are bound
/// byte-for-byte by the v0.2.0 and v0.3.0 freeze manifests, so the Java kernel
/// accepts them the way the Kotlin, C#, Go, and C-family kernels accept the
/// cross-language breadth policy — by accommodating the frozen reference rather
/// than rewriting published evidence.
const BIFROST_DIRECT_POSITIVE_POLICY: &str = "adapters/bifrost/policies/direct-positive.rqlp";
const BIFROST_EXPLICIT_NEGATIVE_POLICY: &str = "adapters/bifrost/policies/explicit-negative.rqlp";
/// The language-qualified Bifrost policy every Java kernel assertion is
/// evaluated with. As with Kotlin and Scala, the frozen direct-propagation pair
/// names its own historical policies, so the run pins this one for the whole
/// population and every assertion shares one configuration hash.
const BIFROST_JAVA_POLICY: &str = "adapters/bifrost/policies/core-java-kernel.rqlp";
/// The language-qualified Bifrost policy every JavaScript kernel assertion is
/// evaluated with. Its frozen direct-propagation pair names the cross-language
/// breadth policy instead, on the same precedent.
const BIFROST_JAVASCRIPT_POLICY: &str = "adapters/bifrost/policies/core-javascript-kernel.rqlp";
/// The language-qualified Bifrost policy that every Kotlin kernel assertion is
/// evaluated with. Two of the 32 Kotlin core assertions — the
/// `dfb-template-direct-propagation` pair — were frozen in v0.2.0 as part of
/// the cross-language direct-flow breadth slice, so their case metadata still
/// names the language-neutral breadth policy. The kernel run deliberately
/// evaluates this policy for the whole population so all 32 assertions share
/// one configuration; see docs/kotlin-kernel.md.
const BIFROST_KOTLIN_POLICY: &str = "adapters/bifrost/policies/core-kotlin-kernel.rqlp";
/// The language-qualified Bifrost policy every Scala kernel assertion is
/// evaluated with. Scala has single-analyzer coverage: CodeQL CLI 2.26.3 has no
/// Scala extractor at all, and the pinned Joern 4.0.610 has no Scala *source*
/// frontend. Both absences are analyzer coverage recorded in
/// docs/scala-kernel.md, never negative results. As with Kotlin, the frozen
/// v0.2.0 direct-propagation pair still names the language-neutral breadth
/// policy in its case metadata, so the run pins this policy for the whole
/// population and all 32 assertions share one configuration.
const BIFROST_SCALA_POLICY: &str = "adapters/bifrost/policies/core-scala-kernel.rqlp";
/// One positive and one negative assertion for each scored template. Runner-side
/// population checks read their denominator from `expected_core_case_count`,
/// which follows the rollout table; this constant is the fixed classic
/// expectation the regression tests pin against.
#[cfg(test)]
const KERNEL_CASE_COUNT: usize = 2 * KERNEL_TEMPLATE_IDS.len();
/// The sixteen scored propagation templates. Every language kernel preserves
/// these identities exactly; see docs/applicability-matrix.md.
const KERNEL_TEMPLATE_IDS: [&str; 16] = [
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
const KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH: [&str; 15] = [
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
const KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH: usize =
    2 * KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH.len();

/// The `template_id` prefix every challenge-tier template carries. It is load
/// bearing in two places: the smoke population refuses any case that carries it
/// (see `smoke_population_case`), and the preregistered Semgrep CE partition is
/// keyed by template ID rather than by fixture tags.
const CHALLENGE_TEMPLATE_PREFIX: &str = "dfb-template-chal-";

/// The thirteen challenge templates preregistered in docs/challenge-tier.md.
/// The IDs are fixed by that document and are never reused for different
/// semantics; a badly posed template is retired by amendment, not rewritten.
/// They carry `score_tier: "core"` — there is no new score tier — so they fold
/// into each language's core denominator as that language's fixtures land.
const CHALLENGE_TEMPLATE_IDS: [&str; 13] = [
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
const CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION: [&str; 12] = [
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
const CHALLENGE_TEMPLATE_IDS_C: [&str; 9] = [
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
struct ChallengeRollout {
    /// The `language` field of the case metadata.
    language: &'static str,
    /// The language's name in diagnostics.
    display: &'static str,
    /// The frozen classic core: sixteen templates, or fifteen where
    /// docs/applicability-matrix.md classifies the exception-catch cell
    /// inapplicable.
    classic: &'static [&'static str],
    /// The challenge templates docs/challenge-tier.md classifies applicable to
    /// this language. This is preregistered and never edited by a wave PR.
    challenge: &'static [&'static str],
    /// **The flag a wave PR flips.** `false` means this language's challenge
    /// fixtures do not exist yet and every population check expects its
    /// classic set; the language PR that authors the fixtures flips it to
    /// `true` in the same change, and every check then expects
    /// `classic + challenge` without any other code moving.
    rolled_out: bool,
}

impl ChallengeRollout {
    /// This language's current core denominator: the classic set until its
    /// fixtures land, the expanded set afterwards.
    fn expected_templates(&self) -> Vec<&'static str> {
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
const CHALLENGE_ROLLOUT: [ChallengeRollout; 13] = [
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
        rolled_out: false,
    },
    ChallengeRollout {
        language: "kotlin",
        display: "Kotlin",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: false,
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
        rolled_out: false,
    },
    ChallengeRollout {
        language: "go",
        display: "Go",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: false,
    },
    ChallengeRollout {
        language: "cpp",
        display: "C++",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION,
        rolled_out: false,
    },
    ChallengeRollout {
        language: "rust",
        display: "Rust",
        classic: &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH,
        challenge: &CHALLENGE_TEMPLATE_IDS_WITHOUT_REFLECTIVE_INVOCATION,
        rolled_out: false,
    },
    ChallengeRollout {
        language: "c",
        display: "C",
        classic: &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH,
        challenge: &CHALLENGE_TEMPLATE_IDS_C,
        rolled_out: false,
    },
    ChallengeRollout {
        language: "php",
        display: "PHP",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: false,
    },
    ChallengeRollout {
        language: "ruby",
        display: "Ruby",
        classic: &KERNEL_TEMPLATE_IDS,
        challenge: &CHALLENGE_TEMPLATE_IDS,
        rolled_out: false,
    },
];

/// This language's row, or `None` for a language the benchmark does not cover.
fn challenge_rollout(language: &str) -> Option<&'static ChallengeRollout> {
    CHALLENGE_ROLLOUT
        .iter()
        .find(|row| row.language == language)
}

/// Whether this language's challenge fixtures have landed. A wave PR flips the
/// row; nothing else in the tree needs to know.
#[cfg(test)]
fn challenge_rolled_out(language: &str) -> bool {
    challenge_rollout(language).is_some_and(|row| row.rolled_out)
}

/// The core denominator every population check for this language uses. A
/// language with no row keeps the sixteen-template classic core, which is what
/// a new language starts from.
fn expected_core_templates(language: &str) -> Vec<&'static str> {
    challenge_rollout(language)
        .map(ChallengeRollout::expected_templates)
        .unwrap_or_else(|| KERNEL_TEMPLATE_IDS.to_vec())
}

/// The core assertion count of this language: one positive and one negative per
/// template in its current denominator.
fn expected_core_case_count(language: &str) -> usize {
    2 * expected_core_templates(language).len()
}

/// Whether a case is a challenge-tier assertion, decided from its
/// `template_id` alone.
fn challenge_template_case(case: &Value) -> bool {
    case["template_id"]
        .as_str()
        .is_some_and(|template| template.starts_with(CHALLENGE_TEMPLATE_PREFIX))
}

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
    /// Assemble a freeze/v1 manifest from committed normalized reports.
    CreateFreeze {
        /// Normalized report paths, repository-relative. Repeatable.
        #[arg(long = "report", required = true)]
        reports: Vec<PathBuf>,
        /// Claim scope: development, release, or website.
        #[arg(long, default_value = "development")]
        scope: String,
        /// Release name; release and website scopes require a v-prefixed tag.
        #[arg(long, default_value = "development")]
        release: String,
        /// Frozen evidence revision; defaults to the checkout HEAD.
        #[arg(long)]
        revision: Option<String>,
        /// Manifest destination, relative to the repository root.
        #[arg(long, default_value = "reports/freeze.json")]
        output: PathBuf,
    },
    /// Generate audited result artifacts from a validated freeze manifest.
    GenerateResults {
        /// Freeze manifest, relative to the repository root.
        #[arg(long, default_value = "reports/freeze.json")]
        manifest: PathBuf,
        /// Directory that receives (or holds) the generated artifacts.
        #[arg(long)]
        output_directory: PathBuf,
        /// Verify that checked-in artifacts are current instead of writing.
        #[arg(long)]
        check: bool,
    },
    RunBifrostSmoke {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Java propagation kernel as its own population, separate from the
    /// cross-language direct-flow breadth slice the frozen smoke run evaluates.
    /// The population is Java's whole core denominator — the classic sixteen
    /// templates today, the expanded set once Java's challenge fixtures land
    /// and its `CHALLENGE_ROLLOUT` row is flipped.
    RunBifrostJavaKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the JavaScript propagation kernel as its own population, on the same
    /// terms as the Java kernel and never mixed with the TypeScript one.
    RunBifrostJavascriptKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Python propagation kernel without mixing it with the Java
    /// kernel or the cross-language direct-flow calibration cases.
    RunBifrostPythonKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Kotlin propagation kernel without mixing it with the Java
    /// kernel or any other language population.
    RunBifrostKotlinKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Scala propagation kernel as its own population. Scala has
    /// single-analyzer coverage — no CodeQL extractor and no Joern source
    /// frontend — so this is the only executing adapter for it.
    RunBifrostScalaKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the TypeScript propagation kernel without mixing it with the
    /// JavaScript kernel or the cross-language direct-flow calibration cases.
    RunBifrostTypescriptKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the C# propagation kernel as its own population, separate from every
    /// other language kernel and from the direct-flow breadth slice.
    RunBifrostCsharpKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Go propagation kernel as its own population, separate from every
    /// other language kernel and from the direct-flow breadth slice.
    RunBifrostGoKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the C propagation kernel as its own population. C's core
    /// denominator is 15 templates; its `language-extension` cases run in the
    /// same slice but keep their own scorecard.
    RunBifrostCKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the C++ propagation kernel as its own population, never merged or
    /// pooled with the C population.
    RunBifrostCppKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Rust propagation kernel as its own population, separate from
    /// every other language kernel and from the direct-flow breadth slice.
    /// Rust's core denominator is 15 templates; the `Result`/`?`
    /// `language-extension` cases run in the same slice on their own tier.
    RunBifrostRustKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the Ruby propagation kernel as its own population, separate from
    /// every other language kernel and from the direct-flow breadth slice.
    /// docs/applicability-matrix.md gates this tranche on Bifrost's Ruby
    /// indexing: whatever the run produces is retained as capability evidence
    /// and is never converted into a negative.
    RunBifrostRubyKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run the PHP propagation kernel as its own population, separate from every
    /// other language kernel and from the direct-flow breadth slice. The pinned
    /// CodeQL CLI has no PHP support at all, so this is one of PHP's two
    /// analyzer slices; the other is `run-joern-php-kernel`.
    RunBifrostPhpKernel {
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    RunCodeqlJavaKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    RunCodeqlJavascriptKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the TypeScript propagation kernel through its dedicated CodeQL
    /// pack. The JavaScript extractor also covers TypeScript, so this command
    /// selects `.ts` cases only and refuses JavaScript ones.
    RunCodeqlTypescriptKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Python propagation kernel through the Python CodeQL extractor.
    RunCodeqlPythonKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Kotlin propagation kernel through the Java CodeQL extractor.
    /// Kotlin extraction traces a real `kotlinc` compile, so a Kotlin compiler
    /// must be on PATH (or named with --kotlinc).
    RunCodeqlKotlinKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
        /// Kotlin compiler used to trace extraction.
        #[arg(long, default_value = "kotlinc")]
        kotlinc: PathBuf,
    },
    /// Run the C# propagation kernel through the C# CodeQL extractor.
    RunCodeqlCsharpKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Go propagation kernel through the Go CodeQL extractor. The Go
    /// extractor has no `none` build mode, so a Go toolchain must be on PATH
    /// (or named with --go) for the traced `go build`.
    RunCodeqlGoKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
        /// Go toolchain used to trace extraction.
        #[arg(long, default_value = "go")]
        go: PathBuf,
    },
    /// Run the C propagation kernel through the shared `cpp` CodeQL extractor.
    /// The extractor covers C and C++ alike, so this command selects `.c`
    /// fixtures only and analyzes them with the C-scoped kernel query.
    RunCodeqlCKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the C++ propagation kernel through the shared `cpp` CodeQL
    /// extractor, selecting `.cpp` fixtures only.
    RunCodeqlCppKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Rust propagation kernel through the CodeQL Rust extractor, whose
    /// support is a public preview in the pinned CLI. Each fixture is extracted
    /// from a generated single-crate Cargo workspace, because the extractor
    /// only runs its semantic analyzer when it finds a Cargo manifest.
    RunCodeqlRustKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Ruby propagation kernel through the CodeQL Ruby extractor. Ruby
    /// is buildless, so each fixture is extracted standalone and findings are
    /// reconciled against the case's `DFB-SINK:` method callsites.
    RunCodeqlRubyKernel {
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run the Java propagation kernel through Joern's `javasrc2cpg` frontend
    /// and the OSS data-flow engine, as its own population.
    RunJoernJavaKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the JavaScript propagation kernel through Joern's `jssrc2cpg`
    /// frontend. That frontend also covers TypeScript, so this command selects
    /// JavaScript cases only and never pools the two populations.
    RunJoernJavascriptKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the Python propagation kernel through Joern's `pysrc2cpg` frontend,
    /// as its own population.
    RunJoernPythonKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the Ruby propagation kernel through Joern's `rubysrc2cpg` frontend,
    /// as its own population.
    RunJoernRubyKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the PHP propagation kernel through Joern's `php2cpg` frontend, as its
    /// own population. `php2cpg` shells out to its bundled PHP-Parser, so a host
    /// `php` interpreter must be on PATH.
    RunJoernPhpKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the Rust propagation kernel through Joern's `rust2cpg` frontend, as
    /// its own population. `rust2cpg` is new in Joern 4.0.610 and extracts
    /// nothing from a bare `.rs` file, so each case is materialized as a
    /// minimal Cargo crate whose binary target points straight at the fixture.
    /// Rust's core denominator is 15 templates; the `Result`/`?`
    /// `language-extension` pair is outside this selection.
    RunJoernRustKernel {
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run the Java propagation kernel through the Semgrep CE (OSS) taint
    /// engine, scoring only the intraprocedural partition of the kernel. Every
    /// other case is `unsupported` by declared capability, decided from case
    /// metadata before Semgrep is invoked.
    RunSemgrepJavaKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the JavaScript propagation kernel through Semgrep CE. Semgrep's
    /// `js` and `ts` analyses share a front end, so this command selects
    /// JavaScript cases only and never pools the two populations.
    RunSemgrepJavascriptKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the TypeScript propagation kernel through Semgrep CE, as its own
    /// population.
    RunSemgrepTypescriptKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Python propagation kernel through Semgrep CE, as its own
    /// population.
    RunSemgrepPythonKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Go propagation kernel through Semgrep CE, as its own population.
    RunSemgrepGoKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Ruby propagation kernel through Semgrep CE, as its own
    /// population.
    RunSemgrepRubyKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the PHP propagation kernel through Semgrep CE, as its own
    /// population. Unlike the Joern PHP kernel this needs no host `php`.
    RunSemgrepPhpKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Kotlin propagation kernel through Semgrep CE, as its own
    /// population. The pinned distribution records Kotlin's maturity as
    /// `beta`; the label is retained in the report and the adapter README.
    RunSemgrepKotlinKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Rust propagation kernel through Semgrep CE, as its own
    /// population. Rust's core denominator is fifteen templates, and the
    /// pinned distribution records its maturity as `alpha`.
    RunSemgrepRustKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the C propagation kernel through Semgrep CE, as its own population.
    /// C's core denominator is fifteen templates, and the pinned distribution
    /// records its maturity as `alpha`.
    RunSemgrepCKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the C++ propagation kernel through Semgrep CE, as its own
    /// population. The pinned distribution records C++'s maturity as `alpha`.
    RunSemgrepCppKernel {
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Commands::Validate => validate_cases(),
        Commands::ValidateReports => validate_reports(),
        Commands::ValidateFreeze { manifest } => validate_freeze(&manifest),
        Commands::CreateFreeze {
            reports,
            scope,
            release,
            revision,
            output,
        } => create_freeze(&reports, &scope, &release, revision.as_deref(), &output),
        Commands::GenerateResults {
            manifest,
            output_directory,
            check,
        } => generate_results(&manifest, &output_directory, check),
        Commands::RunBifrostSmoke { bifrost } => run_bifrost_smoke(&bifrost),
        Commands::RunBifrostJavaKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::JavaKernel),
        Commands::RunBifrostJavascriptKernel { bifrost } => {
            run_bifrost(&bifrost, BifrostRun::JavascriptKernel)
        }
        Commands::RunBifrostPythonKernel { bifrost } => run_bifrost_python_kernel(&bifrost),
        Commands::RunBifrostKotlinKernel { bifrost } => run_bifrost_kotlin_kernel(&bifrost),
        Commands::RunBifrostScalaKernel { bifrost } => {
            run_bifrost(&bifrost, BifrostRun::ScalaKernel)
        }
        Commands::RunBifrostTypescriptKernel { bifrost } => {
            run_bifrost(&bifrost, BifrostRun::TypescriptKernel)
        }
        Commands::RunBifrostCsharpKernel { bifrost } => run_bifrost_csharp_kernel(&bifrost),
        Commands::RunBifrostGoKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::GoKernel),
        Commands::RunBifrostCKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::CKernel),
        Commands::RunBifrostCppKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::CppKernel),
        Commands::RunBifrostRustKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::RustKernel),
        Commands::RunBifrostRubyKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::RubyKernel),
        Commands::RunBifrostPhpKernel { bifrost } => run_bifrost(&bifrost, BifrostRun::PhpKernel),
        Commands::RunCodeqlJavaKernel {
            codeql,
            codeql_packs,
        } => run_codeql_java_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlJavascriptKernel {
            codeql,
            codeql_packs,
        } => run_codeql_ecma_kernel(&codeql, codeql_packs.as_deref(), EcmaKernel::JavaScript),
        Commands::RunCodeqlTypescriptKernel {
            codeql,
            codeql_packs,
        } => run_codeql_ecma_kernel(&codeql, codeql_packs.as_deref(), EcmaKernel::TypeScript),
        Commands::RunCodeqlPythonKernel {
            codeql,
            codeql_packs,
        } => run_codeql_python_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlKotlinKernel {
            codeql,
            codeql_packs,
            kotlinc,
        } => run_codeql_kotlin_kernel(&codeql, codeql_packs.as_deref(), &kotlinc),
        Commands::RunCodeqlCsharpKernel {
            codeql,
            codeql_packs,
        } => run_codeql_csharp_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlGoKernel {
            codeql,
            codeql_packs,
            go,
        } => run_codeql_go_kernel(&codeql, codeql_packs.as_deref(), &go),
        Commands::RunCodeqlCKernel {
            codeql,
            codeql_packs,
        } => run_codeql_c_family_kernel(&codeql, codeql_packs.as_deref(), CFamilyKernel::C),
        Commands::RunCodeqlCppKernel {
            codeql,
            codeql_packs,
        } => run_codeql_c_family_kernel(&codeql, codeql_packs.as_deref(), CFamilyKernel::Cpp),
        Commands::RunCodeqlRustKernel {
            codeql,
            codeql_packs,
        } => run_codeql_rust_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunCodeqlRubyKernel {
            codeql,
            codeql_packs,
        } => run_codeql_ruby_kernel(&codeql, codeql_packs.as_deref()),
        Commands::RunJoernJavaKernel { joern } => run_joern_kernel(&joern, JoernKernel::Java),
        Commands::RunJoernJavascriptKernel { joern } => {
            run_joern_kernel(&joern, JoernKernel::JavaScript)
        }
        Commands::RunJoernPythonKernel { joern } => run_joern_kernel(&joern, JoernKernel::Python),
        Commands::RunJoernRubyKernel { joern } => run_joern_kernel(&joern, JoernKernel::Ruby),
        Commands::RunJoernPhpKernel { joern } => run_joern_kernel(&joern, JoernKernel::Php),
        Commands::RunJoernRustKernel { joern } => run_joern_kernel(&joern, JoernKernel::Rust),
        Commands::RunSemgrepJavaKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Java)
        }
        Commands::RunSemgrepJavascriptKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::JavaScript)
        }
        Commands::RunSemgrepTypescriptKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::TypeScript)
        }
        Commands::RunSemgrepPythonKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Python)
        }
        Commands::RunSemgrepGoKernel { semgrep } => run_semgrep_kernel(&semgrep, SemgrepKernel::Go),
        Commands::RunSemgrepRubyKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Ruby)
        }
        Commands::RunSemgrepPhpKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Php)
        }
        Commands::RunSemgrepKotlinKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Kotlin)
        }
        Commands::RunSemgrepRustKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Rust)
        }
        Commands::RunSemgrepCKernel { semgrep } => run_semgrep_kernel(&semgrep, SemgrepKernel::C),
        Commands::RunSemgrepCppKernel { semgrep } => {
            run_semgrep_kernel(&semgrep, SemgrepKernel::Cpp)
        }
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

/// A ported kernel must carry its scored template identities unchanged, with no
/// template renamed, split, or silently dropped because the language spells a
/// construct differently. The expected set is the language's core denominator
/// from its `CHALLENGE_ROLLOUT` row: the classic set from
/// docs/applicability-matrix.md — sixteen templates for most languages, fifteen
/// for C and Rust, whose inapplicable exception-catch cell reduces only their
/// own denominators — plus that language's applicable challenge templates once
/// its row is rolled out. A language with no core cases yet is simply not a
/// kernel population.
fn validate_scored_kernel_balance(
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
    validate_reports_in(Path::new("."), None)
}

/// Validate every retained report under `<root>/reports`.
///
/// When `own_report` is set, retained-raw-evidence existence checks are
/// limited to that report; the others are still schema-validated. Kernel
/// runners pass their own report here because a concurrently running kernel
/// removes and rewrites files under its own `reports/raw/<slice>/` directory
/// mid-run, so existence checks against another runner's evidence race and
/// fail spuriously.
fn validate_reports_in(root: &Path, own_report: Option<&Path>) -> Result<()> {
    let compiled = schema("schemas/result.schema.json")?;
    let own = own_report
        .map(fs::canonicalize)
        .transpose()
        .context("resolve the runner's own report")?;
    let mut paths: Vec<_> = fs::read_dir(root.join("reports"))
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file() && path.extension().is_some_and(|ext| ext == "json"))
        .collect();
    paths.sort();
    let mut validated = 0usize;
    for path in &paths {
        let report: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        // Freeze manifests live beside normalized reports but follow their
        // own contract; validate-freeze owns them.
        if report.get("benchmark").is_some() && report.get("claim").is_some() {
            continue;
        }
        validated += 1;
        validate_value(&compiled, &report, path)?;
        let check_raw = match &own {
            None => true,
            Some(own) => fs::canonicalize(path).is_ok_and(|path| &path == own),
        };
        if check_raw {
            validate_retained_raw(&report, path, root)?;
        }
    }
    println!("validated {validated} reports");
    Ok(())
}

/// Every `raw_output` a report retains must exist under `root`.
fn validate_retained_raw(report: &Value, path: &Path, root: &Path) -> Result<()> {
    for result in report["results"].as_array().expect("schema validated") {
        let raw = result["raw_output"].as_str().expect("schema validated");
        if !root.join(raw).is_file() {
            bail!("{}: retained raw output {raw:?} is absent", path.display());
        }
    }
    Ok(())
}

/// Publish a runner's report at the end of a run, then sweep the report
/// directory.
///
/// The report is validated against the result schema, and its retained raw
/// evidence confirmed on disk, before anything is written: a runner never
/// publishes a report it did not validate. The report then lands through a
/// same-directory temp file and an atomic rename so a concurrent runner's
/// end-of-run sweep can never parse a half-written report. The closing sweep
/// schema-checks every retained report but scopes raw-evidence checks to this
/// report only, because concurrent runners rewrite their own
/// `reports/raw/<slice>/` evidence mid-run.
fn write_and_validate_report(report_path: &Path, report: &Value) -> Result<()> {
    write_and_validate_report_in(Path::new("."), report_path, report)
}

fn write_and_validate_report_in(root: &Path, report_path: &Path, report: &Value) -> Result<()> {
    let report_path = root.join(report_path);
    let compiled = schema("schemas/result.schema.json")?;
    validate_value(&compiled, report, &report_path)?;
    validate_retained_raw(report, &report_path, root)?;
    let staged = report_path.with_extension("json.tmp");
    fs::write(&staged, serde_json::to_string_pretty(report)? + "\n")
        .with_context(|| format!("stage report {}", staged.display()))?;
    fs::rename(&staged, &report_path)
        .with_context(|| format!("publish report {}", report_path.display()))?;
    validate_reports_in(root, Some(&report_path))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum BifrostRun {
    Smoke,
    JavaKernel,
    JavascriptKernel,
    PythonKernel,
    KotlinKernel,
    ScalaKernel,
    TypescriptKernel,
    CsharpKernel,
    GoKernel,
    CKernel,
    CppKernel,
    RustKernel,
    RubyKernel,
    PhpKernel,
}

impl BifrostRun {
    /// The label a run is named by in diagnostics.
    fn label(self) -> &'static str {
        match self {
            Self::Smoke => "Bifrost smoke",
            Self::JavaKernel => "Bifrost Java kernel",
            Self::JavascriptKernel => "Bifrost JavaScript kernel",
            Self::PythonKernel => "Bifrost Python kernel",
            Self::KotlinKernel => "Bifrost Kotlin kernel",
            Self::ScalaKernel => "Bifrost Scala kernel",
            Self::TypescriptKernel => "Bifrost TypeScript kernel",
            Self::CsharpKernel => "Bifrost C# kernel",
            Self::GoKernel => "Bifrost Go kernel",
            Self::CKernel => "Bifrost C kernel",
            Self::CppKernel => "Bifrost C++ kernel",
            Self::RustKernel => "Bifrost Rust kernel",
            Self::RubyKernel => "Bifrost Ruby kernel",
            Self::PhpKernel => "Bifrost PHP kernel",
        }
    }

    /// The language whose core denominator this run must cover, or `None` for
    /// the cross-language smoke slice, whose population is the frozen
    /// policy-pinned selection rather than one language's kernel.
    fn language(self) -> Option<&'static str> {
        match self {
            Self::Smoke => None,
            Self::JavaKernel => Some("java"),
            Self::JavascriptKernel => Some("javascript"),
            Self::PythonKernel => Some("python"),
            Self::KotlinKernel => Some("kotlin"),
            Self::ScalaKernel => Some("scala"),
            Self::TypescriptKernel => Some("typescript"),
            Self::CsharpKernel => Some("csharp"),
            Self::GoKernel => Some("go"),
            Self::CKernel => Some("c"),
            Self::CppKernel => Some("cpp"),
            Self::RustKernel => Some("rust"),
            Self::RubyKernel => Some("ruby"),
            Self::PhpKernel => Some("php"),
        }
    }

    /// The core denominator a kernel run must cover exactly, or `None` for a
    /// run whose population is defined some other way. The count comes from the
    /// language's `CHALLENGE_ROLLOUT` row, so a wave PR that flips that row
    /// moves this number with it — 32 for a classic Java kernel, 58 once Java's
    /// challenge fixtures land — without the runner being touched. The C and
    /// Rust `language-extension` cases are selected by the same run but are
    /// counted and scored separately, so they never move this number.
    fn expected_core_cases(self) -> Option<usize> {
        match self {
            // The Python and TypeScript runs select by policy reference as
            // well as by language, so their population is not pinned to the
            // denominator here; it is the selector that defines it.
            Self::Smoke | Self::PythonKernel | Self::TypescriptKernel => None,
            other => other.language().map(expected_core_case_count),
        }
    }
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

fn git_is_ancestor(root: &Path, ancestor: &str, descendant: &str) -> Result<bool> {
    let output = Command::new("git")
        .current_dir(root)
        .args(["merge-base", "--is-ancestor", ancestor, descendant])
        .output()
        .context("run git merge-base --is-ancestor")?;
    match output.status.code() {
        Some(0) => Ok(true),
        Some(1) => Ok(false),
        _ => bail!("cannot resolve freeze revision {ancestor} in this checkout"),
    }
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

fn create_freeze(
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
fn build_freeze_manifest(
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

const RESULT_OUTCOME_ORDER: [&str; 5] = [
    "reached",
    "not-reached",
    "inconclusive",
    "unsupported",
    "runner-error",
];
const SCORE_TIER_ORDER: [&str; 4] = ["calibration", "core", "language-extension", "real-project"];

/// Case metadata a result view needs beyond what the freeze manifest binds.
/// Language and semantic dimensions live in the case file, whose bytes the
/// freeze validator has already verified against the manifest digest.
struct GeneratedCaseMeta {
    language: String,
    semantic_dimensions: Vec<String>,
    template_id: String,
    polarity: String,
    score_tier: String,
}

fn generate_results(manifest: &Path, output_directory: &Path, check: bool) -> Result<()> {
    let root = repository_root()?;
    let manifest = if manifest.is_absolute() {
        manifest.to_path_buf()
    } else {
        root.join(manifest)
    };
    generate_results_at(&root, &manifest, output_directory, true, check)?;
    if check {
        println!(
            "result artifacts in {} are current",
            output_directory.display()
        );
    } else {
        println!("wrote result artifacts to {}", output_directory.display());
    }
    Ok(())
}

/// Generate (or, with `check`, verify) result artifacts from a freeze that
/// must first pass full validation. `check_git` mirrors `validate_freeze_at`:
/// only isolated test fixtures may skip the checkout comparison.
fn generate_results_at(
    root: &Path,
    manifest_path: &Path,
    output_directory: &Path,
    check_git: bool,
    check: bool,
) -> Result<()> {
    validate_freeze_at(root, manifest_path, check_git)?;
    let artifacts = build_result_artifacts(root, manifest_path)?;
    if check {
        check_result_artifacts(output_directory, &artifacts)
    } else {
        write_result_artifacts(output_directory, &artifacts)
    }
}

fn build_result_artifacts(root: &Path, manifest_path: &Path) -> Result<BTreeMap<String, Vec<u8>>> {
    let manifest_bytes = fs::read(manifest_path)
        .with_context(|| format!("read freeze manifest {}", manifest_path.display()))?;
    let manifest_sha256 = format!("{:x}", Sha256::digest(&manifest_bytes));
    let manifest: Value = serde_json::from_slice(&manifest_bytes)
        .with_context(|| format!("parse freeze manifest {}", manifest_path.display()))?;
    let manifest_relative = manifest_display_path(root, manifest_path);

    let mut case_meta = BTreeMap::new();
    for selected in manifest["cases"].as_array().expect("freeze validated") {
        let id = required_string(selected, "id", "selected case")?;
        let relative_path = required_string(selected, "path", id)?;
        let case_bytes = fs::read(root.join(relative_path))
            .with_context(|| format!("read case {relative_path}"))?;
        let case: Value = serde_json::from_slice(&case_bytes)
            .with_context(|| format!("parse case {relative_path}"))?;
        let semantic_dimensions = case["semantic_dimensions"]
            .as_array()
            .expect("case schema validated")
            .iter()
            .map(|dimension| {
                dimension
                    .as_str()
                    .expect("case schema validated")
                    .to_string()
            })
            .collect();
        case_meta.insert(
            id.to_string(),
            GeneratedCaseMeta {
                language: required_string(&case, "language", id)?.to_string(),
                semantic_dimensions,
                template_id: required_string(selected, "template_id", id)?.to_string(),
                polarity: required_string(selected, "polarity", id)?.to_string(),
                score_tier: required_string(selected, "score_tier", id)?.to_string(),
            },
        );
    }

    let mut adapters = BTreeMap::new();
    for adapter in manifest["adapters"].as_array().expect("freeze validated") {
        adapters.insert(
            required_string(adapter, "id", "adapter")?.to_string(),
            adapter,
        );
    }

    let mut used_identifiers: BTreeMap<String, usize> = BTreeMap::new();
    let mut scorecard_values = Vec::new();
    let mut scorecard_pages = Vec::new();
    for report in manifest["reports"].as_array().expect("freeze validated") {
        let adapter_id = required_string(report, "adapter", "frozen report")?;
        let adapter = adapters
            .get(adapter_id)
            .with_context(|| format!("frozen report binds unknown adapter {adapter_id}"))?;
        let identifier = scorecard_identifier(&mut used_identifiers, adapter_id, report)?;
        let (value, page) = build_scorecard(
            &identifier,
            adapter,
            report,
            &case_meta,
            &manifest_relative,
            &manifest_sha256,
        )?;
        scorecard_values.push(value);
        scorecard_pages.push((identifier, page));
    }

    let results = json!({
        "schema_version": 1,
        "manifest": {"path": manifest_relative, "sha256": manifest_sha256},
        "benchmark": manifest["benchmark"],
        "claim": manifest["claim"],
        "scorecards": scorecard_values,
    });
    let mut results_bytes = serde_json::to_vec_pretty(&results)?;
    results_bytes.push(b'\n');

    let mut artifacts = BTreeMap::new();
    artifacts.insert("results.json".to_string(), results_bytes);
    artifacts.insert(
        "index.md".to_string(),
        build_index_page(
            &manifest,
            &manifest_relative,
            &manifest_sha256,
            &scorecard_pages,
        )
        .into_bytes(),
    );
    for (identifier, page) in scorecard_pages {
        artifacts.insert(format!("scorecards/{identifier}.md"), page.into_bytes());
    }
    Ok(artifacts)
}

fn manifest_display_path(root: &Path, manifest_path: &Path) -> String {
    let canonical_root = fs::canonicalize(root).unwrap_or_else(|_| root.to_path_buf());
    let canonical_manifest =
        fs::canonicalize(manifest_path).unwrap_or_else(|_| manifest_path.to_path_buf());
    canonical_manifest
        .strip_prefix(&canonical_root)
        .unwrap_or(&canonical_manifest)
        .to_string_lossy()
        .replace('\\', "/")
}

/// A stable page identifier per frozen report. Reports that share an adapter,
/// track, dimension, and profile are distinct result populations, so later
/// occurrences receive an ordinal suffix in manifest order.
fn scorecard_identifier(
    used: &mut BTreeMap<String, usize>,
    adapter_id: &str,
    report: &Value,
) -> Result<String> {
    let mut base = String::new();
    for part in [
        adapter_id,
        required_string(report, "track", "frozen report")?,
        required_string(report, "dimension", "frozen report")?,
        required_string(report, "model_profile", "frozen report")?,
    ] {
        if !base.is_empty() {
            base.push('-');
        }
        for character in part.chars() {
            base.push(match character.to_ascii_lowercase() {
                lower @ ('a'..='z' | '0'..='9') => lower,
                _ => '-',
            });
        }
    }
    let ordinal = used.entry(base.clone()).or_insert(0);
    *ordinal += 1;
    if *ordinal == 1 {
        Ok(base)
    } else {
        Ok(format!("{base}-{ordinal}"))
    }
}

fn classify_outcome(polarity: &str, outcome: &str) -> &'static str {
    match (polarity, outcome) {
        ("positive", "reached") => "true-positive",
        ("positive", "not-reached") => "false-negative",
        ("negative", "reached") => "false-positive",
        ("negative", "not-reached") => "true-negative",
        (_, "inconclusive") => "inconclusive",
        (_, "unsupported") => "unsupported",
        _ => "runner-error",
    }
}

fn rate_fraction(numerator: usize, denominator: usize) -> Value {
    if denominator == 0 {
        Value::Null
    } else {
        json!({
            "numerator": numerator,
            "denominator": denominator,
            "percent": percent_string(numerator as f64 / denominator as f64),
        })
    }
}

fn percent_string(rate: f64) -> String {
    format!("{:.1}", rate * 100.0)
}

fn mean_percent(rates: &[f64]) -> Option<String> {
    if rates.is_empty() {
        None
    } else {
        Some(percent_string(
            rates.iter().sum::<f64>() / rates.len() as f64,
        ))
    }
}

fn build_scorecard(
    identifier: &str,
    adapter: &Value,
    report: &Value,
    case_meta: &BTreeMap<String, GeneratedCaseMeta>,
    manifest_relative: &str,
    manifest_sha256: &str,
) -> Result<(Value, String)> {
    let mut outcomes = BTreeMap::new();
    for record in report["outcomes"].as_array().expect("freeze validated") {
        outcomes.insert(
            required_string(record, "case_id", "outcome record")?,
            required_string(record, "outcome", "outcome record")?,
        );
    }
    let mut raw_evidence = BTreeMap::new();
    for evidence in report["raw_evidence"].as_array().expect("freeze validated") {
        raw_evidence.insert(
            required_string(evidence, "case_id", "raw evidence")?,
            (
                required_string(evidence, "path", "raw evidence")?,
                required_string(evidence, "sha256", "raw evidence")?,
            ),
        );
    }

    // language -> score tier -> case IDs, in deterministic order.
    let mut populations: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
    for case_id in report["case_ids"].as_array().expect("freeze validated") {
        let case_id = case_id.as_str().expect("freeze validated");
        let meta = case_meta
            .get(case_id)
            .with_context(|| format!("frozen report selects unknown case {case_id}"))?;
        populations
            .entry(meta.language.as_str())
            .or_default()
            .entry(meta.score_tier.as_str())
            .or_default()
            .push(case_id);
    }

    let track = required_string(report, "track", "frozen report")?;
    let dimension = required_string(report, "dimension", "frozen report")?;
    let model_profile = required_string(report, "model_profile", "frozen report")?;
    let report_path = required_string(report, "path", "frozen report")?;
    let report_sha256 = required_string(report, "sha256", "frozen report")?;
    let normalized_sha256 = required_string(report, "normalized_report_sha256", "frozen report")?;

    let mut page = String::new();
    page.push_str(&format!("# Scorecard `{identifier}`\n\n"));
    page.push_str(&format!(
        "Adapter `{}`: `{}` `{}` (build `{}`, adapter version `{}`, configuration `{}`).\n\n",
        required_string(adapter, "id", "adapter")?,
        required_string(adapter, "tool", "adapter")?,
        required_string(adapter, "tool_version", "adapter")?,
        required_string(adapter, "build_identity", "adapter")?,
        required_string(adapter, "adapter_version", "adapter")?,
        required_string(adapter, "configuration_hash", "adapter")?,
    ));
    page.push_str(&format!(
        "Track `{track}`, score dimension `{dimension}`, model profile `{model_profile}`. \
         This scorecard is a single result population; it is never pooled with \
         other tracks, dimensions, or model profiles.\n\n"
    ));
    page.push_str(&format!(
        "Normalized report: `{report_path}` (`sha256:{report_sha256}`, normalized \
         `sha256:{normalized_sha256}`). Generated from freeze manifest \
         `{manifest_relative}` (`sha256:{manifest_sha256}`).\n"
    ));

    let mut language_values = Vec::new();
    for (language, tiers) in &populations {
        let mut tier_values = Vec::new();
        for tier in SCORE_TIER_ORDER {
            let Some(case_ids) = tiers.get(tier) else {
                continue;
            };
            let scored = tier != "calibration";
            page.push_str(&format!("\n## Language `{language}`, tier `{tier}`\n\n"));

            let mut coverage: BTreeMap<&str, usize> = BTreeMap::new();
            for case_id in case_ids {
                *coverage.entry(outcomes[case_id]).or_default() += 1;
            }
            let coverage_value: Value = RESULT_OUTCOME_ORDER
                .iter()
                .map(|outcome| {
                    (
                        outcome.to_string(),
                        json!(coverage.get(outcome).copied().unwrap_or(0)),
                    )
                })
                .chain([("total".to_string(), json!(case_ids.len()))])
                .collect::<serde_json::Map<_, _>>()
                .into();
            page.push_str("Outcome coverage: ");
            for outcome in RESULT_OUTCOME_ORDER {
                page.push_str(&format!(
                    "`{outcome}` {}, ",
                    coverage.get(outcome).copied().unwrap_or(0)
                ));
            }
            page.push_str(&format!(
                "total {}. `inconclusive`, `unsupported`, and `runner-error` are \
                 capability and execution coverage; they are never counted as \
                 clean negatives.\n",
                case_ids.len()
            ));
            if !scored {
                page.push_str(
                    "\nCalibration cases exercise schemas and adapters; they do not \
                     contribute to a correctness score.\n",
                );
            }

            // semantic dimension -> template -> case IDs.
            let mut by_dimension: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
            for case_id in case_ids {
                let meta = &case_meta[*case_id];
                for semantic_dimension in &meta.semantic_dimensions {
                    by_dimension
                        .entry(semantic_dimension.as_str())
                        .or_default()
                        .entry(meta.template_id.as_str())
                        .or_default()
                        .push(case_id);
                }
            }

            let mut dimension_values = Vec::new();
            let mut dimension_tprs = Vec::new();
            let mut dimension_fprs = Vec::new();
            if scored {
                page.push_str("\n### Semantic dimension rates\n\n");
                page.push_str(
                    "| Semantic dimension | TP | FN | FP | TN | Inconclusive | \
                     Unsupported | Runner error | TPR (template macro) | \
                     FPR (template macro) |\n",
                );
                page.push_str("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n");
            }
            for (semantic_dimension, templates) in &by_dimension {
                let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
                let mut template_tprs = Vec::new();
                let mut template_fprs = Vec::new();
                for template_cases in templates.values() {
                    let mut template_counts: BTreeMap<&str, usize> = BTreeMap::new();
                    for case_id in template_cases {
                        let classification =
                            classify_outcome(&case_meta[*case_id].polarity, outcomes[case_id]);
                        *template_counts.entry(classification).or_default() += 1;
                        *counts.entry(classification).or_default() += 1;
                    }
                    let true_positives = template_counts.get("true-positive").copied().unwrap_or(0);
                    let false_negatives =
                        template_counts.get("false-negative").copied().unwrap_or(0);
                    let false_positives =
                        template_counts.get("false-positive").copied().unwrap_or(0);
                    let true_negatives = template_counts.get("true-negative").copied().unwrap_or(0);
                    if true_positives + false_negatives > 0 {
                        template_tprs.push(
                            true_positives as f64 / (true_positives + false_negatives) as f64,
                        );
                    }
                    if false_positives + true_negatives > 0 {
                        template_fprs.push(
                            false_positives as f64 / (false_positives + true_negatives) as f64,
                        );
                    }
                }
                let count = |classification: &str| counts.get(classification).copied().unwrap_or(0);
                let tpr = mean_percent(&template_tprs);
                let fpr = mean_percent(&template_fprs);
                if scored {
                    page.push_str(&format!(
                        "| `{semantic_dimension}` | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n",
                        count("true-positive"),
                        count("false-negative"),
                        count("false-positive"),
                        count("true-negative"),
                        count("inconclusive"),
                        count("unsupported"),
                        count("runner-error"),
                        percent_cell(&tpr),
                        percent_cell(&fpr),
                    ));
                }
                if let Some(tpr) = &tpr {
                    dimension_tprs.push(tpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                if let Some(fpr) = &fpr {
                    dimension_fprs.push(fpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                dimension_values.push(json!({
                    "name": semantic_dimension,
                    "counts": {
                        "true_positives": count("true-positive"),
                        "false_negatives": count("false-negative"),
                        "false_positives": count("false-positive"),
                        "true_negatives": count("true-negative"),
                        "inconclusive": count("inconclusive"),
                        "unsupported": count("unsupported"),
                        "runner_errors": count("runner-error"),
                    },
                    "true_positive_rate": rate_fraction(
                        count("true-positive"),
                        count("true-positive") + count("false-negative"),
                    ),
                    "false_positive_rate": rate_fraction(
                        count("false-positive"),
                        count("false-positive") + count("true-negative"),
                    ),
                    "template_macro": {
                        "true_positive_rate_percent": tpr,
                        "false_positive_rate_percent": fpr,
                        "scored_positive_templates": template_tprs.len(),
                        "scored_negative_templates": template_fprs.len(),
                    },
                }));
            }
            let macro_tpr = mean_percent(&dimension_tprs);
            let macro_fpr = mean_percent(&dimension_fprs);
            if scored {
                page.push_str(&format!(
                    "\nMacro-average over semantic dimensions: TPR {}, FPR {}. \
                     Macro-averages pool templates first, then semantic dimensions; \
                     raw case counts are shown for audit only.\n",
                    percent_cell(&macro_tpr),
                    percent_cell(&macro_fpr),
                ));
            }

            page.push_str("\n### Cases\n\n");
            page.push_str(
                "| Template | Case | Polarity | Outcome | Classification | \
                 Raw evidence | Raw SHA-256 |\n",
            );
            page.push_str("| --- | --- | --- | --- | --- | --- | --- |\n");
            let mut case_values = Vec::new();
            let mut ordered_cases: Vec<&&str> = case_ids.iter().collect();
            ordered_cases
                .sort_by_key(|case_id| (case_meta[**case_id].template_id.as_str(), **case_id));
            for case_id in ordered_cases {
                let meta = &case_meta[*case_id];
                let outcome = outcomes[case_id];
                let classification = classify_outcome(&meta.polarity, outcome);
                let (raw_path, raw_sha256) = raw_evidence[case_id];
                page.push_str(&format!(
                    "| `{}` | `{case_id}` | {} | `{outcome}` | {classification} | \
                     `{raw_path}` | `{raw_sha256}` |\n",
                    meta.template_id, meta.polarity,
                ));
                case_values.push(json!({
                    "case_id": case_id,
                    "template_id": meta.template_id,
                    "polarity": meta.polarity,
                    "semantic_dimensions": meta.semantic_dimensions,
                    "outcome": outcome,
                    "classification": classification,
                    "raw_evidence": {"path": raw_path, "sha256": raw_sha256},
                }));
            }

            tier_values.push(json!({
                "score_tier": tier,
                "scored": scored,
                "outcome_coverage": coverage_value,
                "semantic_dimensions": dimension_values,
                "dimension_macro": {
                    "true_positive_rate_percent": macro_tpr,
                    "false_positive_rate_percent": macro_fpr,
                },
                "cases": case_values,
            }));
        }
        language_values.push(json!({
            "language": language,
            "score_tiers": tier_values,
        }));
    }

    let value = json!({
        "id": identifier,
        "adapter": adapter,
        "track": track,
        "dimension": dimension,
        "model_profile": model_profile,
        "report": {
            "path": report_path,
            "sha256": report_sha256,
            "normalized_report_sha256": normalized_sha256,
        },
        "languages": language_values,
    });
    Ok((value, page))
}

fn percent_cell(percent: &Option<String>) -> String {
    match percent {
        Some(percent) => format!("{percent}%"),
        None => "n/a".to_string(),
    }
}

fn build_index_page(
    manifest: &Value,
    manifest_relative: &str,
    manifest_sha256: &str,
    scorecard_pages: &[(String, String)],
) -> String {
    let benchmark = &manifest["benchmark"];
    let claim = &manifest["claim"];
    let mut page = String::new();
    page.push_str("# DataFlowBench frozen results\n\n");
    page.push_str(&format!(
        "Generated from freeze manifest `{manifest_relative}` \
         (`sha256:{manifest_sha256}`), benchmark release `{}` at revision \
         `{}`, fixture revision `{}`.\n\n",
        benchmark["release"].as_str().unwrap_or_default(),
        benchmark["revision"].as_str().unwrap_or_default(),
        benchmark["fixture_revision"].as_str().unwrap_or_default(),
    ));
    page.push_str(&format!(
        "Claim scope `{}`. Every number on these pages is derived from the \
         immutable freeze evidence above; none are maintained by hand. Tracks, \
         score dimensions, score tiers, and model profiles are separate result \
         populations and are never combined into one leaderboard.\n\n",
        claim["scope"].as_str().unwrap_or_default(),
    ));
    for (label, field) in [
        ("Tracks", "tracks"),
        ("Score dimensions", "dimensions"),
        ("Score tiers", "score_tiers"),
        ("Model profiles", "model_profiles"),
    ] {
        let names = claim[field]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(|name| format!("`{name}`"))
            .collect::<Vec<_>>()
            .join(", ");
        page.push_str(&format!("- {label}: {names}\n"));
    }

    page.push_str("\n## Exclusions\n\n");
    let exclusions = claim["exclusions"].as_array().cloned().unwrap_or_default();
    if exclusions.is_empty() {
        page.push_str("None.\n");
    } else {
        page.push_str("| Case | Reason |\n| --- | --- |\n");
        for exclusion in &exclusions {
            page.push_str(&format!(
                "| `{}` | {} |\n",
                exclusion["id"].as_str().unwrap_or_default(),
                exclusion["reason"].as_str().unwrap_or_default(),
            ));
        }
    }

    page.push_str("\n## Scorecards\n\n");
    for (identifier, _) in scorecard_pages {
        page.push_str(&format!("- [`{identifier}`](scorecards/{identifier}.md)\n"));
    }
    page
}

fn write_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    for (relative, bytes) in artifacts {
        let path = output_directory.join(relative);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("create output directory {}", parent.display()))?;
        }
        fs::write(&path, bytes)
            .with_context(|| format!("write result artifact {}", path.display()))?;
    }
    Ok(())
}

/// Prove the checked-in artifacts are byte-identical to a fresh generation.
/// Missing, stale, and unexpected files each fail the check so a stale page
/// cannot survive behind a regenerated sibling.
fn check_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    let mut problems = Vec::new();
    for (relative, expected) in artifacts {
        let path = output_directory.join(relative);
        match fs::read(&path) {
            Ok(actual) if &actual == expected => {}
            Ok(_) => problems.push(format!("stale artifact: {relative}")),
            Err(_) => problems.push(format!("missing artifact: {relative}")),
        }
    }
    if output_directory.is_dir() {
        for entry in WalkDir::new(output_directory) {
            let entry = entry.context("walk output directory")?;
            if !entry.file_type().is_file() {
                continue;
            }
            let relative = entry
                .path()
                .strip_prefix(output_directory)
                .expect("walked under output directory")
                .to_string_lossy()
                .replace('\\', "/");
            if !artifacts.contains_key(&relative) {
                problems.push(format!("unexpected artifact: {relative}"));
            }
        }
    }
    if !problems.is_empty() {
        bail!("result artifacts are not current:\n{}", problems.join("\n"));
    }
    Ok(())
}

fn run_bifrost_smoke(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::Smoke)
}

fn run_bifrost_python_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::PythonKernel)
}

fn run_bifrost_kotlin_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::KotlinKernel)
}

fn run_bifrost_csharp_kernel(binary: &Path) -> Result<()> {
    run_bifrost(binary, BifrostRun::CsharpKernel)
}

fn run_bifrost(binary: &Path, run: BifrostRun) -> Result<()> {
    validate_cases()?;
    let (raw_dir, report_path) = match run {
        BifrostRun::Smoke => (
            Path::new("reports/raw/bifrost"),
            Path::new("reports/bifrost-smoke.json"),
        ),
        BifrostRun::JavaKernel => (
            Path::new("reports/raw/bifrost-java-kernel"),
            Path::new("reports/bifrost-java-kernel.json"),
        ),
        BifrostRun::JavascriptKernel => (
            Path::new("reports/raw/bifrost-javascript-kernel"),
            Path::new("reports/bifrost-javascript-kernel.json"),
        ),
        BifrostRun::PythonKernel => (
            Path::new("reports/raw/bifrost-python-kernel"),
            Path::new("reports/bifrost-python-kernel.json"),
        ),
        BifrostRun::KotlinKernel => (
            Path::new("reports/raw/bifrost-kotlin-kernel"),
            Path::new("reports/bifrost-kotlin-kernel.json"),
        ),
        BifrostRun::ScalaKernel => (
            Path::new("reports/raw/bifrost-scala-kernel"),
            Path::new("reports/bifrost-scala-kernel.json"),
        ),
        BifrostRun::TypescriptKernel => (
            Path::new("reports/raw/bifrost-typescript-kernel"),
            Path::new("reports/bifrost-typescript-kernel.json"),
        ),
        BifrostRun::CsharpKernel => (
            Path::new("reports/raw/bifrost-csharp-kernel"),
            Path::new("reports/bifrost-csharp-kernel.json"),
        ),
        BifrostRun::GoKernel => (
            Path::new("reports/raw/bifrost-go-kernel"),
            Path::new("reports/bifrost-go-kernel.json"),
        ),
        BifrostRun::CKernel => (
            Path::new("reports/raw/bifrost-c-kernel"),
            Path::new("reports/bifrost-c-kernel.json"),
        ),
        BifrostRun::CppKernel => (
            Path::new("reports/raw/bifrost-cpp-kernel"),
            Path::new("reports/bifrost-cpp-kernel.json"),
        ),
        BifrostRun::RustKernel => (
            Path::new("reports/raw/bifrost-rust-kernel"),
            Path::new("reports/bifrost-rust-kernel.json"),
        ),
        BifrostRun::RubyKernel => (
            Path::new("reports/raw/bifrost-ruby-kernel"),
            Path::new("reports/bifrost-ruby-kernel.json"),
        ),
        BifrostRun::PhpKernel => (
            Path::new("reports/raw/bifrost-php-kernel"),
            Path::new("reports/bifrost-php-kernel.json"),
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
    let mut selected_core_cases = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !selected_bifrost_case(&case, run) {
            continue;
        }
        selected_cases += 1;
        if case["score_tier"] == "core" {
            selected_core_cases += 1;
        }
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
            let policy = bifrost_policy_for(&case, run)?;
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
        bail!("no cases selected for {}", run.label());
    }
    if let Some(expected) = run.expected_core_cases()
        && selected_core_cases != expected
    {
        bail!(
            "{} must select exactly {expected} core assertions; found {selected_core_cases}",
            run.label()
        );
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
    write_and_validate_report(report_path, &report)?;
    println!("wrote {}", report_path.display());
    Ok(())
}

/// The Bifrost policy a run evaluates for one case.
///
/// Kernel runs pin the language-qualified policy for the whole population so
/// that a single configuration hash covers all 32 assertions, including the
/// two direct-propagation cases whose frozen v0.2.0 metadata still names the
/// cross-language breadth policy.
fn bifrost_policy_for<'a>(case: &'a Value, run: BifrostRun) -> Result<&'a str> {
    match run {
        BifrostRun::JavaKernel => Ok(BIFROST_JAVA_POLICY),
        BifrostRun::JavascriptKernel => Ok(BIFROST_JAVASCRIPT_POLICY),
        BifrostRun::KotlinKernel => Ok(BIFROST_KOTLIN_POLICY),
        BifrostRun::ScalaKernel => Ok(BIFROST_SCALA_POLICY),
        _ => case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .context("Bifrost case lacks policy reference"),
    }
}

fn selected_bifrost_case(case: &Value, run: BifrostRun) -> bool {
    match run {
        BifrostRun::Smoke => has_bifrost_model_reference(case) && smoke_population_case(case),
        BifrostRun::JavaKernel => java_kernel_bifrost_case(case),
        BifrostRun::JavascriptKernel => javascript_kernel_bifrost_case(case),
        BifrostRun::KotlinKernel => kotlin_core_case(case),
        BifrostRun::ScalaKernel => scala_core_case(case),
        BifrostRun::PythonKernel => {
            case["language"] == "python"
                && case["track"] == "taint"
                && case["score_tier"] == "core"
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| policy.ends_with("core-python-kernel.rqlp"))
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::TypescriptKernel => {
            case["language"] == "typescript"
                && case["track"] == "taint"
                && case["score_tier"] == "core"
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(typescript_kernel_policy)
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::CsharpKernel => {
            csharp_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_CSHARP_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::GoKernel => {
            go_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_GO_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::CKernel => c_family_bifrost_case(case, CFamilyKernel::C),
        BifrostRun::CppKernel => c_family_bifrost_case(case, CFamilyKernel::Cpp),
        BifrostRun::RubyKernel => {
            ruby_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_RUBY_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::RustKernel => {
            rust_kernel_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_RUST_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
        BifrostRun::PhpKernel => {
            php_core_case(case)
                && (case["tool_model_references"]["bifrost"]["policy"]
                    .as_str()
                    .is_some_and(|policy| {
                        policy == BIFROST_PHP_POLICY || policy == BIFROST_DIRECT_POLICY
                    })
                    || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
        }
    }
}

/// A Java assertion the dedicated Bifrost Java kernel run owns: the language's
/// whole core population, classic and — once java's `CHALLENGE_ROLLOUT` row is
/// flipped — challenge alike.
///
/// The run pins `BIFROST_JAVA_POLICY` for every assertion, on the Kotlin
/// precedent, so a case's own policy reference is a provenance check rather than
/// the invocation. Thirty of the thirty-two frozen assertions name the Java
/// kernel policy; the direct-propagation pair predates the kernel and names
/// `direct-positive.rqlp` and `explicit-negative.rqlp`, which the v0.2.0 and
/// v0.3.0 freezes bind byte-for-byte. Both are accepted here rather than
/// rewritten, exactly as the C-family kernels accept the cross-language breadth
/// policy. Challenge cases authored by the wave-1 Java PR will name the Java
/// kernel policy, so they need no further accommodation.
fn java_kernel_bifrost_case(case: &Value) -> bool {
    java_core_case(case)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| {
                policy == BIFROST_JAVA_POLICY
                    || policy == BIFROST_DIRECT_POLICY
                    || policy == BIFROST_DIRECT_POSITIVE_POLICY
                    || policy == BIFROST_EXPLICIT_NEGATIVE_POLICY
            })
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

fn java_core_case(case: &Value) -> bool {
    case["language"] == "java" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A JavaScript assertion the dedicated Bifrost JavaScript kernel run owns.
/// Same shape as the Java kernel; the frozen direct-propagation pair here names
/// the cross-language breadth policy rather than the single-assertion pair.
fn javascript_kernel_bifrost_case(case: &Value) -> bool {
    javascript_core_case(case)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| {
                policy == BIFROST_JAVASCRIPT_POLICY || policy == BIFROST_DIRECT_POLICY
            })
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

fn javascript_core_case(case: &Value) -> bool {
    case["language"] == "javascript" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A PHP core assertion. As with the Kotlin, C#, Go, and C-family kernels, the
/// direct-propagation pair predates this kernel and is frozen in the published
/// v0.2.0 and v0.3.0 evidence naming the cross-language breadth policy, so that
/// policy reference is accepted alongside the language-qualified one.
fn php_core_case(case: &Value) -> bool {
    case["language"] == "php" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A C or C++ case this kernel run evaluates. As with the Kotlin and C#
/// kernels, the direct-propagation pair predates the kernel and is frozen in
/// the published v0.2.0 evidence naming the cross-language breadth policy, so
/// that policy reference is accepted alongside the language-qualified one.
fn c_family_bifrost_case(case: &Value, kernel: CFamilyKernel) -> bool {
    c_family_selected_case(case, kernel)
        && (case["tool_model_references"]["bifrost"]["policy"]
            .as_str()
            .is_some_and(|policy| policy == kernel.policy() || policy == BIFROST_DIRECT_POLICY)
            || case["tool_model_references"]["bifrost"]["unsupported_reason"].is_string())
}

/// Policies that carry a TypeScript kernel assertion.
///
/// The direct-propagation pair belongs to both the TypeScript kernel and the
/// cross-language direct-flow breadth slice, and was frozen in `v0.2.0` while
/// still declaring the language-agnostic `core-direct` policy. Freeze manifests
/// bind those case bytes, so the kernel accepts that policy instead of
/// rewriting published evidence; the two policies differ only by the
/// `(language typescript ...)` selector qualifier, which is redundant for a
/// single-fixture TypeScript workspace.
fn typescript_kernel_policy(policy: &str) -> bool {
    policy.ends_with("core-typescript-kernel.rqlp") || policy.ends_with("core-direct.rqlp")
}

fn has_bifrost_model_reference(case: &Value) -> bool {
    let model = &case["tool_model_references"]["bifrost"];
    model.is_object() && (model["policy"].is_string() || model["unsupported_reason"].is_string())
}

/// The smoke population is frozen by contract: the 13-language direct-flow
/// breadth pairs, the Java and JavaScript propagation kernels, the Python
/// parity kernel, and the calibration cases — 118 cases in total. Every later
/// language kernel has its own dedicated `run-bifrost-<language>-kernel`
/// population, so its policy must never leak into the smoke selection even
/// though its cases also carry Bifrost model references.
///
/// Pinning by policy alone stopped being sufficient once the challenge tier was
/// preregistered: a Java, JavaScript, or Python challenge case names the *same*
/// language kernel policy its classic siblings do, so it would have been swept
/// into the frozen 118 and silently changed what that population means. The
/// exclusion is therefore by template identity, which is the property that
/// actually distinguishes the tiers — any case whose `template_id` starts with
/// `dfb-template-chal-` is never smoke-selected, whatever policy it names and
/// whether or not it declares an `unsupported_reason`. The expanded core is
/// evaluated by the dedicated per-language kernel runs instead.
fn smoke_population_case(case: &Value) -> bool {
    if challenge_template_case(case) {
        return false;
    }
    let model = &case["tool_model_references"]["bifrost"];
    if model["unsupported_reason"].is_string() {
        return true;
    }
    const SMOKE_POLICIES: [&str; 7] = [
        BIFROST_DIRECT_POLICY,
        BIFROST_DIRECT_POSITIVE_POLICY,
        BIFROST_EXPLICIT_NEGATIVE_POLICY,
        "adapters/bifrost/policies/one-hop-positive.rqlp",
        BIFROST_JAVA_POLICY,
        BIFROST_JAVASCRIPT_POLICY,
        "adapters/bifrost/policies/core-python-kernel.rqlp",
    ];
    model["policy"]
        .as_str()
        .is_some_and(|policy| SMOKE_POLICIES.contains(&policy))
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

/// The CodeQL JavaScript extractor covers JavaScript and TypeScript alike, so
/// both kernels share one runner. Everything that separates the two
/// populations — the selected case language, the owning pack and query, and
/// the report and raw-evidence roots — hangs off this descriptor, and the
/// selector below refuses the other language's cases outright.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum EcmaKernel {
    JavaScript,
    TypeScript,
}

impl EcmaKernel {
    fn language(self) -> &'static str {
        match self {
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
        }
    }

    fn display_name(self) -> &'static str {
        match self {
            Self::JavaScript => "JavaScript",
            Self::TypeScript => "TypeScript",
        }
    }

    fn adapter(self) -> &'static str {
        match self {
            Self::JavaScript => "codeql-javascript",
            Self::TypeScript => "codeql-typescript",
        }
    }

    fn query(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_QUERY,
            Self::TypeScript => CODEQL_TYPESCRIPT_QUERY,
        }
    }

    fn raw_dir(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_RAW_DIR,
            Self::TypeScript => CODEQL_TYPESCRIPT_RAW_DIR,
        }
    }

    fn report(self) -> &'static str {
        match self {
            Self::JavaScript => CODEQL_JAVASCRIPT_REPORT,
            Self::TypeScript => CODEQL_TYPESCRIPT_REPORT,
        }
    }

    fn qlpack_directory(self) -> &'static str {
        match self {
            Self::JavaScript => "adapters/codeql/javascript",
            Self::TypeScript => "adapters/codeql/typescript",
        }
    }

    /// Whether a selected case may omit its CodeQL query reference.
    ///
    /// The TypeScript direct-propagation pair is shared with the
    /// cross-language direct-flow breadth slice and was frozen in `v0.2.0`
    /// before this pack existed. Freeze manifests bind those case bytes, so
    /// the runner defaults them to the kernel query rather than rewriting
    /// published evidence. A declared query still has to be this kernel's.
    fn allows_implicit_query_reference(self) -> bool {
        matches!(self, Self::TypeScript)
    }
}

/// CodeQL extracts C and C++ with one `cpp` extractor and Bifrost indexes both
/// from one workspace, but DataFlowBench keeps them as two populations with
/// different core denominators: 16 templates for C++, 15 for C, never merged,
/// pooled, or macro-averaged together. Everything that separates them — the
/// selected case language, the scored template set, the policy, the kernel
/// query, and the report and raw-evidence roots — hangs off this descriptor.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CFamilyKernel {
    C,
    Cpp,
}

impl CFamilyKernel {
    fn language(self) -> &'static str {
        match self {
            Self::C => "c",
            Self::Cpp => "cpp",
        }
    }

    fn display_name(self) -> &'static str {
        match self {
            Self::C => "C",
            Self::Cpp => "C++",
        }
    }

    fn policy(self) -> &'static str {
        match self {
            Self::C => BIFROST_C_POLICY,
            Self::Cpp => BIFROST_CPP_POLICY,
        }
    }

    fn query(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_QUERY,
            Self::Cpp => CODEQL_CPP_QUERY,
        }
    }

    fn raw_dir(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_RAW_DIR,
            Self::Cpp => CODEQL_CPP_RAW_DIR,
        }
    }

    fn report(self) -> &'static str {
        match self {
            Self::C => CODEQL_C_REPORT,
            Self::Cpp => CODEQL_CPP_REPORT,
        }
    }

    /// The scored templates of this language's core denominator, read from its
    /// rollout row.
    fn templates(self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }

    /// Whether this language routes its inapplicable cell to
    /// `language-extension` cases that run in the same slice.
    fn has_language_extension_cases(self) -> bool {
        matches!(self, Self::C)
    }
}

/// A case this kernel evaluates: the language's core population, plus — for C —
/// the `language-extension` cases that stand in for the inapplicable
/// exception-catch cell. Extension cases are scored on their own scorecard and
/// never enter the core denominator.
fn c_family_selected_case(case: &Value, kernel: CFamilyKernel) -> bool {
    case["language"].as_str() == Some(kernel.language())
        && case["track"] == "taint"
        && (case["score_tier"] == "core"
            || (kernel.has_language_extension_cases()
                && case["score_tier"] == "language-extension"))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CodeqlLanguage<'a> {
    Java,
    Python,
    /// Kotlin is extracted by CodeQL's `java` extractor, which only sees
    /// Kotlin sources while it traces a real compile. The traced compiler is
    /// carried here because `--build-mode=none` extracts no Kotlin at all.
    Kotlin {
        kotlinc: &'a Path,
    },
    CSharp,
    /// The Go extractor rejects `--build-mode=none` outright; it only sees Go
    /// sources while it traces a real `go build`, so the toolchain is carried
    /// here the way the Kotlin compiler is.
    Go {
        go: &'a Path,
    },
    /// C and C++ share CodeQL's `cpp` extractor. Which of the two populations a
    /// run belongs to is decided by case selection and the kernel query, not by
    /// the extractor.
    CFamily,
    /// Rust support is a public preview in the pinned CLI. The extractor takes
    /// `--build-mode=none`, but it only runs its semantic analyzer when the
    /// source root contains a Cargo manifest, so the runner generates one.
    Rust,
    /// Ruby is buildless: the extractor parses the sources directly under
    /// `--build-mode=none`, with no manifest, project file, or traced compile.
    Ruby,
}

impl CodeqlLanguage<'_> {
    fn cli_name(self) -> &'static str {
        match self {
            Self::Java | Self::Kotlin { .. } => "java",
            Self::Python => "python",
            Self::CSharp => "csharp",
            Self::Go { .. } => "go",
            Self::CFamily => "cpp",
            Self::Rust => "rust",
            Self::Ruby => "ruby",
        }
    }

    /// True when the extractor is traced through a JVM compile that writes
    /// class files into the workspace.
    fn traces_jvm_compile(self) -> bool {
        matches!(self, Self::Java | Self::Kotlin { .. })
    }
}

fn run_codeql_java_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let raw_dir = Path::new("reports/raw/codeql");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::new();
    let mut query_paths = BTreeSet::new();

    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !selected_codeql_java_case(&case) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
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
    write_and_validate_report(Path::new("reports/codeql-java-kernel.json"), &report)?;
    println!("wrote reports/codeql-java-kernel.json");
    Ok(())
}

fn selected_codeql_java_case(case: &Value) -> bool {
    case["language"] == "java"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"].is_object()
}

/// Run one of the two ECMAScript-family CodeQL kernels. This deliberately does
/// not reuse the Java selector or its database/raw-output roots: CodeQL has
/// shared standard libraries, but the benchmark adapters must remain
/// language-scoped. The JavaScript and TypeScript populations are likewise
/// disjoint, each with its own pack, query, report, and raw-evidence root.
fn run_codeql_ecma_kernel(binary: &Path, packs: Option<&Path>, kernel: EcmaKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_codeql_ecma_cases(kernel)?;
    let raw_dir = Path::new(kernel.raw_dir());
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());
    let mut query_paths = BTreeSet::new();

    for (path, case) in selected {
        let model = &case["tool_model_references"]["codeql"];
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            if let Some(reason) = model["unsupported_reason"].as_str() {
                let raw_path = raw_dir.join(format!("{id}.json"));
                fs::write(
                    &raw_path,
                    serde_json::to_string_pretty(&json!({
                        "adapter": kernel.adapter(),
                        "case_id": id,
                        "state": "unsupported",
                        "reason": reason,
                        "evidence_kind": "adapter-capability-declaration"
                    }))? + "\n",
                )?;
                ("unsupported", vec![reason.to_string()], raw_path)
            } else {
                let query = model["query"].as_str().unwrap_or(kernel.query());
                query_paths.insert(PathBuf::from(query));
                run_codeql_ecma_case(
                    binary,
                    packs,
                    &path,
                    &case,
                    Path::new(query),
                    raw_dir,
                    kernel,
                )?
            };
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let mut configuration_paths = query_paths;
    configuration_paths.insert(PathBuf::from(kernel.query()));
    let qlpack_directory = Path::new(kernel.qlpack_directory());
    configuration_paths.insert(qlpack_directory.join("qlpack.yml"));
    let pack_lock = qlpack_directory.join("codeql-pack.lock.yml");
    if pack_lock.is_file() {
        configuration_paths.insert(pack_lock);
    }
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
    write_and_validate_report(Path::new(kernel.report()), &report)?;
    println!("wrote {}", kernel.report());
    Ok(())
}

fn run_codeql_python_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_python_cases()?;
    let raw_dir = Path::new("reports/raw/codeql-python-kernel");
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());
    let mut query_paths = BTreeSet::new();

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let model = &case["tool_model_references"]["codeql"];
        let query = model["query"]
            .as_str()
            .context("Python CodeQL case lacks query reference")?;
        query_paths.insert(PathBuf::from(query));
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(query),
            raw_dir,
            CodeqlLanguage::Python,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_paths = codeql_python_configuration_paths(&query_paths);
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
    write_and_validate_report(Path::new("reports/codeql-python-kernel.json"), &report)?;
    println!("wrote reports/codeql-python-kernel.json");
    Ok(())
}

/// Run the Kotlin-only CodeQL kernel. Kotlin shares CodeQL's `java` extractor
/// and standard library with the Java kernel, so the selector, query, report,
/// and raw-evidence directory are all deliberately Kotlin-scoped: the two
/// populations must never share a result set.
fn run_codeql_kotlin_kernel(binary: &Path, packs: Option<&Path>, kotlinc: &Path) -> Result<()> {
    validate_cases()?;
    let selected = codeql_kotlin_cases()?;
    let raw_dir = Path::new(CODEQL_KOTLIN_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_KOTLIN_QUERY),
            raw_dir,
            CodeqlLanguage::Kotlin { kotlinc },
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_kotlin_configuration_paths())?;
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
    write_and_validate_report(Path::new(CODEQL_KOTLIN_REPORT), &report)?;
    println!("wrote {CODEQL_KOTLIN_REPORT}");
    Ok(())
}

/// Run the C#-only CodeQL kernel. The C# extractor supports
/// `--build-mode=none`, so each fixture is extracted standalone with no project
/// scaffolding, and findings are reconciled against the case's `DFB-SINK:`
/// method callsites.
fn run_codeql_csharp_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_csharp_cases()?;
    let raw_dir = Path::new(CODEQL_CSHARP_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_CSHARP_QUERY),
            raw_dir,
            CodeqlLanguage::CSharp,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_csharp_configuration_paths())?;
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
    write_and_validate_report(Path::new(CODEQL_CSHARP_REPORT), &report)?;
    println!("wrote {CODEQL_CSHARP_REPORT}");
    Ok(())
}

/// Run the Go-only CodeQL kernel. Unlike Python and C#, the Go extractor has
/// no build-free mode, so each cold database is built from the declared fixture
/// plus a synthesized module manifest and a traced `go build`. Findings are
/// reconciled against the case's `DFB-SINK:` function callsites.
fn run_codeql_go_kernel(binary: &Path, packs: Option<&Path>, go: &Path) -> Result<()> {
    validate_cases()?;
    let selected = codeql_go_cases()?;
    let raw_dir = Path::new(CODEQL_GO_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_GO_QUERY),
            raw_dir,
            CodeqlLanguage::Go { go },
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_go_configuration_paths())?;
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
    write_and_validate_report(Path::new(CODEQL_GO_REPORT), &report)?;
    println!("wrote {CODEQL_GO_REPORT}");
    Ok(())
}

fn go_core_case(case: &Value) -> bool {
    case["language"] == "go" && case["track"] == "taint" && case["score_tier"] == "core"
}

fn codeql_go_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !go_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Go core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_GO_QUERY
        {
            bail!(
                "Go core case {} references non-Go CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population(&selected, "Go CodeQL kernel")?;
    if !Path::new(CODEQL_GO_QUERY).is_file() {
        bail!("Go CodeQL query does not exist: {CODEQL_GO_QUERY}");
    }
    Ok(selected)
}

fn codeql_go_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(CODEQL_GO_QUERY)]);
    for candidate in [
        "adapters/codeql/go/qlpack.yml",
        "adapters/codeql/go/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// Run one of the two C-family CodeQL kernels. C and C++ share the `cpp`
/// extractor and one pack, so the population separation is enforced here: each
/// run selects only its own language's cases, analyzes them with its own
/// extension-scoped kernel query, and writes its own report and raw-evidence
/// directory. The two result sets are never merged.
fn run_codeql_c_family_kernel(
    binary: &Path,
    packs: Option<&Path>,
    kernel: CFamilyKernel,
) -> Result<()> {
    validate_cases()?;
    let selected = codeql_c_family_cases(kernel)?;
    let raw_dir = Path::new(kernel.raw_dir());
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(kernel.query()),
            raw_dir,
            CodeqlLanguage::CFamily,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_c_family_configuration_paths(kernel))?;
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
    write_and_validate_report(Path::new(kernel.report()), &report)?;
    println!("wrote {}", kernel.report());
    Ok(())
}

fn codeql_c_family_cases(kernel: CFamilyKernel) -> Result<Vec<(PathBuf, Value)>> {
    let display = kernel.display_name();
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !c_family_selected_case(&case, kernel) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a selected case does carry must name this kernel's query,
        // so the C and C++ populations can never borrow each other's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != kernel.query()
        {
            bail!(
                "{display} case {} references non-{display} CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_c_family_population(&selected, kernel)?;
    if !Path::new(kernel.query()).is_file() {
        bail!("{display} CodeQL query does not exist: {}", kernel.query());
    }
    Ok(selected)
}

/// The core population must be exactly this language's scored templates,
/// balanced one positive to one negative. `language-extension` cases ride
/// along in the same slice, are scored on their own scorecard, and are
/// excluded from that count.
fn validate_c_family_population(
    selected: &[(PathBuf, Value)],
    kernel: CFamilyKernel,
) -> Result<()> {
    let label = format!("{} kernel", kernel.display_name());
    let core = selected
        .iter()
        .filter(|(_, case)| case["score_tier"] == "core")
        .cloned()
        .collect::<Vec<_>>();
    validate_kernel_population_with(&core, &label, &kernel.templates())?;
    if !kernel.has_language_extension_cases() && core.len() != selected.len() {
        bail!("{label} must select core cases only");
    }
    for (path, case) in selected {
        if case["score_tier"] == "language-extension" && case["polarity"] != "positive" {
            bail!(
                "{}: {label} language-extension cases are authored as positives",
                path.display()
            );
        }
    }
    Ok(())
}

/// Run the Rust-only CodeQL kernel. Rust support is a public preview in the
/// pinned CLI 2.26.3 (extractor `rust` 0.1.0, library pack
/// `codeql/rust-all@0.2.19`), and that status is recorded in
/// `docs/rust-kernel.md` alongside the results this run produces. The
/// population is the 30 core assertions of the 15 applicable templates plus the
/// `Result`/`?` `language-extension` pair, which is scored on its own tier.
fn run_codeql_rust_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_rust_cases()?;
    let raw_dir = Path::new(CODEQL_RUST_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_RUST_QUERY),
            raw_dir,
            CodeqlLanguage::Rust,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_rust_configuration_paths())?;
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
    write_and_validate_report(Path::new(CODEQL_RUST_REPORT), &report)?;
    println!("wrote {CODEQL_RUST_REPORT}");
    Ok(())
}

/// Run the Ruby-only CodeQL kernel. `docs/applicability-matrix.md` gates the
/// Ruby tranche on Bifrost's Ruby indexing and names CodeQL as the primary
/// decisive analyzer, so this is the run the Ruby denominator is decided by.
/// The Ruby extractor is buildless, so each of the 32 core assertions is
/// extracted standalone into its own cold database.
fn run_codeql_ruby_kernel(binary: &Path, packs: Option<&Path>) -> Result<()> {
    validate_cases()?;
    let selected = codeql_ruby_cases()?;
    let raw_dir = Path::new(CODEQL_RUBY_RAW_DIR);
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = codeql_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_codeql_case_for_language(
            binary,
            packs,
            &path,
            &case,
            Path::new(CODEQL_RUBY_QUERY),
            raw_dir,
            CodeqlLanguage::Ruby,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&codeql_ruby_configuration_paths())?;
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
    write_and_validate_report(Path::new(CODEQL_RUBY_REPORT), &report)?;
    println!("wrote {CODEQL_RUBY_REPORT}");
    Ok(())
}

fn ruby_core_case(case: &Value) -> bool {
    case["language"] == "ruby" && case["track"] == "taint" && case["score_tier"] == "core"
}

fn codeql_ruby_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !ruby_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Ruby core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_RUBY_QUERY
        {
            bail!(
                "Ruby core case {} references non-Ruby CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population(&selected, "Ruby CodeQL kernel")?;
    if !Path::new(CODEQL_RUBY_QUERY).is_file() {
        bail!("Ruby CodeQL query does not exist: {CODEQL_RUBY_QUERY}");
    }
    Ok(selected)
}

fn codeql_ruby_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(CODEQL_RUBY_QUERY)]);
    for candidate in [
        "adapters/codeql/ruby/qlpack.yml",
        "adapters/codeql/ruby/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// A Rust assertion this kernel owns: the 30 `core` assertions of the 15
/// applicable templates, plus the `Result`/`?` `language-extension` pair. The
/// two tiers are selected together so one run produces both, and are kept apart
/// in the scorecards by `score_tier`; the extension never enters the core
/// denominator.
fn rust_kernel_case(case: &Value) -> bool {
    case["language"] == "rust"
        && case["track"] == "taint"
        && (case["score_tier"] == "core" || case["score_tier"] == "language-extension")
}

fn codeql_rust_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !rust_kernel_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a Rust case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_RUST_QUERY
        {
            bail!(
                "Rust case {} references non-Rust CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_rust_kernel_population(&selected, "Rust CodeQL kernel")?;
    if !Path::new(CODEQL_RUST_QUERY).is_file() {
        bail!("Rust CodeQL query does not exist: {CODEQL_RUST_QUERY}");
    }
    Ok(selected)
}

/// The Rust core population must be exactly the 15 applicable scored templates,
/// balanced one positive to one negative under one model profile. The
/// `Result`/`?` `language-extension` pair rides along in the same slice, is
/// scored on its own scorecard, and is excluded from that count; anything on
/// another tier is a template smuggled back into the core denominator and is
/// rejected here.
fn validate_rust_kernel_population(selected: &[(PathBuf, Value)], label: &str) -> Result<()> {
    for (path, case) in selected {
        let tier = case["score_tier"]
            .as_str()
            .with_context(|| format!("{} lacks score_tier", path.display()))?;
        if tier != "core" && tier != "language-extension" {
            bail!(
                "{label} selected {} with score tier {tier:?}",
                path.display()
            );
        }
    }
    let core = selected
        .iter()
        .filter(|(_, case)| case["score_tier"] == "core")
        .cloned()
        .collect::<Vec<_>>();
    validate_kernel_population_with(&core, label, &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH)
}

fn codeql_rust_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(CODEQL_RUST_QUERY)]);
    for candidate in [
        "adapters/codeql/rust/qlpack.yml",
        "adapters/codeql/rust/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

fn codeql_c_family_configuration_paths(kernel: CFamilyKernel) -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(kernel.query())]);
    for candidate in [
        "adapters/codeql/cpp/qlpack.yml",
        "adapters/codeql/cpp/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

fn csharp_core_case(case: &Value) -> bool {
    case["language"] == "csharp" && case["track"] == "taint" && case["score_tier"] == "core"
}

fn codeql_csharp_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !csharp_core_case(&case) {
            continue;
        }
        // The direct-propagation pair predates this kernel and is frozen in the
        // published v0.2.0 evidence without a CodeQL model reference. Any
        // reference a C# core case does carry must name this kernel's query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_CSHARP_QUERY
        {
            bail!(
                "C# core case {} references non-C# CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population_with(
        &selected,
        "C# CodeQL kernel",
        &expected_core_templates("csharp"),
    )?;
    if !Path::new(CODEQL_CSHARP_QUERY).is_file() {
        bail!("C# CodeQL query does not exist: {CODEQL_CSHARP_QUERY}");
    }
    Ok(selected)
}

fn codeql_csharp_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(CODEQL_CSHARP_QUERY)]);
    for candidate in [
        "adapters/codeql/csharp/qlpack.yml",
        "adapters/codeql/csharp/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// The exact CLI version and build SHA every normalized CodeQL report records.
fn codeql_version_identity(binary: &Path) -> Result<(String, String)> {
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
    Ok((version, build_identity))
}

fn kotlin_core_case(case: &Value) -> bool {
    case["language"] == "kotlin" && case["track"] == "taint" && case["score_tier"] == "core"
}

/// A Scala assertion the Bifrost kernel run owns. Scala is selected the way
/// Kotlin is — by language, track, and score tier — because its
/// direct-propagation pair is frozen in the v0.2.0 evidence naming the
/// cross-language breadth policy, and the run pins the language-qualified
/// policy for the whole population instead of reading it from each case. No
/// CodeQL or Joern counterpart exists: neither pinned tool can extract Scala
/// source, which is coverage recorded in docs/scala-kernel.md, not a negative.
fn scala_core_case(case: &Value) -> bool {
    case["language"] == "scala" && case["track"] == "taint" && case["score_tier"] == "core"
}

fn codeql_kotlin_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !kotlin_core_case(&case) {
            continue;
        }
        // The two direct-propagation cases were frozen in v0.2.0 as part of
        // the cross-language breadth slice and carry no CodeQL reference; any
        // case that does declare one must name the Kotlin kernel query.
        if let Some(query) = case["tool_model_references"]["codeql"]["query"].as_str()
            && query != CODEQL_KOTLIN_QUERY
        {
            bail!(
                "Kotlin core case {} references non-Kotlin CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    validate_kernel_population(&selected, "Kotlin CodeQL kernel")?;
    if !Path::new(CODEQL_KOTLIN_QUERY).is_file() {
        bail!("Kotlin CodeQL query does not exist: {CODEQL_KOTLIN_QUERY}");
    }
    Ok(selected)
}

fn codeql_kotlin_configuration_paths() -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::from([PathBuf::from(CODEQL_KOTLIN_QUERY)]);
    for candidate in [
        "adapters/codeql/kotlin/qlpack.yml",
        "adapters/codeql/kotlin/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

/// Assert that a selected language kernel is exactly the sixteen scored
/// templates under one model profile, balanced one positive to one negative.
fn validate_kernel_population(cases: &[(PathBuf, Value)], label: &str) -> Result<()> {
    validate_kernel_population_with(cases, label, &KERNEL_TEMPLATE_IDS)
}

/// The same assertion for a language whose core denominator is not the full
/// sixteen templates: docs/applicability-matrix.md reduces C and Rust to
/// fifteen, and an inapplicable cell reduces only that language's denominator.
fn validate_kernel_population_with(
    cases: &[(PathBuf, Value)],
    label: &str,
    expected_templates: &[&str],
) -> Result<()> {
    let expected_case_count = 2 * expected_templates.len();
    if cases.len() != expected_case_count {
        bail!(
            "{label} must select exactly {expected_case_count} core assertions; found {}",
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

/// Shape one entry of `schemas/result.schema.json`. This is pure result-schema
/// serialization shared by every anchored adapter; the tool-specific decisions
/// are all made before the outcome reaches it.
fn normalized_result(
    case: &Value,
    id: &str,
    outcome: &str,
    diagnostics: Vec<String>,
    duration: std::time::Duration,
    raw_path: &Path,
) -> Value {
    json!({
        "case_id": id,
        "outcome": outcome,
        "source_anchors": case["source_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "sink_anchors": case["sink_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "witness_checkpoints": [],
        "diagnostics": diagnostics,
        "duration_ms": duration.as_millis() as u64,
        "peak_memory_mb": Value::Null,
        "raw_output": raw_path.to_string_lossy()
    })
}

fn select_codeql_ecma_cases(kernel: EcmaKernel) -> Result<Vec<(PathBuf, Value)>> {
    let display = kernel.display_name();
    let expected_query = kernel.query();
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if !ecma_core_case(&case, kernel) {
            continue;
        }
        let model = &case["tool_model_references"]["codeql"];
        if !model.is_object() && !kernel.allows_implicit_query_reference() {
            bail!(
                "{display} core case {} lacks a CodeQL model reference",
                case["id"]
            );
        }
        if !model["unsupported_reason"].is_string()
            && model["query"].as_str().is_none()
            && !kernel.allows_implicit_query_reference()
        {
            bail!(
                "{display} core case {} lacks a CodeQL query reference",
                case["id"]
            );
        }
        if let Some(query) = model["query"].as_str()
            && query != expected_query
        {
            bail!(
                "{display} core case {} references non-{display} CodeQL query {query:?}",
                case["id"]
            );
        }
        selected.push((path, case));
    }
    // The denominator comes from this language's rollout row, so the ECMA
    // CodeQL kernels expand with their fixtures and need no edit here.
    validate_kernel_population_with(
        &selected,
        &format!("{display} CodeQL kernel"),
        &expected_core_templates(kernel.language()),
    )?;
    Ok(selected)
}

fn ecma_core_case(case: &Value, kernel: EcmaKernel) -> bool {
    case["language"] == kernel.language()
        && case["track"] == "taint"
        && case["score_tier"] == "core"
}

fn run_codeql_ecma_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
    kernel: EcmaKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let display = kernel.display_name();
    let workspace = materialize_codeql_ecma_workspace(case_path, case, kernel)?;
    let database_root = std::env::temp_dir().join(format!(
        "dataflowbench-codeql-{}-databases",
        kernel.language()
    ));
    fs::create_dir_all(&database_root)?;
    let database = database_root.join(id);
    if database.exists() {
        fs::remove_dir_all(&database).with_context(|| format!("clear {}", database.display()))?;
    }
    let raw_path = raw_dir.join(format!("{id}.sarif.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    for stale in [&raw_path, &error_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let result = (|| {
        let create = Command::new(binary)
            .arg("database")
            .arg("create")
            .arg(&database)
            // Both kernels are extracted by CodeQL's `javascript` extractor,
            // which also covers TypeScript syntax. The populations are kept
            // apart by the case selector and by each query's file-extension
            // guard, not by the extractor.
            .arg("--language=javascript")
            .arg(format!("--source-root={}", workspace.display()))
            .arg("--overwrite")
            .output();
        let create = match create {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL {display} database create with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_ecma_spawn_error(
                    raw_dir,
                    id,
                    "database-create",
                    &diagnostic,
                    kernel,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        if !create.status.success() {
            return write_codeql_ecma_error(raw_dir, id, "database-create", &create, None, kernel);
        }

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
        let analyzed = match analyze.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run CodeQL {display} database analyze with {}: {error}",
                    binary.display()
                );
                let error_path = write_codeql_ecma_spawn_error(
                    raw_dir,
                    id,
                    "database-analyze",
                    &diagnostic,
                    kernel,
                )?;
                return Ok(("runner-error", vec![diagnostic], error_path));
            }
        };
        if !analyzed.status.success() {
            return write_codeql_ecma_error(
                raw_dir,
                id,
                "database-analyze",
                &analyzed,
                raw_path.is_file().then_some(raw_path.as_path()),
                kernel,
            );
        }
        if !raw_path.is_file() {
            let diagnostic = format!("CodeQL {display} analysis produced no SARIF output");
            let error_path = write_codeql_ecma_spawn_error(
                raw_dir,
                id,
                "database-analyze",
                &diagnostic,
                kernel,
            )?;
            return Ok(("runner-error", vec![diagnostic], error_path));
        }

        let raw = match fs::read_to_string(&raw_path) {
            Ok(raw) => raw,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!("read CodeQL SARIF {}: {error}", raw_path.display())],
                    raw_path,
                ));
            }
        };
        let sarif: Value = match serde_json::from_str(&raw) {
            Ok(sarif) => sarif,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "parse CodeQL SARIF {}: {error}",
                        raw_path.display()
                    )],
                    raw_path,
                ));
            }
        };
        let execution_errors = sarif_execution_errors(&sarif);
        if !execution_errors.is_empty() {
            return Ok(("runner-error", execution_errors, raw_path));
        }
        if !sarif["runs"]
            .as_array()
            .is_some_and(|runs| !runs.is_empty())
        {
            return Ok((
                "runner-error",
                vec!["CodeQL SARIF contains no analysis runs".to_string()],
                raw_path,
            ));
        }
        let mut diagnostics = sarif_messages(&sarif);
        let (outcome, anchor_diagnostics) = ecma_sarif_outcome(case_path, case, &sarif);
        diagnostics.extend(anchor_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path))
    })();

    let cleanup = clear_codeql_case_artifacts(&workspace, &database);
    match (result, cleanup) {
        (Ok((outcome, diagnostics, raw_path)), Ok(())) => Ok((outcome, diagnostics, raw_path)),
        (Ok((_, mut diagnostics, raw_path)), Err(error)) => {
            diagnostics.push(format!("CodeQL {display} artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, raw_path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "CodeQL {display} artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

fn materialize_codeql_ecma_workspace(
    case_path: &Path,
    case: &Value,
    kernel: EcmaKernel,
) -> Result<PathBuf> {
    let id = case["id"].as_str().expect("schema validated");
    let workspace = std::env::temp_dir()
        .join(format!(
            "dataflowbench-codeql-{}-workspaces",
            kernel.language()
        ))
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

fn write_codeql_ecma_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    output: &std::process::Output,
    raw_path: Option<&Path>,
    kernel: EcmaKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let diagnostic = format!(
        "CodeQL {} {stage} failed with status {}",
        kernel.display_name(),
        output.status
    );
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": kernel.adapter(),
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "status": output.status.code(),
            "stdout": stdout,
            "stderr": stderr,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok((
        "runner-error",
        vec![diagnostic],
        raw_path.unwrap_or(&error_path).to_path_buf(),
    ))
}

fn write_codeql_ecma_spawn_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    kernel: EcmaKernel,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &error_path,
        serde_json::to_string_pretty(&json!({
            "adapter": kernel.adapter(),
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "diagnostic": diagnostic,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(error_path)
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct SinkAnchorLocation {
    file: String,
    marker_line: u64,
    function_name: String,
    callsite_lines: BTreeSet<u64>,
}

/// Anchor reconciliation is language-neutral apart from two surface questions:
/// which function a `DFB-SINK:` marker declares, and which lines call it. One
/// dialect covers JavaScript and TypeScript, which share the surface syntax the
/// reconciler inspects; C# and Go spell both differently from ECMAScript but
/// identically to each other, so they share the second dialect's rules while
/// staying separately named populations; C and C++ declare a sink the same way
/// again but reach a member through `.`, `->`, and `::`; Rust declares it the
/// same way once more and reaches a member through `.` and `::`, but never
/// `->`. Java declares a sink as an identifier before a parameter list and
/// reaches a member through `.` alone — the same two rules as C# and Go — but
/// it stays a separately named dialect so a Java population is never reconciled
/// by a selector that happens to be spelled for another language. Python
/// declares a sink the same way again and also reaches a member through `.`
/// alone, but its comments open with `#` rather than `//`, so it needs its own
/// literal/comment stripping.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum AnchorDialect {
    Ecma,
    CSharp,
    Go,
    Cpp,
    Rust,
    Java,
    Python,
    Ruby,
    Php,
}

impl AnchorDialect {
    /// The function name declared on the line carrying an anchor marker. The
    /// same rule resolves a `DFB-SINK:` and a `DFB-SOURCE:` declaration: both
    /// markers sit on the endpoint function's own declaration line.
    fn declared_function_name(self, declaration: &str, marker: &str) -> Option<String> {
        match self {
            Self::Ecma => ecma_function_name(declaration, marker),
            Self::CSharp
            | Self::Go
            | Self::Cpp
            | Self::Rust
            | Self::Java
            | Self::Python
            | Self::Php => parameter_list_function_name(declaration, marker),
            Self::Ruby => ruby_declared_function_name(declaration, marker),
        }
    }

    fn is_call(self, line: &str, function_name: &str) -> bool {
        match self {
            Self::Ecma => ecma_function_call(line, function_name),
            Self::CSharp | Self::Go | Self::Java => {
                parameter_list_function_call(line, function_name)
            }
            Self::Cpp => cpp_function_call(line, function_name),
            Self::Rust => rust_function_call(line, function_name),
            Self::Python => python_function_call(line, function_name),
            Self::Ruby => ruby_function_call(line, function_name),
            Self::Php => php_function_call(line, function_name),
        }
    }
}

/// How a dialect opens a line comment. Everything else `code_without_literals`
/// inspects — single and double quotes with backslash escapes — coincides
/// across every dialect reconciled here.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CommentSyntax {
    DoubleSlash,
    Hash,
    /// PHP accepts both `//` and `#` as line-comment openers, and the kernel
    /// fixtures may legitimately use either.
    DoubleSlashOrHash,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SarifAnchorMatch {
    Matched,
    Unmatched,
    Ambiguous,
}

fn ecma_sarif_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
) -> (&'static str, Vec<String>) {
    sarif_anchor_outcome(case_path, case, sarif, AnchorDialect::Ecma)
}

/// Reconcile a SARIF document against the case's sink callsites and merge the
/// query's own messages into the retained diagnostics.
fn callsite_anchored_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = sarif_messages(sarif);
    let (outcome, anchor_diagnostics) = sarif_anchor_outcome(case_path, case, sarif, dialect);
    diagnostics.extend(anchor_diagnostics);
    diagnostics.sort();
    diagnostics.dedup();
    (outcome, diagnostics)
}

fn sarif_anchor_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    if sarif_result_count(sarif) == 0 {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove SARIF finding against sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for result in sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
    {
        match sarif_result_anchor_match(result, &sink_locations) {
            SarifAnchorMatch::Matched => matched += 1,
            SarifAnchorMatch::Unmatched => unmatched += 1,
            SarifAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} SARIF finding(s) have ambiguous sink-anchor locations"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} SARIF finding(s) did not match the case sink anchor"
        )],
    )
}

fn sink_anchor_locations(
    case_path: &Path,
    case: &Value,
    dialect: AnchorDialect,
) -> std::result::Result<Vec<SinkAnchorLocation>, String> {
    let fixture_root = case_path
        .parent()
        .ok_or_else(|| "case path has no parent".to_string())?;
    let mut locations = Vec::new();
    for anchor in case["sink_anchors"]
        .as_array()
        .ok_or_else(|| "case has no sink anchors".to_string())?
    {
        let file = anchor["file"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks file".to_string())?;
        let marker = anchor["marker"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks marker".to_string())?;
        let body = fs::read_to_string(fixture_root.join(file))
            .map_err(|error| format!("read sink fixture {file}: {error}"))?;
        let line = anchor_marker_line(&body, marker, anchor["line_hint"].as_u64())?;
        let declaration = body
            .lines()
            .nth(line as usize - 1)
            .ok_or_else(|| format!("sink anchor line {line} is outside {file}"))?;
        let function_name = dialect
            .declared_function_name(declaration, marker)
            .ok_or_else(|| format!("sink marker {marker:?} is not on a function declaration"))?;
        let callsite_lines = body
            .lines()
            .enumerate()
            .filter_map(|(index, candidate)| {
                let candidate_line = index as u64 + 1;
                (candidate_line != line && dialect.is_call(candidate, &function_name))
                    .then_some(candidate_line)
            })
            .collect::<BTreeSet<_>>();
        if callsite_lines.is_empty() {
            return Err(format!(
                "sink function {function_name} has no callsites in {file}"
            ));
        }
        locations.push(SinkAnchorLocation {
            file: file.to_string(),
            marker_line: line,
            function_name,
            callsite_lines,
        });
    }
    if locations.is_empty() {
        return Err("case has no resolvable sink locations".to_string());
    }
    if locations
        .iter()
        .map(|location| (&location.file, location.marker_line))
        .collect::<BTreeSet<_>>()
        .len()
        != locations.len()
    {
        return Err("case contains duplicate sink anchors".to_string());
    }
    Ok(locations)
}

/// Resolve the single line an anchor marker sits on: the declared hint when the
/// case supplies one, and otherwise the marker's only occurrence. An ambiguous
/// marker is an error rather than a guess.
fn anchor_marker_line(
    body: &str,
    marker: &str,
    hinted_line: Option<u64>,
) -> std::result::Result<u64, String> {
    let lines = body
        .lines()
        .enumerate()
        .filter_map(|(index, line)| line.contains(marker).then_some(index as u64 + 1))
        .collect::<Vec<_>>();
    if let Some(line) = hinted_line {
        if !lines.contains(&line) {
            return Err(format!("marker {marker:?} is not on hinted line {line}"));
        }
        return Ok(line);
    }
    if lines.len() == 1 {
        return Ok(lines[0]);
    }
    Err(format!(
        "marker {marker:?} has {} possible lines",
        lines.len()
    ))
}

fn ecma_function_name(line: &str, marker: &str) -> Option<String> {
    let marker_start = line.find(marker)?;
    let declaration = &line[..marker_start];
    let function_start = declaration
        .match_indices("function")
        .filter(|(start, _)| {
            let before = declaration[..*start].chars().next_back();
            let after = declaration[*start + "function".len()..].chars().next();
            !before.is_some_and(ecma_identifier_char) && !after.is_some_and(ecma_identifier_char)
        })
        .map(|(start, _)| start)
        .last()?;
    let mut name = declaration[function_start + "function".len()..].trim_start();
    if let Some(rest) = name.strip_prefix('*') {
        name = rest.trim_start();
    }
    let end = name
        .char_indices()
        .find_map(|(index, character)| (!ecma_identifier_char(character)).then_some(index))
        .unwrap_or(name.len());
    (end > 0).then(|| name[..end].to_string())
}

fn ecma_identifier_char(character: char) -> bool {
    character == '_' || character == '$' || character.is_ascii_alphanumeric()
}

/// The C#, Go, C, and C++ sink markers all sit on a declaration such as
/// `static void dfb_sink(int value) { } // DFB-SINK: ...` or
/// `func dfb_sink(value int) {} // DFB-SINK: ...`. In every one the declared
/// name is the identifier immediately before the parameter list.
fn parameter_list_function_name(declaration: &str, marker: &str) -> Option<String> {
    let marker_start = declaration.find(marker)?;
    let declaration = &declaration[..marker_start];
    let declaration = declaration.split("//").next().unwrap_or(declaration);
    let parameters = declaration.find('(')?;
    let name = declaration[..parameters].trim_end();
    let start = name
        .char_indices()
        .rev()
        .find(|(_, character)| !ascii_identifier_char(*character))
        .map(|(index, character)| index + character.len_utf8())
        .unwrap_or(0);
    let name = &name[start..];
    (!name.is_empty() && !name.starts_with(|character: char| character.is_ascii_digit()))
        .then(|| name.to_string())
}

fn ascii_identifier_char(character: char) -> bool {
    character == '_' || character.is_ascii_alphanumeric()
}

/// C#, Go, and Java reach a member through `.` only. Java's `::` is a method
/// reference, never a call, so it never has to be excluded here.
fn parameter_list_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.'])
}

/// Python reaches a member through `.` only, and opens a comment with `#`.
fn python_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(line, function_name, &['.'], CommentSyntax::Hash)
}

/// Ruby reaches a method through `.` and a constant path through `::`, and
/// opens a comment with `#`. A parenless Ruby call carries no argument list, so
/// it is not a sink callsite under this rule: every benchmark sink takes one
/// positional argument and every fixture spells that call with parentheses.
/// The receiverless source calls the fixtures do spell parenlessly are resolved
/// from their declaration lines, never from a callsite scan.
fn ruby_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(line, function_name, &['.', ':'], CommentSyntax::Hash)
}

/// A Ruby endpoint marker sits on a `def` line, and Ruby's parameter list is
/// optional: `def dfb_source # DFB-SOURCE: ...` declares a method exactly as
/// `def dfb_sink(value) # DFB-SINK: ...` does. The declared name is therefore
/// read after the `def` keyword rather than before a parameter list, which is
/// the one surface rule Ruby does not share with the parameter-list dialects.
fn ruby_declared_function_name(declaration: &str, marker: &str) -> Option<String> {
    let marker_start = declaration.find(marker)?;
    let declaration = &declaration[..marker_start];
    let declaration = declaration.split('#').next().unwrap_or(declaration);
    let (keyword, _) = declaration.match_indices("def").find(|(start, _)| {
        let before = declaration[..*start].chars().next_back();
        let after = declaration[*start + "def".len()..].chars().next();
        !before.is_some_and(ascii_identifier_char)
            && after.is_some_and(|character| character.is_whitespace())
    })?;
    let name = declaration[keyword + "def".len()..].trim_start();
    let name = name.strip_prefix("self.").unwrap_or(name);
    let end = name
        .char_indices()
        .find_map(|(index, character)| (!ascii_identifier_char(character)).then_some(index))
        .unwrap_or(name.len());
    (end > 0 && !name.starts_with(|character: char| character.is_ascii_digit()))
        .then(|| name[..end].to_string())
}

/// PHP reaches an instance member through `->` and a static member or class
/// constant through `::`. Its `.` is string concatenation, not a member
/// operator, so — unlike every other dialect here — a call preceded by `.` is a
/// genuine call of the free benchmark function and must not be excluded. PHP
/// opens a line comment with either `//` or `#`.
fn php_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(
        line,
        function_name,
        &['>', ':'],
        CommentSyntax::DoubleSlashOrHash,
    )
}

/// C and C++ reach a member through `.`, `->`, and `::`; none of those is a
/// call of the free benchmark sink function the anchor declares.
fn cpp_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.', '>', ':'])
}

/// Rust reaches a member through `.` and a path through `::`; it has no `->`
/// member operator, so — unlike C and C++ — `>` is not a qualifying prefix.
fn rust_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.', ':'])
}

fn member_prefixed_function_call(
    line: &str,
    function_name: &str,
    member_prefixes: &[char],
) -> bool {
    member_prefixed_call_in(
        line,
        function_name,
        member_prefixes,
        CommentSyntax::DoubleSlash,
    )
}

fn member_prefixed_call_in(
    line: &str,
    function_name: &str,
    member_prefixes: &[char],
    comment: CommentSyntax,
) -> bool {
    let line = code_without_literals_in(line, comment);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        if !before.is_some_and(ascii_identifier_char)
            && !before.is_some_and(|character| member_prefixes.contains(&character))
            && after == Some('(')
        {
            return true;
        }
        search_from = end;
    }
    false
}

fn ecma_function_call(line: &str, function_name: &str) -> bool {
    let line = code_without_literals(line);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        let preceded_by_member = before == Some('.') || before == Some('?');
        if !before.is_some_and(ecma_identifier_char) && !preceded_by_member && after == Some('(') {
            let prefix = line[..start].trim_end();
            if !prefix.ends_with("function") {
                return true;
            }
        }
        search_from = end;
    }
    false
}

/// Blank out string literals and drop line comments so a call-shaped substring
/// inside a literal never counts as a callsite. Single/double/backtick quotes
/// with backslash escapes are common to every dialect reconciled here; only the
/// comment opener differs.
fn code_without_literals(line: &str) -> String {
    code_without_literals_in(line, CommentSyntax::DoubleSlash)
}

fn code_without_literals_in(line: &str, comment: CommentSyntax) -> String {
    let mut output = String::with_capacity(line.len());
    let mut quote = None;
    let mut escaped = false;
    let mut characters = line.chars().peekable();
    while let Some(character) = characters.next() {
        if let Some(active_quote) = quote {
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == active_quote {
                quote = None;
            }
            output.push(' ');
            continue;
        }
        let opens_comment = match comment {
            CommentSyntax::DoubleSlash => character == '/' && characters.peek() == Some(&'/'),
            CommentSyntax::Hash => character == '#',
            CommentSyntax::DoubleSlashOrHash => {
                character == '#' || (character == '/' && characters.peek() == Some(&'/'))
            }
        };
        if opens_comment {
            break;
        }
        if matches!(character, '\'' | '"' | '`') {
            quote = Some(character);
            output.push(' ');
        } else {
            output.push(character);
        }
    }
    output
}

fn sarif_result_anchor_match(
    result: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> SarifAnchorMatch {
    let Some(locations) = result["locations"].as_array() else {
        return SarifAnchorMatch::Ambiguous;
    };
    if locations.is_empty() {
        return SarifAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    let mut malformed = false;
    for location in locations {
        let Some(uri) = location["physicalLocation"]["artifactLocation"]["uri"].as_str() else {
            malformed = true;
            continue;
        };
        let Some(line) = location["physicalLocation"]["region"]["startLine"].as_u64() else {
            malformed = true;
            continue;
        };
        for (index, anchor) in sink_locations.iter().enumerate() {
            if evidence_path_matches_file(uri, &anchor.file)
                && anchor.callsite_lines.contains(&line)
            {
                matches.insert(index);
            }
        }
    }
    if malformed || matches.len() > 1 {
        SarifAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        SarifAnchorMatch::Matched
    } else {
        SarifAnchorMatch::Unmatched
    }
}

/// Does a path reported by a tool denote the case's fixture file? SARIF reports
/// a URI and Joern reports a CPG filename; both are matched the same way,
/// against absolute, workspace-relative, and bare-filename spellings.
fn evidence_path_matches_file(uri: &str, file: &str) -> bool {
    let uri = uri.replace('\\', "/");
    let uri = uri.split(['?', '#']).next().unwrap_or(&uri);
    let uri = uri.strip_prefix("file://").unwrap_or(uri);
    let uri = uri.trim_start_matches('/');
    let normalize = |path: &str| path.trim_start_matches("./").replace('\\', "/");
    let uri = normalize(uri);
    let file = normalize(file);
    uri == file
        || uri.ends_with(&format!("/{file}"))
        || Path::new(&uri).file_name().and_then(|name| name.to_str())
            == Path::new(&file).file_name().and_then(|name| name.to_str())
}

fn selected_codeql_python_case(case: &Value) -> bool {
    case["language"] == "python"
        && case["track"] == "taint"
        && case["score_tier"] == "core"
        && case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .is_some_and(|query| query == CODEQL_PYTHON_QUERY)
}

fn codeql_python_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut all_cases = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if selected_codeql_python_case(&case) {
            all_cases.push((path, case));
        }
    }
    let query = validate_codeql_python_population(&all_cases)?;
    if !query.is_file() {
        bail!("Python CodeQL query does not exist: {}", query.display());
    }
    Ok(all_cases)
}

fn validate_codeql_python_population(cases: &[(PathBuf, Value)]) -> Result<PathBuf> {
    let mut queries = BTreeSet::new();
    for (path, case) in cases {
        if !selected_codeql_python_case(case) {
            bail!(
                "Python CodeQL selection contains a non-core or non-Python case: {}",
                path.display()
            );
        }
        let query = case["tool_model_references"]["codeql"]["query"]
            .as_str()
            .context("Python CodeQL case lacks query reference")?;
        queries.insert(PathBuf::from(query));
    }
    let templates = expected_core_templates("python");
    validate_kernel_population_with(cases, "Python CodeQL kernel", &templates)?;
    if queries.len() != 1 {
        let case_count = 2 * templates.len();
        bail!("Python CodeQL kernel must use one query across all {case_count} cases");
    }
    let query = queries.into_iter().next().expect("one query validated");
    Ok(query)
}

fn codeql_python_configuration_paths(query_paths: &BTreeSet<PathBuf>) -> BTreeSet<PathBuf> {
    let mut paths = query_paths.clone();
    for candidate in [
        "adapters/codeql/python/qlpack.yml",
        "adapters/codeql/python/codeql-pack.lock.yml",
    ]
    .into_iter()
    .map(PathBuf::from)
    {
        if candidate.is_file() {
            paths.insert(candidate);
        }
    }
    paths
}

fn run_codeql_case(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    run_codeql_case_for_language(
        binary,
        packs,
        case_path,
        case,
        query,
        raw_dir,
        CodeqlLanguage::Java,
    )
}

fn run_codeql_case_for_language(
    binary: &Path,
    packs: Option<&Path>,
    case_path: &Path,
    case: &Value,
    query: &Path,
    raw_dir: &Path,
    language: CodeqlLanguage,
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
    let mut create_command = Command::new(binary);
    if language.traces_jvm_compile() {
        let classes = workspace.join("classes");
        fs::create_dir_all(&classes)?;
    }
    if matches!(language, CodeqlLanguage::Go { .. }) {
        fs::write(workspace.join("go.mod"), GO_MODULE_MANIFEST)
            .with_context(|| format!("write Go module manifest in {}", workspace.display()))?;
    }
    if matches!(language, CodeqlLanguage::Rust) {
        write_rust_cargo_manifest(&workspace, case)?;
    }
    create_command.args(codeql_database_create_args(
        &database, &workspace, case, language,
    )?);
    let create = match create_command.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database create: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-create", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
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
    let analyzed = match analyze.output() {
        Ok(output) => output,
        Err(error) => {
            let diagnostic = format!("failed to run CodeQL database analyze: {error}");
            let raw_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    if !analyzed.status.success() {
        let error = write_codeql_error(raw_dir, id, "database-analyze", &analyzed)?;
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(error);
    }
    let sarif_text = match fs::read_to_string(&raw_path) {
        Ok(text) => text,
        Err(error) => {
            let (outcome, diagnostics, error_path) =
                codeql_missing_sarif_error(raw_dir, id, &raw_path, &error)?;
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok((outcome, diagnostics, error_path));
        }
    };
    let sarif: Value = match serde_json::from_str(&sarif_text) {
        Ok(sarif) => sarif,
        Err(error) => {
            let diagnostic = format!("parse CodeQL SARIF {}: {error}", raw_path.display());
            clear_codeql_case_artifacts(&workspace, &database)?;
            return Ok(("runner-error", vec![diagnostic], raw_path));
        }
    };
    let execution_errors = sarif_execution_errors(&sarif);
    if !execution_errors.is_empty() {
        clear_codeql_case_artifacts(&workspace, &database)?;
        return Ok(("runner-error", execution_errors, raw_path));
    }
    let (outcome, diagnostics) = match language {
        CodeqlLanguage::Python => normalize_anchored_codeql_sarif(case, &sarif, "Python"),
        CodeqlLanguage::Kotlin { .. } => normalize_anchored_codeql_sarif(case, &sarif, "Kotlin"),
        // C#, Go, C, C++, and Rust fixtures all declare a `DFB-SINK:` function,
        // so the finding is reconciled against that function's callsites rather
        // than the sink file alone.
        CodeqlLanguage::CSharp => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::CSharp)
        }
        CodeqlLanguage::Go { .. } => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Go)
        }
        CodeqlLanguage::CFamily => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Cpp)
        }
        CodeqlLanguage::Rust => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Rust)
        }
        CodeqlLanguage::Ruby => {
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::Ruby)
        }
        CodeqlLanguage::Java => {
            let result_count = sarif_result_count(&sarif);
            let diagnostics = sarif_messages(&sarif);
            let outcome = if result_count == 0 {
                "not-reached"
            } else {
                "reached"
            };
            (outcome, diagnostics)
        }
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

/// Give a materialized Rust workspace the Cargo manifest its extractor needs.
///
/// Both Rust analyzers want a crate, not a loose file: CodeQL's extractor and
/// Joern's `rust2cpg` each walk a Cargo manifest. `rust2cpg` given a bare `.rs`
/// file produces an empty CPG — no methods, no calls — so the manifest is the
/// difference between an analyzed case and one that silently looks negative.
/// Pointing the binary target straight at the fixture rather than moving it to
/// `src/main.rs` also keeps every reported location on the case's own anchor
/// filename, so no anchor reconciliation has to map a crate-relative path back.
///
/// The CodeQL extractor accepts `--build-mode=none` and never compiles the fixture,
/// but with no manifest in the source root it logs "semantic analyzer
/// unavailable (no manifest found)" and produces a syntax-only database that
/// resolves no call targets. The manifest is generated rather than checked in
/// so the fixtures stay single-file, exactly like every other language kernel:
/// the case metadata lists only the `.rs` file, and the crate root points
/// straight at it instead of moving it under `src/`, which keeps SARIF
/// locations on the case's own anchor paths. `[workspace]` stops Cargo from
/// walking out of the temporary directory looking for a parent workspace.
fn write_rust_cargo_manifest(workspace: &Path, case: &Value) -> Result<()> {
    let fixtures = codeql_fixture_names(case)?;
    let [fixture] = fixtures[..] else {
        bail!(
            "Rust case {} must declare exactly one fixture file; found {}",
            case["id"],
            fixtures.len()
        );
    };
    let manifest = format!(
        "[package]\n\
         name = \"dataflowbench_case\"\n\
         version = \"0.0.0\"\n\
         edition = \"2021\"\n\
         \n\
         [[bin]]\n\
         name = \"dataflowbench_case\"\n\
         path = \"{fixture}\"\n\
         \n\
         [workspace]\n"
    );
    fs::write(workspace.join("Cargo.toml"), manifest)
        .with_context(|| format!("write Cargo manifest in {}", workspace.display()))?;
    Ok(())
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

fn write_codeql_spawn_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
) -> Result<PathBuf> {
    let raw_path = raw_dir.join(format!("{id}-error.json"));
    fs::write(
        &raw_path,
        serde_json::to_string_pretty(&json!({
            "adapter": "codeql",
            "case_id": id,
            "state": "runner-error",
            "stage": stage,
            "diagnostic": diagnostic,
            "evidence_kind": "retained-process-diagnostics"
        }))? + "\n",
    )?;
    Ok(raw_path)
}

fn codeql_missing_sarif_error(
    raw_dir: &Path,
    id: &str,
    raw_path: &Path,
    error: &std::io::Error,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let diagnostic = format!("read CodeQL SARIF {}: {error}", raw_path.display());
    let error_path = write_codeql_spawn_error(raw_dir, id, "database-analyze", &diagnostic)?;
    Ok(("runner-error", vec![diagnostic], error_path))
}

fn codeql_database_create_args(
    database: &Path,
    workspace: &Path,
    case: &Value,
    language: CodeqlLanguage,
) -> Result<Vec<String>> {
    let mut args = vec![
        "database".to_string(),
        "create".to_string(),
        database.to_string_lossy().into_owned(),
        format!("--language={}", language.cli_name()),
        format!("--source-root={}", workspace.display()),
        "--overwrite".to_string(),
    ];
    match language {
        CodeqlLanguage::Java => {
            let fixtures = codeql_fixture_names(case)?;
            args.push(format!("--command=javac -d classes {}", fixtures.join(" ")));
        }
        // CodeQL 2.26.3 extracts no Kotlin at all under `--build-mode=none`;
        // the java extractor only sees Kotlin while it traces a real compile.
        CodeqlLanguage::Kotlin { kotlinc } => {
            let fixtures = codeql_fixture_names(case)?;
            args.push(format!(
                "--command={} -nowarn -d classes {}",
                kotlinc.display(),
                fixtures.join(" ")
            ));
        }
        // The Python, C#, C/C++, and Rust extractors all support
        // `--build-mode=none`, so the fixtures need no project scaffolding, no
        // restore step, and no traced compile. For C/C++ the buildless
        // extractor still discovers a real compiler (clang) to resolve the
        // translation unit; Rust still needs the generated Cargo manifest in
        // the workspace, because without a manifest the extractor reports
        // "semantic analyzer unavailable" and extracts syntax only.
        CodeqlLanguage::Python
        | CodeqlLanguage::CSharp
        | CodeqlLanguage::CFamily
        | CodeqlLanguage::Rust
        | CodeqlLanguage::Ruby => args.push("--build-mode=none".to_string()),
        // CodeQL 2.26.3 rejects `--build-mode=none` for Go. The traced build is
        // `go build ./...` over the workspace's synthesized module manifest,
        // which keeps extraction reproducible instead of letting autobuild
        // write its own manifest and resolve dependencies.
        CodeqlLanguage::Go { go } => {
            args.push("--build-mode=manual".to_string());
            args.push(format!("--command={} build ./...", go.display()));
        }
    }
    Ok(args)
}

fn codeql_fixture_names(case: &Value) -> Result<Vec<&str>> {
    case["fixture_files"]
        .as_array()
        .context("CodeQL case lacks fixture_files")?
        .iter()
        .map(|fixture| {
            fixture
                .as_str()
                .context("CodeQL fixture_files must contain strings")
        })
        .collect()
}

/// Reconcile SARIF findings with the case's `DFB-SINK:` anchor file. A finding
/// that lands in an anchored sink file is `reached`; findings that carry no
/// usable location, or that never map onto a canonical sink anchor, are
/// incomplete evidence and stay `inconclusive` rather than becoming a clean
/// negative.
fn normalize_anchored_codeql_sarif(
    case: &Value,
    sarif: &Value,
    language: &str,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = sarif_messages(sarif);
    let Some(runs) = sarif["runs"].as_array() else {
        diagnostics.push("CodeQL SARIF is missing its runs array".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    };
    if runs.is_empty() {
        diagnostics.push("CodeQL SARIF contains no analysis runs".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    }
    if runs.iter().any(|run| run["results"].as_array().is_none()) {
        diagnostics.push("CodeQL SARIF contains a run without a results array".to_string());
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    }
    let results = runs
        .iter()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
        .collect::<Vec<_>>();
    if results.is_empty() {
        return ("not-reached", diagnostics);
    }

    let mut anchored_findings = 0;
    let mut unmappable_findings = 0;
    for result in results {
        let Some(locations) = result["locations"].as_array() else {
            unmappable_findings += 1;
            continue;
        };
        let mut has_valid_location = false;
        let mut maps_to_sink = false;
        for location in locations {
            let Some(uri) = location["physicalLocation"]["artifactLocation"]["uri"].as_str() else {
                continue;
            };
            let Some(line) = location["physicalLocation"]["region"]["startLine"].as_u64() else {
                continue;
            };
            if line == 0 {
                continue;
            }
            has_valid_location = true;
            if sink_anchor_file_matches(case, uri) {
                maps_to_sink = true;
            }
        }
        if maps_to_sink {
            anchored_findings += 1;
        } else {
            unmappable_findings += 1;
            if !has_valid_location {
                diagnostics
                    .push("CodeQL SARIF finding has no usable physical location".to_string());
            }
        }
    }
    if anchored_findings > 0 {
        if unmappable_findings > 0 {
            diagnostics.push(format!(
                "CodeQL SARIF retained {unmappable_findings} finding(s) that did not map to a canonical {language} sink anchor"
            ));
        }
        diagnostics.sort();
        diagnostics.dedup();
        ("reached", diagnostics)
    } else {
        diagnostics.push(format!(
            "CodeQL SARIF findings could not be mapped to a canonical {language} sink anchor; analysis evidence is incomplete"
        ));
        diagnostics.sort();
        diagnostics.dedup();
        ("inconclusive", diagnostics)
    }
}

fn sink_anchor_file_matches(case: &Value, uri: &str) -> bool {
    case["sink_anchors"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|anchor| {
            let Some(file) = anchor["file"].as_str() else {
                return false;
            };
            evidence_path_matches_file(uri, file)
        })
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

/// One Joern kernel: a single language, its own case selection, its own
/// frontend, its own normalized report, and its own retained-evidence root.
/// Joern shares one CPG query language and one data-flow engine across all of
/// them, exactly as CodeQL shares a standard library; the populations are kept
/// apart by the selector and the report paths, never by the engine.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum JoernKernel {
    Java,
    JavaScript,
    Python,
    Ruby,
    Php,
    Rust,
}

impl JoernKernel {
    fn language(self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::JavaScript => "javascript",
            Self::Python => "python",
            Self::Ruby => "ruby",
            Self::Php => "php",
            Self::Rust => "rust",
        }
    }

    fn display_name(self) -> &'static str {
        match self {
            Self::Java => "Java",
            Self::JavaScript => "JavaScript",
            Self::Python => "Python",
            Self::Ruby => "Ruby",
            Self::Php => "PHP",
            Self::Rust => "Rust",
        }
    }

    /// The `importCode` language identifier the script is invoked with, which
    /// selects `javasrc2cpg`, `jssrc2cpg`, `pysrc2cpg`, `rubysrc2cpg`,
    /// `php2cpg`, and `rust2cpg` respectively. Each kernel names exactly one
    /// source frontend; none of the six is analyzed through a bytecode or
    /// binary frontend.
    fn frontend(self) -> &'static str {
        match self {
            Self::Java => "JAVASRC",
            Self::JavaScript => "JSSRC",
            Self::Python => "PYTHONSRC",
            Self::Ruby => "RUBYSRC",
            Self::Php => "PHP",
            Self::Rust => "RUST",
        }
    }

    fn report(self) -> &'static str {
        match self {
            Self::Java => JOERN_JAVA_REPORT,
            Self::JavaScript => JOERN_JAVASCRIPT_REPORT,
            Self::Python => JOERN_PYTHON_REPORT,
            Self::Ruby => JOERN_RUBY_REPORT,
            Self::Php => JOERN_PHP_REPORT,
            Self::Rust => JOERN_RUST_REPORT,
        }
    }

    fn raw_dir(self) -> &'static str {
        match self {
            Self::Java => JOERN_JAVA_RAW_DIR,
            Self::JavaScript => JOERN_JAVASCRIPT_RAW_DIR,
            Self::Python => JOERN_PYTHON_RAW_DIR,
            Self::Ruby => JOERN_RUBY_RAW_DIR,
            Self::Php => JOERN_PHP_RAW_DIR,
            Self::Rust => JOERN_RUST_RAW_DIR,
        }
    }

    fn dialect(self) -> AnchorDialect {
        match self {
            Self::Java => AnchorDialect::Java,
            Self::JavaScript => AnchorDialect::Ecma,
            Self::Python => AnchorDialect::Python,
            Self::Ruby => AnchorDialect::Ruby,
            Self::Php => AnchorDialect::Php,
            Self::Rust => AnchorDialect::Rust,
        }
    }

    /// The scored templates of this language's core denominator, read from its
    /// rollout row. Rust's exception-catch cell is inapplicable —
    /// docs/applicability-matrix.md records why — so its classic core is 15
    /// templates, and the `Result`/`?` `language-extension` pair that stands in
    /// for the missing cell is scored on its own tier and is not selected here.
    fn templates(self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }

    /// Whether a case of this language needs a synthesized build manifest in
    /// its workspace before the frontend can extract it. `rust2cpg` walks a
    /// Cargo crate, not a loose `.rs` file: given a bare fixture it produces an
    /// empty CPG. The manifest is generated per workspace and never written
    /// beside a fixture, so nothing under `cases/` moves.
    fn needs_cargo_manifest(self) -> bool {
        matches!(self, Self::Rust)
    }

    fn label(self) -> String {
        format!("Joern {} kernel", self.display_name())
    }
}

fn joern_core_case(case: &Value, kernel: JoernKernel) -> bool {
    case["language"] == kernel.language()
        && case["track"] == "taint"
        && case["score_tier"] == "core"
}

/// Select a Joern kernel population runner-side. The v0.3.0 freeze binds every
/// `case.json` byte, so no case declares a Joern model reference; the selection
/// is by language, track, and score tier alone, and the invocation is pinned
/// here the way the Kotlin Bifrost run pins its policy.
fn select_joern_cases(kernel: JoernKernel) -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if joern_core_case(&case, kernel) {
            selected.push((path, case));
        }
    }
    validate_kernel_population_with(&selected, &kernel.label(), &kernel.templates())?;
    Ok(selected)
}

fn run_joern_kernel(binary: &Path, kernel: JoernKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_joern_cases(kernel)?;
    let script = Path::new(JOERN_KERNEL_SCRIPT);
    if !script.is_file() {
        bail!("Joern kernel script does not exist: {JOERN_KERNEL_SCRIPT}");
    }
    let script = fs::canonicalize(script).context("resolve the Joern kernel script")?;
    let raw_dir = Path::new(kernel.raw_dir());
    fs::create_dir_all(raw_dir)?;
    let raw_root = fs::canonicalize(raw_dir).context("resolve the Joern evidence directory")?;
    let started = now_seconds()?;
    let (version, build_identity) = joern_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            run_joern_case(binary, &script, &path, &case, raw_dir, &raw_root, kernel)?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&BTreeSet::from([PathBuf::from(JOERN_KERNEL_SCRIPT)]))?;
    let report = json!({
        "schema_version": 1,
        "tool": "joern",
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
    write_and_validate_report(Path::new(kernel.report()), &report)?;
    println!("wrote {}", kernel.report());
    Ok(())
}

/// The exact Joern version every normalized Joern report records. The pinned
/// distribution reports no separate build SHA, so the released version is the
/// build identity.
fn joern_version_identity(binary: &Path) -> Result<(String, String)> {
    let output = Command::new(binary)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", binary.display()))?;
    if !output.status.success() {
        bail!(
            "{} --version failed with status {}",
            binary.display(),
            output.status
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let version = stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("Version:"))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("Joern did not report a version")?
        .to_string();
    let build_identity = format!("joern-cli:{version}");
    Ok((version, build_identity))
}

/// The two benchmark-controlled endpoint identifiers of one case, read out of
/// the fixture's own marker lines.
#[derive(Clone, Debug, PartialEq, Eq)]
struct BenchmarkEndpoints {
    source_function: String,
    sink_function: String,
}

/// Resolve a case's source and sink function names from its anchors. The
/// fixtures are frozen and mostly spell both `dfb_source`/`dfb_sink`, but the
/// two Java direct-propagation assertions predate that convention, so the names
/// are always read from the marker line rather than assumed. Both the Joern
/// kernels and the Semgrep kernels resolve their benchmark-controlled endpoint
/// contract through this one function, so neither can drift from the other.
fn benchmark_endpoint_names(
    case_path: &Path,
    case: &Value,
    dialect: AnchorDialect,
) -> std::result::Result<BenchmarkEndpoints, String> {
    let sink_functions = sink_anchor_locations(case_path, case, dialect)?
        .into_iter()
        .map(|location| location.function_name)
        .collect::<BTreeSet<_>>();
    let sink_function = match sink_functions.len() {
        1 => sink_functions.into_iter().next().expect("length checked"),
        count => {
            return Err(format!(
                "case declares {count} distinct sink functions; the kernel query tags exactly one"
            ));
        }
    };
    let source_functions = anchor_function_names(case_path, case, "source_anchors", dialect)?;
    let source_function = match source_functions.len() {
        1 => source_functions.into_iter().next().expect("length checked"),
        count => {
            return Err(format!(
                "case declares {count} distinct source functions; the kernel query tags exactly one"
            ));
        }
    };
    Ok(BenchmarkEndpoints {
        source_function,
        sink_function,
    })
}

/// The distinct function names declared on one anchor set's marker lines.
fn anchor_function_names(
    case_path: &Path,
    case: &Value,
    anchor_field: &str,
    dialect: AnchorDialect,
) -> std::result::Result<BTreeSet<String>, String> {
    let fixture_root = case_path
        .parent()
        .ok_or_else(|| "case path has no parent".to_string())?;
    let anchors = case[anchor_field]
        .as_array()
        .ok_or_else(|| format!("case has no {anchor_field}"))?;
    let mut names = BTreeSet::new();
    for anchor in anchors {
        let file = anchor["file"]
            .as_str()
            .ok_or_else(|| format!("{anchor_field} entry lacks file"))?;
        let marker = anchor["marker"]
            .as_str()
            .ok_or_else(|| format!("{anchor_field} entry lacks marker"))?;
        let body = fs::read_to_string(fixture_root.join(file))
            .map_err(|error| format!("read fixture {file}: {error}"))?;
        let line = anchor_marker_line(&body, marker, anchor["line_hint"].as_u64())?;
        let declaration = body
            .lines()
            .nth(line as usize - 1)
            .ok_or_else(|| format!("anchor line {line} is outside {file}"))?;
        names.insert(
            dialect
                .declared_function_name(declaration, marker)
                .ok_or_else(|| format!("marker {marker:?} is not on a function declaration"))?,
        );
    }
    if names.is_empty() {
        return Err(format!("case has no resolvable {anchor_field}"));
    }
    Ok(names)
}

fn run_joern_case(
    binary: &Path,
    script: &Path,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
    raw_root: &Path,
    kernel: JoernKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    for stale in [&raw_path, &error_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence. That is `inconclusive` with a retained reason; it
    // is never a clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, kernel.dialect()) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Joern endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "joern",
                    "case_id": id,
                    "state": "inconclusive",
                    "stage": "endpoint-resolution",
                    "reason": diagnostic,
                    "evidence_kind": "retained-anchor-resolution"
                }))? + "\n",
            )?;
            return Ok(("inconclusive", vec![diagnostic], error_path));
        }
    };

    let scratch = joern_case_scratch(kernel, id)?;
    let workspace = scratch.join("source");
    fs::create_dir_all(&workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }
    if kernel.needs_cargo_manifest() {
        write_rust_cargo_manifest(&workspace, case)?;
    }
    let absolute_raw_path = raw_root.join(format!("{id}.json"));

    let result = (|| {
        let mut command = Command::new(binary);
        command
            // Joern materializes its console project under the working
            // directory; keeping that inside the per-case scratch root means no
            // case can observe another case's CPG.
            .current_dir(&scratch)
            .arg("--script")
            .arg(script)
            .arg("--param")
            .arg(format!("inputPath={}", workspace.display()))
            .arg("--param")
            .arg(format!("language={}", kernel.frontend()))
            .arg("--param")
            .arg(format!("sourceName={}", endpoints.source_function))
            .arg("--param")
            .arg(format!("sinkName={}", endpoints.sink_function))
            .arg("--param")
            .arg(format!("outputPath={}", absolute_raw_path.display()))
            .stdin(std::process::Stdio::null());
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Joern {} kernel script with {}: {error}",
                    kernel.display_name(),
                    binary.display()
                );
                let path = write_joern_error(raw_dir, id, "script-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        if !output.status.success() {
            let diagnostic = format!(
                "Joern {} kernel script failed with status {}",
                kernel.display_name(),
                output.status
            );
            let path =
                write_joern_error(raw_dir, id, "script-execution", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        if !raw_path.is_file() {
            let diagnostic = format!(
                "Joern {} kernel script produced no evidence document",
                kernel.display_name()
            );
            let path = write_joern_error(raw_dir, id, "script-output", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let text = match fs::read_to_string(&raw_path) {
            Ok(text) => text,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "read Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        let raw: Value = match serde_json::from_str(&text) {
            Ok(raw) => raw,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "parse Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        let (outcome, diagnostics) = joern_flow_outcome(case_path, case, &raw, kernel.dialect());
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Joern case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Joern case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

fn joern_case_scratch(kernel: JoernKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-joern-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

fn write_joern_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let mut evidence = json!({
        "adapter": "joern",
        "case_id": id,
        "state": "runner-error",
        "stage": stage,
        "diagnostic": diagnostic,
        "evidence_kind": "retained-process-diagnostics"
    });
    if let Some(output) = output {
        evidence["status"] = json!(output.status.code());
        evidence["stdout"] = json!(String::from_utf8_lossy(&output.stdout).trim());
        evidence["stderr"] = json!(String::from_utf8_lossy(&output.stderr).trim());
    }
    fs::write(&error_path, serde_json::to_string_pretty(&evidence)? + "\n")?;
    Ok(error_path)
}

/// How one piece of retained non-SARIF evidence reconciles against a case's
/// sink anchors. A Joern flow and a Semgrep finding are reconciled by the same
/// three-way answer, so neither adapter can drift into treating unusable
/// evidence as a negative.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum EvidenceAnchorMatch {
    Matched,
    Unmatched,
    Ambiguous,
}

/// Normalize one retained Joern evidence document.
///
/// A flow counts as `reached` only when one of its elements sits on a callsite
/// of the case's own anchored sink function, in the anchored file — the same
/// reconciliation the CodeQL C#, Go, C, C++, and Rust kernels apply to SARIF.
/// Every other state is preserved distinctly: a script, frontend, or engine
/// failure is `runner-error`; a run that never observed one of the two
/// benchmark-controlled endpoints, or that produced flows with no usable
/// location, is `inconclusive`. Only a complete run that observed both
/// endpoints and produced no flow is `not-reached`.
fn joern_flow_outcome(
    case_path: &Path,
    case: &Value,
    raw: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    match raw["state"].as_str() {
        Some("analyzed") => {}
        Some("runner-error") => {
            return (
                "runner-error",
                vec![
                    raw["diagnostic"]
                        .as_str()
                        .unwrap_or("Joern reported a runner error without a diagnostic")
                        .to_string(),
                ],
            );
        }
        Some(other) => {
            return (
                "runner-error",
                vec![format!(
                    "Joern evidence declares unexpected state {other:?}"
                )],
            );
        }
        None => {
            return (
                "runner-error",
                vec!["Joern evidence declares no state".to_string()],
            );
        }
    }
    let Some(flows) = raw["flows"].as_array() else {
        return (
            "runner-error",
            vec!["Joern evidence lacks its flows array".to_string()],
        );
    };
    let (Some(sources), Some(sinks)) = (
        raw["source_node_count"].as_u64(),
        raw["sink_node_count"].as_u64(),
    ) else {
        return (
            "runner-error",
            vec!["Joern evidence lacks its endpoint node counts".to_string()],
        );
    };
    if sources == 0 || sinks == 0 {
        return (
            "inconclusive",
            vec![format!(
                "Joern resolved {sources} source node(s) and {sinks} sink node(s); the run never observed both benchmark-controlled endpoints"
            )],
        );
    }
    if flows.is_empty() {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove a Joern flow against the sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for flow in flows {
        match joern_flow_anchor_match(flow, &sink_locations) {
            EvidenceAnchorMatch::Matched => matched += 1,
            EvidenceAnchorMatch::Unmatched => unmatched += 1,
            EvidenceAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} Joern flow(s) carry no usable or an ambiguous sink-anchor location"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} Joern flow(s) did not match the case sink anchor"
        )],
    )
}

fn joern_flow_anchor_match(
    flow: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> EvidenceAnchorMatch {
    let Some(elements) = flow["elements"].as_array() else {
        return EvidenceAnchorMatch::Ambiguous;
    };
    if elements.is_empty() {
        return EvidenceAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    let mut usable = false;
    for element in elements {
        let (Some(file), Some(line)) = (element["file"].as_str(), element["line"].as_u64()) else {
            continue;
        };
        if line == 0 {
            continue;
        }
        usable = true;
        for (index, anchor) in sink_locations.iter().enumerate() {
            if evidence_path_matches_file(file, &anchor.file)
                && anchor.callsite_lines.contains(&line)
            {
                matches.insert(index);
            }
        }
    }
    if !usable || matches.len() > 1 {
        EvidenceAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        EvidenceAnchorMatch::Matched
    } else {
        EvidenceAnchorMatch::Unmatched
    }
}

/// One Semgrep CE kernel: a single language, its own case selection, its own
/// committed rule file, its own normalized report, and its own
/// retained-evidence root. Semgrep shares one taint engine across all of them,
/// exactly as Joern shares one data-flow engine; the populations are kept apart
/// by the selector and the report paths, never by the engine.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SemgrepKernel {
    Java,
    JavaScript,
    TypeScript,
    Python,
    Go,
    Ruby,
    Php,
    Kotlin,
    Rust,
    C,
    Cpp,
}

impl SemgrepKernel {
    fn language(self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
            Self::Python => "python",
            Self::Go => "go",
            Self::Ruby => "ruby",
            Self::Php => "php",
            Self::Kotlin => "kotlin",
            Self::Rust => "rust",
            Self::C => "c",
            Self::Cpp => "cpp",
        }
    }

    fn display_name(self) -> &'static str {
        match self {
            Self::Java => "Java",
            Self::JavaScript => "JavaScript",
            Self::TypeScript => "TypeScript",
            Self::Python => "Python",
            Self::Go => "Go",
            Self::Ruby => "Ruby",
            Self::Php => "PHP",
            Self::Kotlin => "Kotlin",
            Self::Rust => "Rust",
            Self::C => "C",
            Self::Cpp => "C++",
        }
    }

    /// The maturity the pinned distribution records for this kernel's Semgrep
    /// language in its own `semgrep_interfaces/lang.json`. It is retained
    /// verbatim in the adapter README and in every capability-decision
    /// document, exactly as the CodeQL Rust kernel retains that extractor's
    /// preview status. A maturity label is a property of the front end, never
    /// a reason to move a case between the scored and `unsupported`
    /// partitions.
    fn documented_maturity(self) -> &'static str {
        match self {
            Self::Java
            | Self::JavaScript
            | Self::TypeScript
            | Self::Python
            | Self::Go
            | Self::Ruby
            | Self::Php => "ga",
            Self::Kotlin => "beta",
            Self::Rust | Self::C | Self::Cpp => "alpha",
        }
    }

    /// The scored template set of this kernel's language, read from its rollout
    /// row. docs/applicability-matrix.md classifies the exception-catch cell as
    /// inapplicable to both C and Rust, so those two kernels have a
    /// fifteen-template, thirty-assertion classic core; every other Semgrep
    /// kernel has the full sixteen. Selection expands with the row; what is
    /// *scored* is decided separately, per case, by
    /// `semgrep_capability_exclusion`.
    fn templates(self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }

    /// The committed rule file for this kernel. Each is its own file even
    /// where two would be byte-identical apart from the `languages:` key, so a
    /// population is never scored by a rule spelled for another language.
    fn rule(self) -> String {
        format!("{SEMGREP_RULES_DIR}/{}.yaml", self.language())
    }

    fn report(self) -> String {
        format!("reports/semgrep-{}-kernel.json", self.language())
    }

    fn raw_dir(self) -> String {
        format!("reports/raw/semgrep-{}-kernel", self.language())
    }

    fn dialect(self) -> AnchorDialect {
        match self {
            Self::Java => AnchorDialect::Java,
            Self::JavaScript | Self::TypeScript => AnchorDialect::Ecma,
            Self::Python => AnchorDialect::Python,
            Self::Go => AnchorDialect::Go,
            Self::Ruby => AnchorDialect::Ruby,
            Self::Php => AnchorDialect::Php,
            // A Kotlin endpoint marker sits on a `fun name(params)`
            // declaration and every Kotlin fixture calls its sink
            // receiverlessly, with `.` the only member operator that could
            // precede the name and `//` the line-comment opener. That is
            // exactly the Java arm's surface contract, verified against the
            // real fixtures rather than assumed, so Kotlin reuses it instead
            // of adding a dialect whose rules would be a copy.
            Self::Kotlin => AnchorDialect::Java,
            Self::Rust => AnchorDialect::Rust,
            // The C and C++ arm is shared, as it is in the CodeQL adapter:
            // both reach a member through `.`, `->`, and `::`.
            Self::C | Self::Cpp => AnchorDialect::Cpp,
        }
    }

    fn label(self) -> String {
        format!("Semgrep {} kernel", self.display_name())
    }
}

fn semgrep_core_case(case: &Value, kernel: SemgrepKernel) -> bool {
    case["language"] == kernel.language()
        && case["track"] == "taint"
        && case["score_tier"] == "core"
}

/// Select a Semgrep kernel population runner-side. The v0.3.0 freeze binds
/// every `case.json` byte, so no case declares a Semgrep model reference; the
/// selection is by language, track, and score tier alone, exactly as the Joern
/// kernels select theirs. The whole core population is always selected and
/// balance-checked against that language's own template set — sixteen
/// templates for most kernels, fifteen for C and Rust, whose exception-catch
/// cell docs/applicability-matrix.md classifies as inapplicable. The
/// `score_tier == "core"` filter is what keeps C's `language-extension`
/// error-code-return and goto-cleanup cases and Rust's `Result`/`?` extension
/// pair out of the core run. The bounded profile is applied afterwards, per
/// case, by `semgrep_capability_exclusion`.
fn select_semgrep_cases(kernel: SemgrepKernel) -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if semgrep_core_case(&case, kernel) {
            selected.push((path, case));
        }
    }
    validate_kernel_population_with(&selected, &kernel.label(), &kernel.templates())?;
    Ok(selected)
}

/// The preregistered Semgrep CE partition for the thirteen challenge templates,
/// decided from the pinned distribution's own documentation **before any
/// challenge fixture was authored or any analyzer was pointed at one**, and
/// recorded in full in `adapters/semgrep/README.md`.
///
/// The pinned CE engine documents itself as intra-file, intraprocedural,
/// flow-sensitive, path-insensitive taint with only "Experimental support for
/// basic field-sensitive taint tracking"; interprocedural taint
/// (`--pro-intrafile`), path sensitivity (`--pro-path-sensitive`), index
/// sensitivity, and inter-procedural field sensitivity are each sold as Pro.
/// The already-published classic partition follows exactly from that: the seven
/// `intraprocedural` templates are scored and every heap-access-path and
/// interprocedural template is `unsupported`.
///
/// Applied to the challenge tier, that same documented boundary excludes all
/// thirteen. This is not a convenience: a challenge template is a challenge
/// template *because* its flow routes through dispatch, a function value, a
/// container or computed key, a deep field chain, or a call chain — and each of
/// those is precisely a construct the CE documentation places outside the
/// engine. None of the thirteen is a pure local value flow, which is the only
/// shape the CE partition scores. Every entry is `unsupported` by declared
/// capability, never a false negative, and the decision cannot be revisited
/// after a run without an amendment on the preregistration's terms.
const CHALLENGE_SEMGREP_PARTITION: [(&str, &str); 13] = [
    (
        "dfb-template-chal-reflective-invocation",
        "the case resolves a callee from a run-time string and the sink is reached inside that callee's body; CE has no interprocedural taint at all (`--pro-intrafile`, \"Intra-file inter-procedural taint analysis ... Requires Semgrep Pro Engine\"), and the pinned CE documentation nowhere claims to resolve a reflective handle",
    ),
    (
        "dfb-template-chal-computed-property",
        "the case writes and reads a member located by a run-time key; the pinned CE engine documents only \"Experimental support for basic field-sensitive taint tracking\", while \"Pro: taint-mode: Added basic support for 'index sensitivity'\" places keyed access outside CE — the same documented boundary that already excludes `dfb-template-array-element-separation` and `dfb-template-same-object-field-separation`",
    ),
    (
        "dfb-template-chal-dispatch-table",
        "the callee is a function value fetched from a standard-library map and the sink is inside it; the call-graph edge and the sink are both outside the intraprocedural CE engine (`--pro-intrafile` is Pro)",
    ),
    (
        "dfb-template-chal-closure-capture",
        "the sink is inside a closure body invoked from a different function than the one that captured the tainted local; CE has no interprocedural taint",
    ),
    (
        "dfb-template-chal-function-field",
        "the callee is stored in an object field, fetched elsewhere, and invoked; this needs both field sensitivity beyond CE's experimental basic support and the interprocedural step CE documents as Pro",
    ),
    (
        "dfb-template-chal-callback-registration",
        "a callback registered by one method is invoked by a separate driver method; inversion of control is interprocedural by construction and CE has no interprocedural taint",
    ),
    (
        "dfb-template-chal-anonymous-implementation",
        "the sink is inside an anonymous implementation invoked through a declared interface type; resolving that call-graph edge and following taint into the callee are both outside the CE engine",
    ),
    (
        "dfb-template-chal-map-iteration",
        "the value is retrieved by iterating a standard-library container's entries; container element taint through an iteration protocol is not within CE's documented \"basic field-sensitive\" support, and index sensitivity is recorded as Pro",
    ),
    (
        "dfb-template-chal-nested-access-path",
        "the case reads and writes a field chain of depth three or more; the pinned CE engine documents only *basic* experimental field sensitivity, with inter-procedural field sensitivity recorded as Pro",
    ),
    (
        "dfb-template-chal-element-object",
        "the case combines element separation with field separation in one query; index sensitivity is recorded as Pro and CE's field sensitivity is experimental and basic",
    ),
    (
        "dfb-template-chal-deep-relay-chain",
        "the case declares a six-hop interprocedural relay; CE has no interprocedural taint at all (`--pro-intrafile` is Pro), which docs/challenge-tier.md already records as this stratum's expected outcome",
    ),
    (
        "dfb-template-chal-recursive-carry",
        "the carried value crosses a self-recursive call boundary five times; a recursive summary is interprocedural, and CE has no interprocedural taint",
    ),
    (
        "dfb-template-chal-context-pair-depth2",
        "the case declares two-level context sensitivity; CE has no interprocedural taint and therefore no calling context to be sensitive to",
    ),
];

/// The preregistered CE decision for a challenge template, or `None` for a
/// classic template, which the tag rule below decides as it always has.
fn challenge_semgrep_exclusion(template: &str) -> Option<&'static str> {
    CHALLENGE_SEMGREP_PARTITION
        .iter()
        .find(|(id, _)| *id == template)
        .map(|(_, reason)| *reason)
}

/// The bounded Semgrep CE profile, decided from the case's own declared
/// capability metadata and the pinned distribution's documentation — never
/// from an observed result.
///
/// Semgrep CE's taint mode is documented by the pinned CLI itself as
/// intra-file and intraprocedural: `semgrep scan --help` offers
/// `--pro-intrafile` ("Intra-file inter-procedural taint analysis. Implies
/// --pro-languages. Requires Semgrep Pro Engine") and `--pro` ("Inter-file
/// analysis ... Requires Semgrep Pro Engine"), so neither interprocedural nor
/// cross-file propagation is in the CE engine at all. Its heap support is
/// likewise bounded: the pinned CHANGELOG records only "Experimental support
/// for basic field-sensitive taint tracking" in CE, while index sensitivity
/// (`E[i]`) and inter-procedural field sensitivity are both recorded as Pro.
///
/// So the scored profile is exactly the `intraprocedural` partition of each
/// kernel. Every other case returns a retained reason here and is normalized
/// `unsupported` *without invoking Semgrep*: a capability exclusion can never
/// be dressed up as a false negative, and no result can talk the runner into
/// or out of the partition.
fn semgrep_capability_exclusion(case: &Value) -> Option<String> {
    let tags: BTreeSet<&str> = case["feature_tags"]
        .as_array()
        .map(|tags| tags.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default();
    let capability = case["expected_analysis_capability"]["kind"]
        .as_str()
        .unwrap_or("an undeclared capability");
    // The challenge tier's partition is preregistered by template ID, decided
    // from the pinned CE documentation before any challenge fixture existed and
    // recorded in adapters/semgrep/README.md. It is consulted *before* the tag
    // rule so that no fixture's tag choices — and no observed result — can move
    // a challenge case between the scored and `unsupported` partitions after
    // the fact.
    if let Some(template) = case["template_id"].as_str()
        && let Some(reason) = challenge_semgrep_exclusion(template)
    {
        return Some(format!(
            "outside the bounded Semgrep CE profile: {reason}. The case requires {capability:?}; the scored CE profile is the kernel's `intraprocedural` partition only."
        ));
    }
    if tags.contains("intraprocedural") {
        return None;
    }
    let reason = if tags.contains("interprocedural-deep") {
        "the case declares a multi-hop interprocedural relay; Semgrep CE has no interprocedural taint at all (`--pro-intrafile`, \"Intra-file inter-procedural taint analysis ... Requires Semgrep Pro Engine\")"
    } else if tags.contains("interprocedural-one-hop") {
        "the case declares an interprocedural relay; Semgrep CE has no interprocedural taint at all (`--pro-intrafile`, \"Intra-file inter-procedural taint analysis ... Requires Semgrep Pro Engine\")"
    } else if tags.contains("heap-access-path") {
        "the case declares a heap access path; the pinned CE engine documents only \"Experimental support for basic field-sensitive taint tracking\", with index sensitivity and inter-procedural field sensitivity both recorded as Pro-only"
    } else if tags.contains("exceptional") {
        "the case declares an exceptional value transfer, which the pinned CE taint documentation nowhere claims to model"
    } else {
        "the case is outside the documented CE local/intraprocedural taint profile"
    };
    Some(format!(
        "outside the bounded Semgrep CE profile: {reason}. The case requires {capability:?}; the scored CE profile is the kernel's `intraprocedural` partition only."
    ))
}

/// The one-line maturity record every Semgrep assertion carries. The value is
/// read off the pinned distribution's own machine-readable language table
/// (`semgrep_interfaces/lang.json`, the `maturity` field), so the label is a
/// citation rather than a judgement.
fn semgrep_maturity_diagnostic(kernel: SemgrepKernel) -> String {
    format!(
        "pinned Semgrep CE records the {} front end's maturity as {:?} (semgrep_interfaces/lang.json `maturity`); the label describes the parser, not the scored partition",
        kernel.display_name(),
        kernel.documented_maturity()
    )
}

fn run_semgrep_kernel(binary: &Path, kernel: SemgrepKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_semgrep_cases(kernel)?;
    let rule_path = kernel.rule();
    let template = fs::read_to_string(&rule_path)
        .with_context(|| format!("read the Semgrep kernel rule {rule_path}"))?;
    for placeholder in [SEMGREP_SOURCE_PLACEHOLDER, SEMGREP_SINK_PLACEHOLDER] {
        if !template.contains(placeholder) {
            bail!("Semgrep kernel rule {rule_path} does not carry {placeholder}");
        }
    }
    let raw_dir = PathBuf::from(kernel.raw_dir());
    fs::create_dir_all(&raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = semgrep_version_identity(binary)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, mut diagnostics, raw_path) =
            run_semgrep_case(binary, &template, &path, &case, &raw_dir, kernel)?;
        // `schemas/result.schema.json` has no report-level field for a front
        // end's maturity, so the label the pinned distribution records for
        // this language rides on every assertion's retained diagnostics. It is
        // a property of the parser, never an outcome: an `alpha` or `beta`
        // front end is still scored on exactly the same partition a `ga` one
        // is, and the label never moves a case out of it.
        diagnostics.insert(0, semgrep_maturity_diagnostic(kernel));
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&semgrep_rule_paths()?)?;
    let report = json!({
        "schema_version": 1,
        "tool": "semgrep",
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
    let report_path = kernel.report();
    write_and_validate_report(Path::new(&report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

/// Every committed Semgrep rule file, so one `configuration_hash` binds the
/// whole rule set rather than only the language that happened to run.
fn semgrep_rule_paths() -> Result<BTreeSet<PathBuf>> {
    let mut paths = BTreeSet::new();
    for entry in fs::read_dir(SEMGREP_RULES_DIR)
        .with_context(|| format!("read {SEMGREP_RULES_DIR}"))?
        .filter_map(std::result::Result::ok)
    {
        let path = entry.path();
        if path.is_file() && path.extension().is_some_and(|ext| ext == "yaml") {
            paths.insert(path);
        }
    }
    if paths.is_empty() {
        bail!("{SEMGREP_RULES_DIR} holds no committed Semgrep rule");
    }
    Ok(paths)
}

/// The exact Semgrep version every normalized Semgrep report records. The
/// pinned CE distribution reports no build SHA separate from its released
/// version, so the released version *is* the build identity, recorded
/// literally rather than padded with a synthetic identifier. `semgrep
/// --version` needs no `--metrics` flag: it performs no scan.
fn semgrep_version_identity(binary: &Path) -> Result<(String, String)> {
    let output = Command::new(binary)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", binary.display()))?;
    if !output.status.success() {
        bail!(
            "{} --version failed with status {}",
            binary.display(),
            output.status
        );
    }
    let version = String::from_utf8_lossy(&output.stdout)
        .lines()
        .map(str::trim)
        .find(|line| !line.is_empty())
        .context("Semgrep did not report a version")?
        .to_string();
    let build_identity = format!("semgrep-oss:{version}");
    Ok((version, build_identity))
}

fn run_semgrep_case(
    binary: &Path,
    template: &str,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
    kernel: SemgrepKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let unsupported_path = raw_dir.join(format!("{id}-unsupported.json"));
    let rule_path = raw_dir.join(format!("{id}-rule.yaml"));
    for stale in [&raw_path, &error_path, &unsupported_path, &rule_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // The capability decision comes first and is made from the case's own
    // declared metadata. An excluded case is never handed to Semgrep, so it
    // cannot produce an empty finding list that later looks like a negative.
    if let Some(reason) = semgrep_capability_exclusion(case) {
        fs::write(
            &unsupported_path,
            serde_json::to_string_pretty(&json!({
                "adapter": "semgrep",
                "case_id": id,
                "state": "unsupported",
                "stage": "declared-capability",
                "reason": reason,
                "feature_tags": case["feature_tags"],
                "expected_analysis_capability": case["expected_analysis_capability"],
                "engine_profile": "semgrep-ce-oss-intrafile-intraprocedural-taint",
                "language": kernel.language(),
                "language_maturity": kernel.documented_maturity(),
                "language_maturity_source": "semgrep_interfaces/lang.json (pinned distribution)",
                "evidence_kind": "retained-capability-decision"
            }))? + "\n",
        )?;
        return Ok(("unsupported", vec![reason], unsupported_path));
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence. That is `inconclusive` with a retained reason; it
    // is never a clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, kernel.dialect()) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Semgrep endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "semgrep",
                    "case_id": id,
                    "state": "inconclusive",
                    "stage": "endpoint-resolution",
                    "reason": diagnostic,
                    "evidence_kind": "retained-anchor-resolution"
                }))? + "\n",
            )?;
            return Ok(("inconclusive", vec![diagnostic], error_path));
        }
    };

    let rule = template
        .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
        .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function);
    // The resolved rule is retained beside the finding document: the committed
    // template is hash-bound into the report, and the exact configuration this
    // case was analyzed under is auditable on its own.
    fs::write(&rule_path, &rule)?;

    let scratch = semgrep_case_scratch(kernel, id)?;
    let workspace = scratch.join("source");
    fs::create_dir_all(&workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }

    let result = (|| {
        let mut command = Command::new(binary);
        command
            .current_dir(&scratch)
            .arg("scan")
            // Never report usage metrics, and never let the Pro engine or the
            // registry enter the run: this population is CE-only by contract.
            .arg("--metrics=off")
            .arg("--oss-only")
            .arg("--disable-version-check")
            .arg("--no-git-ignore")
            .arg("--quiet")
            .arg("--json")
            .arg("--config")
            .arg(fs::canonicalize(&rule_path).unwrap_or_else(|_| rule_path.clone()))
            .arg(&workspace)
            .stdin(std::process::Stdio::null());
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Semgrep {} kernel scan with {}: {error}",
                    kernel.display_name(),
                    binary.display()
                );
                let path = write_semgrep_error(raw_dir, id, "scan-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        // Semgrep exits 0 with or without findings and reserves higher codes
        // for its own failures, so anything non-zero is a runner error and can
        // never be read as an empty finding list.
        if !output.status.success() {
            let diagnostic = format!(
                "Semgrep {} kernel scan failed with status {}",
                kernel.display_name(),
                output.status
            );
            let path =
                write_semgrep_error(raw_dir, id, "scan-execution", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::write(&raw_path, &output.stdout)?;
        let raw: Value = match serde_json::from_slice(&output.stdout) {
            Ok(raw) => raw,
            Err(error) => {
                let diagnostic = format!("parse Semgrep evidence {}: {error}", raw_path.display());
                let path = write_semgrep_error(raw_dir, id, "scan-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (outcome, diagnostics) =
            semgrep_finding_outcome(case_path, case, &raw, kernel.dialect());
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Semgrep case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Semgrep case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

fn semgrep_case_scratch(kernel: SemgrepKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-semgrep-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

fn write_semgrep_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let mut evidence = json!({
        "adapter": "semgrep",
        "case_id": id,
        "state": "runner-error",
        "stage": stage,
        "diagnostic": diagnostic,
        "evidence_kind": "retained-process-diagnostics"
    });
    if let Some(output) = output {
        evidence["status"] = json!(output.status.code());
        evidence["stdout"] = json!(String::from_utf8_lossy(&output.stdout).trim());
        evidence["stderr"] = json!(String::from_utf8_lossy(&output.stderr).trim());
    }
    fs::write(&error_path, serde_json::to_string_pretty(&evidence)? + "\n")?;
    Ok(error_path)
}

/// Normalize one retained Semgrep `--json` document.
///
/// A finding counts as `reached` only when it sits on a callsite of the case's
/// own anchored sink function, in the anchored file — the same reconciliation
/// the Joern kernels and the CodeQL C#, Go, C, C++, Rust, and Ruby kernels
/// apply. Every other state stays distinct: any entry in Semgrep's own
/// `errors` array, or a finding the pinned CE engine did not produce, is
/// `runner-error`; a scan that never opened the fixture, or findings that
/// cannot be reconciled, is `inconclusive`. Only a clean scan of the fixture
/// that produced no finding at all is `not-reached`.
fn semgrep_finding_outcome(
    case_path: &Path,
    case: &Value,
    raw: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    let Some(results) = raw["results"].as_array() else {
        return (
            "runner-error",
            vec!["Semgrep evidence lacks its results array".to_string()],
        );
    };
    let Some(errors) = raw["errors"].as_array() else {
        return (
            "runner-error",
            vec!["Semgrep evidence lacks its errors array".to_string()],
        );
    };
    if !errors.is_empty() {
        let mut diagnostics: Vec<String> = errors
            .iter()
            .map(|error| {
                error["long_msg"]
                    .as_str()
                    .or_else(|| error["message"].as_str())
                    .or_else(|| error["type"].as_str())
                    .unwrap_or("Semgrep reported an error without a message")
                    .to_string()
            })
            .collect();
        diagnostics.sort();
        diagnostics.dedup();
        return ("runner-error", diagnostics);
    }
    // A rule Semgrep declined to run produces no finding for a reason that has
    // nothing to do with the program, so it must not read as a negative.
    if raw["skipped_rules"]
        .as_array()
        .is_some_and(|skipped| !skipped.is_empty())
    {
        return (
            "runner-error",
            vec!["Semgrep skipped the benchmark-controlled rule".to_string()],
        );
    }
    let scanned = raw["paths"]["scanned"]
        .as_array()
        .map(|paths| paths.len())
        .unwrap_or_default();
    if scanned == 0 {
        return (
            "inconclusive",
            vec!["Semgrep scanned no target; the run never analyzed the case fixture".to_string()],
        );
    }
    // The report claims a CE result. If any finding carries another engine the
    // pinning is broken, and that is a runner error rather than a data point.
    for result in results {
        match result["extra"]["engine_kind"].as_str() {
            Some("OSS") | None => {}
            Some(other) => {
                return (
                    "runner-error",
                    vec![format!(
                        "Semgrep finding reports engine {other:?}; this population is pinned to the CE (OSS) engine"
                    )],
                );
            }
        }
    }
    if results.is_empty() {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove a Semgrep finding against the sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0usize;
    let mut unmatched = 0usize;
    let mut ambiguous = 0usize;
    for result in results {
        match semgrep_finding_anchor_match(result, &sink_locations) {
            EvidenceAnchorMatch::Matched => matched += 1,
            EvidenceAnchorMatch::Unmatched => unmatched += 1,
            EvidenceAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} Semgrep finding(s) carry no usable or an ambiguous sink-anchor location"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} Semgrep finding(s) did not match the case sink anchor"
        )],
    )
}

/// A Semgrep finding is a single location, not a path, so reconciliation is the
/// one-location form of the Joern flow match: the finding's own file and line
/// must land on a callsite of the case's anchored sink.
fn semgrep_finding_anchor_match(
    result: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> EvidenceAnchorMatch {
    let (Some(file), Some(line)) = (result["path"].as_str(), result["start"]["line"].as_u64())
    else {
        return EvidenceAnchorMatch::Ambiguous;
    };
    if line == 0 {
        return EvidenceAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    for (index, anchor) in sink_locations.iter().enumerate() {
        if evidence_path_matches_file(file, &anchor.file) && anchor.callsite_lines.contains(&line) {
            matches.insert(index);
        }
    }
    if matches.len() > 1 {
        EvidenceAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        EvidenceAnchorMatch::Matched
    } else {
        EvidenceAnchorMatch::Unmatched
    }
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
    // A run that Bifrost itself reports as failed is an execution error, even
    // when the process exits with the inconclusive status 2. This mirrors the
    // freeze validator's `raw_special_outcome` precedence exactly: an
    // explicitly inconclusive completion still outranks a failed sibling run,
    // but a failure never normalizes to `inconclusive`.
    let has_inconclusive_completion = report["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|run| run["completion"]["type"] == "inconclusive");
    if !has_inconclusive_completion && let Some(reason) = bifrost_runner_error_reason(report) {
        report_diagnostics.push(reason);
        report_diagnostics.sort();
        report_diagnostics.dedup();
        return Ok(("runner-error", report_diagnostics, Vec::new()));
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

    /// A scratch benchmark root holding an "own" kernel report and a
    /// concurrently running "other" kernel's report, for exercising the
    /// end-of-run report sweep.
    struct ReportSweepFixture {
        root: PathBuf,
    }

    impl ReportSweepFixture {
        fn new() -> Self {
            let unique = format!(
                "dataflowbench-report-sweep-test-{}-{}",
                std::process::id(),
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            );
            let root = std::env::temp_dir().join(unique);
            fs::create_dir_all(root.join("reports/raw/own-kernel")).unwrap();
            fs::create_dir_all(root.join("reports/raw/other-kernel")).unwrap();
            Self { root }
        }

        fn report(raw_relative: &str) -> Value {
            json!({
                "schema_version": 1,
                "tool": "test-tool",
                "tool_version": "1.0.0",
                "tool_build_identity": "test-build-1",
                "adapter_version": "1.0.0",
                "configuration_hash": "0".repeat(64),
                "fixture_revision": "test",
                "started_at_unix_seconds": 1,
                "ended_at_unix_seconds": 2,
                "cold_or_warm": "cold",
                "results": [{
                    "case_id": "dfb-taint-test",
                    "outcome": "reached",
                    "source_anchors": ["DFB-SOURCE: input"],
                    "sink_anchors": ["DFB-SINK: sink"],
                    "witness_checkpoints": [],
                    "diagnostics": [],
                    "duration_ms": 1,
                    "peak_memory_mb": null,
                    "raw_output": raw_relative
                }]
            })
        }

        fn write_report(&self, name: &str, report: &Value) -> PathBuf {
            let path = self.root.join("reports").join(name);
            fs::write(&path, serde_json::to_vec_pretty(report).unwrap()).unwrap();
            path
        }

        fn write_raw(&self, raw_relative: &str) {
            fs::write(self.root.join(raw_relative), "{}\n").unwrap();
        }
    }

    impl Drop for ReportSweepFixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.root);
        }
    }

    #[test]
    fn end_of_run_sweep_tolerates_a_concurrent_runner_rewriting_its_raw_evidence() {
        let fixture = ReportSweepFixture::new();
        let own_raw = "reports/raw/own-kernel/case.json";
        fixture.write_raw(own_raw);
        let own = fixture.write_report("own-kernel.json", &ReportSweepFixture::report(own_raw));
        // The other kernel's report is intact, but its raw evidence is mid
        // removal-and-rewrite: the retained file is momentarily absent.
        fixture.write_report(
            "other-kernel.json",
            &ReportSweepFixture::report("reports/raw/other-kernel/case.json"),
        );
        validate_reports_in(&fixture.root, Some(&own)).unwrap();
        let full = validate_reports_in(&fixture.root, None).unwrap_err();
        assert!(full.to_string().contains("is absent"), "{full}");
    }

    #[test]
    fn end_of_run_sweep_still_checks_the_runners_own_raw_evidence() {
        let fixture = ReportSweepFixture::new();
        let own = fixture.write_report(
            "own-kernel.json",
            &ReportSweepFixture::report("reports/raw/own-kernel/case.json"),
        );
        let error = validate_reports_in(&fixture.root, Some(&own)).unwrap_err();
        assert!(error.to_string().contains("is absent"), "{error}");
    }

    #[test]
    fn end_of_run_sweep_still_schema_checks_other_reports() {
        let fixture = ReportSweepFixture::new();
        let own_raw = "reports/raw/own-kernel/case.json";
        fixture.write_raw(own_raw);
        let own = fixture.write_report("own-kernel.json", &ReportSweepFixture::report(own_raw));
        let mut malformed = ReportSweepFixture::report("reports/raw/other-kernel/case.json");
        malformed.as_object_mut().unwrap().remove("tool");
        fixture.write_report("other-kernel.json", &malformed);
        let error = validate_reports_in(&fixture.root, Some(&own)).unwrap_err();
        assert!(error.to_string().contains("other-kernel.json"), "{error}");
    }

    #[test]
    fn runner_never_publishes_a_report_it_did_not_validate() {
        let fixture = ReportSweepFixture::new();
        // Schema-invalid report: publishing must fail before anything lands.
        let mut invalid = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
        invalid.as_object_mut().unwrap().remove("tool");
        let report_path = Path::new("reports/own-kernel.json");
        write_and_validate_report_in(&fixture.root, report_path, &invalid).unwrap_err();
        // Valid schema but absent raw evidence: same conservative refusal.
        let unbacked = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
        write_and_validate_report_in(&fixture.root, report_path, &unbacked).unwrap_err();
        let leftovers: Vec<_> = fs::read_dir(fixture.root.join("reports"))
            .unwrap()
            .filter_map(Result::ok)
            .filter(|entry| entry.path().is_file())
            .collect();
        assert!(leftovers.is_empty(), "{leftovers:?}");
    }

    #[test]
    fn runner_publishes_a_validated_report_atomically() {
        let fixture = ReportSweepFixture::new();
        let own_raw = "reports/raw/own-kernel/case.json";
        fixture.write_raw(own_raw);
        // A concurrent kernel's evidence is mid-rewrite; publishing must
        // still succeed.
        fixture.write_report(
            "other-kernel.json",
            &ReportSweepFixture::report("reports/raw/other-kernel/case.json"),
        );
        let report_path = Path::new("reports/own-kernel.json");
        write_and_validate_report_in(
            &fixture.root,
            report_path,
            &ReportSweepFixture::report(own_raw),
        )
        .unwrap();
        let published: Value =
            serde_json::from_str(&fs::read_to_string(fixture.root.join(report_path)).unwrap())
                .unwrap();
        assert_eq!(published["tool"], "test-tool");
        assert!(!fixture.root.join("reports/own-kernel.json.tmp").exists());
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
    fn kotlin_kernel_selection_is_separate_from_java_and_every_other_language() {
        let kotlin_core = json!({
            "language": "kotlin",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": BIFROST_KOTLIN_POLICY}
            }
        });
        // Frozen v0.2.0 breadth metadata: the Kotlin kernel still selects it.
        let kotlin_direct = json!({
            "language": "kotlin",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
            }
        });
        let java_core = json!({
            "language": "java",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {"bifrost": {"policy": BIFROST_KOTLIN_POLICY}}
        });
        let kotlin_calibration = json!({
            "language": "kotlin",
            "track": "taint",
            "score_tier": "calibration",
            "tool_model_references": {"bifrost": {"policy": BIFROST_KOTLIN_POLICY}}
        });
        assert!(selected_bifrost_case(
            &kotlin_core,
            BifrostRun::KotlinKernel
        ));
        assert!(selected_bifrost_case(
            &kotlin_direct,
            BifrostRun::KotlinKernel
        ));
        assert!(!selected_bifrost_case(&java_core, BifrostRun::KotlinKernel));
        assert!(!selected_bifrost_case(
            &kotlin_calibration,
            BifrostRun::KotlinKernel
        ));
        assert!(!selected_bifrost_case(
            &kotlin_core,
            BifrostRun::PythonKernel
        ));

        // Both kernel assertions are evaluated with the language-qualified
        // Kotlin policy, including the frozen direct pair.
        assert_eq!(
            bifrost_policy_for(&kotlin_direct, BifrostRun::KotlinKernel).unwrap(),
            BIFROST_KOTLIN_POLICY
        );
        assert_eq!(
            bifrost_policy_for(&kotlin_direct, BifrostRun::Smoke).unwrap(),
            "adapters/bifrost/policies/core-direct.rqlp"
        );
    }

    #[test]
    fn scala_kernel_selection_is_separate_from_every_other_language() {
        let scala_core = json!({
            "language": "scala",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {"bifrost": {"policy": BIFROST_SCALA_POLICY}}
        });
        // Frozen v0.2.0 breadth metadata: the Scala kernel still selects it.
        let scala_direct = json!({
            "language": "scala",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
            }
        });
        let kotlin_core = json!({
            "language": "kotlin",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {"bifrost": {"policy": BIFROST_SCALA_POLICY}}
        });
        assert!(selected_bifrost_case(&scala_core, BifrostRun::ScalaKernel));
        assert!(selected_bifrost_case(
            &scala_direct,
            BifrostRun::ScalaKernel
        ));
        assert!(!selected_bifrost_case(
            &kotlin_core,
            BifrostRun::ScalaKernel
        ));
        assert!(!selected_bifrost_case(
            &scala_core,
            BifrostRun::KotlinKernel
        ));
        assert!(!selected_bifrost_case(&scala_core, BifrostRun::Smoke));

        // Every Scala assertion is evaluated with the language-qualified Scala
        // policy, including the frozen direct pair, while the frozen smoke
        // population keeps evaluating that pair through the breadth policy.
        assert_eq!(
            bifrost_policy_for(&scala_direct, BifrostRun::ScalaKernel).unwrap(),
            BIFROST_SCALA_POLICY
        );
        assert_eq!(
            bifrost_policy_for(&scala_direct, BifrostRun::Smoke).unwrap(),
            "adapters/bifrost/policies/core-direct.rqlp"
        );
    }

    /// Scala has no CodeQL and no Joern population, so the only in-repo
    /// guarantee that its 32 assertions are complete and balanced is the
    /// Bifrost run's own core denominator.
    #[test]
    fn scala_bifrost_population_is_exactly_32_balanced_assertions() {
        let selected = case_paths()
            .into_iter()
            .map(|path| {
                let case: Value =
                    serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
                (path, case)
            })
            .filter(|(_, case)| scala_core_case(case))
            .collect::<Vec<_>>();
        assert_eq!(
            selected.len(),
            BifrostRun::ScalaKernel.expected_core_cases().unwrap()
        );
        assert!(
            selected
                .iter()
                .all(|(path, _)| path.starts_with("cases/taint/scala"))
        );
        validate_kernel_population(&selected, "Bifrost Scala kernel").unwrap();
        assert!(Path::new(BIFROST_SCALA_POLICY).is_file());
    }

    #[test]
    fn kotlin_codeql_population_is_exactly_32_balanced_assertions() {
        let selected = codeql_kotlin_cases().unwrap();
        assert_eq!(selected.len(), KERNEL_CASE_COUNT);
        let templates = selected
            .iter()
            .map(|(_, case)| case["template_id"].as_str().unwrap())
            .collect::<BTreeSet<_>>();
        assert_eq!(
            templates,
            KERNEL_TEMPLATE_IDS.iter().copied().collect::<BTreeSet<_>>()
        );
        assert!(
            selected
                .iter()
                .all(|(path, _)| path.starts_with("cases/taint/kotlin"))
        );
    }

    #[test]
    fn kotlin_kernel_population_rejects_an_unbalanced_or_foreign_template_set() {
        let case = |template: &str, polarity: &str| {
            (
                PathBuf::from(format!(
                    "cases/taint/kotlin/{template}-{polarity}/case.json"
                )),
                json!({
                    "template_id": template,
                    "polarity": polarity,
                    "model_profile": "benchmark-controlled"
                }),
            )
        };
        let mut balanced = Vec::new();
        for template in KERNEL_TEMPLATE_IDS {
            balanced.push(case(template, "positive"));
            balanced.push(case(template, "negative"));
        }
        assert!(validate_kernel_population(&balanced, "Kotlin CodeQL kernel").is_ok());

        let mut unbalanced = balanced.clone();
        unbalanced[1] = case(KERNEL_TEMPLATE_IDS[0], "positive");
        assert!(validate_kernel_population(&unbalanced, "Kotlin CodeQL kernel").is_err());

        let mut foreign = balanced.clone();
        foreign[0] = case("dfb-template-one-hop-relay", "positive");
        assert!(validate_kernel_population(&foreign, "Kotlin CodeQL kernel").is_err());

        assert!(validate_kernel_population(&balanced[..2], "Kotlin CodeQL kernel").is_err());
    }

    #[test]
    fn kotlin_codeql_databases_trace_a_real_kotlin_compile() {
        let case = json!({"fixture_files": ["LocalChainPositive.kt"]});
        let args = codeql_database_create_args(
            Path::new("/tmp/db"),
            Path::new("/tmp/workspace"),
            &case,
            CodeqlLanguage::Kotlin {
                kotlinc: Path::new("kotlinc"),
            },
        )
        .unwrap();
        assert!(args.contains(&"--language=java".to_string()));
        assert!(
            args.iter()
                .any(|arg| arg == "--command=kotlinc -nowarn -d classes LocalChainPositive.kt")
        );
        // CodeQL 2.26.3 extracts no Kotlin under build-mode=none.
        assert!(!args.iter().any(|arg| arg.starts_with("--build-mode")));
    }

    #[test]
    fn kotlin_codeql_report_paths_are_dedicated() {
        for path in [
            CODEQL_KOTLIN_REPORT,
            CODEQL_KOTLIN_RAW_DIR,
            BIFROST_KOTLIN_POLICY,
        ] {
            assert!(path.contains("kotlin"), "{path} is not Kotlin-scoped");
        }
        assert_ne!(CODEQL_KOTLIN_QUERY, "adapters/codeql/queries/JavaKernel.ql");
        assert!(Path::new(CODEQL_KOTLIN_QUERY).is_file());
        assert!(Path::new(BIFROST_KOTLIN_POLICY).is_file());
    }

    #[test]
    fn typescript_bifrost_kernel_selection_excludes_other_languages() {
        let kernel = json!({
            "language": "typescript",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {
                "bifrost": {"policy": "adapters/bifrost/policies/core-typescript-kernel.rqlp"}
            }
        });
        assert!(selected_bifrost_case(&kernel, BifrostRun::TypescriptKernel));

        // The frozen direct-propagation pair keeps the language-agnostic
        // policy but is still a TypeScript kernel assertion.
        let mut direct = kernel.clone();
        direct["tool_model_references"]["bifrost"]["policy"] =
            json!("adapters/bifrost/policies/core-direct.rqlp");
        assert!(selected_bifrost_case(&direct, BifrostRun::TypescriptKernel));

        for language in ["javascript", "python", "java"] {
            let mut other = kernel.clone();
            other["language"] = json!(language);
            assert!(!selected_bifrost_case(&other, BifrostRun::TypescriptKernel));
        }
        let mut javascript_kernel = kernel.clone();
        javascript_kernel["language"] = json!("javascript");
        javascript_kernel["tool_model_references"]["bifrost"]["policy"] =
            json!("adapters/bifrost/policies/core-javascript-kernel.rqlp");
        assert!(!selected_bifrost_case(
            &javascript_kernel,
            BifrostRun::TypescriptKernel
        ));
        assert!(!selected_bifrost_case(&kernel, BifrostRun::PythonKernel));

        let mut calibration = kernel.clone();
        calibration["score_tier"] = json!("calibration");
        assert!(!selected_bifrost_case(
            &calibration,
            BifrostRun::TypescriptKernel
        ));
        let mut unsupported = kernel.clone();
        unsupported["tool_model_references"]["bifrost"] =
            json!({"unsupported_reason": "requires an external model catalog"});
        assert!(selected_bifrost_case(
            &unsupported,
            BifrostRun::TypescriptKernel
        ));
    }

    #[test]
    fn ecma_codeql_selection_refuses_the_other_kernel_query() {
        assert_ne!(
            EcmaKernel::JavaScript.query(),
            EcmaKernel::TypeScript.query()
        );
        assert_ne!(
            EcmaKernel::JavaScript.raw_dir(),
            EcmaKernel::TypeScript.raw_dir()
        );
        assert_ne!(
            EcmaKernel::JavaScript.report(),
            EcmaKernel::TypeScript.report()
        );
        assert_eq!(
            EcmaKernel::TypeScript.query(),
            "adapters/codeql/typescript/queries/TypeScriptKernel.ql"
        );
        assert!(!EcmaKernel::JavaScript.allows_implicit_query_reference());

        // The committed populations must already agree with the selector.
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            let query = case["tool_model_references"]["codeql"]["query"].as_str();
            if ecma_core_case(&case, EcmaKernel::TypeScript) {
                assert!(query.is_none_or(|query| query == EcmaKernel::TypeScript.query()));
            }
            if ecma_core_case(&case, EcmaKernel::JavaScript) {
                assert_eq!(query, Some(EcmaKernel::JavaScript.query()));
            }
        }
        assert_eq!(
            select_codeql_ecma_cases(EcmaKernel::TypeScript)
                .unwrap()
                .len(),
            expected_core_case_count("typescript")
        );
        assert_eq!(
            select_codeql_ecma_cases(EcmaKernel::JavaScript)
                .unwrap()
                .len(),
            expected_core_case_count("javascript")
        );
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
    fn ecma_core_selections_are_exactly_32_balanced_assertions() {
        for kernel in [EcmaKernel::JavaScript, EcmaKernel::TypeScript] {
            let mut selected = Vec::new();
            for path in case_paths() {
                let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
                if ecma_core_case(&case, kernel) {
                    selected.push(case);
                }
            }
            assert_eq!(selected.len(), expected_core_case_count(kernel.language()));
            let mut templates = BTreeMap::<String, (usize, usize)>::new();
            for case in selected {
                let counts = templates
                    .entry(case["template_id"].as_str().unwrap().to_string())
                    .or_default();
                if case["polarity"] == "positive" {
                    counts.0 += 1;
                } else {
                    counts.1 += 1;
                }
            }
            assert_eq!(
                templates.len(),
                expected_core_templates(kernel.language()).len()
            );
            assert!(
                templates
                    .values()
                    .all(|(positive, negative)| *positive == 1 && *negative == 1)
            );
        }
    }

    #[test]
    fn java_javascript_and_typescript_codeql_selectors_are_language_disjoint() {
        let mut java = 0;
        let mut javascript = 0;
        let mut typescript = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_codeql_java_case(&case) {
                java += 1;
                assert_eq!(case["language"], "java");
            }
            if ecma_core_case(&case, EcmaKernel::JavaScript) {
                javascript += 1;
                assert_eq!(case["language"], "javascript");
                assert!(!ecma_core_case(&case, EcmaKernel::TypeScript));
            }
            if ecma_core_case(&case, EcmaKernel::TypeScript) {
                typescript += 1;
                assert_eq!(case["language"], "typescript");
                assert!(!ecma_core_case(&case, EcmaKernel::JavaScript));
            }
        }
        assert_eq!(java, expected_core_case_count("java"));
        assert_eq!(javascript, expected_core_case_count("javascript"));
        assert_eq!(typescript, expected_core_case_count("typescript"));
    }

    /// The JavaScript kernel selects `.js` fixtures and the TypeScript kernel
    /// `.ts` fixtures; neither population may contain the other's extension.
    #[test]
    fn ecma_kernel_fixtures_carry_their_own_extension() {
        for (kernel, extension, other) in [
            (EcmaKernel::JavaScript, "js", "ts"),
            (EcmaKernel::TypeScript, "ts", "js"),
        ] {
            for path in case_paths() {
                let case: Value =
                    serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
                if !ecma_core_case(&case, kernel) {
                    continue;
                }
                for fixture in case["fixture_files"].as_array().unwrap() {
                    let fixture = fixture.as_str().unwrap();
                    assert!(fixture.ends_with(&format!(".{extension}")), "{fixture}");
                    assert!(!fixture.ends_with(&format!(".{other}")), "{fixture}");
                }
            }
        }
    }

    #[test]
    fn csharp_core_selection_is_the_expanded_balanced_population() {
        let expected_templates = expected_core_templates("csharp");
        let selected = codeql_csharp_cases().unwrap();
        assert_eq!(selected.len(), expected_core_case_count("csharp"));
        // C#'s challenge row is rolled out, so the population is the expanded
        // 29 templates / 58 assertions, not the classic 32.
        assert_eq!(selected.len(), 58);
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for (_, case) in &selected {
            assert_eq!(case["language"], "csharp");
            assert_eq!(case["track"], "taint");
            assert_eq!(case["score_tier"], "core");
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(templates.len(), expected_templates.len());
        assert_eq!(templates.len(), 29);
        assert!(
            templates
                .values()
                .all(|(positive, negative)| *positive == 1 && *negative == 1)
        );
    }

    #[test]
    fn csharp_core_selection_is_language_and_track_scoped() {
        let csharp = json!({
            "language": "csharp",
            "track": "taint",
            "score_tier": "core"
        });
        assert!(csharp_core_case(&csharp));
        for language in ["java", "javascript", "typescript", "python", "kotlin"] {
            let mut other = csharp.clone();
            other["language"] = json!(language);
            assert!(!csharp_core_case(&other));
        }
        let mut other = csharp.clone();
        other["track"] = json!("value-flow");
        assert!(!csharp_core_case(&other));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!csharp_core_case(&other));
    }

    #[test]
    fn bifrost_csharp_kernel_selects_only_csharp_core_cases() {
        let mut selected = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::CsharpKernel) {
                selected += 1;
                assert_eq!(case["language"], "csharp");
                assert_eq!(case["score_tier"], "core");
                for other in [
                    BifrostRun::PythonKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::TypescriptKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            }
        }
        // The C# row is rolled out, so the kernel run covers the expanded core.
        assert_eq!(selected, expected_core_case_count("csharp"));
        assert!(selected > KERNEL_CASE_COUNT);
    }

    /// C and C++ are two populations with two denominators. The C core is the
    /// fifteen applicable templates; the C++ core is all sixteen; the C
    /// `language-extension` cases ride along in the C slice without changing
    /// its core denominator.
    #[test]
    fn c_and_cpp_core_populations_keep_their_own_denominators() {
        let c = codeql_c_family_cases(CFamilyKernel::C).unwrap();
        let cpp = codeql_c_family_cases(CFamilyKernel::Cpp).unwrap();
        let core = |cases: &[(PathBuf, Value)]| {
            cases
                .iter()
                .filter(|(_, case)| case["score_tier"] == "core")
                .count()
        };
        assert_eq!(core(&c), KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
        assert_eq!(core(&c), 30);
        assert_eq!(core(&cpp), KERNEL_CASE_COUNT);
        assert_eq!(core(&cpp), 32);
        assert_eq!(c.len() - core(&c), 2);
        assert_eq!(cpp.len(), core(&cpp));

        let c_templates = c
            .iter()
            .filter(|(_, case)| case["score_tier"] == "core")
            .map(|(_, case)| case["template_id"].as_str().unwrap().to_string())
            .collect::<BTreeSet<_>>();
        assert!(!c_templates.contains("dfb-template-exception-catch"));
        assert_eq!(
            c_templates.len(),
            KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH.len()
        );
        for (_, case) in &c {
            assert_eq!(case["language"], "c");
            assert!(
                case["fixture_files"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .all(|fixture| fixture.as_str().unwrap().ends_with(".c"))
            );
        }
        for (_, case) in &cpp {
            assert_eq!(case["language"], "cpp");
            assert_eq!(case["score_tier"], "core");
            assert!(
                case["fixture_files"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .all(|fixture| fixture.as_str().unwrap().ends_with(".cpp"))
            );
        }
    }

    /// The C denominator is the sixteen scored templates minus the
    /// inapplicable exception-catch cell, and nothing else.
    #[test]
    fn the_reduced_template_set_is_the_scored_set_without_exception_catch() {
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

    /// A C population that lost an applicable template, or gained the
    /// inapplicable one, is not a C kernel.
    #[test]
    fn c_kernel_population_rejects_a_foreign_or_short_template_set() {
        let case = |template: &str, polarity: &str| {
            (
                PathBuf::from(format!("cases/taint/c/{template}-{polarity}/case.json")),
                json!({
                    "template_id": template,
                    "polarity": polarity,
                    "model_profile": "benchmark-controlled"
                }),
            )
        };
        let balanced = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
            .iter()
            .flat_map(|template| [case(template, "positive"), case(template, "negative")])
            .collect::<Vec<_>>();
        assert!(
            validate_kernel_population_with(
                &balanced,
                "C kernel",
                &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
            )
            .is_ok()
        );
        assert!(
            validate_kernel_population_with(&balanced, "C kernel", &KERNEL_TEMPLATE_IDS).is_err()
        );
        let mut with_exception_catch = balanced.clone();
        with_exception_catch.push(case("dfb-template-exception-catch", "positive"));
        with_exception_catch.push(case("dfb-template-exception-catch", "negative"));
        assert!(
            validate_kernel_population_with(
                &with_exception_catch,
                "C kernel",
                &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
            )
            .is_err()
        );
        assert!(
            validate_kernel_population_with(
                &balanced[..2],
                "C kernel",
                &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
            )
            .is_err()
        );
    }

    #[test]
    fn bifrost_c_and_cpp_kernels_select_disjoint_populations() {
        let mut c = 0;
        let mut c_core = 0;
        let mut cpp = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::CKernel) {
                c += 1;
                if case["score_tier"] == "core" {
                    c_core += 1;
                }
                assert_eq!(case["language"], "c");
                assert!(!selected_bifrost_case(&case, BifrostRun::CppKernel));
            }
            if selected_bifrost_case(&case, BifrostRun::CppKernel) {
                cpp += 1;
                assert_eq!(case["language"], "cpp");
                assert_eq!(case["score_tier"], "core");
                for other in [
                    BifrostRun::CKernel,
                    BifrostRun::CsharpKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::PythonKernel,
                    BifrostRun::TypescriptKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            }
        }
        assert_eq!(c_core, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
        assert_eq!(c - c_core, 2);
        assert_eq!(cpp, KERNEL_CASE_COUNT);
    }

    /// The two C-family kernels share the `cpp` extractor and one pack, so
    /// their reports, raw-evidence roots, and queries must stay distinct.
    #[test]
    fn c_family_codeql_report_paths_are_dedicated() {
        assert_ne!(CFamilyKernel::C.report(), CFamilyKernel::Cpp.report());
        assert_ne!(CFamilyKernel::C.raw_dir(), CFamilyKernel::Cpp.raw_dir());
        assert_ne!(CFamilyKernel::C.query(), CFamilyKernel::Cpp.query());
        assert_ne!(CFamilyKernel::C.policy(), CFamilyKernel::Cpp.policy());
        for kernel in [CFamilyKernel::C, CFamilyKernel::Cpp] {
            assert!(kernel.report().starts_with("reports/codeql-"));
            assert!(kernel.raw_dir().starts_with("reports/raw/codeql-"));
        }
        assert_eq!(CodeqlLanguage::CFamily.cli_name(), "cpp");
        assert!(!CodeqlLanguage::CFamily.traces_jvm_compile());
    }

    /// C and C++ reach members through `.`, `->`, and `::`; none of those is a
    /// call of the free sink function the `DFB-SINK:` marker declares.
    #[test]
    fn cpp_sink_declarations_and_callsites_resolve_through_the_cpp_dialect() {
        assert_eq!(
            parameter_list_function_name(
                "void dfb_sink(int value) {} // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            parameter_list_function_name(
                "const char *dfb_sink(const char *value) {} // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
            Some("dfb_sink")
        );
        assert!(cpp_function_call("    dfb_sink(holder.value);", "dfb_sink"));
        assert!(cpp_function_call("    dfb_sink(alias->value);", "dfb_sink"));
        assert!(!cpp_function_call(
            "    other->dfb_sink(value);",
            "dfb_sink"
        ));
        assert!(!cpp_function_call(
            "    Other::dfb_sink(value);",
            "dfb_sink"
        ));
        assert!(!cpp_function_call("    other.dfb_sink(value);", "dfb_sink"));
        assert!(!cpp_function_call("    my_dfb_sink(value);", "dfb_sink"));
        assert!(!cpp_function_call("    // dfb_sink(value);", "dfb_sink"));
    }

    #[test]
    fn csharp_sarif_mapping_requires_the_sink_file_and_callsite() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-csharp-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("Fixture.cs"),
            "    static void dfb_sink(int value) { } // DFB-SINK: sink\n    static void Other(int value) { }\n        Other(input);\n        dfb_sink(input);\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "Fixture.cs",
                "line_hint": 1
            }]
        });
        let matching = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "file:///tmp/work/Fixture.cs"},
                "region": {"startLine": 4}
            }}]}]}]
        });
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &matching, AnchorDialect::CSharp).0,
            "reached"
        );
        let wrong_line = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "Fixture.cs"},
                "region": {"startLine": 3}
            }}]}]}]
        });
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &wrong_line, AnchorDialect::CSharp).0,
            "inconclusive"
        );
        let missing_location = json!({
            "runs": [{"results": [{"message": {"text": "flow"}}]}]
        });
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &missing_location, AnchorDialect::CSharp).0,
            "inconclusive"
        );
        let no_results = json!({"runs": [{"results": []}]});
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &no_results, AnchorDialect::CSharp).0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn go_core_selection_is_exactly_32_balanced_assertions() {
        let selected = codeql_go_cases().unwrap();
        assert_eq!(selected.len(), KERNEL_CASE_COUNT);
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for (_, case) in &selected {
            assert_eq!(case["language"], "go");
            assert_eq!(case["track"], "taint");
            assert_eq!(case["score_tier"], "core");
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(templates.len(), KERNEL_TEMPLATE_IDS.len());
        assert!(
            templates
                .values()
                .all(|(positive, negative)| *positive == 1 && *negative == 1)
        );
    }

    #[test]
    fn go_core_selection_is_language_and_track_scoped() {
        let go = json!({
            "language": "go",
            "track": "taint",
            "score_tier": "core"
        });
        assert!(go_core_case(&go));
        for language in [
            "java",
            "javascript",
            "typescript",
            "python",
            "kotlin",
            "csharp",
        ] {
            let mut other = go.clone();
            other["language"] = json!(language);
            assert!(!go_core_case(&other));
        }
        let mut other = go.clone();
        other["track"] = json!("value-flow");
        assert!(!go_core_case(&other));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!go_core_case(&other));
    }

    #[test]
    fn bifrost_go_kernel_selects_only_go_core_cases() {
        let mut selected = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::GoKernel) {
                selected += 1;
                assert_eq!(case["language"], "go");
                assert_eq!(case["score_tier"], "core");
                for other in [
                    BifrostRun::PythonKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::TypescriptKernel,
                    BifrostRun::CsharpKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            }
        }
        assert_eq!(selected, KERNEL_CASE_COUNT);
    }

    #[test]
    fn php_core_selection_is_language_and_track_scoped() {
        let php = json!({
            "language": "php",
            "track": "taint",
            "score_tier": "core"
        });
        assert!(php_core_case(&php));
        for language in ["java", "javascript", "typescript", "python", "ruby", "go"] {
            let mut other = php.clone();
            other["language"] = json!(language);
            assert!(!php_core_case(&other));
        }
        let mut other = php.clone();
        other["track"] = json!("value-flow");
        assert!(!php_core_case(&other));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!php_core_case(&other));
    }

    /// PHP has no CodeQL support in the pinned CLI, so Bifrost and Joern are its
    /// two analyzers. The Bifrost slice still may not overlap any other
    /// language's kernel population.
    #[test]
    fn bifrost_php_kernel_selects_only_php_core_cases() {
        let mut selected = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::PhpKernel) {
                selected += 1;
                assert_eq!(case["language"], "php");
                assert_eq!(case["score_tier"], "core");
                for other in [
                    BifrostRun::PythonKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::TypescriptKernel,
                    BifrostRun::CsharpKernel,
                    BifrostRun::GoKernel,
                    BifrostRun::CKernel,
                    BifrostRun::CppKernel,
                    BifrostRun::RustKernel,
                    BifrostRun::RubyKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            }
        }
        assert_eq!(selected, KERNEL_CASE_COUNT);
        assert_eq!(
            BifrostRun::PhpKernel.expected_core_cases(),
            Some(KERNEL_CASE_COUNT)
        );
    }

    #[test]
    fn go_sarif_mapping_requires_the_sink_file_and_callsite() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-go-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.go"),
            "func dfb_sink(value int) {} // DFB-SINK: sink\nfunc other(value int) {}\n\tother(input)\n\tdfb_sink(input)\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.go",
                "line_hint": 1
            }]
        });
        let matching = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "file:///tmp/work/fixture.go"},
                "region": {"startLine": 4}
            }}]}]}]
        });
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &matching, AnchorDialect::Go).0,
            "reached"
        );
        let wrong_line = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.go"},
                "region": {"startLine": 3}
            }}]}]}]
        });
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &wrong_line, AnchorDialect::Go).0,
            "inconclusive"
        );
        let no_results = json!({"runs": [{"results": []}]});
        assert_eq!(
            sarif_anchor_outcome(&case_path, &case, &no_results, AnchorDialect::Go).0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn go_sink_declarations_resolve_to_the_declared_function() {
        assert_eq!(
            parameter_list_function_name(
                "func dfb_sink(value int) {} // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            parameter_list_function_name("\tvalue := 0 // DFB-SINK: sink", "DFB-SINK: sink"),
            None
        );
        assert!(parameter_list_function_call(
            "\tdfb_sink(values[0])",
            "dfb_sink"
        ));
        assert!(parameter_list_function_call(
            "\t\t\tdfb_sink(recovered.(int))",
            "dfb_sink"
        ));
        assert!(!parameter_list_function_call(
            "\tlog(`dfb_sink(value)`)",
            "dfb_sink"
        ));
        assert!(!parameter_list_function_call(
            "\tother.dfb_sink(0)",
            "dfb_sink"
        ));
    }

    /// The Rust kernel scores 30 core assertions over 15 templates. The
    /// excluded exception-catch cell stays excluded, and the `Result`/`?`
    /// extension pair rides in the same slice without changing the denominator.
    #[test]
    fn rust_core_selection_is_exactly_30_balanced_assertions() {
        let selected = codeql_rust_cases().unwrap();
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        let mut extensions = 0;
        for (_, case) in &selected {
            assert_eq!(case["language"], "rust");
            assert_eq!(case["track"], "taint");
            if case["score_tier"] == "language-extension" {
                extensions += 1;
                continue;
            }
            assert_eq!(case["score_tier"], "core");
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(templates.len(), 15);
        assert_eq!(
            templates.values().map(|(p, n)| p + n).sum::<usize>(),
            KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH
        );
        assert!(
            templates
                .values()
                .all(|(positive, negative)| *positive == 1 && *negative == 1)
        );
        // The excluded template stays excluded: it reduces only Rust's
        // denominator, and the language-extension pair replaces nothing.
        assert!(!templates.contains_key("dfb-template-exception-catch"));
        assert_eq!(extensions, 2);
    }

    /// C and Rust exclude the same template for different reasons, so they
    /// share one 15-template constant instead of two identical copies. Their
    /// language-extension cases stay distinct and never enter either core
    /// denominator.
    #[test]
    fn c_and_rust_share_the_scored_set_without_exception_catch() {
        let cases = case_paths()
            .into_iter()
            .map(|path| {
                let case: Value =
                    serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
                (path, case)
            })
            .collect::<Vec<_>>();
        for language in ["c", "rust"] {
            let core = core_templates_for_language(&cases, language);
            assert_eq!(
                core,
                KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
                    .iter()
                    .copied()
                    .collect::<BTreeSet<_>>()
            );
        }
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

    /// A Rust population that reintroduced the excluded template, or that
    /// smuggled a non-kernel tier into the slice, is not a Rust kernel.
    #[test]
    fn rust_kernel_population_rejects_the_excluded_or_a_foreign_template() {
        let base = json!({
            "language": "rust",
            "track": "taint",
            "score_tier": "core",
            "model_profile": "benchmark-controlled"
        });
        let mut cases = Vec::new();
        for template in KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH {
            for polarity in ["positive", "negative"] {
                let mut case = base.clone();
                case["template_id"] = json!(template);
                case["polarity"] = json!(polarity);
                cases.push((PathBuf::from(format!("{template}-{polarity}")), case));
            }
        }
        validate_rust_kernel_population(&cases, "test").unwrap();

        let mut with_exception = cases.clone();
        for polarity in ["positive", "negative"] {
            let mut case = base.clone();
            case["template_id"] = json!("dfb-template-exception-catch");
            case["polarity"] = json!(polarity);
            with_exception.push((PathBuf::from(polarity), case));
        }
        assert!(validate_rust_kernel_population(&with_exception, "test").is_err());

        // A language-extension assertion rides along without changing the
        // 30-assertion core denominator.
        let mut with_extension = cases.clone();
        let mut extension = base.clone();
        extension["score_tier"] = json!("language-extension");
        extension["template_id"] = json!("dfb-template-result-error-propagation");
        extension["polarity"] = json!("positive");
        with_extension.push((PathBuf::from("extension"), extension));
        validate_rust_kernel_population(&with_extension, "test").unwrap();

        // A calibration case is not part of this population at all.
        let mut with_calibration = cases.clone();
        let mut calibration = base.clone();
        calibration["score_tier"] = json!("calibration");
        calibration["template_id"] = json!("dfb-template-one-hop-relay");
        calibration["polarity"] = json!("positive");
        with_calibration.push((PathBuf::from("calibration"), calibration));
        assert!(validate_rust_kernel_population(&with_calibration, "test").is_err());
    }

    #[test]
    fn bifrost_rust_kernel_selects_only_rust_cases() {
        let mut core = 0;
        let mut extension = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::RustKernel) {
                assert!(rust_kernel_case(&case));
                if case["score_tier"] == "core" {
                    core += 1;
                } else {
                    assert_eq!(case["score_tier"], "language-extension");
                    extension += 1;
                }
                for other in [
                    BifrostRun::PythonKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::TypescriptKernel,
                    BifrostRun::CsharpKernel,
                    BifrostRun::GoKernel,
                    BifrostRun::CKernel,
                    BifrostRun::CppKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            }
        }
        assert_eq!(core, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
        assert_eq!(
            BifrostRun::RustKernel.expected_core_cases(),
            Some(KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH)
        );
        assert_eq!(extension, 2);
    }

    #[test]
    fn rust_codeql_report_paths_are_dedicated() {
        for other in [
            CODEQL_KOTLIN_REPORT,
            CODEQL_CSHARP_REPORT,
            CODEQL_JAVASCRIPT_REPORT,
            CODEQL_TYPESCRIPT_REPORT,
            CODEQL_GO_REPORT,
            CODEQL_C_REPORT,
            CODEQL_CPP_REPORT,
            "reports/codeql-python-kernel.json",
        ] {
            assert_ne!(CODEQL_RUST_REPORT, other);
        }
        for other in [
            CODEQL_KOTLIN_RAW_DIR,
            CODEQL_CSHARP_RAW_DIR,
            CODEQL_JAVASCRIPT_RAW_DIR,
            CODEQL_TYPESCRIPT_RAW_DIR,
            CODEQL_GO_RAW_DIR,
            CODEQL_C_RAW_DIR,
            CODEQL_CPP_RAW_DIR,
        ] {
            assert_ne!(CODEQL_RUST_RAW_DIR, other);
        }
        assert_ne!(CODEQL_RUST_QUERY, CODEQL_CSHARP_QUERY);
        assert_eq!(CodeqlLanguage::Rust.cli_name(), "rust");
        assert!(!CodeqlLanguage::Rust.traces_jvm_compile());
    }

    #[test]
    fn rust_codeql_databases_carry_a_generated_cargo_manifest() {
        let case = json!({"id": "dfb-taint-rust-test", "fixture_files": ["direct_flow.rs"]});
        let args = codeql_database_create_args(
            Path::new("/tmp/rust-db"),
            Path::new("/tmp/rust-workspace"),
            &case,
            CodeqlLanguage::Rust,
        )
        .unwrap();
        assert!(args.iter().any(|arg| arg == "--language=rust"));
        assert!(args.iter().any(|arg| arg == "--build-mode=none"));
        assert!(!args.iter().any(|arg| arg.starts_with("--command=")));

        let workspace = std::env::temp_dir().join(format!(
            "dataflowbench-rust-manifest-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&workspace).unwrap();
        write_rust_cargo_manifest(&workspace, &case).unwrap();
        let manifest = fs::read_to_string(workspace.join("Cargo.toml")).unwrap();
        // Without a manifest the extractor logs "semantic analyzer unavailable
        // (no manifest found)" and resolves no call targets, so the crate root
        // must point straight at the case's single fixture file.
        assert!(manifest.contains("path = \"direct_flow.rs\""), "{manifest}");
        assert!(manifest.contains("[workspace]"), "{manifest}");

        let two_fixtures = json!({"id": "x", "fixture_files": ["a.rs", "b.rs"]});
        assert!(write_rust_cargo_manifest(&workspace, &two_fixtures).is_err());
        fs::remove_dir_all(workspace).unwrap();
    }

    /// Rust declares a sink the way C#, Go, and C/C++ do, but reaches a member
    /// through `.` and `::` only — it has no `->` operator to exclude.
    #[test]
    fn rust_sink_declarations_resolve_to_the_declared_function() {
        assert_eq!(
            parameter_list_function_name(
                "fn dfb_sink(value: i32) {} // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            parameter_list_function_name("    let value = 0; // DFB-SINK: sink", "DFB-SINK: sink"),
            None
        );
        assert!(rust_function_call("    dfb_sink(input);", "dfb_sink"));
        assert!(rust_function_call(
            "    dfb_sink(holder.value);",
            "dfb_sink"
        ));
        assert!(!rust_function_call(
            "    other.dfb_sink(value);",
            "dfb_sink"
        ));
        assert!(!rust_function_call(
            "    other::dfb_sink(value);",
            "dfb_sink"
        ));
        assert!(!rust_function_call("    my_dfb_sink(value);", "dfb_sink"));
        assert!(!rust_function_call("    // dfb_sink(value);", "dfb_sink"));

        let root = std::env::temp_dir().join(format!(
            "dataflowbench-rust-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.rs"),
            "fn dfb_sink(value: i32) {} // DFB-SINK: sink\nfn other(value: i32) {}\n    other(input);\n    dfb_sink(input);\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.rs",
                "line_hint": 1
            }]
        });
        let outcome = |sarif: &Value| {
            callsite_anchored_outcome(&case_path, &case, sarif, AnchorDialect::Rust).0
        };
        let matching = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.rs"},
                "region": {"startLine": 4}
            }}]}]}]
        });
        assert_eq!(outcome(&matching), "reached");
        let wrong_line = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.rs"},
                "region": {"startLine": 3}
            }}]}]}]
        });
        assert_eq!(outcome(&wrong_line), "inconclusive");
        let no_results = json!({"runs": [{"results": []}]});
        assert_eq!(outcome(&no_results), "not-reached");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn csharp_sink_declarations_resolve_to_the_declared_method() {
        assert_eq!(
            parameter_list_function_name(
                "    static void dfb_sink(int value) { } // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            parameter_list_function_name(
                "        int value = 0; // DFB-SINK: sink",
                "DFB-SINK: sink"
            ),
            None
        );
        assert!(parameter_list_function_call(
            "        dfb_sink(values[0]);",
            "dfb_sink"
        ));
        assert!(!parameter_list_function_call(
            "        Log(\"dfb_sink(value)\");",
            "dfb_sink"
        ));
        assert!(!parameter_list_function_call(
            "        other.dfb_sink(0);",
            "dfb_sink"
        ));
        assert!(!parameter_list_function_call(
            "        int dfb_sinkValue = 0;",
            "dfb_sink"
        ));
    }

    #[test]
    fn ecma_core_selection_is_language_and_track_scoped() {
        for (kernel, language, others) in [
            (
                EcmaKernel::JavaScript,
                "javascript",
                ["typescript", "java", "python"],
            ),
            (
                EcmaKernel::TypeScript,
                "typescript",
                ["javascript", "java", "python"],
            ),
        ] {
            let selected = json!({
                "language": language,
                "track": "taint",
                "score_tier": "core"
            });
            assert!(ecma_core_case(&selected, kernel));
            for other_language in others {
                let mut other = selected.clone();
                other["language"] = json!(other_language);
                assert!(!ecma_core_case(&other, kernel));
            }
            let mut other = selected.clone();
            other["track"] = json!("value-flow");
            assert!(!ecma_core_case(&other, kernel));
            other["track"] = json!("taint");
            other["score_tier"] = json!("calibration");
            assert!(!ecma_core_case(&other, kernel));
        }
    }

    #[test]
    fn javascript_sarif_mapping_requires_the_sink_file_and_line() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-javascript-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.js"),
            "function sink(value) {} // DFB-SINK: sink\nfunction other(value) {}\nother(input);\nsink(input);\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.js",
                "line_hint": 1
            }]
        });
        let matching = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "file:///tmp/work/fixture.js"},
                "region": {"startLine": 4}
            }}]}]}]
        });
        assert_eq!(
            ecma_sarif_outcome(&case_path, &case, &matching).0,
            "reached"
        );
        let wrong_line = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.js"},
                "region": {"startLine": 3}
            }}]}]}]
        });
        assert_eq!(
            ecma_sarif_outcome(&case_path, &case, &wrong_line).0,
            "inconclusive"
        );
        let missing_location = json!({
            "runs": [{"results": [{"message": {"text": "flow"}}]}]
        });
        assert_eq!(
            ecma_sarif_outcome(&case_path, &case, &missing_location).0,
            "inconclusive"
        );
        let no_results = json!({"runs": [{"results": []}]});
        assert_eq!(
            ecma_sarif_outcome(&case_path, &case, &no_results).0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn javascript_sarif_ambiguous_locations_stay_inconclusive() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-javascript-ambiguous-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.js"),
            "// DFB-SINK: duplicate\n// DFB-SINK: duplicate\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{"marker": "DFB-SINK: duplicate", "file": "fixture.js"}]
        });
        let sarif = json!({
            "runs": [{"results": [{"locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "fixture.js"},
                "region": {"startLine": 1}
            }}]}]}]
        });
        assert_eq!(
            ecma_sarif_outcome(&case_path, &case, &sarif).0,
            "inconclusive"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn javascript_codeql_report_paths_are_dedicated() {
        assert_eq!(CODEQL_JAVASCRIPT_RAW_DIR, "reports/raw/codeql-javascript");
        assert_eq!(
            CODEQL_JAVASCRIPT_REPORT,
            "reports/codeql-javascript-kernel.json"
        );
        assert_eq!(
            CODEQL_JAVASCRIPT_QUERY,
            "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
        );
        assert_eq!(CODEQL_TYPESCRIPT_RAW_DIR, "reports/raw/codeql-typescript");
        assert_eq!(
            CODEQL_TYPESCRIPT_REPORT,
            "reports/codeql-typescript-kernel.json"
        );
        assert_eq!(
            CODEQL_TYPESCRIPT_QUERY,
            "adapters/codeql/typescript/queries/TypeScriptKernel.ql"
        );
    }

    #[test]
    fn python_codeql_population_requires_the_expanded_core() {
        let expected = expected_core_templates("python");
        let mut cases = Vec::new();
        for index in 0..expected.len() {
            for polarity in ["positive", "negative"] {
                cases.push((
                    PathBuf::from(format!("case-{index}-{polarity}.json")),
                    json!({
                        "id": format!("dfb-taint-python-template-{index}-{polarity}"),
                        "template_id": expected[index],
                        "polarity": polarity,
                        "score_tier": "core",
                        "track": "taint",
                        "language": "python",
                        "model_profile": "benchmark-controlled",
                        "tool_model_references": {
                            "codeql": {"query": CODEQL_PYTHON_QUERY}
                        }
                    }),
                ));
            }
        }
        // Population validation is metadata-only; the checked-in query path
        // is verified by the command-facing selection helper.
        assert_eq!(
            validate_codeql_python_population(&cases).unwrap(),
            PathBuf::from("adapters/codeql/python/queries/PythonKernel.ql")
        );
        let mut drifted = cases.clone();
        drifted[0].1["template_id"] = json!("dfb-template-unapproved-drift");
        assert!(validate_codeql_python_population(&drifted).is_err());
        cases.pop();
        assert!(validate_codeql_python_population(&cases).is_err());
    }

    #[test]
    fn python_codeql_selection_requires_canonical_query() {
        let mut case = json!({
            "language": "python",
            "track": "taint",
            "score_tier": "core",
            "tool_model_references": {"codeql": {"query": CODEQL_PYTHON_QUERY}}
        });
        assert!(selected_codeql_python_case(&case));
        case["tool_model_references"]["codeql"]["query"] =
            json!("adapters/codeql/python/queries/OtherKernel.ql");
        assert!(!selected_codeql_python_case(&case));
    }

    #[test]
    fn codeql_database_creation_uses_language_specific_build_modes() {
        let case = json!({"fixture_files": ["direct_flow.py"]});
        let python_args = codeql_database_create_args(
            Path::new("/tmp/python-db"),
            Path::new("/tmp/python-workspace"),
            &case,
            CodeqlLanguage::Python,
        )
        .unwrap();
        assert!(python_args.iter().any(|arg| arg == "--language=python"));
        assert!(python_args.iter().any(|arg| arg == "--build-mode=none"));
        assert!(!python_args.iter().any(|arg| arg.starts_with("--command=")));

        let java_args = codeql_database_create_args(
            Path::new("/tmp/java-db"),
            Path::new("/tmp/java-workspace"),
            &case,
            CodeqlLanguage::Java,
        )
        .unwrap();
        assert!(java_args.iter().any(|arg| arg == "--language=java"));
        assert!(
            java_args
                .iter()
                .any(|arg| arg == "--command=javac -d classes direct_flow.py")
        );
        assert!(!java_args.iter().any(|arg| arg == "--build-mode=none"));

        let csharp_args = codeql_database_create_args(
            Path::new("/tmp/csharp-db"),
            Path::new("/tmp/csharp-workspace"),
            &case,
            CodeqlLanguage::CSharp,
        )
        .unwrap();
        assert!(csharp_args.iter().any(|arg| arg == "--language=csharp"));
        assert!(csharp_args.iter().any(|arg| arg == "--build-mode=none"));
        assert!(!csharp_args.iter().any(|arg| arg.starts_with("--command=")));

        let go_args = codeql_database_create_args(
            Path::new("/tmp/go-db"),
            Path::new("/tmp/go-workspace"),
            &case,
            CodeqlLanguage::Go {
                go: Path::new("/usr/local/bin/go"),
            },
        )
        .unwrap();
        assert!(go_args.iter().any(|arg| arg == "--language=go"));
        assert!(go_args.iter().any(|arg| arg == "--build-mode=manual"));
        assert!(
            go_args
                .iter()
                .any(|arg| arg == "--command=/usr/local/bin/go build ./...")
        );
        assert!(!go_args.iter().any(|arg| arg == "--build-mode=none"));
    }

    #[test]
    fn codeql_missing_sarif_keeps_runner_error_evidence() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-codeql-missing-sarif-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let raw_path = root.join("case.sarif.json");
        let read_error = fs::read_to_string(&raw_path).unwrap_err();
        let (outcome, diagnostics, evidence_path) =
            codeql_missing_sarif_error(&root, "case", &raw_path, &read_error).unwrap();

        assert_eq!(outcome, "runner-error");
        assert!(diagnostics[0].contains("read CodeQL SARIF"));
        assert_eq!(evidence_path, root.join("case-error.json"));
        let evidence: Value =
            serde_json::from_str(&fs::read_to_string(&evidence_path).unwrap()).unwrap();
        assert_eq!(evidence["state"], "runner-error");
        assert_eq!(evidence["stage"], "database-analyze");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn python_codeql_sarif_requires_a_canonical_sink_anchor() {
        let case = json!({
            "sink_anchors": [{"file": "direct_flow.py", "line_hint": 5}]
        });
        let reached = json!({
            "runs": [{"results": [{
                "message": {"text": "flow"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "file:///tmp/codeql/direct_flow.py"},
                    "region": {"startLine": 11}
                }}]
            }]}]
        });
        assert_eq!(
            normalize_anchored_codeql_sarif(&case, &reached, "Python").0,
            "reached"
        );

        let wrong_file = json!({
            "runs": [{"results": [{
                "message": {"text": "unrelated finding"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "other_fixture.py"},
                    "region": {"startLine": 4}
                }}]
            }]}]
        });
        assert_eq!(
            normalize_anchored_codeql_sarif(&case, &wrong_file, "Python").0,
            "inconclusive"
        );

        let clean = json!({"runs": [{"results": []}]});
        assert_eq!(
            normalize_anchored_codeql_sarif(&case, &clean, "Python").0,
            "not-reached"
        );

        let malformed = json!({"runs": [{"results": [{}]}]});
        assert_eq!(
            normalize_anchored_codeql_sarif(&case, &malformed, "Python").0,
            "inconclusive"
        );
        assert_eq!(
            normalize_anchored_codeql_sarif(&case, &json!({"runs": []}), "Python").0,
            "runner-error"
        );
    }

    /// Each Joern kernel is its own population: the balanced core assertions of
    /// exactly one language — 32 where all sixteen templates apply, 30 for Rust,
    /// whose exception-catch cell is inapplicable — with no case shared between
    /// them and no case borrowed from a CodeQL or Bifrost selection. Rust's
    /// `Result`/`?` `language-extension` pair is never pulled into the core
    /// denominator.
    #[test]
    fn joern_kernel_selections_are_language_disjoint_and_balanced() {
        let mut populations = BTreeMap::new();
        for kernel in [
            JoernKernel::Java,
            JoernKernel::JavaScript,
            JoernKernel::Python,
            JoernKernel::Ruby,
            JoernKernel::Php,
            JoernKernel::Rust,
        ] {
            let selected = select_joern_cases(kernel).unwrap();
            assert_eq!(selected.len(), 2 * kernel.templates().len());
            if challenge_rolled_out(kernel.language()) {
                assert!(selected.len() > KERNEL_CASE_COUNT);
            } else if kernel == JoernKernel::Rust {
                assert_eq!(selected.len(), KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
            } else {
                assert_eq!(selected.len(), KERNEL_CASE_COUNT);
            }
            let mut templates = BTreeMap::<String, (usize, usize)>::new();
            for (_, case) in &selected {
                assert_eq!(case["language"], kernel.language());
                assert_eq!(case["track"], "taint");
                assert_eq!(case["score_tier"], "core");
                assert_eq!(case["model_profile"], "benchmark-controlled");
                let counts = templates
                    .entry(case["template_id"].as_str().unwrap().to_string())
                    .or_default();
                if case["polarity"] == "positive" {
                    counts.0 += 1;
                } else {
                    counts.1 += 1;
                }
            }
            assert_eq!(templates.len(), kernel.templates().len());
            assert!(templates.values().all(|counts| *counts == (1, 1)));
            assert!(
                templates
                    .keys()
                    .all(|id| kernel.templates().contains(&id.as_str()))
            );
            populations.insert(
                kernel.language(),
                selected
                    .iter()
                    .map(|(_, case)| case["id"].as_str().unwrap().to_string())
                    .collect::<BTreeSet<_>>(),
            );
        }
        for left in populations.values() {
            for right in populations.values() {
                if left != right {
                    assert!(left.is_disjoint(right));
                }
            }
        }
    }

    #[test]
    fn joern_report_paths_are_dedicated() {
        let kernels = [
            JoernKernel::Java,
            JoernKernel::JavaScript,
            JoernKernel::Python,
            JoernKernel::Ruby,
            JoernKernel::Php,
            JoernKernel::Rust,
        ];
        let reports = kernels
            .iter()
            .map(|kernel| kernel.report())
            .collect::<BTreeSet<_>>();
        let raw_dirs = kernels
            .iter()
            .map(|kernel| kernel.raw_dir())
            .collect::<BTreeSet<_>>();
        let frontends = kernels
            .iter()
            .map(|kernel| kernel.frontend())
            .collect::<BTreeSet<_>>();
        assert_eq!(reports.len(), kernels.len());
        assert_eq!(raw_dirs.len(), kernels.len());
        assert_eq!(frontends.len(), kernels.len());
        for kernel in kernels {
            assert!(kernel.report().starts_with("reports/joern-"));
            assert!(kernel.raw_dir().starts_with("reports/raw/joern-"));
            // A Joern report must never land on a CodeQL or Bifrost path.
            assert_ne!(kernel.report(), CODEQL_JAVASCRIPT_REPORT);
            assert_ne!(kernel.raw_dir(), CODEQL_JAVASCRIPT_RAW_DIR);
        }
        assert!(Path::new(JOERN_KERNEL_SCRIPT).is_file());
    }

    /// The kernel query is parameterized by the endpoints the fixture itself
    /// declares. Two frozen Java assertions predate the `dfb_source`/`dfb_sink`
    /// convention, so an adapter that assumed those names would silently
    /// analyze nothing; the runner reads both names off the marker lines.
    #[test]
    fn joern_endpoints_come_from_the_case_markers() {
        let resolve = |id: &str, dialect: AnchorDialect| {
            for path in case_paths() {
                let case: Value =
                    serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
                if case["id"] == id {
                    return benchmark_endpoint_names(&path, &case, dialect).unwrap();
                }
            }
            panic!("case {id} is absent");
        };
        assert_eq!(
            resolve(
                "dfb-taint-java-alias-propagation-positive",
                AnchorDialect::Java
            ),
            BenchmarkEndpoints {
                source_function: "dfb_source".to_string(),
                sink_function: "dfb_sink".to_string()
            }
        );
        assert_eq!(
            resolve("dfb-taint-java-direct-positive", AnchorDialect::Java),
            BenchmarkEndpoints {
                source_function: "directUntrustedInput".to_string(),
                sink_function: "recordDirect".to_string()
            }
        );
        assert_eq!(
            resolve(
                "dfb-taint-javascript-alias-propagation-positive",
                AnchorDialect::Ecma
            ),
            BenchmarkEndpoints {
                source_function: "dfb_source".to_string(),
                sink_function: "dfb_sink".to_string()
            }
        );
        assert_eq!(
            resolve(
                "dfb-taint-python-alias-propagation-positive",
                AnchorDialect::Python
            ),
            BenchmarkEndpoints {
                source_function: "dfb_source".to_string(),
                sink_function: "dfb_sink".to_string()
            }
        );
        // Ruby's source declaration carries no parameter list at all, so the
        // endpoint name has to come from the `def` keyword rather than from an
        // identifier before `(`.
        assert_eq!(
            resolve(
                "dfb-taint-ruby-alias-propagation-positive",
                AnchorDialect::Ruby
            ),
            BenchmarkEndpoints {
                source_function: "dfb_source".to_string(),
                sink_function: "dfb_sink".to_string()
            }
        );
        assert_eq!(
            resolve(
                "dfb-taint-php-alias-propagation-positive",
                AnchorDialect::Php
            ),
            BenchmarkEndpoints {
                source_function: "dfb_source".to_string(),
                sink_function: "dfb_sink".to_string()
            }
        );
    }

    /// Ruby is the one dialect whose endpoint declarations may carry no
    /// parameter list: `def dfb_source # DFB-SOURCE: ...` is a method
    /// declaration exactly as `def dfb_sink(value) # DFB-SINK: ...` is. It
    /// reaches a method through `.` and a constant path through `::`, and opens
    /// comments with `#`.
    #[test]
    fn ruby_endpoint_declarations_resolve_through_the_ruby_dialect() {
        assert_eq!(
            AnchorDialect::Ruby
                .declared_function_name("def dfb_sink(value) # DFB-SINK: sink", "DFB-SINK: sink")
                .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            AnchorDialect::Ruby
                .declared_function_name("def dfb_source # DFB-SOURCE: input", "DFB-SOURCE: input")
                .as_deref(),
            Some("dfb_source")
        );
        assert_eq!(
            AnchorDialect::Ruby
                .declared_function_name(
                    "  def self.dfb_source # DFB-SOURCE: input",
                    "DFB-SOURCE: input"
                )
                .as_deref(),
            Some("dfb_source")
        );
        // A marker that is not on a declaration resolves to nothing rather than
        // to a guess.
        assert_eq!(
            AnchorDialect::Ruby
                .declared_function_name("  value = 0 # DFB-SINK: sink", "DFB-SINK: sink"),
            None
        );
        assert_eq!(
            AnchorDialect::Ruby
                .declared_function_name("  undef dfb_sink # DFB-SINK: sink", "DFB-SINK: sink"),
            None
        );
        assert!(AnchorDialect::Ruby.is_call("  dfb_sink(aliased.value)", "dfb_sink"));
        assert!(!AnchorDialect::Ruby.is_call("  other.dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Ruby.is_call("  Other::dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Ruby.is_call("  my_dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Ruby.is_call("  # dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Ruby.is_call("  log(\"dfb_sink(value)\")", "dfb_sink"));
    }

    /// PHP declares a function name before its parameter list, reaches an
    /// instance member through `->` and a static one through `::`, and opens a
    /// line comment with either `//` or `#`. Its `.` is string concatenation,
    /// not a member operator, so a concatenated call is still a callsite.
    #[test]
    fn php_sink_declarations_and_callsites_resolve_through_the_php_dialect() {
        assert_eq!(
            AnchorDialect::Php
                .declared_function_name(
                    "function dfb_sink(string $value): void {} // DFB-SINK: sink",
                    "DFB-SINK: sink"
                )
                .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            AnchorDialect::Php
                .declared_function_name(
                    "function dfb_source(): string { # DFB-SOURCE: input",
                    "DFB-SOURCE: input"
                )
                .as_deref(),
            Some("dfb_source")
        );
        assert!(AnchorDialect::Php.is_call("    dfb_sink($alias->value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    $other->dfb_sink($value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    Other::dfb_sink($value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    my_dfb_sink($value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    // dfb_sink($value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    # dfb_sink($value);", "dfb_sink"));
        assert!(!AnchorDialect::Php.is_call("    log(\"dfb_sink($value)\");", "dfb_sink"));
        // `.` concatenates in PHP; it never qualifies a member.
        assert!(AnchorDialect::Php.is_call("    $text = $prefix . dfb_sink($value);", "dfb_sink"));
    }

    /// The Ruby kernel is its own Bifrost population. The tranche is gated on
    /// Bifrost's Ruby indexing, so whatever this run produces is capability
    /// evidence — but the selection itself must still be exactly the 32 Ruby
    /// core assertions and nothing else.
    #[test]
    fn bifrost_ruby_kernel_selects_only_ruby_core_cases() {
        let mut core = 0;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::RubyKernel) {
                assert!(ruby_core_case(&case));
                core += 1;
                for other in [
                    BifrostRun::PythonKernel,
                    BifrostRun::KotlinKernel,
                    BifrostRun::TypescriptKernel,
                    BifrostRun::CsharpKernel,
                    BifrostRun::GoKernel,
                    BifrostRun::CKernel,
                    BifrostRun::CppKernel,
                    BifrostRun::RustKernel,
                    BifrostRun::PhpKernel,
                ] {
                    assert!(!selected_bifrost_case(&case, other));
                }
            } else {
                assert!(!ruby_core_case(&case));
            }
        }
        assert_eq!(core, KERNEL_CASE_COUNT);
        assert_eq!(
            BifrostRun::RubyKernel.expected_core_cases(),
            Some(KERNEL_CASE_COUNT)
        );
    }

    /// The Ruby CodeQL slice owns its own pack, query, report, and evidence
    /// root, and is never pooled with another language's population.
    #[test]
    fn ruby_codeql_report_paths_are_dedicated() {
        for other in [
            CODEQL_KOTLIN_REPORT,
            CODEQL_CSHARP_REPORT,
            CODEQL_JAVASCRIPT_REPORT,
            CODEQL_TYPESCRIPT_REPORT,
            CODEQL_GO_REPORT,
            CODEQL_C_REPORT,
            CODEQL_CPP_REPORT,
            CODEQL_RUST_REPORT,
            "reports/codeql-python-kernel.json",
        ] {
            assert_ne!(CODEQL_RUBY_REPORT, other);
        }
        for other in [
            CODEQL_KOTLIN_RAW_DIR,
            CODEQL_CSHARP_RAW_DIR,
            CODEQL_JAVASCRIPT_RAW_DIR,
            CODEQL_TYPESCRIPT_RAW_DIR,
            CODEQL_GO_RAW_DIR,
            CODEQL_C_RAW_DIR,
            CODEQL_CPP_RAW_DIR,
            CODEQL_RUST_RAW_DIR,
        ] {
            assert_ne!(CODEQL_RUBY_RAW_DIR, other);
        }
        assert_ne!(CODEQL_RUBY_QUERY, CODEQL_PYTHON_QUERY);
        assert_eq!(CodeqlLanguage::Ruby.cli_name(), "ruby");
        assert!(!CodeqlLanguage::Ruby.traces_jvm_compile());

        // Ruby is buildless: no traced compile, no generated manifest.
        let case = json!({"id": "dfb-taint-ruby-test", "fixture_files": ["direct_flow.rb"]});
        let args = codeql_database_create_args(
            Path::new("/tmp/ruby-db"),
            Path::new("/tmp/ruby-workspace"),
            &case,
            CodeqlLanguage::Ruby,
        )
        .unwrap();
        assert!(args.iter().any(|arg| arg == "--language=ruby"));
        assert!(args.iter().any(|arg| arg == "--build-mode=none"));
        assert!(!args.iter().any(|arg| arg.starts_with("--command=")));

        let selected = codeql_ruby_cases().unwrap();
        assert_eq!(selected.len(), KERNEL_CASE_COUNT);
        for (_, case) in &selected {
            assert_eq!(case["language"], "ruby");
            assert_eq!(case["score_tier"], "core");
        }
    }

    /// Java declares a sink as an identifier before a parameter list and calls
    /// it unqualified; Python does the same but opens its comments with `#`.
    #[test]
    fn java_and_python_sink_declarations_resolve_through_their_dialects() {
        assert_eq!(
            AnchorDialect::Java
                .declared_function_name(
                    "    static void dfb_sink(int value) { } // DFB-SINK: sink",
                    "DFB-SINK: sink"
                )
                .as_deref(),
            Some("dfb_sink")
        );
        assert_eq!(
            AnchorDialect::Python
                .declared_function_name("def dfb_sink(value):  # DFB-SINK: sink", "DFB-SINK: sink")
                .as_deref(),
            Some("dfb_sink")
        );
        assert!(AnchorDialect::Java.is_call("        dfb_sink(alias.value);", "dfb_sink"));
        assert!(!AnchorDialect::Java.is_call("        other.dfb_sink(value);", "dfb_sink"));
        assert!(!AnchorDialect::Java.is_call("        my_dfb_sink(value);", "dfb_sink"));
        assert!(!AnchorDialect::Java.is_call("        // dfb_sink(value);", "dfb_sink"));
        assert!(AnchorDialect::Python.is_call("    dfb_sink(alias.value)", "dfb_sink"));
        assert!(!AnchorDialect::Python.is_call("    other.dfb_sink(value)", "dfb_sink"));
        // A Python comment must not be read as a callsite, even though it is
        // not a `//` comment.
        assert!(!AnchorDialect::Python.is_call("    # dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Python.is_call("    log(\"dfb_sink(value)\")", "dfb_sink"));
    }

    /// A Joern flow is only `reached` when it lands on a callsite of the case's
    /// own anchored sink function.
    #[test]
    fn joern_flow_evidence_requires_the_sink_callsite() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-joern-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.py"),
            "def dfb_sink(value):  # DFB-SINK: sink\n    pass\n\n\ndef run():\n    other(value)\n    dfb_sink(value)\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.py",
                "line_hint": 1
            }]
        });
        let analyzed = |flows: Value| {
            json!({
                "state": "analyzed",
                "source_node_count": 1,
                "sink_node_count": 1,
                "flows": flows
            })
        };
        let matching = analyzed(json!([{"elements": [
            {"file": "/tmp/work/fixture.py", "line": 7, "code": "value"}
        ]}]));
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &matching, AnchorDialect::Python).0,
            "reached"
        );
        let wrong_line = analyzed(json!([{"elements": [
            {"file": "fixture.py", "line": 6, "code": "value"}
        ]}]));
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &wrong_line, AnchorDialect::Python).0,
            "inconclusive"
        );
        let no_location = analyzed(json!([{"elements": [{"code": "value"}]}]));
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &no_location, AnchorDialect::Python).0,
            "inconclusive"
        );
        let empty_flow = analyzed(json!([{"elements": []}]));
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &empty_flow, AnchorDialect::Python).0,
            "inconclusive"
        );
        let clean = analyzed(json!([]));
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &clean, AnchorDialect::Python).0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    /// A Joern script, frontend, or engine failure — and a run that never
    /// observed one of the two benchmark-controlled endpoints — must never be
    /// normalized to a clean negative.
    #[test]
    fn joern_runner_failures_never_become_clean_negatives() {
        let case_path = PathBuf::from("cases/taint/python/direct-positive/case.json");
        let case = json!({"sink_anchors": []});
        let failed = json!({
            "state": "runner-error",
            "stage": "joern-script",
            "diagnostic": "java.lang.RuntimeException: frontend failed"
        });
        let (outcome, diagnostics) =
            joern_flow_outcome(&case_path, &case, &failed, AnchorDialect::Python);
        assert_eq!(outcome, "runner-error");
        assert!(
            diagnostics
                .iter()
                .any(|line| line.contains("frontend failed"))
        );
        // The same document must also be refused as a downgraded negative by
        // the freeze's raw-evidence guard.
        assert_eq!(raw_special_outcome(&failed), Some("runner-error"));

        for broken in [
            json!({"state": "analyzed", "source_node_count": 1, "sink_node_count": 1}),
            json!({"state": "analyzed", "flows": []}),
            json!({"state": "surprise", "flows": []}),
            json!({"flows": []}),
        ] {
            assert_eq!(
                joern_flow_outcome(&case_path, &case, &broken, AnchorDialect::Python).0,
                "runner-error"
            );
        }

        for unobserved in [
            json!({"state": "analyzed", "source_node_count": 0, "sink_node_count": 1, "flows": []}),
            json!({"state": "analyzed", "source_node_count": 1, "sink_node_count": 0, "flows": []}),
        ] {
            assert_eq!(
                joern_flow_outcome(&case_path, &case, &unobserved, AnchorDialect::Python).0,
                "inconclusive"
            );
        }

        // An unresolvable sink anchor keeps a produced flow inconclusive rather
        // than crediting or discrediting it.
        let flows = json!({
            "state": "analyzed",
            "source_node_count": 1,
            "sink_node_count": 1,
            "flows": [{"elements": [{"file": "direct_flow.py", "line": 10}]}]
        });
        assert_eq!(
            joern_flow_outcome(&case_path, &case, &flows, AnchorDialect::Python).0,
            "inconclusive"
        );
    }

    const SEMGREP_KERNELS: [SemgrepKernel; 11] = [
        SemgrepKernel::Java,
        SemgrepKernel::JavaScript,
        SemgrepKernel::TypeScript,
        SemgrepKernel::Python,
        SemgrepKernel::Go,
        SemgrepKernel::Ruby,
        SemgrepKernel::Php,
        SemgrepKernel::Kotlin,
        SemgrepKernel::Rust,
        SemgrepKernel::C,
        SemgrepKernel::Cpp,
    ];

    /// Each Semgrep kernel is its own population: the balanced core assertions
    /// of exactly one language, with no case shared between the eleven and no
    /// case borrowed from a CodeQL, Joern, or Bifrost selection. The bounded
    /// profile narrows what is *scored*, never what is selected — the balance
    /// check still sees the whole kernel. C and Rust carry a fifteen-template
    /// core because docs/applicability-matrix.md classifies their
    /// exception-catch cell as inapplicable; an inapplicable cell reduces only
    /// its own language's denominator.
    #[test]
    fn semgrep_kernel_selections_are_language_disjoint_and_balanced() {
        let mut populations = BTreeMap::new();
        for kernel in SEMGREP_KERNELS {
            let selected = select_semgrep_cases(kernel).unwrap();
            let expected_templates = kernel.templates();
            assert_eq!(selected.len(), 2 * expected_templates.len());
            if challenge_rolled_out(kernel.language()) {
                assert!(selected.len() > KERNEL_CASE_COUNT);
            } else {
                match kernel {
                    SemgrepKernel::C | SemgrepKernel::Rust => {
                        assert_eq!(selected.len(), KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
                    }
                    _ => assert_eq!(selected.len(), KERNEL_CASE_COUNT),
                }
            }
            let mut templates = BTreeMap::<String, (usize, usize)>::new();
            for (_, case) in &selected {
                assert_eq!(case["language"], kernel.language());
                assert_eq!(case["track"], "taint");
                assert_eq!(case["score_tier"], "core");
                assert_eq!(case["model_profile"], "benchmark-controlled");
                let counts = templates
                    .entry(case["template_id"].as_str().unwrap().to_string())
                    .or_default();
                if case["polarity"] == "positive" {
                    counts.0 += 1;
                } else {
                    counts.1 += 1;
                }
            }
            assert_eq!(
                templates
                    .keys()
                    .map(String::as_str)
                    .collect::<BTreeSet<_>>(),
                expected_templates.iter().copied().collect::<BTreeSet<_>>()
            );
            assert!(templates.values().all(|counts| *counts == (1, 1)));
            populations.insert(
                kernel.language(),
                selected
                    .iter()
                    .map(|(_, case)| case["id"].as_str().unwrap().to_string())
                    .collect::<BTreeSet<_>>(),
            );
        }
        for left in populations.values() {
            for right in populations.values() {
                if left != right {
                    assert!(left.is_disjoint(right));
                }
            }
        }
        // The `language-extension` tier is what C's error-code-return and
        // goto-cleanup cases and Rust's `Result`/`?` pair are scored on. None
        // of them is a core template, and none may be selected into a core
        // Semgrep run, where they would silently inflate the denominator.
        for extension in [
            "dfb-taint-c-error-code-return-positive",
            "dfb-taint-c-goto-cleanup-positive",
            "dfb-taint-rust-result-error-propagation-positive",
            "dfb-taint-rust-result-error-propagation-negative",
        ] {
            for population in populations.values() {
                assert!(
                    !population.contains(extension),
                    "{extension} is a language-extension case and must never enter a core Semgrep population"
                );
            }
        }
    }

    /// The maturity label is read off the pinned distribution's own
    /// machine-readable language table and retained verbatim. Kotlin is
    /// recorded `beta`; Rust, C, and C++ are recorded `alpha`; the seven
    /// kernels that landed first are all `ga`. The label is retained evidence
    /// about the front end, and it never appears in the partition decision:
    /// `semgrep_capability_exclusion` reads only the case metadata.
    #[test]
    fn semgrep_language_maturity_is_recorded_and_never_scored_on() {
        assert_eq!(SemgrepKernel::Kotlin.documented_maturity(), "beta");
        for kernel in [SemgrepKernel::Rust, SemgrepKernel::C, SemgrepKernel::Cpp] {
            assert_eq!(kernel.documented_maturity(), "alpha");
        }
        for kernel in [
            SemgrepKernel::Java,
            SemgrepKernel::JavaScript,
            SemgrepKernel::TypeScript,
            SemgrepKernel::Python,
            SemgrepKernel::Go,
            SemgrepKernel::Ruby,
            SemgrepKernel::Php,
        ] {
            assert_eq!(kernel.documented_maturity(), "ga");
        }
        for kernel in SEMGREP_KERNELS {
            let diagnostic = semgrep_maturity_diagnostic(kernel);
            assert!(diagnostic.contains(kernel.display_name()));
            assert!(diagnostic.contains(kernel.documented_maturity()));
            assert!(diagnostic.contains("lang.json"));
        }
        // Two cases identical but for language: the exclusion decision cannot
        // see a maturity label, so it cannot differ between them.
        let case = |language: &str| {
            json!({
                "language": language,
                "feature_tags": ["heap-access-path"],
                "expected_analysis_capability": {"kind": "heap-alias-sensitive-taint"}
            })
        };
        assert_eq!(
            semgrep_capability_exclusion(&case("rust")),
            semgrep_capability_exclusion(&case("java"))
        );
    }

    /// The dialect a kernel picks has to be verified against that language's
    /// real fixtures, not assumed from family resemblance. Kotlin adds no
    /// `AnchorDialect` of its own: its markers sit on `fun name(params)`
    /// declarations, its fixtures call the sink receiverlessly, `.` is the only
    /// member operator that could precede the name, and `//` opens a comment —
    /// which is the Java arm's contract exactly. This resolves every scored
    /// case of all four newly covered kernels through its chosen dialect and
    /// fails if any one of them cannot name its own endpoints.
    #[test]
    fn semgrep_new_kernels_resolve_every_scored_endpoint() {
        for kernel in [
            SemgrepKernel::Kotlin,
            SemgrepKernel::Rust,
            SemgrepKernel::C,
            SemgrepKernel::Cpp,
        ] {
            let mut scored = 0usize;
            for (path, case) in select_semgrep_cases(kernel).unwrap() {
                if semgrep_capability_exclusion(&case).is_some() {
                    continue;
                }
                scored += 1;
                let endpoints = benchmark_endpoint_names(&path, &case, kernel.dialect())
                    .unwrap_or_else(|reason| {
                        panic!("{} endpoints: {reason}", case["id"]);
                    });
                assert_eq!(endpoints.source_function, "dfb_source", "{}", case["id"]);
                assert_eq!(endpoints.sink_function, "dfb_sink", "{}", case["id"]);
            }
            assert_eq!(scored, 14, "{} scored partition", kernel.label());
        }
        // The Kotlin surface rules the Java arm is being reused for, stated
        // directly rather than only exercised through the fixtures.
        assert_eq!(
            AnchorDialect::Java.declared_function_name(
                "    fun dfb_sink(value: String) {} // DFB-SINK: direct-sink",
                "DFB-SINK: direct-sink"
            ),
            Some("dfb_sink".to_string())
        );
        assert_eq!(
            AnchorDialect::Java.declared_function_name(
                "    fun dfb_source(): String { // DFB-SOURCE: direct-input",
                "DFB-SOURCE: direct-input"
            ),
            Some("dfb_source".to_string())
        );
        assert!(AnchorDialect::Java.is_call("        dfb_sink(alias.value)", "dfb_sink"));
        assert!(!AnchorDialect::Java.is_call("        other.dfb_sink(value)", "dfb_sink"));
        assert!(!AnchorDialect::Java.is_call("        // dfb_sink(value)", "dfb_sink"));
    }

    #[test]
    fn semgrep_report_paths_and_rules_are_dedicated() {
        let reports = SEMGREP_KERNELS
            .iter()
            .map(|kernel| kernel.report())
            .collect::<BTreeSet<_>>();
        let raw_dirs = SEMGREP_KERNELS
            .iter()
            .map(|kernel| kernel.raw_dir())
            .collect::<BTreeSet<_>>();
        let rules = SEMGREP_KERNELS
            .iter()
            .map(|kernel| kernel.rule())
            .collect::<BTreeSet<_>>();
        assert_eq!(reports.len(), SEMGREP_KERNELS.len());
        assert_eq!(raw_dirs.len(), SEMGREP_KERNELS.len());
        assert_eq!(rules.len(), SEMGREP_KERNELS.len());
        for kernel in SEMGREP_KERNELS {
            assert!(kernel.report().starts_with("reports/semgrep-"));
            assert!(kernel.raw_dir().starts_with("reports/raw/semgrep-"));
            // A Semgrep report must never land on another adapter's path.
            assert_ne!(kernel.report().as_str(), CODEQL_JAVASCRIPT_REPORT);
            assert_ne!(kernel.report().as_str(), JOERN_JAVA_REPORT);
            assert_ne!(kernel.raw_dir().as_str(), JOERN_JAVA_RAW_DIR);
            // Every kernel's rule is committed, carries both placeholders, and
            // is written for that kernel's own Semgrep language.
            let rule = fs::read_to_string(kernel.rule()).unwrap();
            assert!(rule.contains(SEMGREP_SOURCE_PLACEHOLDER));
            assert!(rule.contains(SEMGREP_SINK_PLACEHOLDER));
            assert!(rule.contains("mode: taint"));
        }
        // The configuration hash binds every committed rule, so a change to any
        // one of them invalidates every retained Semgrep report.
        let hashed = semgrep_rule_paths().unwrap();
        for kernel in SEMGREP_KERNELS {
            assert!(hashed.contains(&PathBuf::from(kernel.rule())));
        }
    }

    /// The bounded profile is a declared-capability decision taken from the
    /// case's own metadata *before* Semgrep is invoked. This test reads only
    /// `case.json` files — no Semgrep binary is required or consulted — so an
    /// out-of-profile case can never be run and then counted as a miss.
    #[test]
    fn semgrep_unsupported_partition_is_metadata_driven() {
        for kernel in SEMGREP_KERNELS {
            let selected = select_semgrep_cases(kernel).unwrap();
            let mut scored = 0usize;
            let mut excluded = 0usize;
            for (_, case) in &selected {
                let tags: BTreeSet<&str> = case["feature_tags"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter_map(Value::as_str)
                    .collect();
                match semgrep_capability_exclusion(case) {
                    None => {
                        assert!(
                            tags.contains("intraprocedural"),
                            "{} is scored but is not tagged intraprocedural",
                            case["id"]
                        );
                        scored += 1;
                    }
                    Some(reason) => {
                        assert!(
                            !tags.contains("intraprocedural"),
                            "{} is tagged intraprocedural but was excluded",
                            case["id"]
                        );
                        assert!(reason.contains("outside the bounded Semgrep CE profile"));
                        excluded += 1;
                    }
                }
            }
            // Seven templates are intraprocedural in every language, and the
            // partition keeps each one's positive/negative pair together, so
            // the scored subset is 14 assertions everywhere. Only the
            // `unsupported` remainder differs: C and Rust have no
            // exception-catch pair to exclude, so theirs is 16 rather than 18,
            // and a language whose challenge row is rolled out carries the
            // whole challenge tier in the remainder — every challenge template
            // is outside the CE profile, so none of them moves the scored
            // subset off 14.
            assert_eq!(scored, 14, "{} scored partition", kernel.label());
            let expected_excluded = 2 * kernel.templates().len() - 14;
            assert_eq!(
                excluded,
                expected_excluded,
                "{} unsupported partition",
                kernel.label()
            );
            if challenge_rolled_out(kernel.language()) {
                assert!(expected_excluded > 18);
            } else {
                match kernel {
                    SemgrepKernel::C | SemgrepKernel::Rust => assert_eq!(expected_excluded, 16),
                    _ => assert_eq!(expected_excluded, 18),
                }
            }
        }
        // Every interprocedural and heap relay is excluded by tag, whatever the
        // language, and the retained reason names the documented boundary.
        let interprocedural = json!({
            "feature_tags": ["interprocedural-one-hop"],
            "expected_analysis_capability": {"kind": "context-sensitive-interprocedural-taint"}
        });
        let reason = semgrep_capability_exclusion(&interprocedural).unwrap();
        assert!(reason.contains("--pro-intrafile"));
        let heap = json!({
            "feature_tags": ["heap-access-path"],
            "expected_analysis_capability": {"kind": "heap-alias-sensitive-taint"}
        });
        assert!(
            semgrep_capability_exclusion(&heap)
                .unwrap()
                .contains("field-sensitive")
        );
        assert_eq!(
            semgrep_capability_exclusion(&json!({
                "feature_tags": ["intraprocedural"],
                "expected_analysis_capability": {"kind": "intraprocedural-taint"}
            })),
            None
        );
    }

    /// A Semgrep finding is only `reached` when it lands on a callsite of the
    /// case's own anchored sink function.
    #[test]
    fn semgrep_finding_evidence_requires_the_sink_callsite() {
        let root = std::env::temp_dir().join(format!(
            "dataflowbench-semgrep-anchor-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let case_path = root.join("case.json");
        fs::write(
            root.join("fixture.py"),
            "def dfb_sink(value):  # DFB-SINK: sink\n    pass\n\n\ndef run():\n    other(value)\n    dfb_sink(value)\n",
        )
        .unwrap();
        let case = json!({
            "sink_anchors": [{
                "marker": "DFB-SINK: sink",
                "file": "fixture.py",
                "line_hint": 1
            }]
        });
        let scanned = |results: Value| {
            json!({
                "version": "1.174.0",
                "results": results,
                "errors": [],
                "skipped_rules": [],
                "paths": {"scanned": ["/tmp/work/fixture.py"]}
            })
        };
        let finding = |file: &str, line: u64| {
            json!({
                "check_id": "dfb-taint-endpoint-contract",
                "path": file,
                "start": {"line": line, "col": 5},
                "extra": {"engine_kind": "OSS"}
            })
        };
        assert_eq!(
            semgrep_finding_outcome(
                &case_path,
                &case,
                &scanned(json!([finding("/tmp/work/fixture.py", 7)])),
                AnchorDialect::Python
            )
            .0,
            "reached"
        );
        assert_eq!(
            semgrep_finding_outcome(
                &case_path,
                &case,
                &scanned(json!([finding("fixture.py", 6)])),
                AnchorDialect::Python
            )
            .0,
            "inconclusive"
        );
        assert_eq!(
            semgrep_finding_outcome(
                &case_path,
                &case,
                &scanned(json!([{"path": "fixture.py", "extra": {"engine_kind": "OSS"}}])),
                AnchorDialect::Python
            )
            .0,
            "inconclusive"
        );
        assert_eq!(
            semgrep_finding_outcome(
                &case_path,
                &case,
                &scanned(json!([])),
                AnchorDialect::Python
            )
            .0,
            "not-reached"
        );
        fs::remove_dir_all(root).unwrap();
    }

    /// A Semgrep engine, rule, or parse failure — and a scan that never opened
    /// the fixture — must never be normalized to a clean negative, whatever the
    /// finding list says.
    #[test]
    fn semgrep_runner_failures_never_become_clean_negatives() {
        let case_path = PathBuf::from("cases/taint/python/direct-positive/case.json");
        let case = json!({"sink_anchors": []});
        let failed = json!({
            "results": [],
            "errors": [{"type": "SyntaxError", "long_msg": "Syntax error at line fixture.py:3"}],
            "skipped_rules": [],
            "paths": {"scanned": []}
        });
        let (outcome, diagnostics) =
            semgrep_finding_outcome(&case_path, &case, &failed, AnchorDialect::Python);
        assert_eq!(outcome, "runner-error");
        assert!(diagnostics.iter().any(|line| line.contains("Syntax error")));
        // The same document must also be refused as a downgraded negative by
        // the freeze's raw-evidence guard.
        assert_eq!(raw_special_outcome(&failed), Some("runner-error"));

        // A rule Semgrep declined to run explains its empty finding list, so
        // that list is not evidence about the program.
        let skipped = json!({
            "results": [],
            "errors": [],
            "skipped_rules": [{"rule_id": "dfb-taint-endpoint-contract"}],
            "paths": {"scanned": ["/tmp/work/fixture.py"]}
        });
        assert_eq!(
            semgrep_finding_outcome(&case_path, &case, &skipped, AnchorDialect::Python).0,
            "runner-error"
        );

        // A finding from any engine other than the pinned CE engine breaks the
        // pinning; that is an execution failure, not a data point.
        let wrong_engine = json!({
            "results": [{"path": "fixture.py", "start": {"line": 7}, "extra": {"engine_kind": "PRO"}}],
            "errors": [],
            "skipped_rules": [],
            "paths": {"scanned": ["/tmp/work/fixture.py"]}
        });
        assert_eq!(
            semgrep_finding_outcome(&case_path, &case, &wrong_engine, AnchorDialect::Python).0,
            "runner-error"
        );

        for malformed in [
            json!({"errors": [], "paths": {"scanned": []}}),
            json!({"results": [], "paths": {"scanned": []}}),
        ] {
            assert_eq!(
                semgrep_finding_outcome(&case_path, &case, &malformed, AnchorDialect::Python).0,
                "runner-error"
            );
        }

        // A clean run that never opened a target proves nothing either way.
        let untargeted = json!({
            "results": [],
            "errors": [],
            "skipped_rules": [],
            "paths": {"scanned": []}
        });
        assert_eq!(
            semgrep_finding_outcome(&case_path, &case, &untargeted, AnchorDialect::Python).0,
            "inconclusive"
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

    /// Every checked-in normalized report must declare the fixture revision of
    /// the freeze it is published under. Comparing against the freeze — rather
    /// than against `fixture_revision()` over the working tree — is the
    /// invariant `validate_freeze` and `create_freeze` actually enforce, and it
    /// stays meaningful while a new language kernel is authored but not yet
    /// re-run and re-frozen. Once a release freeze is assembled, `create_freeze`
    /// still refuses reports that predate the selected case population, so a
    /// grown benchmark cannot be published without re-running every adapter.
    #[test]
    fn checked_reports_match_the_frozen_fixture_revision() {
        let freeze: Value =
            serde_json::from_str(&fs::read_to_string("reports/freeze.json").unwrap()).unwrap();
        let frozen_revision = freeze["benchmark"]["fixture_revision"].as_str().unwrap();
        assert!(
            frozen_revision
                .strip_prefix("sha256:")
                .is_some_and(|digest| digest.len() == 64)
        );
        let frozen_reports = freeze["reports"]
            .as_array()
            .unwrap()
            .iter()
            .map(|report| report["path"].as_str().unwrap())
            .collect::<BTreeSet<_>>();
        assert!(!frozen_reports.is_empty());
        for path in frozen_reports {
            let report: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            assert_eq!(
                report["fixture_revision"].as_str(),
                Some(frozen_revision),
                "{path} does not declare the frozen fixture revision"
            );
        }
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

    #[test]
    fn create_freeze_manifest_matches_validated_fixture() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let manifest = build_freeze_manifest(
            &fixture.root,
            &[PathBuf::from("reports/test.json")],
            "development",
            "development",
            &"a".repeat(40),
        )
        .unwrap();
        // The assembler reconstructs the hand-built fixture manifest exactly.
        assert_eq!(manifest, fixture.read_manifest());
        let assembled = fixture.root.join("reports/assembled.json");
        fs::write(&assembled, serde_json::to_vec_pretty(&manifest).unwrap()).unwrap();
        validate_freeze_at(&fixture.root, &assembled, false).unwrap();
    }

    #[test]
    fn create_freeze_rejects_stale_fixture_bytes() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
        let error = build_freeze_manifest(
            &fixture.root,
            &[PathBuf::from("reports/test.json")],
            "development",
            "development",
            &"a".repeat(40),
        )
        .unwrap_err()
        .to_string();
        assert!(error.contains("re-run the adapters"), "{error}");
    }

    #[test]
    fn freeze_git_state_accepts_ancestor_revisions_and_containing_tags() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let run_git = |args: &[&str]| {
            assert!(
                Command::new("git")
                    .args([
                        "-c",
                        "user.email=dataflowbench-test@example.invalid",
                        "-c",
                        "user.name=DataFlowBench Test",
                        "-c",
                        "commit.gpgsign=false",
                        "-c",
                        "tag.gpgsign=false",
                    ])
                    .args(args)
                    .current_dir(&fixture.root)
                    .status()
                    .unwrap()
                    .success()
            );
        };
        run_git(&["init", "-q"]);
        run_git(&["add", "."]);
        run_git(&["commit", "-qm", "evidence"]);
        let evidence = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();
        fs::write(fixture.root.join("later.txt"), "later\n").unwrap();
        run_git(&["add", "."]);
        run_git(&["commit", "-qm", "manifest"]);
        let head = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();

        // The evidence commit validates as an ancestor of HEAD.
        validate_freeze_git_state(&fixture.root, &evidence, "development", "development").unwrap();
        assert!(
            validate_freeze_git_state(&fixture.root, &"b".repeat(40), "development", "development")
                .is_err()
        );

        // A release tag must contain the frozen evidence revision.
        run_git(&["tag", "v0.1.0"]);
        validate_freeze_git_state(&fixture.root, &evidence, "v0.1.0", "release").unwrap();
        run_git(&["tag", "v0.0.1", &evidence]);
        assert!(validate_freeze_git_state(&fixture.root, &head, "v0.0.1", "release").is_err());
    }

    #[test]
    fn generate_results_writes_deterministic_artifacts() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let output = fixture.root.join("generated");
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();

        let results: Value =
            serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
        assert_eq!(results["schema_version"], 1);
        let manifest_bytes = fs::read(&fixture.manifest).unwrap();
        assert_eq!(
            results["manifest"]["sha256"],
            json!(format!("{:x}", Sha256::digest(&manifest_bytes)))
        );
        let scorecard = &results["scorecards"][0];
        assert_eq!(
            scorecard["id"],
            json!("test-taint-taint-benchmark-controlled")
        );
        let tier = &scorecard["languages"][0]["score_tiers"][0];
        assert_eq!(scorecard["languages"][0]["language"], json!("c"));
        assert_eq!(tier["score_tier"], json!("core"));
        assert_eq!(tier["outcome_coverage"]["reached"], json!(1));
        assert_eq!(tier["outcome_coverage"]["total"], json!(1));
        assert_eq!(tier["cases"][0]["classification"], json!("true-positive"));
        let dimension = &tier["semantic_dimensions"][0];
        assert_eq!(dimension["name"], json!("local-flow"));
        assert_eq!(dimension["true_positive_rate"]["numerator"], json!(1));
        assert_eq!(dimension["true_positive_rate"]["percent"], json!("100.0"));
        assert_eq!(dimension["false_positive_rate"], Value::Null);
        assert_eq!(
            dimension["template_macro"]["true_positive_rate_percent"],
            json!("100.0")
        );
        assert_eq!(
            tier["dimension_macro"]["false_positive_rate_percent"],
            Value::Null
        );

        let index = fs::read_to_string(output.join("index.md")).unwrap();
        assert!(index.contains("test-taint-taint-benchmark-controlled"));
        let page =
            fs::read_to_string(output.join("scorecards/test-taint-taint-benchmark-controlled.md"))
                .unwrap();
        assert!(page.contains("`dfb-taint-test`"));
        assert!(page.contains("true-positive"));
        assert!(page.contains("reports/raw/test.json"));

        // Repeated generation from identical evidence is byte-stable.
        let before = fs::read(output.join("results.json")).unwrap();
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        assert_eq!(before, fs::read(output.join("results.json")).unwrap());
    }

    #[test]
    fn generate_results_classifies_incomplete_outcomes_separately() {
        let fixture = FreezeFixture::new("inconclusive", json!({"state": "inconclusive"}));
        let output = fixture.root.join("generated");
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        let results: Value =
            serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
        let tier = &results["scorecards"][0]["languages"][0]["score_tiers"][0];
        assert_eq!(tier["cases"][0]["classification"], json!("inconclusive"));
        let dimension = &tier["semantic_dimensions"][0];
        assert_eq!(dimension["counts"]["inconclusive"], json!(1));
        assert_eq!(dimension["counts"]["false_negatives"], json!(0));
        // No definitive positive result: the rate stays null, never zero.
        assert_eq!(dimension["true_positive_rate"], Value::Null);
        assert_eq!(
            dimension["template_macro"]["true_positive_rate_percent"],
            Value::Null
        );
    }

    #[test]
    fn generate_results_check_detects_current_stale_missing_and_extra() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        let output = fixture.root.join("generated");
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("missing artifact")
        );
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, true).unwrap();

        fs::write(output.join("index.md"), "stale\n").unwrap();
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("stale artifact: index.md")
        );

        generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
        fs::write(output.join("extra.md"), "extra\n").unwrap();
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
                .unwrap_err()
                .to_string()
                .contains("unexpected artifact: extra.md")
        );
    }

    #[test]
    fn generate_results_requires_a_valid_freeze() {
        let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
        fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
        let output = fixture.root.join("generated");
        assert!(
            generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).is_err()
        );
        assert!(!output.exists());
    }

    #[test]
    fn scorecard_identifiers_disambiguate_repeated_populations() {
        let mut used = BTreeMap::new();
        let report = json!({
            "track": "taint",
            "dimension": "taint",
            "model_profile": "benchmark-controlled"
        });
        assert_eq!(
            scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
            "test-adapter-taint-taint-benchmark-controlled"
        );
        assert_eq!(
            scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
            "test-adapter-taint-taint-benchmark-controlled-2"
        );
    }
    /// Every challenge case that exists in the corpus belongs to a language
    /// whose row is rolled out, and lands in that language's core population
    /// with a preregistered template ID.
    #[test]
    fn challenge_cases_exist_only_for_rolled_out_languages() {
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

    /// The smoke population must stay pinned to its frozen 118-case contract:
    /// dedicated language-kernel policies never leak into it.
    #[test]
    fn smoke_selection_is_pinned_to_the_frozen_population() {
        let mut selected = 0usize;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::Smoke) {
                selected += 1;
                let policy = case["tool_model_references"]["bifrost"]["policy"].as_str();
                if let Some(policy) = policy {
                    assert!(
                        !policy.contains("kotlin")
                            && !policy.contains("typescript")
                            && !policy.contains("csharp")
                            && !policy.contains("go")
                            && !policy.contains("rust")
                            && !policy.contains("core-c-kernel")
                            && !policy.contains("core-cpp-kernel"),
                        "smoke selected a dedicated-kernel policy: {policy}"
                    );
                }
            }
        }
        assert_eq!(selected, 118, "the smoke population is frozen at 118 cases");
    }

    /// A challenge case is refused by the smoke selector on template identity
    /// alone. The Java, JavaScript, and Python challenge fixtures will name the
    /// *same* kernel policies their classic siblings name, so pinning by policy
    /// could not have kept them out; without this exclusion the frozen 118
    /// would have silently become a different population.
    #[test]
    fn smoke_refuses_a_challenge_case_that_names_a_smoke_policy() {
        for policy in [
            BIFROST_JAVA_POLICY,
            BIFROST_JAVASCRIPT_POLICY,
            "adapters/bifrost/policies/core-python-kernel.rqlp",
            BIFROST_DIRECT_POLICY,
            BIFROST_DIRECT_POSITIVE_POLICY,
            BIFROST_EXPLICIT_NEGATIVE_POLICY,
        ] {
            let classic = json!({
                "template_id": "dfb-template-direct-propagation",
                "tool_model_references": {"bifrost": {"policy": policy}}
            });
            assert!(
                selected_bifrost_case(&classic, BifrostRun::Smoke),
                "the frozen smoke population still selects {policy}"
            );
            for template in CHALLENGE_TEMPLATE_IDS {
                let challenge = json!({
                    "template_id": template,
                    "tool_model_references": {"bifrost": {"policy": policy}}
                });
                assert!(
                    !selected_bifrost_case(&challenge, BifrostRun::Smoke),
                    "smoke selected challenge template {template} through {policy}"
                );
            }
        }
        // Not even a declared capability exclusion re-admits one: the smoke
        // selector short-circuits on `unsupported_reason`, and the challenge
        // refusal is checked first.
        let unsupported = json!({
            "template_id": "dfb-template-chal-deep-relay-chain",
            "tool_model_references": {"bifrost": {"unsupported_reason": "declared out of scope"}}
        });
        assert!(!selected_bifrost_case(&unsupported, BifrostRun::Smoke));
    }

    /// The rollout table is the one authoritative statement of each language's
    /// denominator, and it must reproduce docs/challenge-tier.md's expanded
    /// core table exactly.
    #[test]
    fn the_rollout_table_matches_the_preregistered_denominators() {
        let expanded: BTreeMap<&str, (usize, usize)> = BTreeMap::from([
            // language => (classic templates, applicable challenge templates)
            ("java", (16, 13)),
            ("javascript", (16, 13)),
            ("python", (16, 13)),
            ("typescript", (16, 13)),
            ("kotlin", (16, 13)),
            ("scala", (16, 13)),
            ("csharp", (16, 13)),
            ("go", (16, 13)),
            ("php", (16, 13)),
            ("ruby", (16, 13)),
            ("cpp", (16, 12)),
            ("c", (15, 9)),
            ("rust", (15, 12)),
        ]);
        assert_eq!(CHALLENGE_ROLLOUT.len(), expanded.len());
        for row in &CHALLENGE_ROLLOUT {
            let (classic, challenge) = expanded[row.language];
            assert_eq!(row.classic.len(), classic, "{} classic", row.language);
            assert_eq!(row.challenge.len(), challenge, "{} challenge", row.language);
            // Every challenge cell is one of the thirteen preregistered
            // templates; a language can narrow the set, never invent one.
            for template in row.challenge {
                assert!(
                    CHALLENGE_TEMPLATE_IDS.contains(template),
                    "{} claims unpreregistered template {template}",
                    row.language
                );
                assert!(template.starts_with(CHALLENGE_TEMPLATE_PREFIX));
            }
            // Python, JavaScript, Java, and C# are the waves that have landed
            // their fixtures; every other language validates against its
            // classic set alone, so a language whose fixtures do not exist yet
            // is never failed for missing them.
            let rolled_out = matches!(row.language, "python" | "javascript" | "java" | "csharp");
            assert_eq!(
                challenge_rolled_out(row.language),
                rolled_out,
                "{} rollout state",
                row.language
            );
            let expected = if rolled_out {
                classic + challenge
            } else {
                classic
            };
            assert_eq!(row.expected_templates().len(), expected);
            assert_eq!(expected_core_case_count(row.language), 2 * expected);
            // Flipping the row is the whole of a wave PR's validator change.
            let flipped = ChallengeRollout {
                language: row.language,
                display: row.display,
                classic: row.classic,
                challenge: row.challenge,
                rolled_out: true,
            };
            assert_eq!(
                flipped.expected_templates().len(),
                classic + challenge,
                "{} expanded core",
                row.language
            );
        }
        // The exclusions docs/challenge-tier.md states, by name.
        let cpp = challenge_rollout("cpp").unwrap().challenge;
        let rust = challenge_rollout("rust").unwrap().challenge;
        let c = challenge_rollout("c").unwrap().challenge;
        for set in [cpp, rust, c] {
            assert!(!set.contains(&"dfb-template-chal-reflective-invocation"));
        }
        for excluded in [
            "dfb-template-chal-computed-property",
            "dfb-template-chal-closure-capture",
            "dfb-template-chal-anonymous-implementation",
        ] {
            assert!(!c.contains(&excluded), "C must exclude {excluded}");
        }
    }

    /// The dedicated Java and JavaScript Bifrost kernels own their language's
    /// whole core population, accept the frozen per-case policies, and pin the
    /// language-qualified policy for the run.
    #[test]
    fn java_and_javascript_bifrost_kernels_own_their_language_population() {
        let mut java = 0usize;
        let mut javascript = 0usize;
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            if selected_bifrost_case(&case, BifrostRun::JavaKernel) {
                java += 1;
                assert_eq!(case["language"], "java");
                assert_eq!(case["score_tier"], "core");
                assert_eq!(
                    bifrost_policy_for(&case, BifrostRun::JavaKernel).unwrap(),
                    BIFROST_JAVA_POLICY
                );
                assert!(!selected_bifrost_case(&case, BifrostRun::JavascriptKernel));
            }
            if selected_bifrost_case(&case, BifrostRun::JavascriptKernel) {
                javascript += 1;
                assert_eq!(case["language"], "javascript");
                assert_eq!(case["score_tier"], "core");
                assert_eq!(
                    bifrost_policy_for(&case, BifrostRun::JavascriptKernel).unwrap(),
                    BIFROST_JAVASCRIPT_POLICY
                );
                assert!(!selected_bifrost_case(&case, BifrostRun::JavaKernel));
            }
        }
        assert_eq!(java, expected_core_case_count("java"));
        assert_eq!(javascript, expected_core_case_count("javascript"));
        // Both rows are rolled out, so both kernels are the expanded 58.
        assert_eq!(java, 58);
        assert_eq!(javascript, 58);
        assert_eq!(
            BifrostRun::JavaKernel.expected_core_cases(),
            Some(expected_core_case_count("java"))
        );
        assert_eq!(
            BifrostRun::JavascriptKernel.expected_core_cases(),
            Some(expected_core_case_count("javascript"))
        );
        // The frozen direct-propagation pair keeps its historical single
        // assertion policies and is still part of the Java kernel population.
        for policy in [
            BIFROST_DIRECT_POSITIVE_POLICY,
            BIFROST_EXPLICIT_NEGATIVE_POLICY,
        ] {
            let frozen = json!({
                "language": "java",
                "track": "taint",
                "score_tier": "core",
                "template_id": "dfb-template-direct-propagation",
                "tool_model_references": {"bifrost": {"policy": policy}}
            });
            assert!(selected_bifrost_case(&frozen, BifrostRun::JavaKernel));
            assert_eq!(
                bifrost_policy_for(&frozen, BifrostRun::JavaKernel).unwrap(),
                BIFROST_JAVA_POLICY
            );
        }
        // A challenge case joins its language kernel as soon as it exists, and
        // the run's expected count follows the rollout row rather than a
        // hard-coded 32.
        let challenge = json!({
            "language": "javascript",
            "track": "taint",
            "score_tier": "core",
            "template_id": "dfb-template-chal-dispatch-table",
            "tool_model_references": {"bifrost": {"policy": BIFROST_JAVASCRIPT_POLICY}}
        });
        assert!(selected_bifrost_case(
            &challenge,
            BifrostRun::JavascriptKernel
        ));
        assert!(!selected_bifrost_case(&challenge, BifrostRun::Smoke));
    }

    /// The Semgrep CE partition for the challenge tier is preregistered by
    /// template ID and decided from the pinned distribution's documentation. It
    /// must cover all thirteen templates, and no fixture's `feature_tags` may
    /// move a challenge case into the scored partition after the fact.
    #[test]
    fn the_challenge_semgrep_partition_is_preregistered_and_tag_proof() {
        assert_eq!(
            CHALLENGE_SEMGREP_PARTITION.len(),
            CHALLENGE_TEMPLATE_IDS.len()
        );
        for template in CHALLENGE_TEMPLATE_IDS {
            let reason = challenge_semgrep_exclusion(template)
                .unwrap_or_else(|| panic!("{template} has no preregistered CE decision"));
            assert!(!reason.is_empty());
            // Even tagged as a purely local flow, the case stays outside the
            // scored partition: the decision is the document's, not the
            // fixture's.
            let case = json!({
                "template_id": template,
                "feature_tags": ["intraprocedural"],
                "expected_analysis_capability": {"kind": "recursive-carry-taint"}
            });
            let exclusion = semgrep_capability_exclusion(&case)
                .unwrap_or_else(|| panic!("{template} was scored by the CE partition"));
            assert!(exclusion.contains("outside the bounded Semgrep CE profile"));
            assert!(exclusion.contains(reason));
        }
        // The classic partition is untouched: the seven intraprocedural
        // templates stay scored and the heap and interprocedural ones stay
        // excluded.
        let classic_scored = json!({
            "template_id": "dfb-template-direct-propagation",
            "feature_tags": ["intraprocedural"],
            "expected_analysis_capability": {"kind": "intraprocedural-taint"}
        });
        assert!(semgrep_capability_exclusion(&classic_scored).is_none());
        let classic_excluded = json!({
            "template_id": "dfb-template-same-object-field-separation",
            "feature_tags": ["heap-access-path"],
            "expected_analysis_capability": {"kind": "heap-field-sensitive-taint"}
        });
        assert!(semgrep_capability_exclusion(&classic_excluded).is_some());
    }
    /// A failed Bifrost run is an execution error even under exit status 2;
    /// this must match `raw_special_outcome` so a freeze can bind the report.
    #[test]
    fn failed_bifrost_completion_normalizes_to_runner_error_despite_status_2() {
        let case = json!({"expected_flows": []});
        let raw = json!({
            "runs": [{
                "completion": {"type": "failed", "reasons": ["internal_invariant"]},
                "diagnostics": []
            }]
        });
        let (outcome, _, _) = normalize_bifrost(&case, &raw, Some(2)).unwrap();
        assert_eq!(outcome, "runner-error");
        assert_eq!(raw_special_outcome(&raw), Some("runner-error"));

        let inconclusive = json!({
            "runs": [
                {"completion": {"type": "inconclusive"}, "diagnostics": []},
                {"completion": {"type": "failed"}, "diagnostics": []}
            ]
        });
        let (outcome, _, _) = normalize_bifrost(&case, &inconclusive, Some(2)).unwrap();
        assert_eq!(outcome, "inconclusive");
        assert_eq!(raw_special_outcome(&inconclusive), Some("inconclusive"));
    }
}
