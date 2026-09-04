//! The benchmark-controlled taint-modeling tier: its preregistered partition,
//! the load-bearing checks that prove each committed modeling artifact is the
//! reason a flow is found, and the tier's run planner. See
//! docs/modeling-matrix.md.

use crate::adapters::bifrost::{require_bifrost_modeling_load_bearing, run_bifrost_modeling_case};
use crate::adapters::codeql::{modeling_codeql_language, run_codeql_case_for_language};
use crate::adapters::flowdroid::{
    FLOWDROID_CONFIG_DIR, FLOWDROID_MODELING_SUMMARY_FILES, FLOWDROID_TEMPLATE_DIR,
    require_flowdroid_modeling_declarations,
};
use crate::adapters::infer::{require_infer_modeling_load_bearing, run_infer_modeling_case};
use crate::adapters::joern::{JOERN_MODELING_SCRIPT, run_joern_modeling_case};
use crate::adapters::normalized_report;
use crate::adapters::pysa::{pysa_taint_config_path, require_pysa_modeling_load_bearing};
use crate::adapters::semgrep::{require_semgrep_modeling_load_bearing, run_semgrep_modeling_case};
use crate::adapters::{ModelingLanguage, ModelingTool, witness_tool_identity};
use crate::cases::{case_paths, fixture_revision, validate_cases, validate_kernel_population_with};
use crate::evidence::AnchorDialect;
use crate::freeze::required_string;
use crate::native::NATIVE_TEMPLATE_PREFIX;
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{clear_stale_case_timing, now_seconds, write_run_environment};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, time::Instant};

// ---------------------------------------------------------------------------
// The benchmark-controlled taint-modeling matrix.
//
// Everything in this section is transcribed from docs/modeling-matrix.md, the
// preregistration artifact that merged before any modeling fixture, model
// artifact, or run existed. The twelve template identities, their six
// categories, and the per-tool capability partition are **immutable** on that
// document's terms: a cell revised after a run is a result being relabelled,
// not a capability classification. Corrections are dated amendments in the
// document, never silent edits here.
// ---------------------------------------------------------------------------

/// Every modeling template ID carries this prefix. It is the property that
/// distinguishes the tier structurally, the same way `dfb-template-chal-`
/// distinguishes the challenge tier, so no selector has to reason about tags.
pub(crate) const MODELING_TEMPLATE_PREFIX: &str = "dfb-template-model-";

/// The twelve preregistered modeling templates, in the document's own order —
/// six categories of two. `docs/modeling-matrix.md#the-twelve-templates`.
pub(crate) const MODELING_TEMPLATE_IDS: [&str; 12] = [
    "dfb-template-model-declared-source",
    "dfb-template-model-declared-sink",
    "dfb-template-model-opaque-propagator",
    "dfb-template-model-propagator-position",
    "dfb-template-model-sanitizer-kill",
    "dfb-template-model-sanitizer-selectivity",
    "dfb-template-model-summary-through",
    "dfb-template-model-summary-field",
    "dfb-template-model-entrypoint-parameter",
    "dfb-template-model-entrypoint-selectivity",
    "dfb-template-model-store-roundtrip",
    "dfb-template-model-store-separation",
];

/// One positive and one minimally different negative per template — 24
/// assertions for a language whose modeling population exists at all.
pub(crate) const MODELING_CASE_COUNT: usize = 2 * MODELING_TEMPLATE_IDS.len();

/// Every modeling case is `benchmark-controlled`: the models come from
/// DataFlowBench and are supplied equally to every tool. The counterpart
/// `tool-native` profile (issue #16) supplies no models and is never pooled
/// with this one.
pub(crate) const MODELING_MODEL_PROFILE: &str = "benchmark-controlled";

/// The six preregistered categories. The partition below is stated per
/// category, exactly as the document states it, and templates inherit their
/// category's decision — a category is the unit a tool can or cannot express.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub(crate) enum ModelingCategory {
    /// S — declared sources and sinks.
    SourcesAndSinks,
    /// P — declared propagators.
    Propagators,
    /// Z — declared sanitizers.
    Sanitizers,
    /// O — opaque procedure summaries.
    Summaries,
    /// E — framework entry points.
    EntryPoints,
    /// B — persistence boundaries.
    Persistence,
}

impl ModelingCategory {
    pub(crate) const ALL: [Self; 6] = [
        Self::SourcesAndSinks,
        Self::Propagators,
        Self::Sanitizers,
        Self::Summaries,
        Self::EntryPoints,
        Self::Persistence,
    ];

    /// The one-letter key the document's tables use.
    pub(crate) fn key(self) -> &'static str {
        match self {
            Self::SourcesAndSinks => "S",
            Self::Propagators => "P",
            Self::Sanitizers => "Z",
            Self::Summaries => "O",
            Self::EntryPoints => "E",
            Self::Persistence => "B",
        }
    }

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::SourcesAndSinks => "declared sources and sinks",
            Self::Propagators => "declared propagators",
            Self::Sanitizers => "declared sanitizers",
            Self::Summaries => "opaque procedure summaries",
            Self::EntryPoints => "framework entry points",
            Self::Persistence => "persistence boundaries",
        }
    }

    /// The two templates of this category, by the document's numbering.
    pub(crate) fn templates(self) -> [&'static str; 2] {
        match self {
            Self::SourcesAndSinks => [MODELING_TEMPLATE_IDS[0], MODELING_TEMPLATE_IDS[1]],
            Self::Propagators => [MODELING_TEMPLATE_IDS[2], MODELING_TEMPLATE_IDS[3]],
            Self::Sanitizers => [MODELING_TEMPLATE_IDS[4], MODELING_TEMPLATE_IDS[5]],
            Self::Summaries => [MODELING_TEMPLATE_IDS[6], MODELING_TEMPLATE_IDS[7]],
            Self::EntryPoints => [MODELING_TEMPLATE_IDS[8], MODELING_TEMPLATE_IDS[9]],
            Self::Persistence => [MODELING_TEMPLATE_IDS[10], MODELING_TEMPLATE_IDS[11]],
        }
    }
}

