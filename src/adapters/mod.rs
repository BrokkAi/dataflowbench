//! The adapter contract.
//!
//! One module per analyzer. Each owns its pinned identity, its committed
//! configuration, its case selection, its invocation, and the normalization of
//! its own retained evidence — and nothing else owns any of that. What is
//! genuinely uniform across all eight lives here:
//!
//! - [`ToolIdentity`] — the witnessed `(tool_version, tool_build_identity)`
//!   pair every normalized report carries.
//! - [`KernelPopulation`] — the identity of one scored population: its
//!   language, its report and raw-evidence roots, its scored template set, and
//!   the predicate that decides which canonical cases belong to it.
//! - [`select_kernel_cases`] — the shared selection, which revalidates the
//!   expected balanced denominator so an omitted template cannot hide in a
//!   smaller subset.
//! - [`normalized_report`] — the report envelope, identical for every adapter
//!   and every tier.
//!
//! Everything else is deliberately left bespoke. An analyzer's invocation, its
//! workspace materialization, and its outcome normalization are where the
//! adapter contract's real obligations live (docs/adapters.md), and forcing
//! them behind a shared abstraction would hide the guards rather than
//! enforce them.

pub(crate) mod bifrost;
pub(crate) mod codeql;
pub(crate) mod flowdroid;
pub(crate) mod infer;
pub(crate) mod joern;
pub(crate) mod opentaint;
pub(crate) mod pysa;
pub(crate) mod semgrep;

use crate::adapters::codeql::codeql_version_identity;
use crate::adapters::flowdroid::FLOWDROID_MODELING_SUMMARIES_DIR;
use crate::adapters::infer::witness_infer_identity;
use crate::adapters::joern::joern_version_identity;
use crate::adapters::semgrep::semgrep_version_identity;
use crate::cases::{LoadedCases, case_paths, validate_kernel_population_with};
use crate::report::ADAPTER_VERSION;
use crate::runtime::{command_output, now_seconds, witnessed_version_line};
use crate::templates::expected_core_templates;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command};

/// The four adapters the preregistration partitions, plus the adapters that
/// joined later, each by a dated amendment with its own partition row, never
/// by inheriting another's. Infer joined by Amendment A13 with a
/// field-evaluated row (`reports/raw/amendment-a13-infer-partition/`);
/// FlowDroid joined by Amendment A18 on retained probe evidence
/// (`reports/raw/load-bearing-java-modeling/flowdroid-*.json`), and like
/// Infer its row applies to Java alone — the analyzer consumes JVM bytecode,
/// so the other modeling languages are outside its reach entirely, which is
/// different from being declined. OpenTaint joined by Amendments A22 and
/// A23, likewise decided by execution before its first modeling or native
/// run (`reports/raw/opentaint-modeling-surface-probe/`).
#[derive(Clone, Copy, PartialEq, Eq, Debug, clap::ValueEnum)]
pub(crate) enum ModelingTool {
    Bifrost,
    Codeql,
    Flowdroid,
    Infer,
    Joern,
    Semgrep,
    Pysa,
    Opentaint,
}

