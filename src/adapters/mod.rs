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
use crate::runtime::command_output;
use anyhow::{Context, Result, bail};
use std::{path::Path, path::PathBuf, process::Command};

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
            Self::Bifrost => "Bifrost v0.10.8",
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
pub(crate) fn witness_tool_identity(tool: ModelingTool, binary: &Path) -> Result<(String, String)> {
    match tool {
        ModelingTool::Bifrost => Ok((
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
