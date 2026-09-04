//! The tool-native model profile: the preregistered activation surface each
//! analyzer's shipped models are invoked through, its partition and
//! amendments, and the tier's run planner. Never pooled with the
//! benchmark-controlled matrix. See docs/native-profile.md.

use crate::adapters::bifrost::BIFROST_NATIVE_POLICY_PACK_FLAG;
use crate::adapters::codeql::{
    CODEQL_NATIVE_QUERY_PACKS, CODEQL_NATIVE_SUITE_KIND, CODEQL_NATIVE_THREAT_MODEL,
    run_codeql_native_case,
};
use crate::adapters::flowdroid::FLOWDROID_NATIVE_CATALOG_ARGUMENT;
use crate::adapters::joern::JOERN_MODELING_SCRIPT;
use crate::adapters::pysa::PYSA_NATIVE_SUITE_RELATIVE;
use crate::adapters::semgrep::{
    SEMGREP_NATIVE_PROVENANCE_FILE, SEMGREP_NATIVE_UPSTREAM, run_semgrep_native_case,
    semgrep_native_rules_dir,
};
use crate::adapters::{ModelingLanguage, ModelingTool, witness_tool_identity};
use crate::cases::{case_paths, fixture_revision, validate_cases, validate_kernel_population_with};
use crate::evidence::{
    SarifAnchorMatch, SinkAnchorLocation, anchor_marker_line, sarif_messages,
    sarif_result_anchor_match, sarif_result_count,
};
use crate::freeze::required_string;
use crate::modeling::{MODELING_TEMPLATE_PREFIX, ModelingCategory, modeling_case};
use crate::report::{ADAPTER_VERSION, normalized_result, write_and_validate_report};
use crate::runtime::{clear_stale_case_timing, now_seconds, write_run_environment};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, time::Instant};

// ---------------------------------------------------------------------------
// The tool-native model profile.
//
// Everything in this section is transcribed from docs/native-profile.md, the
// preregistration artifact that merged before any native fixture, vendored
// ruleset, or run existed. The six template identities, their mapping onto the
// modeling matrix's six categories, and the per-tool activation partition are
// **immutable** on that document's terms: a cell revised after a run is a
// result being relabelled, not an activation classification. Corrections are
// dated amendments in the document, never silent edits here.
//
// The profile shares the `modeling` score tier with the benchmark-controlled
// matrix and is separated from it by `model_profile` alone, so every selector
// below filters on the profile and a corpus-wide check asserts the two
// populations never cross-select.
// ---------------------------------------------------------------------------

/// Every tool-native template ID carries this prefix, the way
/// `dfb-template-model-` distinguishes the benchmark-controlled matrix and
/// `dfb-template-chal-` the challenge tier. No selector has to reason about
/// tags.
pub(crate) const NATIVE_TEMPLATE_PREFIX: &str = "dfb-template-native-";

/// The six preregistered tool-native templates, in the document's own order —
/// one per modeling category, S P Z O E B.
/// `docs/native-profile.md#the-six-native-templates`.
pub(crate) const NATIVE_TEMPLATE_IDS: [&str; 6] = [
    "dfb-template-native-source-sink",
    "dfb-template-native-propagator",
    "dfb-template-native-sanitizer",
    "dfb-template-native-summary",
    "dfb-template-native-entrypoint",
    "dfb-template-native-persistence",
];

/// One positive and one minimally different negative per template — 12
/// assertions for a language whose native population exists at all.
pub(crate) const NATIVE_CASE_COUNT: usize = 2 * NATIVE_TEMPLATE_IDS.len();

/// Every native case is `tool-native`: the models come from the vendor and the
/// benchmark supplies none. The counterpart `benchmark-controlled` profile is
/// never pooled with this one.
pub(crate) const NATIVE_MODEL_PROFILE: &str = "tool-native";

/// The category a native template reports under, decided from the template ID
/// alone. The six templates are one per category, in `ModelingCategory::ALL`
/// order, which is what lets a native scorecard be read beside a
/// benchmark-controlled one category for category.
pub(crate) fn native_category(template: &str) -> Option<ModelingCategory> {
    NATIVE_TEMPLATE_IDS
        .iter()
        .position(|id| *id == template)
        .map(|index| ModelingCategory::ALL[index])
}

/// One cell of the preregistered per-tool activation partition: a tool, a
/// template, and either a scored decision or the document's verbatim rationale
/// for declining it.
///
/// Unlike `MODELING_PARTITION`, this partition is keyed by **template** rather
/// than by category. The modeling matrix partitions a declaration *surface*,
/// which a tool has or lacks per category; this one partitions an *activation*,
/// which a vendor can ship for one template of a category and not another.
pub(crate) struct NativePartitionCell {
    pub(crate) tool: ModelingTool,
    pub(crate) template: &'static str,
    /// `None` when the template is scored for this tool. `Some(reason)` when
    /// its activation is `unsupported`, carrying the rationale the report
    /// retains.
    pub(crate) unsupported_reason: Option<&'static str>,
}

