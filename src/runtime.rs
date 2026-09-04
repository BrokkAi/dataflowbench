//! Process and environment plumbing shared by every adapter: command capture,
//! the phase-timing sidecars, and the per-run environment stamp.
//!
//! Timing is additive metadata. No correctness outcome may read it, and a case
//! arm that never invokes the analyzer retains none.

use crate::adapters::ToolIdentity;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{
    fs, path::Path, path::PathBuf, process::Command, time::Duration, time::SystemTime,
    time::UNIX_EPOCH,
};

pub(crate) fn command_output(command: &mut Command) -> Result<String> {
    let output = command.output()?;
    if !output.status.success() {
        bail!("command failed");
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub(crate) fn now_seconds() -> Result<u64> {
    Ok(SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs())
}

// ---------------------------------------------------------------------------
// Phase-timing capture (#90, the instrumentation half of the latency tier).
//
// The runner times exactly what it already invokes as a separate subprocess,
// and nothing else: no analyzer internals are instrumented, and the stated
// exclusions — harness compile time, fixture materialization, report
// normalization, validation — never enter a phase. Durations come from the
// monotonic clock (`Instant`), so a wall-clock adjustment mid-run cannot
// corrupt a phase.
//
// Timings are retained as a per-case sidecar in the run's raw-evidence
// directory (`<case-id>-timing.json`) rather than inside the analyzer's own
// document, for two reasons. First, several raw artifacts are the tool's
// verbatim bytes (Semgrep's `--json` stdout, CodeQL's SARIF), and injecting
// runner metadata into them would cost the verbatim property. Second, the
// normalized reports are frozen bytes with `additionalProperties: false`, so
// the raw directory is the only additive home. The sidecar is **additive
// metadata**: validation never requires it, pre-existing frozen artifacts
// never carry it, and no correctness outcome may ever read a value from it.
// ---------------------------------------------------------------------------

/// Where one case's phase-timing sidecar lives, beside its raw evidence.
pub(crate) fn case_timing_path(raw_dir: &Path, id: &str) -> PathBuf {
    raw_dir.join(format!("{id}-timing.json"))
}

/// Remove a previous run's timing sidecar for one case, so an arm that does
/// not invoke the analyzer (an `unsupported` declaration, a preregistered
/// partition decision) can never leave a stale timing beside a fresh decision.
pub(crate) fn clear_stale_case_timing(raw_dir: &Path, id: &str) -> Result<()> {
    let path = case_timing_path(raw_dir, id);
    if path.exists() {
        fs::remove_file(&path).with_context(|| format!("clear {}", path.display()))?;
    }
    Ok(())
}

/// Retain the wall-clock phases the runner witnessed around one case's
/// analyzer subprocesses.
///
/// Each entry is a phase label and the monotonic-clock duration of exactly one
/// subprocess invocation. The labels state the boundary the adapter genuinely
/// observes, per the semi-granular rule of the latency tier (#89):
/// `database-create` / `database-analyze` for CodeQL (extraction including the
/// traced compile, then query evaluation *and* SARIF interpretation, which the
/// pinned CLI performs inside the same `database analyze` subprocess), and
/// `total` for Joern, Semgrep, and Bifrost, whose single invocation is
/// indivisible from the adapter's vantage. Unequal granularity is stated, not
/// papered over.
///
/// The write is incremental: a caller may retain the first phase before the
/// second runs, so a case that fails mid-sequence still keeps the cost it
/// already paid. The sidecar is rewritten whole each time, never appended.
pub(crate) fn write_case_phase_timings(
    raw_dir: &Path,
    adapter: &str,
    id: &str,
    phases: &[(&str, Duration)],
) -> Result<()> {
    let phases: Vec<Value> = phases
        .iter()
        .map(|(phase, duration)| json!({"phase": phase, "wall_ms": duration.as_millis() as u64}))
        .collect();
    fs::write(
        case_timing_path(raw_dir, id),
        serde_json::to_string_pretty(&json!({
            "schema_version": 1,
            "adapter": adapter,
            "case_id": id,
            "clock": "monotonic",
            "phases": phases,
            "evidence_kind": "retained-phase-timing"
        }))? + "\n",
    )?;
    Ok(())
}

/// The hardware model the machine reports for itself, best-effort.
///
/// A latency number is only comparable within the environment that produced
/// it, so the stamp names the machine — but reading that name is never worth
/// failing a run over, hence the `"unknown"` fallbacks.
pub(crate) fn hardware_model() -> String {
    #[cfg(target_os = "macos")]
    let model = command_output(Command::new("sysctl").args(["-n", "hw.model"])).ok();
    #[cfg(target_os = "linux")]
    let model = fs::read_to_string("/sys/devices/virtual/dmi/id/product_name")
        .ok()
        .map(|name| name.trim().to_string());
    #[cfg(not(any(target_os = "macos", target_os = "linux")))]
    let model: Option<String> = None;
    model
        .filter(|model| !model.is_empty())
        .unwrap_or_else(|| "unknown".into())
}

/// Stamp the environment one run measured in, once per run, beside its raw
/// evidence.
///
/// The stamp pairs the machine (hardware model, OS and kernel release, CPU
/// count) with the tool identity the run **witnessed** from the binary, so a
/// latency page can later attribute every per-case timing in the directory to
/// one environment and one witnessed tool without re-measurement. Like the
/// per-case sidecars this is additive metadata: no validation requires it and
/// no outcome reads it.
pub(crate) fn write_run_environment(
    raw_dir: &Path,
    tool: &str,
    identity: &ToolIdentity,
) -> Result<()> {
    let os_release =
        command_output(Command::new("uname").arg("-r")).unwrap_or_else(|_| "unknown".into());
    let cpu_count = std::thread::available_parallelism()
        .map(|count| json!(count.get()))
        .unwrap_or(Value::Null);
    fs::write(
        raw_dir.join("run-environment.json"),
        serde_json::to_string_pretty(&json!({
            "schema_version": 1,
            "captured_at_unix_seconds": now_seconds()?,
            "hardware_model": hardware_model(),
            "os": std::env::consts::OS,
            "os_release": os_release,
            "cpu_architecture": std::env::consts::ARCH,
            "cpu_count": cpu_count,
            "tool": tool,
            "witnessed_tool_version": identity.version,
            "witnessed_tool_build_identity": identity.build_identity,
            "evidence_kind": "retained-run-environment"
        }))? + "\n",
    )?;
    Ok(())
}
