#!/usr/bin/env python3
"""Compile and execute the Rust recursive-composition fixture pairs.

The fixtures intentionally keep ``dfb_sink`` as a no-op and use a fixed source
literal. This bounded, analyzer-independent check copies each fixture to a
temporary executable, instruments the sink, and varies the source between 7
and 11. Repository files and frozen reports are never modified.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


EXPECTED = {
    "recursive-payload-transform": {"positive": 13, "negative": 3},
    "mutual-recursive-transform": {"positive": 13, "negative": 3},
    "recursive-heap-unwind": {"positive": 10, "negative": 3},
    "recursive-callback-transform": {"positive": 13, "negative": 3},
}
SOURCE_VALUES = (7, 11)
TIMEOUT_SECONDS = 30
SOURCE_LITERAL = re.compile(r"(?m)^([ \t]*)7[ \t]*$")


def marker_line(body: str, marker: str) -> int:
    lines = [line_number for line_number, line in enumerate(body.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        raise AssertionError(f"marker {marker!r} must occur exactly once (found {len(lines)})")
    return lines[0]


def run_command(command: list[str], fixture: Path, context: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{context} timed out for {fixture}") from error


def source_variant(original: str, source_value: int, fixture: Path) -> str:
    matches = list(SOURCE_LITERAL.finditer(original))
    if len(matches) != 1:
        raise AssertionError(f"{fixture}: expected exactly one source literal 7 (found {len(matches)})")
    match = matches[0]
    return original[: match.start()] + f"{match.group(1)}{source_value}" + original[match.end() :]


def check_fixture(root: Path, stem: str, polarity: str, rustc: str) -> str:
    case_dir = root / "cases" / "taint" / "rust" / f"{stem}-{polarity}"
    metadata = json.loads((case_dir / "case.json").read_text())
    fixture = case_dir / metadata["fixture_files"][0]
    original = fixture.read_text()

    for anchor in metadata["source_anchors"] + metadata["sink_anchors"]:
        marker_line(original, anchor["marker"])
    for checkpoint in metadata["witness_checkpoints"]:
        marker_line(original, checkpoint)
    if polarity == "negative" and "DFB-KILL:" not in original:
        raise AssertionError(f"{fixture}: negative fixture is missing DFB-KILL")

    with tempfile.TemporaryDirectory(prefix="dfb-rust-168-compile-") as temporary:
        metadata_output = Path(temporary) / "fixture.rmeta"
        syntax = run_command(
            [
                rustc,
                "--edition",
                "2021",
                "--crate-type=lib",
                "--emit=metadata",
                "-o",
                str(metadata_output),
                str(fixture),
            ],
            fixture,
            "rustc syntax check",
        )
        if syntax.returncode != 0:
            raise RuntimeError(
                f"rustc syntax check failed for {fixture}:\n{syntax.stdout}{syntax.stderr}"
            )

    observed: dict[int, int] = {}
    for source_value in SOURCE_VALUES:
        source = source_variant(original, source_value, fixture)
        instrumented = source.replace(
            "fn dfb_sink(value: i32) {}",
            "fn dfb_sink(value: i32) { println!(\"{}\", value); }",
            1,
        )
        if instrumented == source:
            raise AssertionError(f"{fixture}: cannot instrument sink")
        probe_source = instrumented + "\nfn main() { run(); }\n"

        with tempfile.TemporaryDirectory(prefix="dfb-rust-168-probe-") as temporary:
            temporary_path = Path(temporary)
            probe = temporary_path / fixture.name
            executable = temporary_path / "probe"
            probe.write_text(probe_source)
            compile_result = run_command(
                [rustc, "--edition", "2021", str(probe), "-o", str(executable)],
                fixture,
                "rustc probe compile",
            )
            if compile_result.returncode != 0:
                raise RuntimeError(
                    f"rustc probe compile failed for {fixture}:\n"
                    f"{compile_result.stdout}{compile_result.stderr}"
                )
            execution = run_command([str(executable)], fixture, "Rust probe execution")
            if execution.returncode != 0:
                raise RuntimeError(
                    f"Rust probe execution failed for {fixture}:\n"
                    f"{execution.stdout}{execution.stderr}"
                )
            output = execution.stdout.strip().splitlines()
            if len(output) != 1:
                raise AssertionError(f"{fixture}: expected one integer sink output, got {output!r}")
            try:
                observed[source_value] = int(output[0])
            except ValueError as error:
                raise AssertionError(
                    f"{fixture}: expected integer sink output, got {output[0]!r}"
                ) from error

    expected_base = EXPECTED[stem][polarity]
    if observed[SOURCE_VALUES[0]] != expected_base:
        raise AssertionError(
            f"{fixture}: source {SOURCE_VALUES[0]} expected {expected_base}, "
            f"got {observed[SOURCE_VALUES[0]]}"
        )
    source_delta = SOURCE_VALUES[1] - SOURCE_VALUES[0]
    observed_delta = observed[SOURCE_VALUES[1]] - observed[SOURCE_VALUES[0]]
    expected_delta = source_delta if polarity == "positive" else 0
    if observed_delta != expected_delta:
        raise AssertionError(
            f"{fixture}: source delta {source_delta} produced sink delta {observed_delta}; "
            f"expected {expected_delta} for {polarity}"
        )
    return (
        f"{stem}-{polarity}: rustc + execution => "
        f"{SOURCE_VALUES[0]}:{observed[SOURCE_VALUES[0]]}, "
        f"{SOURCE_VALUES[1]}:{observed[SOURCE_VALUES[1]]} (delta {observed_delta})"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="DataFlowBench checkout (defaults to this script's repository)",
    )
    parser.add_argument("--rustc", default="rustc", help="Rust compiler executable")
    args = parser.parse_args()

    for stem in EXPECTED:
        for polarity in ("positive", "negative"):
            print(check_fixture(args.root, stem, polarity, args.rustc))


if __name__ == "__main__":
    main()
