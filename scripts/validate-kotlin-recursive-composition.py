#!/usr/bin/env python3
"""Compile and execute the Kotlin recursive-composition fixture pairs.

The fixtures intentionally keep ``dfb_sink`` as a no-op and use a fixed source
literal. This bounded, analyzer-independent check copies each fixture into a
temporary probe, instruments the sink, and varies the source between 7 and 11.
Repository files and frozen reports are never modified.
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
    "recursive-exception-persistence": {"positive": 8, "negative": 1},
}
SOURCE_VALUES = (7, 11)
TIMEOUT_SECONDS = 30


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


def check_fixture(root: Path, stem: str, polarity: str, kotlinc: str, kotlin: str) -> str:
    case_dir = root / "cases" / "taint" / "kotlin" / f"{stem}-{polarity}"
    metadata = json.loads((case_dir / "case.json").read_text())
    fixture = case_dir / metadata["fixture_files"][0]
    original = fixture.read_text()

    for anchor in metadata["source_anchors"] + metadata["sink_anchors"]:
        line = marker_line(original, anchor["marker"])
        if anchor.get("line_hint") != line:
            raise AssertionError(
                f"{fixture}: {anchor['marker']} expected line {anchor.get('line_hint')}, got {line}"
            )
    for checkpoint in metadata["witness_checkpoints"]:
        marker_line(original, checkpoint)
    if polarity == "negative" and "DFB-KILL:" not in original:
        raise AssertionError(f"{fixture}: negative fixture is missing DFB-KILL")
    if original.count("return 7") != 1:
        raise AssertionError(f"{fixture}: expected exactly one source literal")

    object_match = re.search(r"object\s+([A-Za-z0-9_]+)\s*\{", original)
    if object_match is None:
        raise AssertionError(f"{fixture}: cannot find Kotlin object declaration")
    object_name = object_match.group(1)

    with tempfile.TemporaryDirectory(prefix="dfb-kotlin-168-compile-") as temporary:
        classes = Path(temporary) / "classes"
        classes.mkdir()
        compile_result = run_command(
            [kotlinc, "-nowarn", "-d", str(classes), str(fixture)],
            fixture,
            "kotlinc compile",
        )
        if compile_result.returncode != 0:
            raise RuntimeError(
                f"kotlinc compile failed for {fixture}:\n"
                f"{compile_result.stdout}{compile_result.stderr}"
            )

    observed: dict[int, int] = {}
    for source_value in SOURCE_VALUES:
        source = original.replace("return 7", f"return {source_value}", 1)
        instrumented = source.replace(
            "fun dfb_sink(value: Int) {}",
            "fun dfb_sink(value: Int) { println(value) }",
            1,
        )
        if instrumented == source:
            raise AssertionError(f"{fixture}: cannot instrument sink")

        with tempfile.TemporaryDirectory(prefix="dfb-kotlin-168-probe-") as temporary:
            temporary_root = Path(temporary)
            probe = temporary_root / "Probe.kt"
            probe.write_text(
                "package dataflowbench\n\n"
                f"fun main() {{ {object_name}.run() }}\n"
            )
            probe_fixture = temporary_root / fixture.name
            probe_fixture.write_text(instrumented)
            classes = temporary_root / "classes"
            classes.mkdir()
            compile_result = run_command(
                [kotlinc, "-nowarn", "-d", str(classes), str(probe_fixture), str(probe)],
                fixture,
                "kotlinc probe compile",
            )
            if compile_result.returncode != 0:
                raise RuntimeError(
                    f"kotlinc probe compile failed for {fixture}:\n"
                    f"{compile_result.stdout}{compile_result.stderr}"
                )
            execution = run_command(
                [kotlin, "-classpath", str(classes), "dataflowbench.ProbeKt"],
                fixture,
                "Kotlin probe execution",
            )
            if execution.returncode != 0:
                raise RuntimeError(
                    f"Kotlin probe execution failed for {fixture}:\n"
                    f"{execution.stdout}{execution.stderr}"
                )
            output = execution.stdout.strip().splitlines()
            if len(output) != 1:
                raise AssertionError(f"{fixture}: expected one integer sink output, got {output!r}")
            try:
                observed[source_value] = int(output[0])
            except ValueError as error:
                raise AssertionError(f"{fixture}: expected integer sink output, got {output[0]!r}") from error

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
        f"{stem}-{polarity}: kotlinc + execution => "
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
    parser.add_argument("--kotlinc", default="kotlinc", help="Kotlin compiler executable")
    parser.add_argument("--kotlin", default="kotlin", help="Kotlin runner executable")
    args = parser.parse_args()

    for stem in EXPECTED:
        for polarity in ("positive", "negative"):
            print(check_fixture(args.root, stem, polarity, args.kotlinc, args.kotlin))


if __name__ == "__main__":
    main()
