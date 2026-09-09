#!/usr/bin/env python3
"""Syntax-check and execute the JavaScript recursive-composition fixture pairs.

The benchmark fixtures intentionally have a no-op ``dfb_sink`` and a fixed
source literal. For this bounded source-dependence check, each fixture is
copied to a temporary file, its sink is instrumented to print the integer
argument, and the source literal is varied between 7 and 11. Repository
fixtures are never modified and no analyzer is invoked.
"""

from __future__ import annotations

import argparse
import json
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
SUBPROCESS_TIMEOUT_SECONDS = 30


def marker_line(body: str, marker: str) -> int:
    lines = [number for number, line in enumerate(body.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        raise AssertionError(
            f"marker {marker!r} must occur exactly once in fixture (found {len(lines)})"
        )
    return lines[0]


def run_case(root: Path, stem: str, polarity: str) -> None:
    case_dir = root / "cases" / "taint" / "javascript" / f"{stem}-{polarity}"
    metadata = json.loads((case_dir / "case.json").read_text())
    fixture_name = metadata["fixture_files"][0]
    fixture = case_dir / fixture_name
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

    syntax = subprocess.run(
        ["node", "--check", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if syntax.returncode != 0:
        raise RuntimeError(f"node --check failed for {fixture}:\n{syntax.stdout}{syntax.stderr}")

    if original.count("return 7;") != 1:
        raise AssertionError(f"{fixture}: expected one source literal")
    observed = {}
    for source_value in SOURCE_VALUES:
        source = original.replace("return 7;", f"return {source_value};", 1)
        instrumented = source.replace(
            "function dfb_sink(value) { }",
            "function dfb_sink(value) { console.log(value); }",
            1,
        )
        if instrumented == source:
            raise AssertionError(f"{fixture}: cannot instrument sink")

        with tempfile.TemporaryDirectory(prefix="dfb-js-168-") as temporary:
            probe = Path(temporary) / fixture.name
            probe.write_text(instrumented + "\nrun();\n")
            try:
                execution = subprocess.run(
                    ["node", str(probe)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=SUBPROCESS_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as error:
                raise RuntimeError(f"execution timed out for {fixture}") from error
            if execution.returncode != 0:
                raise RuntimeError(
                    f"execution failed for {fixture}:\n{execution.stdout}{execution.stderr}"
                )
            output = execution.stdout.strip()
            try:
                observed[source_value] = int(output)
            except ValueError as error:
                raise AssertionError(
                    f"{fixture}: expected one integer sink output, got {output!r}"
                ) from error

    expected_base = EXPECTED[stem][polarity]
    if observed[SOURCE_VALUES[0]] != expected_base:
        raise AssertionError(
            f"{fixture}: source {SOURCE_VALUES[0]} expected sink value {expected_base}, "
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
    print(
        f"{stem}-{polarity}: node --check + execution => "
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
    args = parser.parse_args()
    for stem in EXPECTED:
        for polarity in ("positive", "negative"):
            run_case(args.root, stem, polarity)


if __name__ == "__main__":
    main()
