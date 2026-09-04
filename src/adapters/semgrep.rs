//! The Semgrep CE adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/semgrep/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ToolIdentity;
use crate::adapters::normalized_report;
use crate::adapters::write_runner_error;
use crate::adapters::{KernelPopulation, select_kernel_cases};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::LoadedCases;
use crate::cases::{fixture_revision, validate_cases};
use crate::evidence::{
    AnchorDialect, EvidenceAnchorMatch, SarifAnchorMatch, SinkAnchorLocation,
    benchmark_endpoint_names, evidence_path_matches_file, sink_anchor_locations,
};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, WarmBatch, load_average_one_minute,
    overhead_workspace,
};
use crate::modeling::{
    ModelingRunPlan, materialize_modeling_workspace, modeling_anchor_dialect, modeling_case_scratch,
};
use crate::native::{
    NativeRunPlan, native_anchor_tally_outcome, native_case_scratch, native_sink_anchor_locations,
};
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, now_seconds, write_case_phase_timings, write_run_environment,
};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Instant};

/// The committed, benchmark-controlled Semgrep CE taint rules. One rule file
/// per covered language; each carries the two `__DFB_SOURCE__`/`__DFB_SINK__`
/// placeholders the runner resolves from the case's own marker lines. Every
/// Semgrep report hashes this whole directory, so no report can cite a
/// configuration hash that any committed rule no longer has.
pub(crate) const SEMGREP_RULES_DIR: &str = "adapters/semgrep/rules";
/// The placeholder tokens in a committed rule file. Nothing else is templated.
pub(crate) const SEMGREP_SOURCE_PLACEHOLDER: &str = "__DFB_SOURCE__";
pub(crate) const SEMGREP_SINK_PLACEHOLDER: &str = "__DFB_SINK__";
/// The Semgrep rule option that makes a modeling declaration load-bearing.
/// Verified against the pinned CE 1.174.0: with no propagator declared, a
/// taint-mode rule still reports `dfb_sink(prop("clean", t))`; setting this
/// option removes that default and the finding disappears.
pub(crate) const SEMGREP_MODELING_ASSUME_SAFE_OPTION: &str = "taint_assume_safe_functions: true";

/// Enforce the load-bearing-model requirement on a Semgrep modeling rule.
pub(crate) fn require_semgrep_modeling_load_bearing(rule: &str, path: &str) -> Result<()> {
    if !rule.contains(SEMGREP_MODELING_ASSUME_SAFE_OPTION) {
        bail!(
            "{path} does not set `options: {SEMGREP_MODELING_ASSUME_SAFE_OPTION}`; without it the pinned CE engine carries taint from any tainted argument to a call's result and the declared model is not what decides the cell (docs/modeling-matrix.md#the-load-bearing-model-requirement)"
        );
    }
    Ok(())
}

/// Where a language's pinned snapshot of the official Semgrep rulesets is
/// vendored. Registry configurations are network-fetched and unpinnable at run
/// time, so the native profile vendors instead of fetching.
pub(crate) fn semgrep_native_rules_dir(language: ModelingLanguage) -> PathBuf {
    PathBuf::from(format!("adapters/semgrep/native/{}", language.key()))
}

/// The provenance document a vendored snapshot must carry. A snapshot with no
/// recorded source commit is not a snapshot; the runner refuses the run.
pub(crate) const SEMGREP_NATIVE_PROVENANCE_FILE: &str = "provenance.json";

/// The upstream the snapshots are taken from, verified 2026-08-27 (default
/// branch `develop`). The wave PR pins whichever commit it vendors.
pub(crate) const SEMGREP_NATIVE_UPSTREAM: &str = "https://github.com/semgrep/semgrep-rules";

/// One Semgrep CE kernel: a single language, its own case selection, its own
/// committed rule file, its own normalized report, and its own
/// retained-evidence root. Semgrep shares one taint engine across all of them,
/// exactly as Joern shares one data-flow engine; the populations are kept apart
/// by the selector and the report paths, never by the engine.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SemgrepKernel {
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
    /// The maturity the pinned distribution records for this kernel's Semgrep
    /// language in its own `semgrep_interfaces/lang.json`. It is retained
    /// verbatim in the adapter README and in every capability-decision
    /// document, exactly as the CodeQL Rust kernel retains that extractor's
    /// preview status. A maturity label is a property of the front end, never
    /// a reason to move a case between the scored and `unsupported`
    /// partitions.
    pub(crate) fn documented_maturity(self) -> &'static str {
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

    /// The committed rule file for this kernel. Each is its own file even
    /// where two would be byte-identical apart from the `languages:` key, so a
    /// population is never scored by a rule spelled for another language.
    pub(crate) fn rule(self) -> String {
        format!("{SEMGREP_RULES_DIR}/{}.yaml", self.language())
    }

    pub(crate) fn dialect(self) -> AnchorDialect {
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
}