/// The category a modeling template belongs to, decided from the template ID
/// alone. A non-modeling template has none.
pub(crate) fn modeling_category(template: &str) -> Option<ModelingCategory> {
    ModelingCategory::ALL
        .into_iter()
        .find(|category| category.templates().contains(&template))
}

/// One cell of the preregistered per-tool capability partition: a tool, a
/// category, and either a scored decision or the document's verbatim rationale
/// for declining it.
pub(crate) struct ModelingPartitionCell {
    pub(crate) tool: ModelingTool,
    pub(crate) category: ModelingCategory,
    /// `None` when the category is scored for this tool. `Some(reason)` when
    /// it is `unsupported`, carrying the rationale the report retains.
    pub(crate) unsupported_reason: Option<&'static str>,
}

/// The preregistered per-tool capability partition, transcribed cell for cell
/// from `docs/modeling-matrix.md#per-tool-capability-partition`.
///
/// This is `CHALLENGE_SEMGREP_PARTITION`'s mechanism generalized to four
/// tools: a decision keyed by template identity, consulted **before** the tool
/// is invoked and before any tag rule, so that neither a fixture's
/// `feature_tags` nor an observed result can move a cell between the scored
/// and `unsupported` partitions after the fact.
///
/// Cells the document marks *to be verified* are recorded here as
/// `unsupported`, per the rule stated at the head of each of its tables:
/// unverifiable is unsupported until shown otherwise, and promoting one is a
/// dated amendment. That is why Bifrost entered with one scored category rather
/// than four, and why its second — category Z — arrived as
/// [Amendment A9](../docs/modeling-matrix.md#amendments) with a measurement
/// behind it rather than as an edit to this array.
pub(crate) const MODELING_PARTITION: &[ModelingPartitionCell] = &[
    // Bifrost — preregistered 1 / 6; 2 / 6 as amended, after Amendment A9
    // promoted category Z.
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::Propagators,
        unsupported_reason: Some(
            "to be verified — unsupported until shown: no committed policy declares a propagator or transform, and the adapter README makes no propagator claim. Additionally, every committed policy sets `:unmodeled optimistic`, so the modeling policy must also be shown to accept `require-model` before either P cell is load-bearing. Both must be demonstrated on the pinned build",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::Sanitizers,
        // Amendment A9: the preregistration declined this category on the
        // adapter README's "sanitizer lowering is a future Bifrost CLI
        // capability". Measured on v0.10.7, that sentence is false: the RQLP
        // `analysis` grammar accepts a `(sanitizer :id … :selector … :input …
        // :output … :removes […])` stanza, and the declaration is load-bearing
        // on the committed Python fixtures in both directions and selective by
        // identity. A promotion is only ever a dated amendment on the
        // preregistration, never a silent edit here.
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::Summaries,
        unsupported_reason: Some(
            "the adapter README: \"External semantic-model activation requires an embedding with an explicit catalog, so the modeled-external case is reported as `unsupported` by this CLI adapter with an explicit retained reason. It is not a negative result.\" The existing `dfb-taint-java-modeled-external` calibration case already carries that retained reason in the frozen smoke report",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: Some(
            "to be verified — unsupported until shown: nothing in the repository or the README describes an entry-root declaration for the policy CLI",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Bifrost,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "to be verified — unsupported until shown: no persistence-boundary vocabulary is described anywhere for any adapter, Bifrost included",
        ),
    },
    // CodeQL — CLI 2.26.4: 6 / 6.
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::Propagators,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::Summaries,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Codeql,
        category: ModelingCategory::Persistence,
        unsupported_reason: None,
    },
    // FlowDroid — 2.15.1, Java only (Amendment A18): 4 / 6 categories, S, P,
    // Z, and O, with category Z split at the template level (see
    // MODELING_TEMPLATE_OVERRIDES). The row was preregistered on retained
    // probe evidence (reports/raw/load-bearing-java-modeling/flowdroid-*.json,
    // produced by scripts/probe-flowdroid-modeling-load-bearing.sh) before the
    // first modeling run, per the matrix's own joining rule.
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::Propagators,
        // Probed on the pinned 2.15.1: a StubDroid summary is load-bearing —
        // the reflective opaque body carries nothing under the release's
        // default configuration, the declared `carry` flow makes template 3's
        // positive leak, deleting it stops the leak — and positional binding
        // is native to the summary engine, so template 4's undeclared-position
        // negative stays clean.
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::Sanitizers,
        // Template 5 scored (a `<clear>` stanza suppresses on a completing
        // run and deleting it restores the flow through scrub's identity
        // body); template 6 is overridden to unsupported — see
        // MODELING_TEMPLATE_OVERRIDES and Amendment A18.
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::Summaries,
        // Probed: the identical identity bodies of `pass` and `hold` decide
        // nothing — only the summaries do — and template 8's field-destination
        // access path (`out: 1.payload`) is honored, leaving the sibling
        // field's read clean while `deposit`'s empty body writes nothing.
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: Some(
            "the released CLI derives analysis roots exclusively from the APK manifest's Android \
             components; no per-method entry-root declaration surface exists. Probed on the \
             pinned 2.15.1: an XML sources-and-sinks definition binding the handler's parameter \
             as a `callback` source parses (\"Loaded 1 sources\") and the analysis still finds \
             zero sources, because a declaration cannot create a root the manifest does not \
             (reports/raw/load-bearing-java-modeling/flowdroid-entrypoint-parameter-undeclarable.json)",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Flowdroid,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "no FlowDroid declaration surface carries a store identity or a key position: the \
             sources-and-sinks formats declare source/sink/both roles, the EasyTaintWrapper \
             lists declare taint/exclude/kill per method, and a StubDroid summary's positions \
             are parameters, fields, and the return value — none can express the `store:` and \
             `key:` bindings templates 11 and 12 declare, so a persistence declaration has no \
             encoding on the pinned 2.15.1",
        ),
    },
    // Infer — v1.3.0: 3 / 6 categories (S, P, Z), joined by Amendment A13 on
    // a field evaluation executed against the committed Java modeling
    // fixtures before this row existed
    // (reports/raw/amendment-a13-infer-partition/, produced by
    // scripts/probe-infer-modeling-partition.sh). Category P is scored by
    // template 3 alone: template 4 is declined by a template-level override
    // below, on the measured absence of an input-position vocabulary.
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::Propagators,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::Summaries,
        unsupported_reason: Some(
            "measured on the pinned v1.3.0 (Amendment A13): template 7's identity bodies are captured and Pulse reads them — both cells report with no declaration at all, so the cells are decided by body analysis rather than by a summary, and the release has no surface that makes a captured body ignored (`--pulse-taint-opaque-files` is accepted and measured inert for Java). Template 8's `FieldsOfValue` destination is not field-precise: the declared `1.payload` summary taints the sibling field too, so the field-separation negative is decided by the heap approximation rather than by the summary",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: Some(
            "measured on the pinned v1.3.0 (Amendment A13): a source matcher's argument `taint_target` applies at call boundaries only — declared on the uncalled handler's parameter, the analysis synthesizes no root and reports nothing inside the handler's body — and the pulse-taint surface documents no entry-root or endpoint vocabulary",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Infer,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "the pulse-taint configuration surface defines sources, sinks, sanitizers, propagators, policies, and data-flow kinds and nothing else — no store-write/store-read vocabulary and no key discrimination (the binary's own enumeration is retained as amendment A13 evidence) — and `Store.put`/`Store.get` have empty bodies, so nothing else can carry the roundtrip",
        ),
    },
    // Joern — 4.0.617: 4 / 6 (Amendment A2 moved P and O to unsupported).
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::Propagators,
        // Amendment A2: FlowSemantic mappings on the pinned 4.0.610 are
        // additive over the engine's default argument pass-through and cannot
        // restrict it, so a propagator declaration is not load-bearing — the
        // default decides the cell with or without the model.
        unsupported_reason: Some(
            "Joern 4.0.610 FlowSemantic mappings are additive over the \
             default unmodeled-call pass-through and cannot restrict it; a \
             propagator model is not load-bearing on the pinned version \
             (Amendment A2)",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::Summaries,
        // Amendment A2: same additivity, and the field-destination access
        // path of a summary (arg -> field of arg) is ignored — the whole
        // object is tainted — so a summary model is likewise not
        // load-bearing on the pinned version.
        unsupported_reason: Some(
            "Joern 4.0.610 ignores a summary's field-destination access path \
             and its FlowSemantic cannot restrict the default pass-through; \
             a summary model is not load-bearing on the pinned version \
             (Amendment A2)",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Joern,
        category: ModelingCategory::Persistence,
        unsupported_reason: None,
    },
    // Semgrep CE — 1.176.0 (`--oss-only`): 3 / 6 categories, and Amendment A3
    // splits category Z at the template level (see MODELING_TEMPLATE_OVERRIDES).
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::Propagators,
        unsupported_reason: Some(
            "verified twice over. First, `pattern-propagators` binds `to:` to a **metavariable**, not to a call's return value: a propagator written `pattern: prop($A,$B) / from: $B / to: prop(...)` produced no finding when the default pass-through was disabled. Second, with the default enabled, CE reports the sink whether taint sits at the declared position 1 or the undeclared position 0 — so both cells of template 4 are decided by the default, not the model, and the load-bearing-model requirement is violated either way. Arg→return propagation is outside CE's propagator vocabulary",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::Summaries,
        unsupported_reason: Some(
            "template 7 needs arg→return summary semantics, which P has already established CE cannot express, and puts the summarized procedure in a separate file, which CE's intra-file engine does not cross. Template 8's destination is a *field* of an argument; `to: $L` reaches the whole object, and the pinned CE documents only \"Experimental support for basic field-sensitive taint tracking\" — so the field-separation negative would be decided by CE's heap approximation rather than by the summary",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Semgrep,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "the write and the read are in two different procedures by construction, and the pinned CE engine has no interprocedural taint at all: `semgrep scan --help` offers `--pro-intrafile` (\"Intra-file inter-procedural taint analysis … Requires Semgrep Pro Engine\"), so the step from `put` to `get` is outside the engine regardless of what is declared",
        ),
    },
    // Pysa — pyre-check 0.10.0 + Pyrefly 1.2.0: 5 / 6, Python-scoped. Added
    // by Amendment A16, verified by execution on the committed Python
    // modeling fixtures before the adapter's first scored modeling run
    // (reports/raw/amendment-a13-pysa-modeling/,
    // scripts/probe-pysa-modeling-load-bearing.sh). Categories P and O are
    // load-bearing only under the `@SkipAnalysis` + `@SkipObscure` modes the
    // committed artifact declares — the pinned pair resolves the matrix's
    // reflective opaque body on its own, so without the skip modes the
    // engine's body reading would decide those cells
    // (`require_pysa_modeling_load_bearing` enforces the modes).
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::Propagators,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::Summaries,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Pysa,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "the `.pysa` DSL binds taint roles to callables and parameter positions — `TaintSource`, `TaintSink`, `TaintInTaintOut`, `Sanitize`, and mode annotations — and has no store identity, key position, or vocabulary linking a write entity to a read entity through a shared store, per instance or otherwise. The nearest encoding, a source model on `Store.get`, would report both polarities of template 11 without ever reading the key: a different model, not an approximation of this one (Amendment A16)",
        ),
    },
    // OpenTaint — analyzer/2026.09.03.9752bd2, Java only: 3 / 6 (S, P, Z).
    // Added by Amendment A22, decided by executing the pinned analyzer over
    // the committed Java modeling fixtures before any scored run; the probe
    // evidence is retained under reports/raw/opentaint-modeling-surface-probe/
    // (scripts/probe-opentaint-modeling-surface.sh). This adapter has no
    // wave-M1 language other than Java — the engine analyzes JVM bytecode
    // only, so JavaScript and Python have no OpenTaint modeling denominator
    // at all, and `plan_modeling_run` refuses them before this partition is
    // consulted.
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::SourcesAndSinks,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::Propagators,
        // The load-bearing baseline was measured first: with no propagator
        // declared, the reflective `Opaque.carry` body carries nothing, so
        // the engine has no optimistic unmodeled-call default to disable and
        // the assignment-shaped propagator (`$TO = Opaque.carry($FROM)`,
        // matched against the lifted JVM IR where a nested call is a
        // temporary assignment) is what decides both cells.
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::Sanitizers,
        unsupported_reason: None,
    },
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::Summaries,
        unsupported_reason: Some(
            "the engine's whole-program body reading decides template 7 in both cells — with no summary declared, both identity bodies are read and both cells report (probe arms `o-through-*-endpoints-only`) — and the surface has no instruction to ignore a present body, so no summary declaration can be load-bearing; template 8's `out: 1.payload` field destination has no spelling in the propagator's from/to vocabulary, and both attempted store-through encodings produce no flow (`o-field-*`) (Amendment A22)",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::EntryPoints,
        unsupported_reason: Some(
            "the pinned rule front end silently drops method-definition-shaped `pattern-sources` — both the focus-metavariable and the pattern-inside encodings — and the rule degenerates to sink-existence matching that flags constant-argument callsites in both cells (probe arms `e-def-pattern-*`, `e-inside-pattern-*`, against the `e-sink-only-control` arm), so no entry-root declaration is expressible; the invocation's all-methods entry-point selector analyzes the uncalled handlers but nothing can declare their parameters tainted on entry (Amendment A22)",
        ),
    },
    ModelingPartitionCell {
        tool: ModelingTool::Opentaint,
        category: ModelingCategory::Persistence,
        unsupported_reason: Some(
            "the rule surface has no store, key, or cross-procedure vocabulary: a propagator carries taint between the metavariables of one matched callsite and cannot span `put` in one procedure and `get` in another. All three attempted encodings — endpoints only, the static-store spelling through the key argument, and the instance-store spelling through a side-effect-tainted receiver — leave every positive at zero findings (probe arms `b-*`) (Amendment A22)",
        ),
    },
];