impl ModelingTool {
    /// Every adapter the partitions cover, in a fixed display order. A slice
    /// rather than a fixed-size array so that a new adapter's arrival is one
    /// appended line with no length literal to race other pull requests for.
    pub(crate) const ALL: &'static [Self] = &[
        Self::Bifrost,
        Self::Codeql,
        Self::Flowdroid,
        Self::Infer,
        Self::Joern,
        Self::Semgrep,
        Self::Pysa,
        Self::Opentaint,
    ];

    /// The `tool` value the normalized report carries, and the first component
    /// of the report and raw-evidence paths.
    pub(crate) fn key(self) -> &'static str {
        match self {
            Self::Bifrost => "bifrost",
            Self::Codeql => "codeql",
            Self::Flowdroid => "flowdroid",
            Self::Infer => "infer",
            Self::Joern => "joern",
            Self::Semgrep => "semgrep",
            Self::Pysa => "pysa",
            Self::Opentaint => "opentaint",
        }
    }

    /// The pinned identity the partition was decided against, quoted from the
    /// document's table headings so a version drift is visible in the message.
    ///
    /// This is a **document** reference, not a measurement, and it is used only
    /// where the runner is talking about the preregistration — a fail-fast
    /// error that names the tool a document decided a cell for. It must never
    /// reach a report field or a retained rationale: those name the identity
    /// the run *witnessed* from the binary
    /// ([`witness_tool_identity`]), because a constant cannot witness a
    /// version. A run that asserted its own version would keep publishing
    /// `v0.10.8` after the pin moved, which is precisely the corruption a
    /// freeze cannot survive.
    pub(crate) fn pinned_identity(self) -> &'static str {
        match self {
            Self::Bifrost => "Bifrost v0.10.9",
            Self::Codeql => "CodeQL CLI 2.26.4",
            Self::Flowdroid => "FlowDroid 2.15.1",
            Self::Infer => "Infer v1.3.0",
            Self::Joern => "Joern 4.0.614",
            Self::Semgrep => "Semgrep CE 1.175.0",
            Self::Pysa => "Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0)",
            Self::Opentaint => "OpenTaint analyzer/2026.08.27.17eb0fe",
        }
    }
}

/// The three languages wave M1 rolls the matrix out to. No other language has a
/// modeling denominator until the applicability pass the preregistration
/// describes merges — which is different from having a zero.
#[derive(Clone, Copy, PartialEq, Eq, Debug, clap::ValueEnum)]
pub(crate) enum ModelingLanguage {
    Java,
    Javascript,
    Python,
}