/// Semgrep's populations over the shared contract. One taint engine stands
/// behind all eleven; the selector and the dedicated report and evidence roots
/// are what keep them apart.
///
/// The scored template set is the language's rollout row, so C and Rust — whose
/// exception-catch cell docs/applicability-matrix.md classifies as inapplicable
/// — have a fifteen-template, thirty-assertion classic core and every other
/// kernel has the full sixteen. Selection expands with the row; what is
/// *scored* is decided separately, per case, by `semgrep_capability_exclusion`.
impl KernelPopulation for SemgrepKernel {
    fn tool(&self) -> &'static str {
        "semgrep"
    }

    fn language(&self) -> &'static str {
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

    fn display_name(&self) -> &'static str {
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

    fn report(&self) -> String {
        format!("reports/semgrep-{}-kernel.json", self.language())
    }

    fn raw_dir(&self) -> String {
        format!("reports/raw/semgrep-{}-kernel", self.language())
    }

    fn label(&self) -> String {
        format!("Semgrep {} kernel", self.display_name())
    }

    /// Every committed kernel rule, so one hash binds the whole set: a
    /// population is never scored under a rule file that changed without the
    /// report's `configuration_hash` moving with it.
    fn configuration_paths(&self, _cases: &LoadedCases) -> Result<BTreeSet<PathBuf>> {
        semgrep_rule_paths()
    }
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
pub(crate) fn select_semgrep_cases(kernel: SemgrepKernel) -> Result<LoadedCases> {
    select_kernel_cases(&kernel)
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
pub(crate) const CHALLENGE_SEMGREP_PARTITION: [(&str, &str); 13] = [
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
pub(crate) fn challenge_semgrep_exclusion(template: &str) -> Option<&'static str> {
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
pub(crate) fn semgrep_capability_exclusion(case: &Value) -> Option<String> {
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
pub(crate) fn semgrep_maturity_diagnostic(kernel: SemgrepKernel) -> String {
    format!(
        "pinned Semgrep CE records the {} front end's maturity as {:?} (semgrep_interfaces/lang.json `maturity`); the label describes the parser, not the scored partition",
        kernel.display_name(),
        kernel.documented_maturity()
    )
}

pub(crate) fn run_semgrep_kernel(binary: &Path, kernel: SemgrepKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_semgrep_cases(kernel)?;
    let configuration_paths = kernel.configuration_paths(&selected)?;
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
    let identity = semgrep_version_identity(binary)?;
    write_run_environment(&raw_dir, kernel.tool(), &identity)?;
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

    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = normalized_report(
        kernel.tool(),
        &identity,
        &configuration_hash,
        &revision,
        started,
        results,
    )?;
    let report_path = kernel.report();
    write_and_validate_report(Path::new(&report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

/// The prefix a Semgrep **modeling** artifact carries. A modeling rule lives
/// beside the kernel rules but belongs to a different population, so it is
/// excluded from the kernel configuration hash below.
pub(crate) const SEMGREP_MODELING_RULE_PREFIX: &str = "model-";

/// Every committed Semgrep **kernel** rule file, so one `configuration_hash`
/// binds the whole kernel rule set rather than only the language that happened
/// to run.
///
/// Modeling rules are deliberately excluded. The kernel hash is a statement
/// about the kernel configuration, and the modeling matrix is its own
/// population with its own artifact, its own report, and its own hash — which
/// `plan_modeling_run` computes over that artifact alone. Folding a modeling
/// rule in here would have made every published kernel report cite a hash that
/// no longer described the configuration it ran under, for a file no kernel
/// ever loads.
pub(crate) fn semgrep_rule_paths() -> Result<BTreeSet<PathBuf>> {
    let mut paths = BTreeSet::new();
    for entry in fs::read_dir(SEMGREP_RULES_DIR)
        .with_context(|| format!("read {SEMGREP_RULES_DIR}"))?
        .filter_map(std::result::Result::ok)
    {
        let path = entry.path();
        let modeling = path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.starts_with(SEMGREP_MODELING_RULE_PREFIX));
        if path.is_file() && !modeling && path.extension().is_some_and(|ext| ext == "yaml") {
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
pub(crate) fn semgrep_version_identity(binary: &Path) -> Result<ToolIdentity> {
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
    Ok(ToolIdentity::new(version, build_identity))
}

pub(crate) fn run_semgrep_case(
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
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [
        &raw_path,
        &error_path,
        &unsupported_path,
        &rule_path,
        &timing_path,
    ] {
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
        // One CLI invocation is indivisible from the adapter's vantage:
        // `total`, per #89. Any phase timings Semgrep emits itself ride in the
        // verbatim `--json` document retained below.
        let invoked = Instant::now();
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
        write_case_phase_timings(raw_dir, "semgrep", id, &[("total", invoked.elapsed())])?;
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

pub(crate) fn semgrep_case_scratch(kernel: SemgrepKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-semgrep-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

pub(crate) fn write_semgrep_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    write_runner_error("semgrep", raw_dir, id, stage, diagnostic, output)
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
pub(crate) fn semgrep_finding_outcome(
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
pub(crate) fn semgrep_finding_anchor_match(
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

/// Run one scored modeling cell through Semgrep CE.
///
/// Nothing is templated. The kernel rule carries endpoint placeholders because
/// the endpoint identities are a property of each fixture; here the endpoint
/// identities *are* the model, so the committed rule states them literally and
/// the runner substitutes nothing. The capability decision is the
/// preregistered partition's, made before this function is reached, so the
/// kernel's `feature_tags` rule is deliberately not consulted.
pub(crate) fn run_semgrep_modeling_case(
    binary: &Path,
    rule: &Path,
    case_path: &Path,
    case: &Value,
    plan: &ModelingRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let dialect = modeling_anchor_dialect(plan.language)?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let scratch = modeling_case_scratch(ModelingTool::Semgrep, plan.language, id)?;
    let workspace = scratch.join("source");
    materialize_modeling_workspace(case_path, case, &workspace)?;

    let result = (|| {
        let mut command = Command::new(binary);
        command
            .current_dir(&scratch)
            .arg("scan")
            .arg("--metrics=off")
            .arg("--oss-only")
            .arg("--disable-version-check")
            .arg("--no-git-ignore")
            .arg("--quiet")
            .arg("--json")
            .arg("--config")
            .arg(rule)
            .arg(&workspace)
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Semgrep modeling scan with {}: {error}",
                    binary.display()
                );
                let path = write_semgrep_error(&plan.raw_dir, id, "scan-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(
            &plan.raw_dir,
            "semgrep",
            id,
            &[("total", invoked.elapsed())],
        )?;
        if !output.status.success() {
            let diagnostic = format!("Semgrep modeling scan failed with status {}", output.status);
            let path = write_semgrep_error(
                &plan.raw_dir,
                id,
                "scan-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::write(&raw_path, &output.stdout)?;
        let raw: Value = match serde_json::from_slice(&output.stdout) {
            Ok(raw) => raw,
            Err(error) => {
                let diagnostic = format!("parse Semgrep evidence {}: {error}", raw_path.display());
                let path =
                    write_semgrep_error(&plan.raw_dir, id, "scan-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (outcome, diagnostics) = semgrep_finding_outcome(case_path, case, &raw, dialect);
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

/// Run one *scored* native cell through Semgrep CE over the vendored snapshot.
///
/// Two deliberate differences from the benchmark-controlled Semgrep runner, both
/// recorded in docs/native-profile.md#semgrep-ce--11760---oss-only:
/// `--config` points at the vendored rule directory rather than at an authored
/// rule, and `taint_assume_safe_functions` is **not** set. There the permissive
/// default would decide a cell the supplied model was meant to decide; here the
/// default is the product.
///
/// This arm exists because Amendment A8 promoted all six Semgrep CE × Python
/// cells to scored. It is not a second reconciler: the outcome is decided by
/// `native_anchor_tally_outcome`, the same rule the CodeQL arm reaches.
pub(crate) fn run_semgrep_native_case(
    binary: &Path,
    case_path: &Path,
    case: &Value,
    plan: &NativeRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "tool-native case")?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }
    let rules = fs::canonicalize(semgrep_native_rules_dir(plan.language))
        .context("resolve the vendored Semgrep native rule directory")?;
    let scratch = native_case_scratch(ModelingTool::Semgrep, plan.language, id)?;
    let workspace = scratch.join("source");
    materialize_modeling_workspace(case_path, case, &workspace)?;

    let result = (|| {
        let mut command = Command::new(binary);
        command
            .current_dir(&scratch)
            .arg("scan")
            .arg("--metrics=off")
            .arg("--oss-only")
            .arg("--disable-version-check")
            .arg("--no-git-ignore")
            .arg("--quiet")
            .arg("--json")
            .arg(format!("--config={}", rules.display()))
            .arg(&workspace)
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Semgrep tool-native scan with {}: {error}",
                    binary.display()
                );
                let path = write_semgrep_error(&plan.raw_dir, id, "scan-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(
            &plan.raw_dir,
            "semgrep",
            id,
            &[("total", invoked.elapsed())],
        )?;
        if !output.status.success() {
            let diagnostic = format!(
                "Semgrep tool-native scan failed with status {}",
                output.status
            );
            let path = write_semgrep_error(
                &plan.raw_dir,
                id,
                "scan-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::write(&raw_path, &output.stdout)?;
        let raw: Value = match serde_json::from_slice(&output.stdout) {
            Ok(raw) => raw,
            Err(error) => {
                let diagnostic = format!("parse Semgrep evidence {}: {error}", raw_path.display());
                let path =
                    write_semgrep_error(&plan.raw_dir, id, "scan-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (outcome, diagnostics) = native_semgrep_outcome(case_path, case, &raw);
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

/// Where one Semgrep finding landed, relative to the case's sink anchors.
///
/// Semgrep reports a flat `path` and `start.line` where SARIF reports a
/// `locations` array, so the extraction differs; the *classification* is the
/// SARIF one, in the same three-valued vocabulary, so both arms tally through
/// `native_anchor_tally_outcome`.
pub(crate) fn semgrep_result_anchor_match(
    result: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> SarifAnchorMatch {
    let (Some(uri), Some(line)) = (result["path"].as_str(), result["start"]["line"].as_u64())
    else {
        return SarifAnchorMatch::Ambiguous;
    };
    if line == 0 {
        return SarifAnchorMatch::Ambiguous;
    }
    let matches: BTreeSet<usize> = sink_locations
        .iter()
        .enumerate()
        .filter(|(_, anchor)| {
            evidence_path_matches_file(uri, &anchor.file) && anchor.callsite_lines.contains(&line)
        })
        .map(|(index, _)| index)
        .collect();
    match matches.len() {
        0 => SarifAnchorMatch::Unmatched,
        1 => SarifAnchorMatch::Matched,
        _ => SarifAnchorMatch::Ambiguous,
    }
}

/// Normalize one Semgrep tool-native scan against the case's sink anchors.
pub(crate) fn native_semgrep_outcome(
    case_path: &Path,
    case: &Value,
    raw: &Value,
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
    // A vendored rule Semgrep declined to run produces no finding for a reason
    // that has nothing to do with the program, so it must not read as coverage.
    if raw["skipped_rules"]
        .as_array()
        .is_some_and(|skipped| !skipped.is_empty())
    {
        return (
            "runner-error",
            vec!["Semgrep skipped a vendored tool-native rule".to_string()],
        );
    }
    if raw["paths"]["scanned"]
        .as_array()
        .map(|paths| paths.len())
        .unwrap_or_default()
        == 0
    {
        return (
            "inconclusive",
            vec!["Semgrep scanned no target; the run never analyzed the case fixture".to_string()],
        );
    }
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
    let sink_locations = match native_sink_anchor_locations(case_path, case) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove Semgrep finding against the native sink anchor: {reason}"
                )],
            );
        }
    };
    native_anchor_tally_outcome(
        results
            .iter()
            .map(|result| semgrep_result_anchor_match(result, &sink_locations)),
        "Semgrep",
    )
}

/// One Semgrep batch: k case workspaces scanned by one `semgrep scan`.
pub(crate) fn measure_semgrep_warm_batch(
    binary: &Path,
    cases: &[(PathBuf, Value)],
    raw_dir: &Path,
    k: usize,
    repeat: usize,
) -> Result<WarmBatch> {
    let kernel = SemgrepKernel::Java;
    let template = fs::read_to_string(kernel.rule())?;
    let scratch = std::env::temp_dir().join(format!("dataflowbench-warm-semgrep-{repeat}-{k}"));
    if scratch.exists() {
        fs::remove_dir_all(&scratch)?;
    }
    fs::create_dir_all(&scratch)?;

    let mut rules: BTreeSet<String> = BTreeSet::new();
    let mut workspaces = Vec::new();
    let mut case_ids = Vec::new();
    for (index, (case_path, case)) in cases.iter().enumerate() {
        let id = case["id"].as_str().expect("schema validated");
        let endpoints =
            benchmark_endpoint_names(case_path, case, kernel.dialect()).map_err(|reason| {
                anyhow::anyhow!("{id}: cannot derive the Semgrep endpoints: {reason}")
            })?;
        rules.insert(
            template
                .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
                .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function),
        );
        let workspace = scratch.join(format!("source-{index}"));
        fs::create_dir_all(&workspace)?;
        let fixture_root = case_path.parent().expect("case path has parent");
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
        }
        workspaces.push(workspace);
        case_ids.push(id.to_string());
    }
    // The population filter already guarantees this; the check is here so a
    // future population change cannot silently start timing a different
    // configuration than the cold runs it is compared against.
    if rules.len() != 1 {
        bail!(
            "a Semgrep warm batch needs one resolved rule for all {k} cases; got {}",
            rules.len()
        );
    }
    let rule_path = scratch.join("rule.yaml");
    fs::write(&rule_path, rules.iter().next().expect("length checked"))?;
    let findings_path = scratch.join("findings.json");

    let mut command = Command::new(binary);
    command
        .current_dir(&scratch)
        .arg("scan")
        .arg("--metrics=off")
        .arg("--oss-only")
        .arg("--disable-version-check")
        .arg("--no-git-ignore")
        .arg("--quiet")
        .arg("--json")
        .arg("--output")
        .arg(&findings_path)
        .arg("--config")
        .arg(&rule_path)
        .args(&workspaces)
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Semgrep warm batch with {}", binary.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the Semgrep warm batch k={k} failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    let findings: Value = serde_json::from_str(&fs::read_to_string(&findings_path)?)
        .context("parse the Semgrep warm batch findings")?;
    let scanned = findings["paths"]["scanned"]
        .as_array()
        .map(Vec::len)
        .unwrap_or_default();
    if scanned < k {
        bail!("the Semgrep warm batch k={k} scanned only {scanned} files");
    }
    fs::write(
        raw_dir.join(format!("run-{repeat}-batch-{k}-findings.json")),
        serde_json::to_string_pretty(&findings)? + "\n",
    )?;
    fs::remove_dir_all(&scratch).ok();
    Ok(WarmBatch {
        k,
        wall_ms,
        case_ids,
        load_before,
    })
}

/// Semgrep: the committed rule for the language, resolved against the trivial
/// fixture's own endpoint names, and the same scan flags the cold runner uses.
pub(crate) fn overhead_run_semgrep(
    binary: &Path,
    language: OverheadLanguage,
    run: usize,
    raw_dir: &Path,
) -> Result<OverheadRun> {
    let kernel = match language {
        OverheadLanguage::Kotlin => SemgrepKernel::Kotlin,
        OverheadLanguage::Java => SemgrepKernel::Java,
        other => bail!("no Semgrep overhead arm for {}", other.as_str()),
    };
    let rule = fs::read_to_string(kernel.rule())?
        .replace(SEMGREP_SOURCE_PLACEHOLDER, "dfb_source")
        .replace(SEMGREP_SINK_PLACEHOLDER, "dfb_sink");
    let (scratch, workspace) = overhead_workspace(OverheadTool::Semgrep, language, run)?;
    let rule_path = scratch.join("rule.yaml");
    fs::write(&rule_path, &rule)?;
    // The resolved rule is retained beside the artifact, exactly as the cold
    // runner retains one beside each case's finding document.
    fs::write(raw_dir.join("resolved-rule.yaml"), &rule)?;
    let findings = scratch.join("findings.json");

    let mut command = Command::new(binary);
    command
        .current_dir(&scratch)
        .arg("scan")
        .arg("--metrics=off")
        .arg("--oss-only")
        .arg("--disable-version-check")
        .arg("--no-git-ignore")
        .arg("--quiet")
        .arg("--json")
        .arg("--output")
        .arg(&findings)
        .arg("--config")
        .arg(&rule_path)
        .arg(&workspace)
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Semgrep scan with {}", binary.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the Semgrep overhead invocation failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before,
    })
}