/// The preregistered decision for one tool × template cell, keyed by template
/// identity alone: `None` when the category is scored, `Some(reason)` when the
/// tool declines it. Every cell is present, so an unknown template is a
/// programming error rather than a silent scored default.
/// Template-level partition overrides (Amendment A3): consulted before the
/// category cell, for the cells where a tool's capability splits within a
/// category. Semgrep CE can score sanitizer-kill (template 5) but not
/// sanitizer-selectivity (template 6): the mandated
/// `taint_assume_safe_functions: true` — required to keep propagator models
/// load-bearing — itself suppresses flow through the undeclared
/// sanitizer-lookalike, so selectivity's positive is undecidable by
/// construction in a single CE invocation.
/// A second override carries Infer's template 4 (Amendment A13): a Pulse
/// propagator declares an output (`taint_target`) but no input position, and
/// the measured propagator carries taint from the undeclared position 0
/// exactly as from the declared position 1 — both cells are decided by the
/// any-argument default, not the declared position. Unknown configuration
/// fields are silently ignored on the pinned build, so no spelling can be
/// trusted to bind the position either.
pub(crate) const MODELING_TEMPLATE_OVERRIDES: [(ModelingTool, &str, &str); 3] = [
    (
        ModelingTool::Semgrep,
        "dfb-template-model-sanitizer-selectivity",
        "Semgrep CE cannot express sanitizer selectivity and the safe-function \
         assumption in one invocation: taint_assume_safe_functions suppresses \
         flow through the undeclared sanitizer-lookalike, so the positive is \
         undecidable by construction (Amendment A3)",
    ),
    (
        ModelingTool::Infer,
        "dfb-template-model-propagator-position",
        "a Pulse taint propagator declares an output (`taint_target`) but no \
         input position: measured on the pinned v1.3.0, the declared `select` \
         propagator carries taint from the undeclared position 0 exactly as \
         from the declared position 1, so both cells are decided by the \
         any-argument default rather than by the declared binding — and \
         unknown configuration fields are silently ignored, so no spelling \
         can be trusted to bind the position (Amendment A13)",
    ),
    // Amendment A18, measured before the first run: FlowDroid's summary
    // resolution is exclusive for the whole declaring class
    // (SummaryTaintWrapper.isExclusive answers true whenever the class has
    // summaries), so the one declaration that suppresses `scrub` also
    // swallows the undeclared sibling `sanitize` — probed as zero leaks on
    // template 6's positive under the committed Clean summary
    // (reports/raw/load-bearing-java-modeling/flowdroid-sanitizer-selectivity-undecidable.json).
    (
        ModelingTool::Flowdroid,
        "dfb-template-model-sanitizer-selectivity",
        "FlowDroid cannot express sanitizer suppression and selectivity in one \
         invocation: summary resolution is exclusive for the whole declaring \
         class, so the declared scrub kill also suppresses the flow through \
         the undeclared sanitizer-lookalike and the positive is undecidable \
         by construction (Amendment A18)",
    ),
];