/// The preregistered per-tool activation partition, transcribed cell for cell
/// from `docs/native-profile.md#partition-summary`.
///
/// Cells the document marks *to be verified* are recorded here as
/// `unsupported`, per the rule stated at the head of its tables: unverifiable
/// is unsupported until shown otherwise, and promoting one is a dated
/// amendment. That is why three of the four tools enter with nothing scored —
/// which is a statement about product packaging, not about an engine.
pub(crate) const NATIVE_PARTITION: &[NativePartitionCell] = &[
    // Bifrost — v0.10.8: 0 / 6. The standalone policy CLI ships no taint
    // policy and no source/sink endpoint catalog, so no template can produce a
    // finding regardless of what else it can express.
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "the standalone policy CLI ships no taint policy and no source or sink endpoint \
             catalog: the built-in catalog `--list-policies` prints is one `bifrost.code-smells` \
             pack of structural correctness and performance checks. Shipping the first open-core \
             security endpoints — whose candidate inventory names `System.getenv` and \
             `Runtime.exec` — is BrokkAi/bifrost-dev #2620, still open",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "same absent endpoint catalog (BrokkAi/bifrost-dev #2620). Procedure-summary packs \
             (#1871) carry propagation rather than endpoints, and propagation with no source and \
             no sink carries nothing anywhere",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "restated by Amendment A10: a sanitizer declaration arrives only through \
             `--policy-file`, which this profile's activation contract forbids, and the built-in \
             packs declare no sanitizer and — prior to that — no source and no sink for one to \
             sit between (the same absent endpoint catalog as templates 1 and 2, \
             BrokkAi/bifrost-dev #2620). A barrier on a flow that cannot start is unobservable in \
             either direction. The preregistration declined this cell instead on the adapter \
             README's \"Sanitizer lowering is a future Bifrost CLI capability\", which Amendment \
             A9 measured false and withdrew",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "the adapter README: \"External semantic-model activation requires an embedding with \
             an explicit catalog, so the modeled-external case is reported as `unsupported` by \
             this CLI adapter with an explicit retained reason. It is not a negative result.\" \
             Activating a catalog from the standalone CLI is BrokkAi/bifrost-dev #2691, still open",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "to be verified — unsupported until shown: no entry-root convention is described \
             anywhere for the policy CLI, and no endpoint catalog exists for its argument to \
             reach in any case",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Bifrost,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some(
            "to be verified — unsupported until shown: no persistence-boundary vocabulary is \
             described anywhere for any adapter, Bifrost included",
        ),
    },
    // CodeQL — CLI 2.26.4, shipped `security-extended` suites: 6 / 6.
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Codeql,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: None,
    },
    // FlowDroid — 2.15.1, Java only (Amendment A19): 0 / 6, on the evidence of
    // the shipped catalog's own text. The activation contract is live — the
    // released CLI requires `-s`, the vendor's documented default
    // `SourcesAndSinks.txt` ships inside the pinned jar, and pointing the flag
    // at that catalog extracted verbatim (with the release default's
    // summariesManual taint wrapper) is the shipped product deciding — but the
    // catalog binds no identity any native template uses, so every cell is
    // declined the way Amendments A6 and A7 declined Semgrep's JavaScript and
    // Java cells: from shipped-model text, before any run. Amendment A29
    // re-grounded the decline by enumeration and execution
    // (reports/raw/amendment-a29-flowdroid-shipped-surface/, produced by
    // scripts/probe-flowdroid-native-shipped-surface.sh): every declarative
    // surface the pinned jar bundles — the catalog (the only endpoint catalog
    // instance in any format), the EasyTaintWrapper defaults, the callback
    // list, the virtual-edge model, and the 347-class summariesManual set —
    // binds no probe source identity anywhere; a bare invocation has no
    // fallback catalog (zero-exit banner witnessed); the shipped catalog
    // engaged over all twelve Java native fixtures reports `Found 0 leaks
    // from 0 sources` on every one; and a control run with one
    // benchmark-authored getenv source line finds exactly the floor leak,
    // attributing the zeros to the catalog alone.
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "the shipped SourcesAndSinks.txt binds the template's sink — `<java.lang.Runtime: \
             java.lang.Process exec(java.lang.String)> -> _SINK_` is in the catalog — but no \
             shipped source binds a platform environment read: `System.getenv` does not occur \
             in the catalog, whose sources are servlet, Spring, and Android framework \
             identities. A catalog with a bound sink and no applicable source cannot produce a \
             finding on these fixtures (Amendment A19) — and executed with the shipped catalog \
             engaged, the analyzer reports `Found 0 leaks from 0 sources` on both cells, while \
             a one-line control source finds the floor flow (Amendment A29, evidence retained \
             under reports/raw/amendment-a29-flowdroid-shipped-surface/)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "the release default's summariesManual wrapper ships a `String.concat` taint \
             summary, so the propagator half is covered — but no shipped source binds \
             `System.getenv`, and a propagator with nothing to carry produces nothing \
             (Amendment A19; executed silent over both cells, and the EasyTaintWrapper default \
             definitions were enumerated too — the format has no source or sink role at all — \
             Amendment A29)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "the shipped catalog's txt format has no sanitizer role at all — its entries are \
             `_SOURCE_`/`_SINK_`/`_BOTH_` — and the shipped `java.lang.Integer` summary models \
             `parseInt` as taint-*preserving* rather than as a barrier; prior to either, no \
             shipped source binds the flow's environment read, so there is no flow for a \
             sanitizer to be credited against (Amendment A19; executed silent over both cells, \
             Amendment A29)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "summariesManual ships no `java.util.Base64` summary — its five Base64-named \
             summaries are android.util, okio, and commons-codec — and no shipped source binds \
             the environment read that would have to survive the round trip (Amendment A19; \
             executed silent over both cells, Amendment A29)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "FlowDroid's shipped entry convention is the Android component lifecycle derived \
             from the APK manifest; the JVM process-entry convention — `public static void \
             main(String[])` reading its argument vector — does not exist on the analyzed \
             platform, appears in no shipped model, and cannot be a root the manifest does not \
             declare (Amendment A19; executed silent over both cells, Amendment A29)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Flowdroid,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some(
            "no shipped model links `System.setProperty` to `System.getProperty` as a keyed \
             store: the shipped `java.lang.System` summary models `getProperty` as key-argument \
             → return taint — a propagator on the key, not a store read — `setProperty` has no \
             summary at all, and no shipped source binds the environment read that starts the \
             flow (Amendment A19; executed silent over both cells, Amendment A29)",
        ),
    },
    // Infer — v1.3.0, shipped Pulse checker with no taint configuration:
    // 0 / 6, joined by Amendment A14 on a measured silence
    // (reports/raw/amendment-a14-infer-native-silence/, produced by
    // scripts/probe-infer-native-silence.sh): with no `--pulse-taint-config`
    // supplied, `infer analyze --pulse-only --sarif` over the twelve Java
    // native fixtures produced zero findings of any rule, and the invocation
    // passed no configuration path at all — so the pinned release's
    // silently-ignored-missing-config quirk cannot be the explanation; there
    // was nothing to mis-path. Infer's native row exists for Java alone: the
    // pinned distribution executes no JavaScript or Python frontend.
    //
    // Re-grounded by Amendment A28
    // (reports/raw/amendment-a28-infer-native-activation/, produced by
    // scripts/probe-infer-native-activation.sh): the silence is ENGAGED, not
    // merely empty. The distribution bundles one default taint surface —
    // lib/infer/infer/config/taint/, four Objective-C NSLib files declaring
    // `pulse-taint-propagators` only — and a zero-configuration invocation
    // demonstrably parses it (a corrupted copy dies at capture, exit 3, from
    // Config.pulse_taint_config's directory fold). The bundle binds no
    // source, sink, sanitizer, or policy in any language and no Java
    // identity at all, and `infer run` — the full default checker set, not
    // the adapter's `--pulse-only` arm — fires zero findings of any rule on
    // all twelve fixtures, so no live activation decides `not-reached`.
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "the shipped taint bundle is loaded unconditionally and holds no endpoint: the \
             zero-config silence Amendment A14 measured (no configuration supplied — nothing to \
             mis-path, so the silent-missing-config quirk cannot be the explanation) is proven \
             engaged by Amendment A28 — the bundled `config/taint/` tree parses on every \
             invocation, declares Objective-C propagators only, binds no source, sink, or \
             policy in any language, and the full default checker set (`infer run`) decides \
             nothing on any of the twelve Java native fixtures either (Amendments A14, A28)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "same engaged-and-silent measurement (Amendments A14, A28): the one thing the \
             release ships natively is propagators — Objective-C NSLib rows a Java procedure \
             can never match — and a propagator needs a shipped source and sink to carry \
             anything between; the release ships neither, in any language",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "same engaged-and-silent measurement (Amendments A14, A28): the sanitizer surface Amendment A13 measured \
             load-bearing is reachable only through `--pulse-taint-config`, which this profile's \
             activation contract supplies nothing through, and the shipped product declares no \
             sanitizer and no endpoints for one to sit between",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "same engaged-and-silent measurement (Amendments A14, A28): no shipped summary catalog exists — the \
             taint question itself is off absent a `--pulse-taint-config`, so a base64 round \
             trip has no flow to survive",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "same engaged-and-silent measurement (Amendments A14, A28), and doubly out of reach: the shipped product \
             activates no taint question, and Amendment A13 measured that the pulse-taint \
             surface has no entry-root vocabulary even when configured",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Infer,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some(
            "same engaged-and-silent measurement (Amendments A14, A28), and doubly out of reach: the shipped product \
             activates no taint question, and the pulse-taint surface has no store-write/\
             store-read vocabulary even when configured (Amendment A13)",
        ),
    },
    // Joern — 4.0.614, `DefaultSemantics` only: 0 / 6.
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "`DefaultSemantics` is a table of flow constraints — operator semantics, C standard \
             library entries, and a short list of JVM method full names — and ships no source \
             catalog and no sink catalog. Every Joern population in this benchmark selects its \
             endpoints through the adapter's own query parameters, which is exactly what the \
             tool-native activation rule forbids. And the version-pinned `joern-scan` query \
             bundle, installed and executed over every probe fixture with zero benchmark input, \
             fires no query on any cell: it ships no JavaScript or Python query package at all, \
             and its one query naming this profile's command sink (`call-to-exec`) filters the \
             method-name property with a full-match regex that matches zero methods on a \
             `javasrc2cpg` graph (Amendment A26, evidence retained under \
             reports/raw/amendment-a26-joern-scan-native/)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "`DefaultSemantics` carries propagation entries but no endpoints; with no shipped \
             source and no shipped sink there is nothing to propagate between",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "`NilSemantics` is the mechanism a sanitizer would use, but the distribution \
             declares none of the three platform sanitization idioms, and no endpoint catalog \
             ships for a sanitizer to sit between",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "the JVM entries in `DefaultSemantics` do not include `java.util.Base64`, and \
             neither Python nor JavaScript has any entry at all",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "entry roots are query-selected in every Joern population here; the distribution \
             activates no entry-point convention by itself",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Joern,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some("no persistence vocabulary ships with the distribution"),
    },
    // Semgrep CE — 1.175.0 (`--oss-only`): 0 / 6 until a snapshot is vendored.
    // Every cell is *to be verified at vendoring*, which this document's own
    // rule records as unsupported; promotion is a dated amendment carrying the
    // vendored commit as its evidence.
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "to be verified at vendoring — unsupported until shown: the upstream head's \
             taint-mode rules cover the template's command sinks (`dangerous-system-call.yaml` \
             declares `os.system`) but bind their `pattern-sources` to framework endpoints — \
             Flask, Django, DRF — rather than to a platform environment read. Whether any \
             vendored rule binds one is the snapshot's to answer, and no snapshot is vendored",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "to be verified at vendoring — unsupported until shown: which rules the snapshot \
             carries, and how the pinned CE engine's default propagation treats the platform \
             join, are both undecided until a commit is pinned",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "to be verified at vendoring — unsupported until shown: sanitizer credit in the \
             official rules is per-rule rather than global, so it is unverifiable before the \
             snapshot exists",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "arg-to-return summary semantics are outside CE's propagator vocabulary on the \
             pinned version, established by execution in \
             docs/modeling-matrix.md#semgrep-ce--11750---oss-only; a shipped rule cannot supply \
             what the engine does not express",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "to be verified at vendoring — unsupported until shown: the upstream rules' entry \
             conventions are framework-shaped, and whether any covers `sys.argv`, \
             `process.argv`, or a `main` parameter is the snapshot's to answer",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Semgrep,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some(
            "the pinned CE engine has no interprocedural taint at all — `--pro-intrafile` \
             requires Semgrep Pro — so a store round trip the shipped rules do not link \
             themselves is carried by nothing else",
        ),
    },
    // Pysa — pyre-check 0.10.0 + Pyrefly 1.2.0, shipped taint model suite:
    // 6 / 6, Python-scoped. Added by Amendment A17: the pinned wheel ships a
    // real suite (`lib/pyre_check/taint/` — core_privacy_security's
    // taint.config and models plus common's propagation models), activated by
    // pointing `taint_models_path` at it with `--no-verify`, both facts
    // established by probe before any native fixture was scanned
    // (reports/raw/amendment-a14-pysa-native/,
    // scripts/probe-pysa-native-activation.sh). Every category's role is
    // present in the shipped catalog, so every template has an activation to
    // measure; the absent platform sources (`os.environ`, `sys.argv`) are the
    // preregistered expectation the runs measure, never a reason to decline a
    // cell. The Python scoping itself is enforced where the activation is
    // assembled (`native_activation` refuses a non-Python language), never by
    // these cells.
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: None,
    },
    NativePartitionCell {
        tool: ModelingTool::Pysa,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: None,
    },
    // OpenTaint — analyzer/2026.08.27.17eb0fe, Java only: 0 / 6. Added by
    // Amendment A23. The pinned release ships two assets: the analyzer jar
    // and `opentaint-models.tar.gz`. The archive is shipped product — vendor
    // pass-through propagation rows, accumulated-field approximations, and
    // compiled dataflow-approximation classes, this tool's analogue of
    // Joern's DefaultSemantics table — and a native run loads it. But it
    // declares no source, sink, or sanitizer anywhere; every endpoint lives
    // in a `--semgrep-rule-set`, the benchmark's rules are benchmark-authored
    // by definition, and the release ships no rule set of its own. Verified
    // by execution: with the archive loaded and no rule set, the analyzer
    // registers zero rules and reports zero results over the platform's own
    // `System.getenv` → `Runtime.exec`
    // (reports/raw/opentaint-native-activation-probe/, produced by
    // scripts/probe-opentaint-native-activation.sh). This row is Java-only:
    // the other languages have no OpenTaint native denominator, and
    // `native_activation` refuses them before this partition is consulted.
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[0],
        unsupported_reason: Some(
            "the pinned release ships no endpoint catalog: `opentaint-models.tar.gz` is \
             propagation only — passThrough/copy rows, accumulated fields, approximation \
             classes — and no rule set ships, so the analyzer with the shipped assets alone \
             registers zero rules over the platform's own `System.getenv` → `Runtime.exec` \
             (retained native-activation probe). Without a source and a sink, no template in \
             this profile can produce a finding (Amendment A23)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[1],
        unsupported_reason: Some(
            "the shipped models archive is precisely a propagation catalog, and it is \
             genuinely shipped product — but propagation with no shipped source and no \
             shipped sink carries nothing anywhere, the same gap in the same direction as \
             Joern's DefaultSemantics row (Amendment A23)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[2],
        unsupported_reason: Some(
            "no sanitizer appears anywhere in the shipped assets, and prior to that no flow \
             can start for a barrier to be observable against — the same absent endpoint \
             catalog that decides templates 1 and 2 (Amendment A23)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[3],
        unsupported_reason: Some(
            "the archive's dataflow-approximation classes are exactly this template's \
             round-trip material and they do activate — behind endpoints the pinned release \
             does not ship, so the summary has nothing to carry (Amendment A23)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[4],
        unsupported_reason: Some(
            "entry-point *selection* exists (`--debug-run-analysis-on-selected-entry-points`) \
             but selecting a method analyzes it rather than tainting its parameters; sources \
             live in the rule set, and the pinned release ships none (Amendment A23)",
        ),
    },
    NativePartitionCell {
        tool: ModelingTool::Opentaint,
        template: NATIVE_TEMPLATE_IDS[5],
        unsupported_reason: Some(
            "no store vocabulary ships in any asset of the pinned release (Amendment A23)",
        ),
    },
];

/// Dated amendments to `NATIVE_PARTITION`, one row per amended cell.
///
/// The preregistered partition is language-agnostic, because it was written
/// before any snapshot existed and its `TBV` cells said so honestly. A vendored
/// snapshot, though, is *per language*: the document's own vendoring rule puts
/// one under `adapters/semgrep/native/<language>/`, and reading its rules can
/// only answer that language's cells. An amendment therefore carries a language
/// as well as a tool and a template, and this table is where it lands —
/// additive, dated in the document, and never a silent edit to the
/// preregistration above.
///
/// `None` promotes a cell to **scored**; `Some(reason)` retains or restates an
/// `unsupported` decision. A cell with no row here keeps whatever
/// `NATIVE_PARTITION` preregistered for it.
pub(crate) const NATIVE_PARTITION_AMENDMENTS: [(
    ModelingTool,
    ModelingLanguage,
    &str,
    Option<&'static str>,
); 18] = [
    // Amendment A8 (2026-08-27) — Semgrep CE 1.174.0 × Python, all six
    // templates promoted to scored on the evidence of the vendored snapshot
    // (semgrep/semgrep-rules @ 40b8c63f, `python/lang/security/`), read as rule
    // text before any scan. `audit/dangerous-system-call-tainted-env-args.yaml`
    // is a `mode: taint` rule whose `pattern-sources` bind the platform
    // identities `os.environ`, `os.getenv`, and `sys.argv` — not a framework
    // endpoint — and whose `pattern-sinks` bind `os.system`. Both endpoints of
    // every Python template are therefore covered by one shipped rule, and what
    // remains is the measurement rather than the activation.
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[0],
        None,
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[1],
        None,
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[2],
        None,
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[3],
        None,
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[4],
        None,
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        NATIVE_TEMPLATE_IDS[5],
        None,
    ),
    // Amendments A6 (2026-08-27) and A27 (2026-09-02) — Semgrep CE ×
    // JavaScript, all six cells retained unsupported. A6 read the vendored
    // snapshot (semgrep/semgrep-rules @ 40b8c63f, `javascript/lang/security/`,
    // thirty rule documents) and found no rule binding a platform source; the
    // preregistered "no snapshot is vendored" rationale was discharged there
    // but never mirrored here, so the retained reports kept carrying it. A27
    // corrects that, and re-grounds the decline on measurement: the vendored
    // tree is the COMPLETE upstream `javascript/lang/security/` at the pinned
    // commit (file-list and byte identical), no rule anywhere in the upstream
    // `javascript/` or `typescript/` trees at that commit mentions
    // `process.env` or `process.argv`, and the pinned engine run over all
    // twelve fixtures with the snapshot emits zero findings and zero errors
    // (scripts/probe-semgrep-jsjava-native.sh, retained under
    // reports/raw/amendment-a27-semgrep-jsjava-native/).
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[0],
        Some(
            "no shipped platform-source model: the snapshot's two rules binding \
             `child_process.execSync` (`detect-child-process.yaml`, \
             `audit/dangerous-spawn-shell.yaml`) source only from an enclosing function's \
             parameter, and `process.env` occurs in no rule of the snapshot — nor anywhere in \
             the upstream `javascript/` or `typescript/` trees at the pinned commit — and the \
             pinned engine over every fixture with the snapshot emits zero findings \
             (Amendments A6/A27, reports/raw/amendment-a27-semgrep-jsjava-native/)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[1],
        Some(
            "no shipped platform source for the propagator to carry: \
             `audit/path-traversal/path-join-resolve-traversal.yaml` binds the `path.join` hop \
             but sources from a function parameter, and no rule binds `process.env` (Amendment \
             A6, execution-confirmed by A27's zero-finding field run)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[2],
        Some(
            "no rule reaches the cell to credit or refuse the idiom: `encodeURIComponent` \
             occurs nowhere in the snapshot, and sanitizer credit in the official rules is \
             per-rule (Amendment A6, execution-confirmed by A27's zero-finding field run)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[3],
        Some(
            "no shipped platform source, and arg-to-return summary semantics are outside CE's \
             propagator vocabulary on the pinned version, established by execution in \
             docs/modeling-matrix.md#semgrep-ce--11750---oss-only (Amendment A6, \
             execution-confirmed by A27)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[4],
        Some(
            "the snapshot's universal entry convention is a function parameter, not the \
             platform's: `process.argv` appears in no vendored rule, nor anywhere in the \
             upstream `javascript/` or `typescript/` trees at the pinned commit (Amendments \
             A6/A27)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Javascript,
        NATIVE_TEMPLATE_IDS[5],
        Some(
            "no rule links a write to `process.env.<NAME>` to a read of it, and the pinned CE \
             engine has no interprocedural taint (`--pro-intrafile` requires Pro) (Amendment \
             A6, execution-confirmed by A27's zero-finding field run)",
        ),
    ),
    // Amendments A7 (2026-08-27) and A27 (2026-09-02) — Semgrep CE × Java,
    // all six cells retained unsupported, on the same movement as the
    // JavaScript block above: A7's snapshot reading is mirrored here at last,
    // re-grounded by A27's enumeration (the vendored tree is the complete
    // upstream `java/lang/security/` at the pinned commit; `System.getenv`,
    // `System.getProperty`, and `System.setProperty` occur in no rule
    // anywhere in the upstream `java/` tree) and by its field run (twelve
    // scans, zero findings, zero errors).
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[0],
        Some(
            "no shipped platform-source model: `System.getenv` occurs in no rule of the \
             snapshot — nor anywhere in the upstream `java/` tree at the pinned commit — the \
             two rules whose sink is the template's command API bind no source, the one \
             taint-mode rule reaching `Runtime.exec` sources from `HttpServletRequest`, and \
             the pinned engine over every fixture with the snapshot emits zero findings \
             (Amendments A7/A27, reports/raw/amendment-a27-semgrep-jsjava-native/)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[1],
        Some(
            "no vendored rule references `String.concat`, the concatenation-shaped rules match \
             `+` or `String.format` inside a sink argument without binding a source, and no \
             rule binds a platform source for a propagator to carry (Amendment A7, \
             execution-confirmed by A27's zero-finding field run)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[2],
        Some(
            "no vendored rule declares `Integer.parseInt` or `String.valueOf` as a sanitizer — \
             neither identifier occurs in the snapshot — and no applicable rule exists at the \
             cells the idiom would guard (Amendment A7, execution-confirmed by A27's \
             zero-finding field run)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[3],
        Some(
            "`java.util.Base64` occurs nowhere in the snapshot, and arg-to-return summary \
             semantics are outside CE's propagator vocabulary on the pinned version, \
             established by execution in docs/modeling-matrix.md#semgrep-ce--11750---oss-only \
             (Amendments A7/A27)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[4],
        Some(
            "no vendored rule binds `main(String[] args)` or the argument vector — neither \
             `void main` nor `System.` occurs in the snapshot, and every entry convention it \
             carries is framework-shaped (Amendments A7/A27)",
        ),
    ),
    (
        ModelingTool::Semgrep,
        ModelingLanguage::Java,
        NATIVE_TEMPLATE_IDS[5],
        Some(
            "no vendored rule names `System.setProperty` / `System.getProperty` as a store \
             pair — neither occurs anywhere in the upstream `java/` tree at the pinned commit \
             — and the pinned CE engine has no interprocedural taint (Amendment A7, \
             execution-confirmed by A27's zero-finding field run)",
        ),
    ),
];

/// The decision for one tool × language × native template: `None` when the
/// template is scored, `Some(reason)` when the tool's shipped model set cannot
/// be activated for it. Amendments are consulted first; every preregistered
/// cell is present, so an unknown template is a programming error rather than a
/// silent scored default.
pub(crate) fn native_partition_reason(
    tool: ModelingTool,
    language: ModelingLanguage,
    template: &str,
) -> Result<Option<&'static str>> {
    if native_category(template).is_none() {
        bail!("{template:?} is not one of the six preregistered tool-native templates");
    }
    if let Some((_, _, _, decision)) = NATIVE_PARTITION_AMENDMENTS
        .iter()
        .find(|(t, l, id, _)| *t == tool && *l == language && *id == template)
    {
        return Ok(*decision);
    }
    NATIVE_PARTITION
        .iter()
        .find(|cell| cell.tool == tool && cell.template == template)
        .map(|cell| cell.unsupported_reason)
        .with_context(|| {
            format!(
                "the tool-native partition has no cell for {} × {template}",
                tool.key()
            )
        })
}

/// The retained `unsupported` reason for a declined native cell, or `None` when
/// the cell is scored. The partition's rationale is carried verbatim; the prefix
/// names the template, its category, and the tool identity **the run
/// witnessed**, so the reason is auditable without opening the document.
///
/// The Bifrost native row declines all six templates in every language and
/// therefore never hands a fixture to the binary. That is a property of the
/// *cells*, not of the run: the run still reads the binary's own version once
/// ([`witness_tool_identity`]) so that these twelve retained rationales name a
/// build that exists rather than one a constant remembers.
pub(crate) fn native_unsupported_reason(
    tool: ModelingTool,
    language: ModelingLanguage,
    template: &str,
    identity: &str,
) -> Result<Option<String>> {
    let Some(reason) = native_partition_reason(tool, language, template)? else {
        return Ok(None);
    };
    let category = native_category(template).expect("partition resolved the category");
    Ok(Some(format!(
        "tool-native activation of {template} (category {} — {}) is unsupported for {identity} over {} by the activation partition (docs/native-profile.md#partition-summary, as amended): {reason}",
        category.key(),
        category.label(),
        language.display_name(),
    )))
}

/// The native templates a tool is entitled to score for one language, in
/// preregistered order. The preregistered counts are Bifrost 0, CodeQL 6,
/// Joern 0, Semgrep CE 0; amendments move them per language.
pub(crate) fn native_supported_templates(
    tool: ModelingTool,
    language: ModelingLanguage,
) -> Vec<&'static str> {
    NATIVE_TEMPLATE_IDS
        .into_iter()
        .filter(|template| {
            native_partition_reason(tool, language, template)
                .expect("every preregistered template has a partition cell")
                .is_none()
        })
        .collect()
}

/// Everything a tool-native run activates, assembled before the tool is
/// touched. The arguments are the pinned activation shape; they are hashed into
/// the report's `configuration_hash` so that "model/version provenance and
/// activation configuration are retained" is a property of the artifact rather
/// than of a README.
pub(crate) struct NativeActivation {
    /// The pinned identity of the shipped model set, recorded in the retained
    /// evidence and in every declined cell's reason.
    pub(crate) identity: String,
    /// The activation arguments the run passes, in order.
    pub(crate) arguments: Vec<String>,
    /// Vendored activation artifacts that must exist before the run and whose
    /// bytes bind the configuration hash.
    pub(crate) configuration_paths: BTreeSet<PathBuf>,
}

/// The pinned activation shape for one tool and language.
///
/// This is the function the no-benchmark-models gate runs against, and its
/// *arguments* are pinned by tests: a later change that splices a
/// benchmark-authored artifact into a native invocation fails the build rather
/// than quietly publishing engine accuracy as product coverage.
///
/// `identity` is the tool identity the run witnessed from the binary
/// ([`witness_tool_identity`]). It is a parameter rather than a constant
/// because the identity a report and its retained decisions carry must be read
/// from the pinned binary — the Bifrost row declines every cell and so never
/// invokes the analyzer over a fixture, which is exactly the case in which an
/// asserted version would go stale unnoticed.
pub(crate) fn native_activation(
    tool: ModelingTool,
    language: ModelingLanguage,
    identity: &str,
) -> Result<NativeActivation> {
    Ok(match tool {
        ModelingTool::Codeql => {
            let (pack, version) = CODEQL_NATIVE_QUERY_PACKS
                .iter()
                .find(|(pack, _)| *pack == format!("codeql/{}-queries", language.key()))
                .with_context(|| {
                    format!(
                        "no pinned CodeQL native query pack for {}",
                        language.display_name()
                    )
                })?;
            let suite = format!(
                "{pack}@{version}:codeql-suites/{}-{CODEQL_NATIVE_SUITE_KIND}.qls",
                language.key()
            );
            NativeActivation {
                identity: format!("{identity} shipped suite {suite}"),
                arguments: vec![
                    format!("--threat-model={CODEQL_NATIVE_THREAT_MODEL}"),
                    suite,
                ],
                configuration_paths: BTreeSet::new(),
            }
        }
        ModelingTool::Semgrep => {
            let dir = semgrep_native_rules_dir(language);
            NativeActivation {
                identity: format!(
                    "{identity} over the pinned snapshot vendored from {SEMGREP_NATIVE_UPSTREAM} into {}",
                    dir.display()
                ),
                arguments: vec![
                    "--oss-only".to_string(),
                    format!("--config={}", dir.display()),
                ],
                configuration_paths: BTreeSet::from([dir.join(SEMGREP_NATIVE_PROVENANCE_FILE)]),
            }
        }
        ModelingTool::Bifrost => NativeActivation {
            identity: format!("{identity} built-in policy packs"),
            arguments: vec![
                BIFROST_NATIVE_POLICY_PACK_FLAG.to_string(),
                "bifrost.code-smells".to_string(),
            ],
            configuration_paths: BTreeSet::new(),
        },
        // The shipped product as shipped: `analyze --pulse-only --sarif` and
        // no `--pulse-taint-config`, which is precisely the activation the
        // measured silence of Amendment A14 was read from. Java alone: the
        // pinned distribution executes no JavaScript or Python frontend, so
        // those languages have no Infer native denominator at all — which is
        // different from a 0 / 6 decline.
        ModelingTool::Infer => {
            if language != ModelingLanguage::Java {
                bail!(
                    "{} has no {} tool-native denominator: the pinned distribution executes no {} frontend, so its native row exists for Java alone (docs/native-profile.md, Amendment A14). No denominator is different from a zero; refusing to write a report",
                    tool.pinned_identity(),
                    language.display_name(),
                    language.display_name()
                );
            }
            NativeActivation {
                identity: format!("{identity} shipped Pulse checker, no taint configuration"),
                arguments: vec!["--pulse-only".to_string()],
                configuration_paths: BTreeSet::new(),
            }
        }
        // The suite the pinned pyre-check wheel ships in its own
        // distribution, activated by pointing `taint_models_path` at it with
        // `--no-verify` (docs/native-profile.md, Amendment A17; both facts
        // established by probe). The arguments name the shape rather than a
        // machine path — the runner resolves the directory beside the pinned
        // binary it was handed and digests its bytes into the run identity,
        // because a venv-absolute path would make the configuration hash a
        // fact about one machine instead of one suite. Python alone: the
        // engine analyzes one language, so the other languages have no Pysa
        // native denominator at all — which is different from a 0 / 6
        // decline.
        ModelingTool::Pysa => {
            if language != ModelingLanguage::Python {
                bail!(
                    "{} has no {} tool-native denominator: the engine analyzes Python alone, so its native row exists for Python alone (docs/native-profile.md, Amendment A17). No denominator is different from a zero; refusing to write a report",
                    tool.pinned_identity(),
                    language.display_name()
                );
            }
            NativeActivation {
                identity: format!(
                    "{identity} shipped taint model suite {PYSA_NATIVE_SUITE_RELATIVE} with --no-verify"
                ),
                arguments: vec![
                    "--no-verify".to_string(),
                    format!("taint_models_path={PYSA_NATIVE_SUITE_RELATIVE}"),
                ],
                configuration_paths: BTreeSet::new(),
            }
        }
        ModelingTool::Joern => NativeActivation {
            identity: format!("{identity} DefaultSemantics only"),
            arguments: Vec::new(),
            configuration_paths: BTreeSet::new(),
        },
        // FlowDroid's shipped model surface is entirely inside the pinned,
        // digest-witnessed jar: the vendor's documented default
        // `SourcesAndSinks.txt` catalog (the released CLI requires `-s`, so
        // the activation shape extracts that catalog from the jar verbatim
        // and points the flag at it) and the release default's StubDroid
        // `summariesManual` taint wrapper. No vendored snapshot exists to
        // hash — the jar digest gate is the provenance — so the
        // configuration-path set is empty and the arguments name the
        // activation shape (Amendment A19).
        ModelingTool::Flowdroid => {
            if language != ModelingLanguage::Java {
                bail!(
                    "{} has no {} tool-native denominator: the analyzer consumes JVM bytecode, so its native row exists for Java alone (docs/native-profile.md, Amendment A19). No denominator is different from a zero; refusing to write a report",
                    tool.pinned_identity(),
                    language.display_name()
                );
            }
            NativeActivation {
                identity: format!(
                    "FlowDroid {identity} shipped SourcesAndSinks.txt catalog (extracted verbatim from the pinned soot-infoflow-cmd jar) and default summariesManual taint wrapper"
                ),
                arguments: vec![
                    "-s".to_string(),
                    FLOWDROID_NATIVE_CATALOG_ARGUMENT.to_string(),
                ],
                configuration_paths: BTreeSet::new(),
            }
        }
        // The pinned release's two assets, and nothing else. The models
        // archive is shipped product (Amendment A23) and a native run loads
        // it through the pinned flags below; the archive-member notation is
        // symbolic — the runner extracts the digest-verified archive to a
        // scratch root per run — so the pinned shape is stable however the
        // scratch paths fall. The line the activation rule draws for this
        // adapter is `--semgrep-rule-set`: every endpoint lives in a rule
        // set, the benchmark's rules are benchmark-authored by definition,
        // and the release ships none, so the shape carries no rule-set
        // argument at all and a test pins that absence.
        ModelingTool::Opentaint => {
            if language != ModelingLanguage::Java {
                bail!(
                    "{} has no {} tool-native denominator at all: the pinned engine analyzes JVM bytecode only, so its native row exists for Java alone (docs/native-profile.md, Amendment A23). No denominator is different from a zero; refusing to write a report",
                    tool.pinned_identity(),
                    language.display_name()
                );
            }
            NativeActivation {
                identity: format!("{identity} shipped models archive only — no rule set"),
                arguments: vec![
                    "--project-kind=unknown".to_string(),
                    "--debug-run-analysis-on-selected-entry-points=*".to_string(),
                    "--passthrough-approximations=opentaint-models.tar.gz!/java/accumulated-fields.yaml"
                        .to_string(),
                    "--passthrough-approximations=opentaint-models.tar.gz!/java/config".to_string(),
                    "--java-dataflow-approximations=opentaint-models.tar.gz!/java/dataflow/build/classes/java/main"
                        .to_string(),
                ],
                configuration_paths: BTreeSet::new(),
            }
        }
    })
}

/// Every benchmark-authored model artifact in the repository, derived from the
/// benchmark-controlled matrix's own constants rather than restated, so a new
/// modeling artifact is covered by this gate the moment it is declared.
pub(crate) fn benchmark_model_artifacts() -> BTreeSet<String> {
    let mut artifacts = BTreeSet::from([JOERN_MODELING_SCRIPT.to_string()]);
    for tool in ModelingTool::ALL.iter().copied() {
        for language in [
            ModelingLanguage::Java,
            ModelingLanguage::Javascript,
            ModelingLanguage::Python,
        ] {
            if let Some(artifact) = language.artifact(tool) {
                artifacts.insert(artifact.to_string());
            }
        }
    }
    artifacts
}

/// The activation rule, enforced rather than trusted: **only shipped models.**
///
/// A tool-native run must include no benchmark-authored source, sink,
/// sanitizer, propagator, summary, entry-point, or store declaration. This gate
/// reads the pinned activation shape before the analyzer is touched and refuses
/// the run if any argument names a benchmark model artifact — the difference
/// between measuring a product's coverage and measuring our own models is a
/// single spliced path, and that path must not be able to arrive silently.
pub(crate) fn require_no_benchmark_models(tool: ModelingTool, arguments: &[String]) -> Result<()> {
    let artifacts = benchmark_model_artifacts();
    for argument in arguments {
        if let Some(artifact) = artifacts
            .iter()
            .find(|artifact| argument.contains(*artifact))
        {
            bail!(
                "the tool-native activation shape for {} names the benchmark-authored model artifact {artifact} (in argument {argument:?}); docs/native-profile.md#the-activation-rule admits only models the vendor ships, and a run that loaded one would publish engine accuracy as product coverage",
                tool.pinned_identity()
            );
        }
    }
    Ok(())
}

/// Whether a case is a tool-native assertion of this language. The profile
/// clause is what keeps it out of every benchmark-controlled selection.
pub(crate) fn native_case(case: &Value, language: ModelingLanguage) -> bool {
    case["language"] == language.key()
        && case["track"] == "taint"
        && case["score_tier"] == "modeling"
        && case["model_profile"] == NATIVE_MODEL_PROFILE
}

/// A `modeling`-tier case of the tool-native profile, language-agnostic.
pub(crate) fn tool_native_case(case: &Value) -> bool {
    case["score_tier"] == "modeling" && case["model_profile"] == NATIVE_MODEL_PROFILE
}

/// Corpus-wide tool-native checks, run by `validate` over every committed case.
///
/// The mirror of `validate_modeling_cases`, with the one structural difference
/// the shared tier forces: here the template family implies the **profile** as
/// well as the tier, because the tier alone no longer identifies the
/// population.
pub(crate) fn validate_native_cases(cases: &[(PathBuf, Value)]) -> Result<()> {
    for (path, case) in cases {
        let template = required_string(case, "template_id", &path.display().to_string())?;
        let native_template = template.starts_with(NATIVE_TEMPLATE_PREFIX);
        let native_profile = case["model_profile"] == NATIVE_MODEL_PROFILE;
        if native_template != native_profile {
            bail!(
                "{}: template {template:?} and model_profile {:?} disagree; every `{NATIVE_TEMPLATE_PREFIX}` template is `{NATIVE_MODEL_PROFILE}` and every `{NATIVE_MODEL_PROFILE}` case carries one",
                path.display(),
                case["model_profile"]
            );
        }
        if !native_template {
            continue;
        }
        if case["score_tier"] != "modeling" {
            bail!(
                "{}: tool-native cases share the `modeling` score tier with the benchmark-controlled matrix (docs/native-profile.md#same-tier-disjoint-profile); found {:?}",
                path.display(),
                case["score_tier"]
            );
        }
        if !NATIVE_TEMPLATE_IDS.contains(&template) {
            bail!(
                "{}: {template:?} is not one of the six preregistered tool-native templates (docs/native-profile.md#the-six-native-templates)",
                path.display()
            );
        }
        // A native case whose template has no preregistered decision for some
        // adapter would leave that adapter's cell to be decided by a run, which
        // is the one thing the partition exists to prevent.
        let key = required_string(case, "language", &path.display().to_string())?;
        let language = ModelingLanguage::from_key(key).with_context(|| {
            format!(
                "{}: the tool-native profile covers Java, JavaScript, and Python in v1 (docs/native-profile.md#initial-languages); {key:?} has no native denominator",
                path.display()
            )
        })?;
        for tool in ModelingTool::ALL.iter().copied() {
            native_partition_reason(tool, language, template).with_context(|| {
                format!(
                    "{}: no preregistered {} activation decision",
                    path.display(),
                    tool.key()
                )
            })?;
        }
    }
    let languages: BTreeSet<&str> = cases
        .iter()
        .filter(|(_, case)| tool_native_case(case))
        .filter_map(|(_, case)| case["language"].as_str())
        .collect();
    for language in languages {
        let population: Vec<(PathBuf, Value)> = cases
            .iter()
            .filter(|(_, case)| {
                tool_native_case(case) && case["language"].as_str() == Some(language)
            })
            .cloned()
            .collect();
        validate_native_population(&population, &format!("{language} tool-native population"))?;
    }
    Ok(())
}

/// Balance and completeness for one language's tool-native population: exactly
/// one positive and one minimally different negative for each of the six
/// templates — 12 assertions — under one model profile.
///
/// An empty population is not a population: the language has no native
/// denominator and there is nothing to balance.
pub(crate) fn validate_native_population(cases: &[(PathBuf, Value)], label: &str) -> Result<()> {
    if cases.is_empty() {
        return Ok(());
    }
    validate_kernel_population_with(cases, label, &NATIVE_TEMPLATE_IDS)
}

/// The corpus-wide profile-disjointness check.
///
/// Tier isolation keeps both modeling populations out of every core,
/// calibration, `language-extension`, and `real-project` denominator. This
/// check is the other half: within the shared tier, the two profiles' selections
/// must never overlap, in either direction, for any language. It is written
/// against the *selectors* rather than against the case fields, because the
/// failure it guards is a selector that filters on the tier and forgets the
/// profile — a fault no assertion about a case's own fields would catch.
pub(crate) fn validate_profile_disjoint_populations(cases: &[(PathBuf, Value)]) -> Result<()> {
    for (path, case) in cases {
        if case["score_tier"] != "modeling" {
            continue;
        }
        for language in [
            ModelingLanguage::Java,
            ModelingLanguage::Javascript,
            ModelingLanguage::Python,
        ] {
            let controlled = modeling_case(case, language);
            let native = native_case(case, language);
            if controlled && native {
                bail!(
                    "{}: selected by both the benchmark-controlled and the tool-native {} population; the two profiles are never pooled (docs/scoring.md#model-profiles)",
                    path.display(),
                    language.display_name()
                );
            }
            if controlled && case["template_id"].as_str().is_some_and(is_native_template) {
                bail!(
                    "{}: carries a tool-native template but is selected by the benchmark-controlled {} population",
                    path.display(),
                    language.display_name()
                );
            }
            if native
                && case["template_id"]
                    .as_str()
                    .is_some_and(|template| template.starts_with(MODELING_TEMPLATE_PREFIX))
            {
                bail!(
                    "{}: carries a benchmark-controlled template but is selected by the tool-native {} population",
                    path.display(),
                    language.display_name()
                );
            }
        }
    }
    Ok(())
}

pub(crate) fn is_native_template(template: &str) -> bool {
    template.starts_with(NATIVE_TEMPLATE_PREFIX)
}

// ---------------------------------------------------------------------------
// Tool-native runners.
//
// Four commands, parameterized by language, mirroring the modeling runners
// exactly: same fail-fast discipline, same partition-before-invocation rule,
// same one-report-per-tool-per-language convention. What differs is the gate in
// the middle — a native run must prove it is supplying *no* models, where a
// modeling run must prove its models are load-bearing.
// ---------------------------------------------------------------------------

pub(crate) fn native_report_path(tool: ModelingTool, language: ModelingLanguage) -> PathBuf {
    PathBuf::from(format!(
        "reports/{}-{}-native.json",
        tool.key(),
        language.key()
    ))
}

pub(crate) fn native_raw_dir(tool: ModelingTool, language: ModelingLanguage) -> PathBuf {
    PathBuf::from(format!(
        "reports/raw/{}-{}-native",
        tool.key(),
        language.key()
    ))
}

/// The population label validation errors are reported under.
pub(crate) fn native_label(language: ModelingLanguage) -> String {
    format!("{} tool-native population", language.display_name())
}

/// Everything a tool-native run needs, assembled before the tool is touched.
pub(crate) struct NativeRunPlan {
    pub(crate) tool: ModelingTool,
    pub(crate) language: ModelingLanguage,
    pub(crate) cases: Vec<(PathBuf, Value)>,
    pub(crate) activation: NativeActivation,
    pub(crate) report: PathBuf,
    pub(crate) raw_dir: PathBuf,
}

/// Select and validate one language's tool-native population.
pub(crate) fn select_native_cases(language: ModelingLanguage) -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if native_case(&case, language) {
            selected.push((path, case));
        }
    }
    validate_native_population(&selected, &native_label(language))?;
    Ok(selected)
}

/// Assemble a tool-native run, failing fast on every condition that would
/// otherwise produce a report that means nothing: no population, a missing
/// pinned activation artifact, or an activation shape that would load a
/// benchmark-authored model.
pub(crate) fn plan_native_run(
    tool: ModelingTool,
    language: ModelingLanguage,
    identity: &str,
) -> Result<NativeRunPlan> {
    validate_cases()?;
    let cases = select_native_cases(language)?;
    if cases.is_empty() {
        bail!(
            "no tool-native population for {}: the {} selection admits no `model_profile: \"{NATIVE_MODEL_PROFILE}\"` case, so there is nothing for {} to be measured over. A language's {NATIVE_CASE_COUNT} native assertions land with its own pull request (docs/native-profile.md#rollout); refusing to write an empty report",
            language.key(),
            language.display_name(),
            tool.pinned_identity()
        );
    }

    let activation = native_activation(tool, language, identity)?;
    // The activation rule, checked before anything is executed.
    require_no_benchmark_models(tool, &activation.arguments)?;
    // A missing pinned activation artifact is this profile's analogue of the
    // modeling matrix's missing model: a hard error that fails the build, never
    // an outcome, because a native run over an absent ruleset would report the
    // vendor's coverage as zero for a reason that has nothing to do with the
    // vendor.
    for path in &activation.configuration_paths {
        if !path.is_file() {
            bail!(
                "the tool-native run for {} needs the pinned activation artifact {}, which does not exist. docs/native-profile.md#provenance-for-vendored-activation-artifacts makes a missing activation artifact a benchmark defect that fails the build; it is never `unsupported`, never `not-reached`, and never a result",
                tool.pinned_identity(),
                path.display()
            );
        }
    }

    Ok(NativeRunPlan {
        tool,
        language,
        cases,
        activation,
        report: native_report_path(tool, language),
        raw_dir: native_raw_dir(tool, language),
    })
}

/// The configuration hash a native report carries.
///
/// Unlike a modeling run, most of a native run's configuration is not a file in
/// this repository — it is a pinned suite name, a pack version, a threat-model
/// group. Hashing the activation arguments alongside whatever vendored bytes
/// exist is what makes issue #16's *"model/version provenance and activation
/// configuration are retained"* a property of the artifact rather than of a
/// README.
pub(crate) fn native_configuration_hash(activation: &NativeActivation) -> Result<String> {
    let mut hasher = Sha256::new();
    hasher.update(activation.identity.as_bytes());
    for argument in &activation.arguments {
        hasher.update(argument.as_bytes());
    }
    for path in &activation.configuration_paths {
        hasher.update(path.to_string_lossy().as_bytes());
        hasher.update(fs::read(path).with_context(|| format!("read {}", path.display()))?);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// Retain the preregistered `unsupported` activation decision for one declined
/// cell, **without invoking the tool**, and return the result-schema outcome.
pub(crate) fn native_partition_outcome(
    tool: ModelingTool,
    language: ModelingLanguage,
    case: &Value,
    activation: &NativeActivation,
    raw_dir: &Path,
    identity: &str,
) -> Result<Option<(&'static str, String, PathBuf)>> {
    let id = required_string(case, "id", "tool-native case")?;
    let template = required_string(case, "template_id", id)?;
    let Some(reason) = native_unsupported_reason(tool, language, template, identity)? else {
        return Ok(None);
    };
    let category = native_category(template).expect("partition resolved the category");
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
            "stage": "preregistered-native-activation-partition",
            "reason": reason,
            "template_id": template,
            "modeling_category": category.key(),
            "modeling_category_label": category.label(),
            "model_profile": NATIVE_MODEL_PROFILE,
            "witnessed_tool_identity": identity,
            "activation_identity": activation.identity,
            "activation_arguments": activation.arguments,
            "partition_source": "docs/native-profile.md#partition-summary",
            "evidence_kind": "retained-capability-decision"
        }))? + "\n",
    )?;
    Ok(Some(("unsupported", reason, raw_path)))
}

/// Resolve a tool-native case's sink anchors, which sit on the **callsite of
/// the real platform API**.
///
/// Every other population in this benchmark declares its own endpoint function
/// and hangs the marker on that declaration, so reconciliation resolves the
/// declared name and then finds the lines that call it. The tool-native profile
/// has no declared entity, by construction: the sink is
/// `child_process.execSync`, `Runtime.exec`, `os.system`, and its body is inside
/// the platform rather than inside the fixture
/// (docs/native-profile.md#the-native-binding-trap). The marker is therefore
/// placed directly on the line that calls the platform API, and that line *is*
/// the callsite.
///
/// This is still a reconciliation anchor and never a model. It decides which
/// finding belongs to which assertion; it tells the analyzer nothing about what
/// a source or a sink is (docs/native-profile.md#the-activation-rule).
pub(crate) fn native_sink_anchor_locations(
    case_path: &Path,
    case: &Value,
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
        locations.push(SinkAnchorLocation {
            file: file.to_string(),
            marker_line: line,
            function_name: marker.to_string(),
            callsite_lines: BTreeSet::from([line]),
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

/// Reconcile a native SARIF document against the case's platform-API callsite.
///
/// One rule differs from every other SARIF reconciliation here, and it follows
/// from what a native run analyzes. Elsewhere the runner points CodeQL at a
/// single adapter query, so *any* finding is a finding about the assertion and
/// one that does not land on the anchor means the reconciliation is untrustworthy
/// — hence `inconclusive`. A native run points CodeQL at a whole shipped
/// `security-extended` suite, which contains hundreds of queries about
/// everything from weak hashing to regular-expression denial of service. A
/// finding those queries produce somewhere other than this assertion's sink is
/// not evidence about this assertion at all; it is a different query answering a
/// different question, and treating it as ambiguity would make every cell
/// inconclusive and measure nothing.
///
/// So an unmatched finding is **retained in the diagnostics and does not make
/// the cell reached**. What it never does is become evidence of a flow: only a
/// finding at the sink anchor does that. Ambiguity — a malformed location, or
/// one finding that matches two anchors — stays `inconclusive` exactly as
/// everywhere else.
///
/// A finding *on* the sink-anchor line is `reached` whatever query produced it,
/// including a rule that fires on the existence of the sink alone. That is
/// deliberate, and it is the profile's own scoring rule
/// (docs/native-profile.md#sink-existence-only-findings-and-how-they-score):
/// polarity is about the flow, so such a finding is a true positive on the
/// positive cell and a false positive on the negative cell.
pub(crate) fn native_sarif_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = sarif_messages(sarif);
    let (outcome, anchor_diagnostics) = native_sarif_anchor_outcome(case_path, case, sarif);
    diagnostics.extend(anchor_diagnostics);
    diagnostics.sort();
    diagnostics.dedup();
    (outcome, diagnostics)
}

pub(crate) fn native_sarif_anchor_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
) -> (&'static str, Vec<String>) {
    if sarif_result_count(sarif) == 0 {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match native_sink_anchor_locations(case_path, case) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove SARIF finding against the native sink anchor: {reason}"
                )],
            );
        }
    };
    native_anchor_tally_outcome(
        sarif["runs"]
            .as_array()
            .into_iter()
            .flatten()
            .flat_map(|run| run["results"].as_array().into_iter().flatten())
            .map(|result| sarif_result_anchor_match(result, &sink_locations)),
        "SARIF",
    )
}

