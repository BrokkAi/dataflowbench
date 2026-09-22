//! Independently activated Swift runner. Its scratch directories and evidence are never reused.
use super::*;
use sha2::{Digest, Sha256};

const CONFIG: &str = "adapters/codeql/swift";
const SCRIPT: &str = "scripts/run-codeql-swift-case.py";
const QUERY: &str = "adapters/codeql/swift/queries/SwiftKernel.ql";
const PROBE: &str = "adapters/codeql/swift/queries/SwiftKernelEndpointProbe.ql";

pub(crate) fn codeql_swift_configuration_paths() -> BTreeSet<PathBuf> {
    [
        SCRIPT,
        "src/adapters/codeql/swift.rs",
        "adapters/codeql/swift/qlpack.yml",
        "adapters/codeql/swift/codeql-pack.lock.yml",
        "adapters/codeql/swift/activation.json",
        "adapters/codeql/swift/modeling-activation.json",
        "adapters/codeql/swift/partition.json",
        "adapters/codeql/swift/queries/SwiftEndpoints.qll",
        QUERY,
        PROBE,
        "adapters/codeql/swift/queries/SwiftModelIdentity.qll",
        "adapters/codeql/swift/queries/SwiftModelSteps.qll",
        "adapters/codeql/swift/queries/SwiftModeling.ql",
        "adapters/codeql/swift/queries/SwiftModelingOff.ql",
        "adapters/codeql/swift/queries/SwiftModelingEndpointProbe.ql",
        "adapters/codeql/swift/queries/SwiftCalibration.ql",
        "evidence/codeql-swift/activation-218/pack-tree-identities.json",
    ]
    .into_iter()
    .map(PathBuf::from)
    .collect()
}

fn verify_activation() -> Result<Value> {
    for (name, scope) in [
        ("activation.json", "core"),
        ("modeling-activation.json", "modeling-and-calibration"),
    ] {
        let certificate: Value =
            serde_json::from_str(&fs::read_to_string(format!("{CONFIG}/{name}"))?)?;
        if certificate["status"] != "active" || certificate["scope"] != scope {
            bail!("Swift activation is not active: {scope}");
        }
        for key in ["query_sha256", "evidence_sha256"] {
            let entries = certificate[key]
                .as_object()
                .context("missing activation digests")?;
            if entries.is_empty() {
                bail!("empty activation digest set");
            }
            for (path, expected) in entries {
                let digest = format!("{:x}", Sha256::digest(fs::read(path)?));
                if expected.as_str() != Some(&digest) {
                    bail!("Swift activation digest changed: {path}");
                }
            }
        }
    }
    let paths = codeql_swift_configuration_paths();
    if !Command::new("git")
        .args(["ls-files", "--error-unmatch"])
        .args(&paths)
        .output()?
        .status
        .success()
        || !Command::new("git")
            .args(["diff", "--quiet", "HEAD", "--"])
            .args(&paths)
            .status()?
            .success()
    {
        bail!("Swift configuration and partition must be committed unchanged before execution");
    }
    let partition: Value =
        serde_json::from_str(&fs::read_to_string(format!("{CONFIG}/partition.json"))?)?;
    if partition["status"] != "resolved" {
        bail!("Swift partition has not been resolved before scoring");
    }
    Ok(partition)
}

fn at_anchor(result: &Value, anchors: &Value) -> bool {
    result["locations"].as_array().is_some_and(|locations| {
        locations.iter().any(|location| {
            let physical = &location["physicalLocation"];
            let Some(uri) = physical["artifactLocation"]["uri"].as_str() else {
                return false;
            };
            let Some(line) = physical["region"]["startLine"].as_u64() else {
                return false;
            };
            anchors.as_array().is_some_and(|anchors| {
                anchors.iter().any(|anchor| {
                    let Some(file) = anchor["file"].as_str() else {
                        return false;
                    };
                    (uri == file || uri.ends_with(&format!("/{file}")))
                        && anchor["line_hint"].as_u64() == Some(line)
                })
            })
        })
    })
}