pub(crate) fn modeling_partition_reason(
    tool: ModelingTool,
    template: &str,
) -> Result<Option<&'static str>> {
    let category = modeling_category(template).with_context(|| {
        format!("{template:?} is not one of the twelve preregistered modeling templates")
    })?;
    if let Some((_, _, reason)) = MODELING_TEMPLATE_OVERRIDES
        .iter()
        .find(|(t, id, _)| *t == tool && *id == template)
    {
        return Ok(Some(reason));
    }
    MODELING_PARTITION
        .iter()
        .find(|cell| cell.tool == tool && cell.category == category)
        .map(|cell| cell.unsupported_reason)
        .with_context(|| {
            format!(
                "the modeling partition has no cell for {} × category {}",
                tool.key(),
                category.key()
            )
        })
}

/// The retained `unsupported` reason for a declined cell, or `None` when the
/// cell is scored. The partition's rationale is carried verbatim; the prefix
/// names the category and the tool identity **the run witnessed**, so the
/// reason is auditable without opening the document.
///
/// `identity` is [`witness_tool_identity`]'s reading of the binary this run
/// invoked, never a constant: a declined cell is decided without invoking the
/// analyzer over the fixture, but the run as a whole still witnesses the
/// version once, so the rationale names the build that was actually pinned.
pub(crate) fn modeling_unsupported_reason(
    tool: ModelingTool,
    template: &str,
    identity: &str,
) -> Result<Option<String>> {
    let Some(reason) = modeling_partition_reason(tool, template)? else {
        return Ok(None);
    };
    let category = modeling_category(template).expect("partition resolved the category");
    Ok(Some(format!(
        "category {} — {} — is unsupported for {identity} by the preregistered modeling partition (docs/modeling-matrix.md#per-tool-capability-partition): {reason}",
        category.key(),
        category.label(),
    )))
}