/// Decide one native cell from where its shipped suite's findings landed.
///
/// This is the tool-native profile's *only* reconciliation rule, and both
/// execution arms reach it: CodeQL's SARIF results and Semgrep's JSON results
/// are each classified against the same `SinkAnchorLocation` set and then
/// tallied here, so the two adapters cannot drift into two readings of
/// docs/native-profile.md#outcome-honesty.
///
/// The ordering is that section applied literally:
///
/// - Ambiguity — a location this runner cannot read, or one finding that
///   matches two anchors — is the genuinely *incomplete analysis* the document
///   reserves `inconclusive` for.
/// - A finding on the anchor is `reached`, whatever query produced it.
/// - Everything else is `not-reached`: no finding at all, or findings only away
///   from the anchor. Both are a **coverage miss by an activated model set**,
///   which the document says "is neither" `unsupported` nor `inconclusive` — it
///   "is a plain `not-reached`, which on a positive cell is a false negative and
///   is exactly the number this profile is built to publish". Scoring either as
///   `inconclusive` would quietly lift the cell out of the vendor's denominator.
pub(crate) fn native_anchor_tally_outcome(
    matches: impl Iterator<Item = SarifAnchorMatch>,
    evidence: &str,
) -> (&'static str, Vec<String>) {
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for outcome in matches {
        match outcome {
            SarifAnchorMatch::Matched => matched += 1,
            SarifAnchorMatch::Unmatched => unmatched += 1,
            SarifAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} {evidence} finding(s) have ambiguous sink-anchor locations"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "not-reached",
        vec![format!(
            "{unmatched} shipped-suite finding(s) landed away from this case's platform sink anchor and are not evidence about this assertion"
        )],
    )
}