impl ModelingLanguage {
    pub(crate) fn key(self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::Javascript => "javascript",
            Self::Python => "python",
        }
    }

    pub(crate) fn display_name(self) -> &'static str {
        match self {
            Self::Java => "Java",
            Self::Javascript => "JavaScript",
            Self::Python => "Python",
        }
    }

    /// The population label validation errors are reported under.
    pub(crate) fn label(self) -> String {
        format!("{} modeling population", self.display_name())
    }

    /// The three languages the modeling and tool-native profiles cover in v1,
    /// resolved from a case's `language` field. Any other language has no
    /// modeling denominator at all, which is different from having a zero.
    pub(crate) fn from_key(key: &str) -> Option<Self> {
        [Self::Java, Self::Javascript, Self::Python]
            .into_iter()
            .find(|language| language.key() == key)
    }

    /// The per-language modeling artifact this tool encodes its declarations
    /// in. One artifact per tool per language, hash-bound into the report's
    /// `configuration_hash` the way every existing adapter artifact is.
    ///
    /// The CodeQL path departs from the preregistration's schematic
    /// `adapters/codeql/queries/<Language>Modeling.ql` and sits inside that
    /// language's existing `qlpack`, because a query outside a pack cannot
    /// resolve its `codeql/<lang>-all` dependency. That is a location, not a
    /// declaration surface: the document's `ConfigSig` encoding is unchanged.
    ///
    /// Java is the one language for which "that language's existing qlpack" is
    /// the adapter *root*: `adapters/codeql/qlpack.yml` declares
    /// `dataflowbench/codeql-java` with the `codeql/java-all` dependency, and
    /// `adapters/codeql/queries/JavaKernel.ql` already sits beside it. No
    /// `adapters/codeql/java/` pack exists to descend into, so a query placed
    /// under one would resolve no dependency at all. Java therefore lands on
    /// the schematic path, by the same rule that moved the other two off it.
    ///
    /// `None` means the tool has **no modeling denominator** for this language
    /// at all — which is different from having a zero, and different from a
    /// missing artifact (a hard error). Infer's pinned distribution executes
    /// no JavaScript or Python frontend, so its modeling row exists for Java
    /// alone (Amendment A13); OpenTaint analyzes JVM bytecode only, so the
    /// same holds for it (Amendment A18); and Pysa's modeling row exists for
    /// Python alone (Amendment A16).
    pub(crate) fn artifact(self, tool: ModelingTool) -> Option<&'static str> {
        match (tool, self) {
            (ModelingTool::Opentaint, Self::Java) => {
                Some("adapters/opentaint/rules/model-java.yaml")
            }
            (ModelingTool::Opentaint, Self::Javascript | Self::Python) => None,
            (ModelingTool::Bifrost, Self::Java) => {
                Some("adapters/bifrost/policies/model-java.rqlp")
            }
            (ModelingTool::Bifrost, Self::Javascript) => {
                Some("adapters/bifrost/policies/model-javascript.rqlp")
            }
            (ModelingTool::Bifrost, Self::Python) => {
                Some("adapters/bifrost/policies/model-python.rqlp")
            }
            (ModelingTool::Codeql, Self::Java) => Some("adapters/codeql/queries/JavaModeling.ql"),
            (ModelingTool::Codeql, Self::Javascript) => {
                Some("adapters/codeql/javascript/queries/JavaScriptModeling.ql")
            }
            (ModelingTool::Codeql, Self::Python) => {
                Some("adapters/codeql/python/queries/PythonModeling.ql")
            }
            (ModelingTool::Infer, Self::Java) => Some("adapters/infer/config/model-java.json"),
            (ModelingTool::Infer, Self::Javascript | Self::Python) => None,
            // FlowDroid's artifact is a StubDroid summaries *directory* (one
            // XML per declared fixture type); the three files inside it bind
            // the configuration hash individually, because a directory has no
            // bytes to hash. Java only, like Infer's, and for the same
            // bytecode-reach reason (Amendment A18).
            (ModelingTool::Flowdroid, Self::Java) => Some(FLOWDROID_MODELING_SUMMARIES_DIR),
            (ModelingTool::Flowdroid, Self::Javascript | Self::Python) => None,
            // Pysa analyzes Python alone, so its modeling row exists for
            // Python alone (Amendment A16).
            (ModelingTool::Pysa, Self::Python) => Some("adapters/pysa/models/modeling-python.pysa"),
            (ModelingTool::Pysa, Self::Java | Self::Javascript) => None,
            (ModelingTool::Joern, Self::Java) => {
                Some("adapters/joern/semantics/model-java.semantics")
            }
            (ModelingTool::Joern, Self::Javascript) => {
                Some("adapters/joern/semantics/model-javascript.semantics")
            }
            (ModelingTool::Joern, Self::Python) => {
                Some("adapters/joern/semantics/model-python.semantics")
            }
            (ModelingTool::Semgrep, Self::Java) => Some("adapters/semgrep/rules/model-java.yaml"),
            (ModelingTool::Semgrep, Self::Javascript) => {
                Some("adapters/semgrep/rules/model-javascript.yaml")
            }
            (ModelingTool::Semgrep, Self::Python) => {
                Some("adapters/semgrep/rules/model-python.yaml")
            }
        }
    }

    pub(crate) fn report(self, tool: ModelingTool) -> PathBuf {
        PathBuf::from(format!(
            "reports/{}-{}-modeling.json",
            tool.key(),
            self.key()
        ))
    }

    pub(crate) fn raw_dir(self, tool: ModelingTool) -> PathBuf {
        PathBuf::from(format!(
            "reports/raw/{}-{}-modeling",
            tool.key(),
            self.key()
        ))
    }
}