/// The templates a tool is entitled to score, in preregistered order. The
/// counts are the document's partition summary **as amended**: Bifrost 4
/// (Amendment A9), Semgrep 5 (Amendment A3), CodeQL 12, Joern 8
/// (Amendment A2), Infer 5 (Amendment A13).
pub(crate) fn modeling_supported_templates(tool: ModelingTool) -> Vec<&'static str> {
    MODELING_TEMPLATE_IDS
        .into_iter()
        .filter(|template| {
            modeling_partition_reason(tool, template)
                .expect("every preregistered template has a partition cell")
                .is_none()
        })
        .collect()
}

/// Whether a case is a **benchmark-controlled** modeling-tier assertion of this
/// language.
///
/// The profile clause is load-bearing, not decorative: the `modeling` tier is
/// shared with the tool-native profile (docs/native-profile.md), and a selector
/// that filtered on the tier alone would pool the two profiles — the one thing
/// [the scoring contract](docs/scoring.md#model-profiles) forbids outright.
pub(crate) fn modeling_case(case: &Value, language: ModelingLanguage) -> bool {
    case["language"] == language.key()
        && case["track"] == "taint"
        && case["score_tier"] == "modeling"
        && case["model_profile"] == MODELING_MODEL_PROFILE
}

/// Corpus-wide modeling checks, run by `validate` over every committed case.
///
/// **Tier isolation is structural.** A modeling `template_id` and the
/// `modeling` score tier imply each other, so a modeling case can never be
/// selected by a core, calibration, `language-extension`, or `real-project`
/// population — every one of those selectors filters on the tier — and a
/// modeling-tier case can never carry a kernel template.
///
/// **A language with no modeling cases has no modeling denominator**, and
/// validates trivially. Presence of modeling-tier cases is the signal; there is
/// no rollout table to flip, because unlike the challenge tier this population
/// is not a subset of an existing denominator that a flag has to switch
/// between.
pub(crate) fn validate_modeling_cases(cases: &[(PathBuf, Value)]) -> Result<()> {
    for (path, case) in cases {
        let template = required_string(case, "template_id", &path.display().to_string())?;
        let tier = required_string(case, "score_tier", &path.display().to_string())?;
        let modeling_template = template.starts_with(MODELING_TEMPLATE_PREFIX);
        let native_template = template.starts_with(NATIVE_TEMPLATE_PREFIX);
        let modeling_tier = tier == "modeling";
        if (modeling_template || native_template) != modeling_tier {
            bail!(
                "{}: template {template:?} and score_tier {tier:?} disagree; every `{MODELING_TEMPLATE_PREFIX}` and `{NATIVE_TEMPLATE_PREFIX}` template is `modeling`-tier and every `modeling`-tier case carries one",
                path.display()
            );
        }
        if !modeling_tier {
            continue;
        }
        // The tier is shared; the profile is not. A tool-native case answers to
        // `validate_native_cases`, which enforces the mirror of every check
        // below against its own six preregistered templates.
        if native_template {
            continue;
        }
        if !MODELING_TEMPLATE_IDS.contains(&template) {
            bail!(
                "{}: {template:?} is not one of the twelve preregistered modeling templates (docs/modeling-matrix.md#the-twelve-templates)",
                path.display()
            );
        }
        if case["model_profile"] != MODELING_MODEL_PROFILE {
            bail!(
                "{}: modeling cases are `model_profile: {MODELING_MODEL_PROFILE:?}`; the tool-native profile supplies no models and is never pooled with this matrix",
                path.display()
            );
        }
        // Half of "a missing model is a benchmark defect, never a result": no
        // modeling case may exist whose template has no preregistered decision
        // for some adapter. The other half — that a scored cell's declaration
        // is actually present in that adapter's artifact — is enforced by the
        // runner, which refuses to run without the artifact.
        for tool in ModelingTool::ALL.iter().copied() {
            modeling_partition_reason(tool, template).with_context(|| {
                format!(
                    "{}: no preregistered {} partition decision",
                    path.display(),
                    tool.key()
                )
            })?;
        }
    }
    let languages: BTreeSet<&str> = cases
        .iter()
        .filter(|(_, case)| benchmark_controlled_modeling_case(case))
        .filter_map(|(_, case)| case["language"].as_str())
        .collect();
    for language in languages {
        let population: Vec<(PathBuf, Value)> = cases
            .iter()
            .filter(|(_, case)| {
                benchmark_controlled_modeling_case(case)
                    && case["language"].as_str() == Some(language)
            })
            .cloned()
            .collect();
        validate_modeling_population(&population, &format!("{language} modeling population"))?;
    }
    Ok(())
}

/// A `modeling`-tier case of the benchmark-controlled profile, language-agnostic.
pub(crate) fn benchmark_controlled_modeling_case(case: &Value) -> bool {
    case["score_tier"] == "modeling" && case["model_profile"] == MODELING_MODEL_PROFILE
}

/// Balance and completeness for one language's modeling population: exactly one
/// positive and one minimally different negative for each of the twelve
/// templates — 24 assertions — under one model profile.
///
/// An empty population is not a population: the language has no modeling
/// denominator and there is nothing to balance. Everything else must be whole,
/// so a partial fixture landing fails the build rather than silently reducing a
/// denominator.
pub(crate) fn validate_modeling_population(cases: &[(PathBuf, Value)], label: &str) -> Result<()> {
    if cases.is_empty() {
        return Ok(());
    }
    validate_kernel_population_with(cases, label, &MODELING_TEMPLATE_IDS)
}

