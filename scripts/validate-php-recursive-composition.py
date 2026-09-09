#!/usr/bin/env python3
"""Syntax-check and execute the PHP recursive-composition fixture pairs.

The fixtures keep ``dfb_sink`` as a no-op and use a fixed source literal. This
bounded, analyzer-independent check copies each fixture to a temporary file,
instruments the sink, and varies the source between 7 and 11. Repository
fixtures and frozen reports are never modified.
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
TIMEOUT_SECONDS = 30


def marker_line(body: str, marker: str) -> int:
    lines = [line_number for line_number, line in enumerate(body.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        raise AssertionError(f"marker {marker!r} must occur exactly once (found {len(lines)})")
    return lines[0]


def run_case(root: Path, stem: str, polarity: str) -> None:
    case_dir = root / "cases" / "taint" / "php" / f"{stem}-{polarity}"
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
    if original.count("return 7;") != 1:
        raise AssertionError(f"{fixture}: expected exactly one source literal")

    syntax = subprocess.run(
        ["php", "-l", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
        timeout=TIMEOUT_SECONDS,
    )
    if syntax.returncode != 0:
        raise RuntimeError(f"php -l failed for {fixture}:\n{syntax.stdout}{syntax.stderr}")

    observed = {}
    for source_value in SOURCE_VALUES:
        probe_source = original.replace("return 7;", f"return {source_value};", 1)
        instrumented = probe_source.replace(
            "function dfb_sink(int $value): void {}",
            'function dfb_sink(int $value): void { echo $value, "\\n"; }',
            1,
        )
        if instrumented == probe_source:
            raise AssertionError(f"{fixture}: could not instrument sink")

        with tempfile.TemporaryDirectory(prefix="dfb-php-168-probe-") as temporary:
            probe = Path(temporary) / fixture.name
            probe.write_text(instrumented + "\nrun();\n")
            execution = subprocess.run(
                ["php", str(probe)],
                capture_output=True,
                text=True,
                check=False,
                timeout=TIMEOUT_SECONDS,
            )
            if execution.returncode != 0:
                raise RuntimeError(
                    f"execution failed for {fixture}:\n{execution.stdout}{execution.stderr}"
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
    print(
        f"{stem}-{polarity}: php -l + execution => "
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