/// A per-case scratch root for a tool-native run, disjoint from every kernel
/// and modeling run's.
pub(crate) fn native_case_scratch(
    tool: ModelingTool,
    language: ModelingLanguage,
    id: &str,
) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!(
            "dataflowbench-native-{}-{}",
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

/// Run one adapter's tool-native probe set for one language.
///
/// The staged shape mirrors the modeling runners, and is recorded in
/// docs/adapters.md: the population gate, the activation-artifact gate, the
/// no-benchmark-models gate, and the partition's `unsupported` arm are
/// infrastructure; the arm that invokes an analyzer over a *scored* cell lands
/// with the wave-N1 pull request that vendors that adapter's activation
/// snapshot for that language. A tool whose execution arm is not wired yet is a
/// hard error rather than a synthesized outcome — and a tool whose partition
/// scores nothing never reaches that arm, because the partition is consulted
/// first and decided from the template identity.
pub(crate) fn run_native(
    tool: ModelingTool,
    binary: &Path,
    language: ModelingLanguage,
    codeql_packs: Option<&Path>,
) -> Result<()> {
    if let Some(packs) = codeql_packs
        && !packs.is_dir()
    {
        bail!("CodeQL pack search path {} does not exist", packs.display());
    }
    // Witnessed before the plan is assembled, because the plan's activation
    // identity names the tool.
    //
    // This is read **unconditionally**, including for a row the partition
    // scores nothing for. The rule it replaces withheld the version banner from
    // a 0/6 run, on the reasoning that such a run is a capability decision
    // taken before the analyzer is touched. The decision half of that is
    // preserved exactly — no cell is handed to the analyzer, and every outcome
    // is still decided from the template identity — but the conclusion drawn
    // from it was that the report should carry `pinned_identity()`, and an
    // asserted version is not a measurement. A 0/6 row is the case where that
    // matters most: its twelve retained rationales are the whole of its
    // evidence, and a constant would keep naming the previous pin after the
    // binary underneath it moved. Reading `--version` is not analyzing a
    // fixture, so the outcome-honesty contract is untouched by asking.
    let (version, build) = witness_tool_identity(tool, binary)?;
    run_native_with_identity(tool, binary, language, version, build)
}

/// The witnessed-identity half of a tool-native run, shared between the
/// single-binary adapters (whose identity `witness_tool_identity` reads) and
/// FlowDroid (whose identity is two digest-witnessed jars read by
/// `run_flowdroid_native` before this is called).
pub(crate) fn run_native_with_identity(
    tool: ModelingTool,
    binary: &Path,
    language: ModelingLanguage,
    version: String,
    build: String,
) -> Result<()> {
    let plan = plan_native_run(tool, language, &version)?;
    let scored_templates = native_supported_templates(plan.tool, plan.language);

    fs::create_dir_all(&plan.raw_dir)?;
    let started = now_seconds()?;
    let build_identity = format!("{build} — {}", plan.activation.identity);
    write_run_environment(&plan.raw_dir, plan.tool.key(), &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "tool-native case")?;
        let start = Instant::now();
        // The preregistered partition is consulted first and decided from the
        // template identity, so a declined cell is never handed to the analyzer
        // and cannot produce an empty finding list that later reads as a
        // negative.
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            native_partition_outcome(
                plan.tool,
                plan.language,
                case,
                &plan.activation,
                &plan.raw_dir,
                &version,
            )? {
            (outcome, vec![reason], raw_path)
        } else {
            match plan.tool {
                ModelingTool::Codeql => run_codeql_native_case(binary, path, case, &plan)?,
                // Semgrep CE's preregistered partition declines all six
                // templates, and Amendment A8 promoted the six Python cells on
                // the evidence of the vendored snapshot. The rule the document
                // states is that a promotion lands its execution arm in the same
                // pull request, so the arm is here — and it stays unreachable
                // for the languages whose Semgrep cells are still `unsupported`,
                // because the partition above answers those before this match.
                ModelingTool::Semgrep => run_semgrep_native_case(binary, path, case, &plan)?,
                // Bifrost, Infer, and Joern decline every one of the six
                // templates, so the partition arm above answers each of their
                // cells and this arm is unreachable for them today. It stays a
                // hard error rather than a synthesized outcome: an amendment
                // that promotes one of their cells to scored must land the arm
                // that runs it, and until then a promotion fails the run
                // instead of publishing a silent zero.
                // FlowDroid additionally routes through its own runner
                // (`run-flowdroid-native`), which witnesses the jar identity,
                // and OpenTaint through `run-opentaint-native`, which
                // witnesses the release assets' digests; both partitions
                // likewise decline all six templates, so a scored cell
                // reaching this generic arm is the same unwired promotion
                // this error exists to catch.
                ModelingTool::Bifrost
                | ModelingTool::Infer
                | ModelingTool::Joern
                | ModelingTool::Flowdroid
                | ModelingTool::Opentaint => bail!(
                    "the tool-native execution arm for {} × {} is not wired: {id} is a scored cell and no wave has yet had a reason to invoke this adapter natively — its preregistered partition declines all six templates (docs/native-profile.md#partition-summary). A cell promoted by a dated amendment lands its execution arm in the same pull request; synthesizing an outcome here is what docs/adapters.md forbids",
                    plan.tool.pinned_identity(),
                    plan.language.display_name(),
                ),
                // Pysa's identity is a witnessed pair, so its native run is
                // `run_pysa_native` and never dispatches here.
                ModelingTool::Pysa => bail!(
                    "Pysa tool-native runs through run_pysa_native with the pinned pair, not through the single-binary runner"
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
    let report = json!({
        "schema_version": 1,
        "tool": plan.tool.key(),
        "tool_version": version,
        // Both halves of the identity, and both witnessed: the build the binary
        // reported, and the activation surface that build was pointed at.
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": native_configuration_hash(&plan.activation)?,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(&plan.report, &report)?;
    let scored = scored_templates;
    let scored_assertions = plan
        .cases
        .iter()
        .filter(|(_, case)| {
            case["template_id"]
                .as_str()
                .is_some_and(|template| scored.contains(&template))
        })
        .count();
    println!(
        "wrote {} ({scored_assertions} scored, {} preregistered-unsupported, {} of six templates activated for {})",
        plan.report.display(),
        plan.cases.len() - scored_assertions,
        scored.len(),
        plan.tool.pinned_identity()
    );
    Ok(())
}