// ---------------------------------------------------------------------------
// Modeling-matrix runners.
//
// One command per adapter, parameterized by language, rather than twelve
// near-identical commands. The existing per-language kernel commands are
// separate because each language's kernel differs in real toolchain plumbing —
// a `kotlinc` trace, a `go build`, a synthesized Cargo crate, a different
// extractor. The modeling matrix has none of that: it is fixed at three
// languages on three already-wired toolchains, and a modeling run differs from
// its sibling only in which artifact it loads and which population it selects.
// A `--language` argument states that honestly; twelve enum variants would
// state it twelve times.
// ---------------------------------------------------------------------------

/// Everything a modeling run needs, assembled before the tool is touched.
/// Building the plan is the fail-fast gate: no population, a missing artifact,
/// or an artifact that leaves the model non-load-bearing all fail here, and an
/// empty report is never written.
pub(crate) struct ModelingRunPlan {
    pub(crate) tool: ModelingTool,
    pub(crate) language: ModelingLanguage,
    pub(crate) cases: Vec<(PathBuf, Value)>,
    /// The artifacts hash-bound into the report's `configuration_hash`.
    pub(crate) configuration_paths: BTreeSet<PathBuf>,
    pub(crate) report: PathBuf,
    pub(crate) raw_dir: PathBuf,
}

/// Select and validate one language's modeling population.
///
/// The selection is by language, track, and score tier — the same three
/// properties every kernel selection uses — and the tier filter is what keeps
/// the population disjoint from every core, calibration, `language-extension`,
/// and `real-project` denominator.
pub(crate) fn select_modeling_cases(language: ModelingLanguage) -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if modeling_case(&case, language) {
            selected.push((path, case));
        }
    }
    validate_modeling_population(&selected, &language.label())?;
    Ok(selected)
}

/// Assemble a modeling run, failing fast on every condition that would
/// otherwise produce a report that means nothing.
pub(crate) fn plan_modeling_run(
    tool: ModelingTool,
    language: ModelingLanguage,
) -> Result<ModelingRunPlan> {
    validate_cases()?;
    let cases = select_modeling_cases(language)?;
    if cases.is_empty() {
        bail!(
            "no modeling population for {}: the {} selection admits no `score_tier: \"modeling\"` case, so there is nothing for {} to be told. A language's {MODELING_CASE_COUNT} modeling assertions land with its own pull request (docs/modeling-matrix.md#rollout-plan); refusing to write an empty report",
            language.key(),
            language.display_name(),
            tool.pinned_identity()
        );
    }

    // A scored cell with no declaration behind it is a benchmark defect, not
    // evidence about the analyzer. It is a hard error, never an outcome —
    // and it is a different thing again from a tool × language pair with no
    // modeling denominator at all, which is refused here on applicability
    // rather than on a missing file.
    let Some(artifact) = language.artifact(tool) else {
        bail!(
            "{} has no {} modeling denominator at all: the pinned distribution executes no {} frontend, so its modeling row does not extend to the language (docs/modeling-matrix.md — Infer by Amendment A13, Pysa by Amendment A16, FlowDroid by Amendment A18, OpenTaint by Amendment A22). No denominator is different from a zero; refusing to write a report",
            tool.pinned_identity(),
            language.display_name(),
            language.display_name()
        );
    };
    if tool == ModelingTool::Flowdroid {
        // FlowDroid's artifact is a directory of summary XMLs, checked
        // declaration by declaration; its load-bearing property is the
        // invocation shape itself (STUBDROID over these summaries replaces
        // the release default's bundled provider), so there is no textual
        // switch to pin here.
        require_flowdroid_modeling_declarations()?;
    } else {
        let contents = fs::read_to_string(artifact).map_err(|error| {
            anyhow::anyhow!(
                "{} has a {} modeling population but its modeling artifact {artifact} cannot be read: {error}. docs/modeling-matrix.md makes a missing model a benchmark defect that fails the build; it is never `unsupported`, never `not-reached`, and never a result",
                tool.pinned_identity(),
                language.display_name()
            )
        })?;
        match tool {
            ModelingTool::Bifrost => require_bifrost_modeling_load_bearing(&contents, artifact)?,
            ModelingTool::Semgrep => require_semgrep_modeling_load_bearing(&contents, artifact)?,
            // Infer has no unmodeled-call default to pin — where a body is
            // captured, Pulse reads it, which is exactly why Amendment A13 marks
            // category O unsupported rather than gating it here — but its
            // configuration surface has three silent-failure shapes of its own,
            // and the gate refuses each of them.
            ModelingTool::Infer => require_infer_modeling_load_bearing(&contents, artifact)?,
            // Pysa's switch is per-entity: the `@SkipAnalysis` + `@SkipObscure`
            // modes on every declared propagator and summary (Amendment A16).
            ModelingTool::Pysa => require_pysa_modeling_load_bearing(&contents, artifact)?,
            // Neither surface has a switch to pin. CodeQL has no unmodeled-call
            // default that would decide a cell on its own: a `ConfigSig` with no
            // `isAdditionalFlowStep` adds no step. Joern's default pass-through
            // *is* load-bearing, but it cannot be disabled — `FlowSemantic`
            // mappings are additive over it — which is why Amendment A2 moved its
            // propagator and summary categories to unsupported activation instead
            // of gating them here. OpenTaint has no switch either, and needs
            // none: the surface probe measured that with no propagator declared
            // the reflective body carries nothing, so the engine has no
            // optimistic unmodeled-call default to disable (Amendment A22).
            ModelingTool::Codeql | ModelingTool::Joern | ModelingTool::Opentaint => {}
            ModelingTool::Flowdroid => unreachable!("handled above"),
        }
    }

    let configuration_paths = modeling_configuration_paths(tool, language)?
        .expect("the applicability gate above resolved the artifact");

    Ok(ModelingRunPlan {
        tool,
        language,
        cases,
        configuration_paths,
        report: language.report(tool),
        raw_dir: language.raw_dir(tool),
    })
}

