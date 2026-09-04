//! DataFlowBench: an analyzer-neutral benchmark for data-flow analysis.
//!
//! This file is the command surface only — the `dataflowbench` subcommands and
//! their dispatch. Everything a subcommand does lives in a module:
//!
//! - [`cases`] and [`templates`] — the canonical cases and the preregistered
//!   template identities every scored population is built from.
//! - [`adapters`] — one module per analyzer integration, over a shared
//!   contract in `adapters/mod.rs`.
//! - [`modeling`], [`native`], [`latency`] — the three tiers that run beside
//!   the core kernels.
//! - [`report`], [`freeze`], [`results`] — the normalized report, the
//!   immutable evidence manifest, and byte-stable result generation.
//! - [`real_project`] — the preregistered real-project confirmation slice.
//! - [`evidence`] and [`runtime`] — anchor reconciliation and the process,
//!   timing, and environment plumbing every adapter shares.

mod adapters;
mod cases;
mod evidence;
mod freeze;
mod latency;
mod modeling;
mod native;
mod real_project;
mod report;
mod results;
mod runtime;
mod templates;
#[cfg(test)]
mod tests;

use crate::adapters::bifrost::{
    BifrostRun, run_bifrost, run_bifrost_csharp_kernel, run_bifrost_kotlin_kernel,
    run_bifrost_python_kernel, run_bifrost_smoke,
};
use crate::adapters::codeql::{
    CFamilyKernel, EcmaKernel, run_codeql_c_family_kernel, run_codeql_csharp_kernel,
    run_codeql_ecma_kernel, run_codeql_go_kernel, run_codeql_java_kernel, run_codeql_kotlin_kernel,
    run_codeql_python_kernel, run_codeql_ruby_kernel, run_codeql_rust_kernel,
};
use crate::adapters::flowdroid::{
    FlowdroidKernel, FlowdroidTools, run_flowdroid_kernel, run_flowdroid_modeling,
    run_flowdroid_native,
};
use crate::adapters::infer::{InferKernel, run_infer_kernel};
use crate::adapters::joern::{JoernKernel, run_joern_kernel};
use crate::adapters::opentaint::{
    OpentaintKernel, run_opentaint_kernel, run_opentaint_modeling, run_opentaint_native,
};
use crate::adapters::pysa::{
    PysaTools, run_pysa_modeling, run_pysa_native, run_pysa_python_kernel,
};
use crate::adapters::semgrep::{SemgrepKernel, run_semgrep_kernel};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::validate_cases;
use crate::freeze::{create_freeze, validate_freeze};
use crate::latency::{
    OverheadLanguage, OverheadTool, OverheadTools, WarmLanguage, WarmTool,
    estimate_invocation_overhead, measure_warm_latency,
};
use crate::modeling::run_modeling;
use crate::native::run_native;
use crate::report::validate_reports;
use crate::results::generate_results;
use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

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
    /// Run the Java propagation kernel through the pinned OpenTaint analyzer.
    /// Fixtures are compiled per case with `javac` (a harness step, per the
    /// timing convention) and analyzed as bytecode; the analyzer jar and
    /// models archive are the exact release assets the pin names, verified by
    /// witnessed digest before any case runs.
    RunOpentaintJavaKernel {
        /// Path to the pinned `opentaint-project-analyzer.jar` release asset.
        #[arg(long)]
        analyzer_jar: PathBuf,
        /// Path to the pinned `opentaint-models.tar.gz` release asset.
        #[arg(long)]
        models_archive: PathBuf,
        /// Java runtime that executes the analyzer jar.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Java compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run the Kotlin propagation kernel through the pinned OpenTaint
    /// analyzer. Fixtures are compiled per case with `kotlinc` and analyzed as
    /// bytecode with `kotlin-stdlib.jar` on the analysis dependency path.
    RunOpentaintKotlinKernel {
        /// Path to the pinned `opentaint-project-analyzer.jar` release asset.
        #[arg(long)]
        analyzer_jar: PathBuf,
        /// Path to the pinned `opentaint-models.tar.gz` release asset.
        #[arg(long)]
        models_archive: PathBuf,
        /// Java runtime that executes the analyzer jar.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Kotlin compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "kotlinc")]
        kotlinc: PathBuf,
        /// `kotlin-stdlib.jar` handed to the analyzer as the fixtures'
        /// dependency, so stdlib calls resolve instead of dangling.
        #[arg(long)]
        kotlin_stdlib: PathBuf,
    },
    /// Run the Java propagation kernel through the pinned FlowDroid release's
    /// command-line analyzer. The released CLI analyzes APKs only, so each
    /// case materializes a minimal APK — compiled fixtures, a harness
    /// activity calling the fixture's entry method, a committed binary
    /// manifest, and a D8 dex translation — all harness plumbing, per the
    /// timing convention. The jar's embedded version and the digests of the
    /// jar and platform jar are witnessed before any case runs.
    RunFlowdroidJavaKernel {
        /// Path to the pinned `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`.
        #[arg(long)]
        flowdroid_jar: PathBuf,
        /// Path to the pinned android-34 platform `android.jar`, witnessed by
        /// digest; FlowDroid resolves the analyzed framework stubs from it.
        #[arg(long)]
        android_platform: PathBuf,
        /// Path to the pinned r8 jar whose `D8` entry point translates the
        /// compiled fixtures to dex on the same JVM.
        #[arg(long)]
        d8_jar: PathBuf,
        /// Java runtime that executes the analyzer and dex-translator jars.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Java compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run the Kotlin propagation kernel through the pinned FlowDroid
    /// release's command-line analyzer, over the same per-case APK
    /// materialization as the Java kernel; the fixtures are compiled with
    /// `kotlinc` and the pinned `kotlin-stdlib.jar` is dexed into each APK so
    /// standard-library calls resolve inside the analyzed image.
    RunFlowdroidKotlinKernel {
        /// Path to the pinned `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`.
        #[arg(long)]
        flowdroid_jar: PathBuf,
        /// Path to the pinned android-34 platform `android.jar`, witnessed by
        /// digest; FlowDroid resolves the analyzed framework stubs from it.
        #[arg(long)]
        android_platform: PathBuf,
        /// Path to the pinned r8 jar whose `D8` entry point translates the
        /// compiled fixtures to dex on the same JVM.
        #[arg(long)]
        d8_jar: PathBuf,
        /// Java runtime that executes the analyzer and dex-translator jars.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Kotlin compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "kotlinc")]
        kotlinc: PathBuf,
        /// `kotlin-stdlib.jar` dexed into each case's APK as the fixtures'
        /// standard-library dependency.
        #[arg(long)]
        kotlin_stdlib: PathBuf,
    },
    /// Run the Python propagation kernel through Pysa — the taint analysis of
    /// the pinned pyre-check release, whose client drives the pinned Pyrefly
    /// front end for module and call-graph resolution. Each case materializes
    /// an isolated workspace with the committed `taint.config` and the
    /// per-case resolved endpoint models.
    RunPysaPythonKernel {
        /// Path to the pinned pyre-check client (`pyre`); its self-reported
        /// version is witnessed per run.
        #[arg(long)]
        pyre: PathBuf,
        /// Path to the pinned analysis binary (`pyre.bin`), passed to the
        /// client explicitly and witnessed by digest.
        #[arg(long)]
        pyre_binary: PathBuf,
        /// Path to the pinned `pyrefly` binary; the client resolves it from
        /// `PATH`, so the runner prepends this binary's directory, and its
        /// self-reported version is witnessed per run.
        #[arg(long)]
        pyrefly: PathBuf,
    },
    /// Run the C propagation kernel through the pinned Infer release's Pulse
    /// taint analysis. Each case's compile command is materialized per case
    /// and traced by `infer capture` with the distribution's own bundled
    /// clang, then analyzed by `infer analyze` — the two phase boundaries the
    /// adapter genuinely observes.
    RunInferCKernel {
        /// Path to the pinned Infer binary; its self-reported version is
        /// witnessed per run.
        #[arg(long)]
        infer: PathBuf,
    },
    /// Run the C++ propagation kernel through the pinned Infer release's
    /// Pulse taint analysis, as its own population over the same
    /// capture/analyze boundary as the C kernel.
    RunInferCppKernel {
        /// Path to the pinned Infer binary; its self-reported version is
        /// witnessed per run.
        #[arg(long)]
        infer: PathBuf,
    },
    /// Run the Java propagation kernel through the pinned Infer release's
    /// Pulse taint analysis. Fixtures are materialized on their package paths
    /// and compiled under `infer capture`'s traced `javac`.
    RunInferJavaKernel {
        /// Path to the pinned Infer binary; its self-reported version is
        /// witnessed per run.
        #[arg(long)]
        infer: PathBuf,
        /// Java compiler traced by `infer capture` to materialize each
        /// fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run one language's benchmark-controlled taint-modeling matrix through
    /// Bifrost's policy CLI. The partition scores categories S and Z — the
    /// second promoted by Amendment A9 — so the other four categories are
    /// `unsupported` with a retained rationale, decided before the binary is
    /// invoked.
    RunBifrostModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run one language's modeling matrix through CodeQL. All six categories
    /// are scored: a data-flow configuration *is* a model declaration surface.
    RunCodeqlModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run one language's benchmark-controlled taint-modeling matrix through
    /// the pinned Infer release's Pulse taint configuration. The partition
    /// (Amendment A13) scores categories S, P (template 3 alone), and Z; O,
    /// E, and B are `unsupported` with a retained rationale, decided before
    /// the binary is invoked. Java only — the pinned distribution executes no
    /// JavaScript or Python frontend, so those languages have no Infer
    /// modeling denominator.
    RunInferModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned Infer binary; its self-reported version is
        /// witnessed per run.
        #[arg(long, default_value = "infer")]
        infer: PathBuf,
        /// Java compiler traced by `infer capture` to materialize each
        /// fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run one language's modeling matrix through Joern's flow-semantics
    /// surface and a dedicated `modeling.sc`, leaving the kernel script
    /// untouched. All six categories are scored.
    RunJoernModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run one language's modeling matrix through Semgrep CE. The
    /// preregistered partition scores categories S, Z, and E; P, O, and B are
    /// `unsupported` with a retained rationale, decided before the scan.
    RunSemgrepModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Java modeling matrix through the pinned FlowDroid release
    /// (Amendment A18). The partition scores categories S, P, Z, and O —
    /// sanitizer selectivity is template-overridden out, and categories E and
    /// B are `unsupported` with retained rationales, decided before the
    /// analyzer is invoked. Scored cells run under `-tw STUBDROID` over the
    /// committed summaries directory, which replaces the release default's
    /// bundled summary provider.
    RunFlowdroidModeling {
        /// Only `java` is accepted: the adapter consumes JVM bytecode, so the
        /// other modeling languages are outside its reach.
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`.
        #[arg(long)]
        flowdroid_jar: PathBuf,
        /// Path to the pinned android-34 platform `android.jar`, witnessed by
        /// digest; FlowDroid resolves the analyzed framework stubs from it.
        #[arg(long)]
        android_platform: PathBuf,
        /// Path to the pinned r8 jar whose `D8` entry point translates the
        /// compiled fixtures to dex on the same JVM.
        #[arg(long)]
        d8_jar: PathBuf,
        /// Java runtime that executes the analyzer and dex-translator jars.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Java compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run one language's tool-native probe set through Bifrost's built-in
    /// policy packs, supplying no models. The preregistered partition scores
    /// nothing: the standalone policy CLI ships no source or sink endpoint
    /// catalog, so all six templates are `unsupported` with a retained
    /// rationale, decided before the binary is invoked.
    RunBifrostNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
    },
    /// Run one language's tool-native probe set through CodeQL's shipped
    /// `security-extended` suite, with the `local` threat-model group enabled
    /// and no adapter query. All six templates are scored.
    RunCodeqlNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
    },
    /// Run one language's tool-native probe set through the pinned Infer
    /// release as shipped: `analyze --pulse-only --sarif` with no
    /// `--pulse-taint-config`. The partition (Amendment A14) scores nothing —
    /// the shipped product's taint analysis is off absent a configuration, a
    /// silence measured rather than assumed — so all six templates are
    /// `unsupported` with a retained rationale and a witnessed identity. Java
    /// only.
    RunInferNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned Infer binary; its self-reported version is
        /// witnessed per run.
        #[arg(long, default_value = "infer")]
        infer: PathBuf,
    },
    /// Run one language's tool-native probe set through Joern under
    /// `DefaultSemantics` alone. No benchmark semantics file may load; the
    /// preregistered partition scores nothing, because the distribution ships
    /// no source or sink catalog.
    RunJoernNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
    },
    /// Run one language's tool-native probe set through Semgrep CE over the
    /// pinned snapshot vendored into `adapters/semgrep/native/<language>/`.
    /// Every cell is unsupported until a snapshot is vendored and a dated
    /// amendment promotes it.
    RunSemgrepNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Run the Java tool-native probe set for the pinned FlowDroid release
    /// (Amendment A19): the shipped `SourcesAndSinks.txt` catalog and default
    /// summary wrapper constitute a live activation contract, but the catalog
    /// binds no identity any native template uses, so all six templates are
    /// `unsupported` with retained rationales decided from the shipped text —
    /// and the run still witnesses the pinned jar identity by digest.
    RunFlowdroidNative {
        /// Only `java` is accepted: the adapter consumes JVM bytecode, so the
        /// other native populations are outside its reach.
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`.
        #[arg(long)]
        flowdroid_jar: PathBuf,
        /// Path to the pinned android-34 platform `android.jar`, witnessed by
        /// digest alongside the analyzer jar.
        #[arg(long)]
        android_platform: PathBuf,
    },
    /// Run one language's benchmark-controlled taint-modeling matrix through
    /// Pysa's `.pysa` model surface. The partition (Amendment A16) scores
    /// categories S, P, Z, O, and E — P and O load-bearing under the
    /// `@SkipAnalysis` + `@SkipObscure` modes the committed artifact declares
    /// — and declines category B, whose store vocabulary the DSL does not
    /// have. Python only: the engine analyzes one language.
    RunPysaModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned pyre-check client (`pyre`); its self-reported
        /// version is witnessed per run.
        #[arg(long)]
        pyre: PathBuf,
        /// Path to the pinned analysis binary (`pyre.bin`), passed to the
        /// client explicitly and witnessed by digest.
        #[arg(long)]
        pyre_binary: PathBuf,
        /// Path to the pinned `pyrefly` binary; the client resolves it from
        /// `PATH`, so the runner prepends this binary's directory, and its
        /// self-reported version is witnessed per run.
        #[arg(long)]
        pyrefly: PathBuf,
    },
    /// Run one language's tool-native probe set through the taint model suite
    /// the pinned pyre-check wheel ships in `lib/pyre_check/taint/`, resolved
    /// beside the pinned client, with `--no-verify` and no benchmark-authored
    /// model of any kind (Amendment A17). All six templates are scored.
    /// Python only: the engine analyzes one language.
    RunPysaNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned pyre-check client (`pyre`); its self-reported
        /// version is witnessed per run.
        #[arg(long)]
        pyre: PathBuf,
        /// Path to the pinned analysis binary (`pyre.bin`), passed to the
        /// client explicitly and witnessed by digest.
        #[arg(long)]
        pyre_binary: PathBuf,
        /// Path to the pinned `pyrefly` binary; the client resolves it from
        /// `PATH`, so the runner prepends this binary's directory, and its
        /// self-reported version is witnessed per run.
        #[arg(long)]
        pyrefly: PathBuf,
    },
    /// Run one language's benchmark-controlled taint-modeling matrix through
    /// the pinned OpenTaint analyzer. Java is the adapter's one modeling
    /// language (Amendment A22); the partition scores categories S, P, and Z,
    /// so O, E, and B are `unsupported` with a retained rationale, decided
    /// before the analyzer is invoked. The release assets are verified by
    /// witnessed digest before any case runs.
    RunOpentaintModeling {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned `opentaint-project-analyzer.jar` release asset.
        #[arg(long)]
        analyzer_jar: PathBuf,
        /// Path to the pinned `opentaint-models.tar.gz` release asset.
        #[arg(long)]
        models_archive: PathBuf,
        /// Java runtime that executes the analyzer jar.
        #[arg(long, default_value = "java")]
        java: PathBuf,
        /// Java compiler that materializes each fixture's bytecode.
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
    },
    /// Run one language's tool-native probe set against the pinned OpenTaint
    /// release's shipped assets. The partition scores nothing (Amendment
    /// A23): the shipped models archive is propagation only and the release
    /// ships no rule set, so all six templates are `unsupported` with a
    /// retained rationale — but the run still witnesses the release assets'
    /// digests, because a report whose whole evidence is retained rationales
    /// must name a measured identity.
    RunOpentaintNative {
        #[arg(long, value_enum)]
        language: ModelingLanguage,
        /// Path to the pinned `opentaint-project-analyzer.jar` release asset.
        #[arg(long)]
        analyzer_jar: PathBuf,
        /// Path to the pinned `opentaint-models.tar.gz` release asset.
        #[arg(long)]
        models_archive: PathBuf,
    },
    /// Measure one adapter's **warm marginal** per-case cost: the wall-clock
    /// slope of running k cases through a single tool process, per
    /// [Amendment A15](docs/latency-tier.md#amendments).
    ///
    /// Timing-only auxiliary machinery. It writes no normalized report, scores
    /// nothing, and touches no correctness population; its artifacts land under
    /// `reports/raw/warm-latency/` and are never read by the scoring path. The
    /// cold per-invocation rows stay the headline figure and are neither
    /// replaced nor adjusted by anything measured here.
    MeasureWarmLatency {
        /// Adapter to measure. Only the adapters A15's observability table
        /// records as observable are accepted.
        #[arg(long, value_enum)]
        tool: WarmTool,
        /// Kernel language whose case population is batched.
        #[arg(long, value_enum)]
        language: WarmLanguage,
        /// Increasing batch sizes, comma-separated. The slope is fitted over
        /// these points.
        #[arg(long, default_value = "1,2,4,8,16")]
        batch_sizes: String,
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
    },
    /// Estimate one adapter's **per-invocation overhead**: the wall-clock of a
    /// complete adapter invocation over a trivial no-flow fixture, per
    /// [Amendment A24](docs/latency-tier.md#amendments).
    ///
    /// Timing-only auxiliary machinery, exactly like `measure-warm-latency`. It
    /// writes no normalized report, scores nothing, adds no case, and touches
    /// no correctness population; its artifacts land under
    /// `reports/raw/invocation-overhead/` and are never read by the scoring
    /// path. The measurement is an **upper bound** on start-up and warm-up —
    /// it contains the trivial fixture's own (near-zero) analysis — and it is
    /// never subtracted from a cold number.
    EstimateInvocationOverhead {
        /// Adapter to estimate.
        #[arg(long, value_enum)]
        tool: OverheadTool,
        /// Language of the trivial fixture. A24 fixes one per adapter — the
        /// language of its cheapest kernel arm — and Joern additionally takes
        /// `java` so its estimate is comparable with the java warm figures.
        #[arg(long, value_enum)]
        language: OverheadLanguage,
        #[arg(long, default_value = "joern")]
        joern: PathBuf,
        #[arg(long, default_value = "semgrep")]
        semgrep: PathBuf,
        #[arg(long, default_value = "bifrost")]
        bifrost: PathBuf,
        #[arg(long, default_value = "codeql")]
        codeql: PathBuf,
        #[arg(long)]
        codeql_packs: Option<PathBuf>,
        #[arg(long, default_value = "infer")]
        infer: PathBuf,
        #[arg(long, default_value = "opentaint-project-analyzer.jar")]
        analyzer_jar: PathBuf,
        #[arg(long, default_value = "opentaint-models.tar.gz")]
        models_archive: PathBuf,
        #[arg(long, default_value = "soot-infoflow-cmd-jar-with-dependencies.jar")]
        flowdroid_jar: PathBuf,
        #[arg(long, default_value = "android.jar")]
        android_platform: PathBuf,
        #[arg(long, default_value = "r8.jar")]
        d8_jar: PathBuf,
        #[arg(long, default_value = "java")]
        java: PathBuf,
        #[arg(long, default_value = "javac")]
        javac: PathBuf,
        #[arg(long, default_value = "kotlinc")]
        kotlinc: PathBuf,
        #[arg(long, default_value = "kotlin-stdlib.jar")]
        kotlin_stdlib: PathBuf,
        #[arg(long, default_value = "pyre")]
        pyre: PathBuf,
        #[arg(long, default_value = "pyre.bin")]
        pyre_binary: PathBuf,
        #[arg(long, default_value = "pyrefly")]
        pyrefly: PathBuf,
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
        Commands::RunOpentaintJavaKernel {
            analyzer_jar,
            models_archive,
            java,
            javac,
        } => run_opentaint_kernel(
            &analyzer_jar,
            &models_archive,
            &java,
            OpentaintKernel::Java { javac },
        ),
        Commands::RunOpentaintKotlinKernel {
            analyzer_jar,
            models_archive,
            java,
            kotlinc,
            kotlin_stdlib,
        } => run_opentaint_kernel(
            &analyzer_jar,
            &models_archive,
            &java,
            OpentaintKernel::Kotlin {
                kotlinc,
                kotlin_stdlib,
            },
        ),
        Commands::RunFlowdroidJavaKernel {
            flowdroid_jar,
            android_platform,
            d8_jar,
            java,
            javac,
        } => run_flowdroid_kernel(
            &FlowdroidTools {
                flowdroid_jar,
                android_platform,
                d8_jar,
                java,
            },
            FlowdroidKernel::Java { javac },
        ),
        Commands::RunFlowdroidKotlinKernel {
            flowdroid_jar,
            android_platform,
            d8_jar,
            java,
            kotlinc,
            kotlin_stdlib,
        } => run_flowdroid_kernel(
            &FlowdroidTools {
                flowdroid_jar,
                android_platform,
                d8_jar,
                java,
            },
            FlowdroidKernel::Kotlin {
                kotlinc,
                kotlin_stdlib,
            },
        ),
        Commands::RunPysaPythonKernel {
            pyre,
            pyre_binary,
            pyrefly,
        } => run_pysa_python_kernel(&PysaTools {
            pyre,
            pyre_binary,
            pyrefly,
        }),
        Commands::RunInferCKernel { infer } => run_infer_kernel(&infer, InferKernel::C),
        Commands::RunInferCppKernel { infer } => run_infer_kernel(&infer, InferKernel::Cpp),
        Commands::RunInferJavaKernel { infer, javac } => {
            run_infer_kernel(&infer, InferKernel::Java { javac })
        }
        Commands::RunBifrostModeling { language, bifrost } => {
            run_modeling(ModelingTool::Bifrost, &bifrost, language, None, None)
        }
        Commands::RunCodeqlModeling {
            language,
            codeql,
            codeql_packs,
        } => run_modeling(
            ModelingTool::Codeql,
            &codeql,
            language,
            codeql_packs.as_deref(),
            None,
        ),
        Commands::RunInferModeling {
            language,
            infer,
            javac,
        } => run_modeling(ModelingTool::Infer, &infer, language, None, Some(&javac)),
        Commands::RunJoernModeling { language, joern } => {
            run_modeling(ModelingTool::Joern, &joern, language, None, None)
        }
        Commands::RunSemgrepModeling { language, semgrep } => {
            run_modeling(ModelingTool::Semgrep, &semgrep, language, None, None)
        }
        Commands::RunFlowdroidModeling {
            language,
            flowdroid_jar,
            android_platform,
            d8_jar,
            java,
            javac,
        } => run_flowdroid_modeling(
            &FlowdroidTools {
                flowdroid_jar,
                android_platform,
                d8_jar,
                java,
            },
            javac,
            language,
        ),
        Commands::RunFlowdroidNative {
            language,
            flowdroid_jar,
            android_platform,
        } => run_flowdroid_native(&flowdroid_jar, &android_platform, language),
        Commands::RunBifrostNative { language, bifrost } => {
            run_native(ModelingTool::Bifrost, &bifrost, language, None)
        }
        Commands::RunCodeqlNative {
            language,
            codeql,
            codeql_packs,
        } => run_native(
            ModelingTool::Codeql,
            &codeql,
            language,
            codeql_packs.as_deref(),
        ),
        Commands::RunInferNative { language, infer } => {
            run_native(ModelingTool::Infer, &infer, language, None)
        }
        Commands::RunJoernNative { language, joern } => {
            run_native(ModelingTool::Joern, &joern, language, None)
        }
        Commands::MeasureWarmLatency {
            tool,
            language,
            batch_sizes,
            joern,
            semgrep,
        } => measure_warm_latency(
            tool,
            language,
            &batch_sizes,
            match tool {
                WarmTool::Joern => &joern,
                WarmTool::Semgrep => &semgrep,
            },
        ),
        Commands::RunSemgrepNative { language, semgrep } => {
            run_native(ModelingTool::Semgrep, &semgrep, language, None)
        }
        Commands::RunPysaModeling {
            language,
            pyre,
            pyre_binary,
            pyrefly,
        } => run_pysa_modeling(
            &PysaTools {
                pyre,
                pyre_binary,
                pyrefly,
            },
            language,
        ),
        Commands::RunPysaNative {
            language,
            pyre,
            pyre_binary,
            pyrefly,
        } => run_pysa_native(
            &PysaTools {
                pyre,
                pyre_binary,
                pyrefly,
            },
            language,
        ),
        Commands::RunOpentaintModeling {
            language,
            analyzer_jar,
            models_archive,
            java,
            javac,
        } => run_opentaint_modeling(&analyzer_jar, &models_archive, &java, &javac, language),
        Commands::RunOpentaintNative {
            language,
            analyzer_jar,
            models_archive,
        } => run_opentaint_native(&analyzer_jar, &models_archive, language),
        Commands::EstimateInvocationOverhead {
            tool,
            language,
            joern,
            semgrep,
            bifrost,
            codeql,
            codeql_packs,
            infer,
            analyzer_jar,
            models_archive,
            flowdroid_jar,
            android_platform,
            d8_jar,
            java,
            javac,
            kotlinc,
            kotlin_stdlib,
            pyre,
            pyre_binary,
            pyrefly,
        } => estimate_invocation_overhead(
            tool,
            language,
            &OverheadTools {
                joern,
                semgrep,
                bifrost,
                codeql,
                codeql_packs,
                infer,
                analyzer_jar,
                models_archive,
                flowdroid_jar,
                android_platform,
                d8_jar,
                java,
                javac,
                kotlinc,
                kotlin_stdlib,
                pyre,
                pyre_binary,
                pyrefly,
            },
        ),
    }
}