pub(crate) fn normalize_swift(case: &Value, sarif: &Value) -> (&'static str, Vec<String>) {
    let errors = codeql_execution_errors(sarif);
    if !errors.is_empty() {
        return ("runner-error", errors);
    }
    let Some(runs) = sarif["runs"].as_array() else {
        return ("runner-error", vec!["missing SARIF runs".into()]);
    };
    if runs.len() != 1
        || !runs[0]["invocations"].as_array().is_some_and(|inv| {
            !inv.is_empty() && inv.iter().all(|i| i["executionSuccessful"] == true)
        })
    {
        return (
            "runner-error",
            vec!["missing or unsuccessful Swift analysis invocation".into()],
        );
    }
    let Some(results) = runs[0]["results"].as_array() else {
        return ("runner-error", vec!["missing results array".into()]);
    };
    let mut source = false;
    let mut sink = false;
    let mut reached = false;
    for result in results {
        match result["ruleId"].as_str() {
            Some(rule)
                if rule
                    == if case["score_tier"] == "modeling" {
                        "dfb/swift-modeling-endpoint-probe"
                    } else {
                        "dfb/swift-kernel-endpoint-probe"
                    } =>
            {
                let Some(message) = result["message"]["text"].as_str() else {
                    return ("runner-error", vec!["missing endpoint observation".into()]);
                };
                for role in message.lines() {
                    match role {
                        "Benchmark source endpoint observed." => {
                            source |= at_anchor(result, &case["source_anchors"])
                        }
                        "Benchmark sink endpoint observed." => {
                            sink |= at_anchor(result, &case["sink_anchors"])
                        }
                        _ => {
                            return (
                                "runner-error",
                                vec!["unexpected endpoint observation".into()],
                            );
                        }
                    }
                }
            }
            Some(rule)
                if rule
                    == if case["score_tier"] == "modeling" {
                        "dfb/swift-modeling"
                    } else {
                        "dfb/swift-kernel"
                    } =>
            {
                if !at_anchor(result, &case["sink_anchors"]) {
                    return (
                        "inconclusive",
                        vec!["Swift finding does not match exact sink anchor".into()],
                    );
                }
                reached = true;
            }
            _ => return ("runner-error", vec!["unexpected Swift query rule".into()]),
        }
    }
    if !source || !sink {
        return (
            "runner-error",
            vec!["Swift dataflow source/sink missing at the declared file and line".into()],
        );
    }
    (if reached { "reached" } else { "not-reached" }, Vec::new())
}