/// The artifacts a modeling report hash-binds into its `configuration_hash`,
/// shared between [`plan_modeling_run`] and the validate-reports drift check
/// so the planner and the comparator can never disagree. `None` when the tool
/// has no modeling denominator for the language at all.
pub(crate) fn modeling_configuration_paths(
    tool: ModelingTool,
    language: ModelingLanguage,
) -> Result<Option<BTreeSet<PathBuf>>> {
    let Some(artifact) = language.artifact(tool) else {
        return Ok(None);
    };
    let mut configuration_paths = match tool {
        // The directory itself has no bytes; the three committed summary
        // files bind the hash, alongside the endpoint template, the wrapper
        // template, and the manifest blob that shape every materialized APK —
        // the same binding the kernel reports carry, minus the Kotlin pair
        // this Java-only population never touches.
        ModelingTool::Flowdroid => {
            let mut paths: BTreeSet<PathBuf> = FLOWDROID_MODELING_SUMMARY_FILES
                .iter()
                .map(PathBuf::from)
                .collect();
            paths.insert(PathBuf::from(format!(
                "{FLOWDROID_CONFIG_DIR}/sources-sinks.txt"
            )));
            paths.insert(PathBuf::from(format!(
                "{FLOWDROID_TEMPLATE_DIR}/AndroidManifest-java.xml"
            )));
            paths.insert(PathBuf::from(format!(
                "{FLOWDROID_TEMPLATE_DIR}/DfbCaseActivity.java.tmpl"
            )));
            paths
        }
        _ => BTreeSet::from([PathBuf::from(artifact)]),
    };
    if tool == ModelingTool::Joern {
        // Joern's declarations live in two files, so both bind the hash.
        configuration_paths.insert(PathBuf::from(JOERN_MODELING_SCRIPT));
    }
    if tool == ModelingTool::Pysa {
        // Pysa's kind and rule declarations live in the committed
        // taint.config the kernel also binds; the modeling artifact carries
        // only the per-template models, so both bind the hash.
        configuration_paths.insert(PathBuf::from(pysa_taint_config_path()));
    }
    for path in &configuration_paths {
        if !path.is_file() {
            bail!(
                "{} modeling run needs {}, which does not exist",
                tool.pinned_identity(),
                path.display()
            );
        }
    }
    Ok(Some(configuration_paths))
}

/// Retain the preregistered `unsupported` decision for one declined cell,
/// **without invoking the tool**, and return the result-schema outcome.
///
/// This is `CHALLENGE_SEMGREP_PARTITION`'s mechanism, per tool: the decision
/// is read from the partition by template identity, so no fixture's tags and no
/// observed result can move a cell. An excluded case is never handed to the
/// analyzer, so it cannot produce an empty finding list that later reads as a
/// negative.
pub(crate) fn modeling_partition_outcome(
    tool: ModelingTool,
    case: &Value,
    raw_dir: &Path,
    identity: &str,
) -> Result<Option<(&'static str, String, PathBuf)>> {
    let id = required_string(case, "id", "modeling case")?;
    let template = required_string(case, "template_id", id)?;
    let Some(reason) = modeling_unsupported_reason(tool, template, identity)? else {
        return Ok(None);
    };
    let category = modeling_category(template).expect("partition resolved the category");
    let raw_path = raw_dir.join(format!("{id}-unsupported.json"));
    if raw_path.exists() {
        fs::remove_file(&raw_path).with_context(|| format!("clear {}", raw_path.display()))?;
    }
    clear_stale_case_timing(raw_dir, id)?;
    fs::write(
        &raw_path,
        serde_json::to_string_pretty(&json!({
            "adapter": tool.key(),
            "case_id": id,
            "state": "unsupported",
            "stage": "preregistered-modeling-partition",
            "reason": reason,
            "template_id": template,
            "modeling_category": category.key(),
            "modeling_category_label": category.label(),
            "witnessed_tool_identity": identity,
            "partition_source": "docs/modeling-matrix.md#per-tool-capability-partition",
            "evidence_kind": "retained-capability-decision"
        }))? + "\n",
    )?;
    Ok(Some(("unsupported", reason, raw_path)))
}

pub(crate) fn modeling_anchor_dialect(language: ModelingLanguage) -> Result<AnchorDialect> {
    match language {
        ModelingLanguage::Python => Ok(AnchorDialect::Python),
        // JavaScript reconciles under the member-qualified ECMA variant: a
        // modeling declaration binds a type and a member, so a declared sink is
        // reached through its receiver (`Audit.record(v)`), which the kernel
        // dialect deliberately does not count as a callsite of `record`.
        ModelingLanguage::Javascript => Ok(AnchorDialect::EcmaMember),
        // Java for the same reason, and with no exception: the language has no
        // free functions, so every declared modeling entity is reached through
        // its declaring type.
        ModelingLanguage::Java => Ok(AnchorDialect::JavaMember),
    }
}

/// A per-case scratch root for a modeling run, disjoint from every kernel run's.
pub(crate) fn modeling_case_scratch(
    tool: ModelingTool,
    language: ModelingLanguage,
    id: &str,
) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!(
            "dataflowbench-modeling-{}-{}",
            tool.key(),
            language.key()
        ))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

/// Copy one case's fixture files into `workspace`.
pub(crate) fn materialize_modeling_workspace(
    case_path: &Path,
    case: &Value,
    workspace: &Path,
) -> Result<()> {
    fs::create_dir_all(workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }
    Ok(())
}