/// The tool identity a modeling or tool-native run records, **witnessed from
/// the binary** rather than asserted from a constant, read from the same
/// surface each adapter's kernel reports already read it from.
///
/// Called once per run, before the population is walked, and called even when
/// the run's partition declines every cell: a declined cell is decided without
/// handing a fixture to the analyzer, but the report's run-level identity is a
/// claim about which binary was pinned, and that claim has to be measured. The
/// Bifrost tool-native row is the case that makes the rule visible — it invokes
/// the analyzer over nothing at all, and it must still say truthfully which
/// build produced its twelve retained decisions.
///
/// Unlike the kernel runners, a failure to read the version is **not** softened
/// into `"unknown"`. A kernel run that loses the version still has per-case
/// evidence; a run whose every cell is a capability decision has nothing else,
/// so an unwitnessed identity there would be a report that asserts a pin it
/// never observed.
pub(crate) fn witness_tool_identity(tool: ModelingTool, binary: &Path) -> Result<ToolIdentity> {
    match tool {
        ModelingTool::Bifrost => Ok(ToolIdentity::new(
            command_output(Command::new(binary).arg("--version")).with_context(|| {
                format!(
                    "witness the pinned Bifrost version with {} --version; a modeling or tool-native report may not assert a version it could not read",
                    binary.display()
                )
            })?,
            command_output(Command::new(binary).arg("--build-identity")).with_context(|| {
                format!(
                    "witness the pinned Bifrost build identity with {} --build-identity",
                    binary.display()
                )
            })?,
        )),
        ModelingTool::Codeql => codeql_version_identity(binary),
        // The kernel witness, unchanged: it refuses a binary whose
        // self-reported version is not the pinned release, so a modeling or
        // tool-native report can never carry an asserted Infer identity.
        ModelingTool::Infer => witness_infer_identity(binary),
        // FlowDroid's identity is two digest-witnessed jars plus the version
        // its pom.properties self-reports — not a `--version` banner — so its
        // own runners witness it through `witness_flowdroid_identity` and
        // never reach this function.
        ModelingTool::Flowdroid => bail!(
            "FlowDroid's identity is witnessed from the pinned jar digests by its own runners ({}); this single-binary path cannot witness it",
            binary.display()
        ),
        // Pysa's identity is a witnessed *pair* — the pyre client, the
        // analysis binary's digest, and the Pyrefly front end — so its runs
        // witness through `witness_pysa_identity` and never arrive here.
        ModelingTool::Pysa => bail!(
            "Pysa's identity is witnessed from the pinned pair via witness_pysa_identity; a single binary path cannot name it"
        ),
        ModelingTool::Joern => joern_version_identity(binary),
        ModelingTool::Semgrep => semgrep_version_identity(binary),
        // OpenTaint's identity is not a binary's banner: the analyzer jar
        // self-reports no version at all, so its runs witness the release
        // assets' digests through `witness_opentaint_identity`, and the
        // dedicated `run-opentaint-modeling` / `run-opentaint-native`
        // commands never reach this function.
        ModelingTool::Opentaint => bail!(
            "OpenTaint witnesses its identity from the pinned release assets' digests, not from a binary banner; use run-opentaint-modeling or run-opentaint-native, which call witness_opentaint_identity"
        ),
    }
}

/// The identity of the pinned tool a run actually witnessed, as the two
/// fields every normalized report carries.
///
/// Both halves are read from the artifact the run invoked — a `--version`
/// banner, a release-asset digest, a `pom.properties` entry — never from a
/// constant in this repository, so no report can assert a version its run did
/// not observe. The two halves were a bare `(String, String)` tuple until they
/// were named here; the ordering was a standing footgun.
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct ToolIdentity {
    /// The report's `tool_version`: what the invoked artifact calls itself.
    pub(crate) version: String,
    /// The report's `tool_build_identity`: which build of that version it is —
    /// a commit, a digest, or a distribution string.
    pub(crate) build_identity: String,
}

impl ToolIdentity {
    /// Both halves as the run read them out of the artifact it invoked.
    pub(crate) fn new(version: impl Into<String>, build_identity: impl Into<String>) -> Self {
        Self {
            version: version.into(),
            build_identity: build_identity.into(),
        }
    }

    /// The same identity with `version` reduced to its banner's version line.
    ///
    /// A `--version` banner may say more than the version — Bifrost 0.10.9
    /// prints its built-in policy packs and their catalog digest beneath
    /// `bifrost 0.10.9`. The run-environment stamp retains that banner whole,
    /// so a runner reduces its identity only after stamping it, and what the
    /// report and its rationales then carry is the version alone.
    pub(crate) fn version_line_only(self) -> Self {
        Self {
            version: witnessed_version_line(&self.version).to_string(),
            build_identity: self.build_identity,
        }
    }
}