pub(crate) fn run_codeql_swift_kernel(binary: &Path, packs: &Path, tier: &str) -> Result<()> {
    validate_cases()?;
    let partition = verify_activation()?;
    let (suffix, query, probe, templates) = match tier {
        "core" => ("kernel", QUERY, PROBE, expected_core_templates("swift")),
        "modeling" => (
            "modeling",
            "adapters/codeql/swift/queries/SwiftModeling.ql",
            "adapters/codeql/swift/queries/SwiftModelingEndpointProbe.ql",
            crate::modeling::SWIFT_MODELING_TEMPLATE_IDS.to_vec(),
        ),
        "calibration" => (
            "calibration",
            "adapters/codeql/swift/queries/SwiftCalibration.ql",
            PROBE,
            vec![
                "dfb-template-one-hop-relay",
                "dfb-template-modeled-external-summary",
            ],
        ),
        _ => bail!("unknown Swift tier"),
    };
    let selected: Vec<_> = case_paths()
        .into_iter()
        .map(|path| -> Result<_> {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
            Ok((path, case))
        })
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .filter(|(_, case)| {
            case["language"] == "swift"
                && case["score_tier"] == tier
                && case["model_profile"] == "benchmark-controlled"
        })
        .collect();
    validate_kernel_population_with(&selected, "Swift CodeQL tier", &templates)?;
    for (_, case) in &selected {
        let entry = &partition["templates"][case["template_id"].as_str().context("template id")?];
        if entry["decision"] != "execute"
            || entry["tier"] != tier
            || entry["profile"] != case["model_profile"]
        {
            bail!(
                "Swift case is not in the committed executable partition: {}",
                case["id"]
            );
        }
    }
    let raw_root = format!("reports/raw/codeql-swift-{suffix}");
    let raw_dir = Path::new(&raw_root);
    if raw_dir.exists() {
        bail!("refusing to overwrite prior Swift run evidence");
    }
    fs::create_dir_all(raw_dir)?;
    let started = now_seconds()?;
    let identity = codeql_version_identity(binary)?;
    if identity.version != "2.27.0" {
        bail!("Swift requires pinned CodeQL 2.27.0");
    }
    write_run_environment(raw_dir, "codeql", &identity)?;
    let revision = fixture_revision()?;
    let configuration = hash_paths(&codeql_swift_configuration_paths())?;
    let mut results = Vec::new();
    for (path, case) in selected {
        let id = case["id"].as_str().context("case id")?;
        let output = raw_dir.join(id);
        let start = Instant::now();
        let status = Command::new("python3")
            .arg(SCRIPT)
            .arg("--codeql")
            .arg(binary)
            .arg("--packs")
            .arg(packs)
            .arg("--case")
            .arg(&path)
            .arg("--output")
            .arg(&output)
            .arg("--query")
            .arg(query)
            .arg("--probe")
            .arg(probe)
            .status()?;
        if !status.success() {
            bail!("Swift evidence recorder failed for {id}");
        }
        let execution: Value =
            serde_json::from_str(&fs::read_to_string(output.join("execution.json"))?)?;
        let phases: Vec<(&str, Duration)> = execution["phases"]
            .as_object()
            .context("execution phases")?
            .iter()
            .map(|(name, seconds)| {
                let seconds = seconds.as_f64().context("phase duration")?;
                Ok((name.as_str(), Duration::try_from_secs_f64(seconds)?))
            })
            .collect::<Result<_>>()?;
        write_case_phase_timings(raw_dir, "codeql", id, &phases)?;
        let raw = output.join(if execution["outcome"] == "analyzed" {
            "results.sarif.json"
        } else {
            "execution.json"
        });
        let (mut outcome, mut diagnostics) = if execution["outcome"] == "analyzed" {
            normalize_swift(&case, &serde_json::from_str(&fs::read_to_string(&raw)?)?)
        } else {
            let outcome = if execution["outcome"] == "inconclusive" {
                "inconclusive"
            } else {
                "runner-error"
            };
            (
                outcome,
                execution["diagnostics"]
                    .as_array()
                    .context("execution diagnostics")?
                    .iter()
                    .filter_map(|v| v.as_str().map(str::to_string))
                    .collect(),
            )
        };
        if outcome == "inconclusive" && output.join("results.sarif.json").exists() {
            let sarif: Value =
                serde_json::from_str(&fs::read_to_string(output.join("results.sarif.json"))?)?;
            let (native_outcome, native_diagnostics) = normalize_swift(&case, &sarif);
            if native_outcome == "runner-error" {
                outcome = native_outcome;
                diagnostics.extend(native_diagnostics);
            }
        }
        println!("{id}: {outcome}");
        let mut normalized =
            normalized_result(&case, id, outcome, diagnostics, start.elapsed(), &raw);
        normalized["peak_memory_mb"] = execution["peak_memory_mb"].clone();
        results.push(normalized);
        let report = normalized_report(
            "codeql",
            &identity,
            &configuration,
            &revision,
            started,
            results.clone(),
        )?;
        fs::write(
            raw_dir.join("progress.json"),
            serde_json::to_vec_pretty(&report)?,
        )?;
    }
    let report = normalized_report(
        "codeql",
        &identity,
        &configuration,
        &revision,
        started,
        results,
    )?;
    write_and_validate_report(
        Path::new(&format!("reports/codeql-swift-{suffix}.json")),
        &report,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    fn case() -> Value {
        json!({"source_anchors":[{"file":"main.swift","line_hint":4}],"sink_anchors":[{"file":"main.swift","line_hint":5}]})
    }
    fn result(rule: &str, message: &str, line: u64) -> Value {
        json!({"ruleId":rule,"message":{"text":message},"locations":[{"physicalLocation":{"artifactLocation":{"uri":"main.swift"},"region":{"startLine":line}}}]})
    }
    fn negative() -> Value {
        json!({"runs":[{"invocations":[{"executionSuccessful":true}],"results":[result("dfb/swift-kernel-endpoint-probe","Benchmark source endpoint observed.",4),result("dfb/swift-kernel-endpoint-probe","Benchmark sink endpoint observed.",5)]}]})
    }
    #[test]
    fn swift_clean_negative_requires_both_exact_anchors() {
        assert_eq!(normalize_swift(&case(), &negative()).0, "not-reached");
        let mut sarif = negative();
        sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] =
            json!(9);
        assert_eq!(normalize_swift(&case(), &sarif).0, "runner-error");
    }
    #[test]
    fn swift_error_notification_overrides_successful_exit() {
        let mut sarif = negative();
        sarif["runs"][0]["invocations"][0]["toolExecutionNotifications"] =
            json!([{"level":"error","message":{"text":"extraction failed"}}]);
        assert_eq!(normalize_swift(&case(), &sarif).0, "runner-error");
    }
    #[test]
    fn swift_findings_require_exact_sink_location() {
        let mut sarif = negative();
        sarif["runs"][0]["results"]
            .as_array_mut()
            .unwrap()
            .push(result("dfb/swift-kernel", "flow", 5));
        assert_eq!(normalize_swift(&case(), &sarif).0, "reached");
        sarif["runs"][0]["results"][2]["locations"][0]["physicalLocation"]["region"]["startLine"] =
            json!(9);
        assert_eq!(normalize_swift(&case(), &sarif).0, "inconclusive");
    }
}