/// Run one adapter's modeling matrix for one language.
///
/// The staged shape of this command is recorded in docs/adapters.md: the
/// population gate, the artifact gate, the load-bearing gate, and the
/// partition's `unsupported` arm are infrastructure; the arm that invokes an
/// analyzer over a *scored* cell lands with the language pull request that
/// authors that adapter's declarations. A language whose execution arm is not
/// wired yet is still a hard error rather than a synthesized outcome, which
/// `docs/adapters.md` forbids.
pub(crate) fn run_modeling(
    tool: ModelingTool,
    binary: &Path,
    language: ModelingLanguage,
    codeql_packs: Option<&Path>,
    javac: Option<&Path>,
) -> Result<()> {
    if let Some(packs) = codeql_packs
        && !packs.is_dir()
    {
        bail!("CodeQL pack search path {} does not exist", packs.display());
    }
    let plan = plan_modeling_run(tool, language)?;

    fs::create_dir_all(&plan.raw_dir)?;
    // Joern's two extra path resolutions happen once for the whole run rather
    // than per case: the script and the semantics file are read by a process
    // whose working directory is the per-case scratch root.
    let joern_paths = if plan.tool == ModelingTool::Joern {
        let script =
            fs::canonicalize(JOERN_MODELING_SCRIPT).context("resolve the Joern modeling script")?;
        let semantics = fs::canonicalize(
            plan.language
                .artifact(ModelingTool::Joern)
                .expect("every wave-M1 language has a Joern semantics file"),
        )
        .context("resolve the Joern modeling semantics")?;
        let raw_root =
            fs::canonicalize(&plan.raw_dir).context("resolve the Joern evidence directory")?;
        Some((script, semantics, raw_root))
    } else {
        None
    };
    let semgrep_rule = if plan.tool == ModelingTool::Semgrep {
        Some(
            fs::canonicalize(
                plan.language
                    .artifact(ModelingTool::Semgrep)
                    .expect("every wave-M1 language has a Semgrep modeling rule"),
            )
            .context("resolve the Semgrep modeling rule")?,
        )
    } else {
        None
    };
    // Infer's committed configuration is resolved once for the whole run: the
    // analyzer's working directory is the per-case scratch root, so the path
    // it receives must be absolute.
    let infer_config = if plan.tool == ModelingTool::Infer {
        Some(
            fs::canonicalize(
                plan.language
                    .artifact(ModelingTool::Infer)
                    .expect("the Infer modeling row exists for Java"),
            )
            .context("resolve the Infer modeling configuration")?,
        )
    } else {
        None
    };

    let started = now_seconds()?;
    let identity = witness_tool_identity(plan.tool, binary)?;
    write_run_environment(&plan.raw_dir, plan.tool.key(), &identity)?;
    let identity = identity.version_line_only();
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "modeling case")?;
        let start = Instant::now();
        // The preregistered partition is consulted first and decided from the
        // template identity, so a declined cell is never handed to the
        // analyzer and cannot produce an empty finding list that later reads
        // as a negative.
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            modeling_partition_outcome(plan.tool, case, &plan.raw_dir, &identity.version)?
        {
            (outcome, vec![reason], raw_path)
        } else {
            match plan.tool {
                ModelingTool::Bifrost => run_bifrost_modeling_case(binary, path, case, &plan)?,
                ModelingTool::Codeql => run_codeql_case_for_language(
                    binary,
                    codeql_packs,
                    path,
                    case,
                    Path::new(
                        plan.language
                            .artifact(ModelingTool::Codeql)
                            .expect("every wave-M1 language has a CodeQL modeling query"),
                    ),
                    // The modeling matrix runs no endpoint probe: an absent
                    // *declared* endpoint is frequently the assertion a
                    // modeling negative makes.
                    None,
                    &plan.raw_dir,
                    modeling_codeql_language(plan.language)?,
                )?,
                // FlowDroid's modeling run needs the full APK-materialization
                // toolchain and a digest-witnessed jar identity rather than a
                // single binary path, so `run_flowdroid_modeling` owns it and
                // the CLI never routes the tool here.
                ModelingTool::Flowdroid => bail!(
                    "FlowDroid modeling runs through run-flowdroid-modeling, which witnesses the pinned jar identity; this generic path has no toolchain for it"
                ),
                ModelingTool::Infer => run_infer_modeling_case(
                    binary,
                    javac.unwrap_or(Path::new("javac")),
                    infer_config
                        .as_ref()
                        .expect("Infer run resolved its configuration"),
                    path,
                    case,
                    &plan,
                )?,
                ModelingTool::Joern => {
                    let (script, semantics, raw_root) =
                        joern_paths.as_ref().expect("Joern run resolved its paths");
                    run_joern_modeling_case(binary, script, semantics, path, case, &plan, raw_root)?
                }
                ModelingTool::Semgrep => run_semgrep_modeling_case(
                    binary,
                    semgrep_rule
                        .as_ref()
                        .expect("Semgrep run resolved its rule"),
                    path,
                    case,
                    &plan,
                )?,
                // Pysa's identity is a witnessed pair, so its modeling run is
                // `run_pysa_modeling` and never dispatches here.
                ModelingTool::Pysa => bail!(
                    "Pysa modeling runs through run_pysa_modeling with the pinned pair, not through the single-binary runner"
                ),
                // OpenTaint's run is driven by `run_opentaint_modeling`,
                // which witnesses the release assets' digests instead of a
                // binary banner; `run_modeling` is never entered for it.
                ModelingTool::Opentaint => bail!(
                    "the OpenTaint modeling run is driven by run-opentaint-modeling, which witnesses the pinned release assets; run_modeling has no OpenTaint arm"
                ),
            }
        };
        results.push(normalized_result(
            case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }
    let report = normalized_report(
        plan.tool.key(),
        &identity,
        &hash_paths(&plan.configuration_paths)?,
        &revision,
        started,
        results,
    )?;
    write_and_validate_report(&plan.report, &report)?;
    // The scored/declined split is a property of the preregistered partition,
    // not of the run, so it is stated from the partition rather than counted
    // off the outcomes: a reader who sees "20 declined" is reading a
    // capability classification made before the analyzer was invoked.
    let scored = modeling_supported_templates(plan.tool);
    let scored_assertions = plan
        .cases
        .iter()
        .filter(|(_, case)| {
            case["template_id"]
                .as_str()
                .is_some_and(|template| scored.contains(&template))
        })
        .count();
    // Categories are counted from the scored templates rather than divided out
    // of them: Amendment A3's template-level override splits one of Semgrep's
    // categories, so a category can be scored by one of its two templates.
    let scored_categories: BTreeSet<ModelingCategory> = scored
        .iter()
        .filter_map(|template| modeling_category(template))
        .collect();
    println!(
        "wrote {} ({scored_assertions} scored, {} preregistered-unsupported, {} of six categories scored for {})",
        plan.report.display(),
        plan.cases.len() - scored_assertions,
        scored_categories.len(),
        plan.tool.pinned_identity()
    );
    Ok(())
}