/// One scored population: a single analyzer over a single language, with its
/// own case selection, its own committed configuration, its own normalized
/// report, and its own retained-evidence root.
///
/// This is the uniform half of an adapter. The bespoke half — the invocation,
/// the workspace materialization, and the outcome normalization with its
/// anti-vacuous-negative guards — is deliberately not behind this trait: those
/// are where docs/adapters.md places an adapter's real obligations, and a
/// shared abstraction over them would hide the guards rather than enforce
/// them.
pub(crate) trait KernelPopulation {
    /// The tool key this population's normalized report carries.
    fn tool(&self) -> &'static str;

    /// The benchmark language whose core denominator this population scores.
    fn language(&self) -> &'static str;

    /// How that language is spelled in operator-facing output.
    fn display_name(&self) -> &'static str;

    /// The dedicated normalized-report path. Report paths are never shared
    /// between adapters or between languages.
    fn report(&self) -> String;

    /// The dedicated retained-evidence root, one native document per case.
    fn raw_dir(&self) -> String;

    /// The population label carried in progress output and in the balance
    /// check's diagnostics.
    fn label(&self) -> String;

    /// The committed configuration this population's `configuration_hash`
    /// covers. Some adapters read the selection to resolve it, so the
    /// selection is passed in; most ignore it.
    fn configuration_paths(&self, cases: &LoadedCases) -> Result<BTreeSet<PathBuf>>;

    /// The scored template set of this language's core denominator, read from
    /// its rollout row.
    fn templates(&self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }

    /// Whether a canonical case belongs to this population. The default is the
    /// selection every kernel uses: this language's `core` cases on the taint
    /// track. An adapter overrides it only where its population is genuinely
    /// different, never to narrow a denominator.
    fn selects(&self, case: &Value) -> bool {
        case["language"] == self.language()
            && case["track"] == "taint"
            && case["score_tier"] == "core"
    }
}

/// Select one population's cases runner-side, then revalidate the expected
/// balanced denominator.
///
/// The revalidation is the point: an omitted template cannot hide in a smaller
/// balanced subset, because the selection is checked against the template set
/// this language's rollout row declares, not against whatever it happened to
/// find.
pub(crate) fn select_kernel_cases(population: &impl KernelPopulation) -> Result<LoadedCases> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if population.selects(&case) {
            selected.push((path, case));
        }
    }
    validate_kernel_population_with(&selected, &population.label(), &population.templates())?;
    Ok(selected)
}

/// The normalized report envelope, identical for every adapter and every tier.
///
/// Everything above the results list is fixed by `schemas/result.schema.json`:
/// the witnessed identity, the adapter version, the hash of the committed
/// configuration the run used, the fixture revision it read, and the run's own
/// clock bounds.
pub(crate) fn normalized_report(
    tool: &str,
    identity: &ToolIdentity,
    configuration_hash: &str,
    fixture_revision: &str,
    started_at_unix_seconds: u64,
    results: Vec<Value>,
) -> Result<Value> {
    Ok(json!({
        "schema_version": 1,
        "tool": tool,
        "tool_version": identity.version,
        "tool_build_identity": identity.build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": fixture_revision,
        "started_at_unix_seconds": started_at_unix_seconds,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    }))
}

/// Retain one case's runner-error document.
///
/// A failed invocation is evidence, not an absence of findings: the failure is
/// written to the population's evidence root and the result points at it, so
/// `validate-reports` and the freeze digest cover it exactly as they cover a
/// native finding document. `output` carries the process diagnostics when the
/// tool ran at all, and is `None` when the failure was in reaching it.
pub(crate) fn write_runner_error(
    adapter: &str,
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let mut evidence = json!({
        "adapter": adapter,
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
