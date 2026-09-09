#!/usr/bin/env python3
"""Syntax-check and execute the Ruby recursive-composition fixture pairs.

This is an analyzer-independent source-dependence probe. It copies each
fixture to a temporary file, instruments the no-op sink, and runs it with
source values 7 and 11. Repository fixtures and frozen reports are never
modified.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


CASES = {
    "recursive-payload-transform": {
        "positive": 13,
        "negative": 3,
        "dimensions": ["recursion", "interprocedural-flow", "flow-sensitivity"],
        "tags": ["recursive"],
    },
    "mutual-recursive-transform": {
        "positive": 13,
        "negative": 3,
        "dimensions": ["recursion", "interprocedural-flow", "flow-sensitivity"],
        "tags": ["recursive"],
    },
    "recursive-heap-unwind": {
        "positive": 10,
        "negative": 3,
        "dimensions": [
            "recursion",
            "interprocedural-flow",
            "flow-sensitivity",
            "heap-field-sensitivity",
        ],
        "tags": ["recursive", "heap-access-path"],
    },
    "recursive-callback-transform": {
        "positive": 13,
        "negative": 3,
        "dimensions": ["recursion", "interprocedural-flow", "flow-sensitivity"],
        "tags": ["recursive", "higher-order"],
    },
    "recursive-exception-persistence": {
        "positive": 8,
        "negative": 1,
        "dimensions": [
            "recursion",
            "interprocedural-flow",
            "flow-sensitivity",
            "heap-field-sensitivity",
            "exceptional-flow",
        ],
        "tags": ["recursive", "heap-access-path", "exceptional"],
    },
}
SOURCE_VALUES = (7, 11)
TIMEOUT_SECONDS = 30


def marker_line(body: str, marker: str) -> int:
    lines = [number for number, line in enumerate(body.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        raise AssertionError(f"marker {marker!r} must occur exactly once (found {len(lines)})")
    return lines[0]


def check_metadata(metadata: dict, stem: str, polarity: str, fixture: Path, body: str) -> None:
    expected = CASES[stem]
    if metadata["schema_version"] != 2:
        raise AssertionError(f"{fixture}: unexpected schema version")
    if metadata["template_id"] != f"dfb-template-chal-{stem}":
        raise AssertionError(f"{fixture}: template identity does not match directory")
    if metadata["polarity"] != polarity or metadata["language"] != "ruby":
        raise AssertionError(f"{fixture}: polarity/language metadata mismatch")
    if metadata["score_tier"] != "core" or metadata["track"] != "taint":
        raise AssertionError(f"{fixture}: fixture is outside the scored taint core")
    if metadata["semantic_dimensions"] != expected["dimensions"]:
        raise AssertionError(f"{fixture}: semantic dimensions drifted")
    if metadata["feature_tags"] != expected["tags"]:
        raise AssertionError(f"{fixture}: feature tags drifted")
    if metadata["fixture_provenance"]["revision"] != "v0.8.0-recursive-composition-ruby":
        raise AssertionError(f"{fixture}: unexpected provenance revision")
    for anchor in metadata["source_anchors"] + metadata["sink_anchors"]:
        line = marker_line(body, anchor["marker"])
        if anchor.get("line_hint") != line:
            raise AssertionError(
                f"{fixture}: {anchor['marker']} expected line {anchor.get('line_hint')}, got {line}"
            )
    for checkpoint in metadata["witness_checkpoints"]:
        marker_line(body, checkpoint)
    if polarity == "negative":
        if metadata.get("negative_mechanism") != "overwrite-kill":
            raise AssertionError(f"{fixture}: negative mechanism is not overwrite-kill")
        if "DFB-KILL:" not in body:
            raise AssertionError(f"{fixture}: negative fixture is missing DFB-KILL")
    if body.count("return 7") != 1:
        raise AssertionError(f"{fixture}: expected exactly one source literal")


def instrument(body: str, source_value: int) -> str:
    replaced = body.replace("return 7", f"return {source_value}", 1)
    instrumented, count = re.subn(
        r"^(def dfb_sink\(value\)[^\n]*\n)(end)$",
        r"\1  puts value\n\2",
        replaced,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise AssertionError("could not instrument the Ruby sink")
    return instrumented + "\nrun\n"


def run_case(root: Path, stem: str, polarity: str, ruby: str) -> None:
    case_dir = root / "cases" / "taint" / "ruby" / f"{stem}-{polarity}"
    metadata = json.loads((case_dir / "case.json").read_text())
    fixture = case_dir / metadata["fixture_files"][0]
    body = fixture.read_text()
    check_metadata(metadata, stem, polarity, fixture, body)

    syntax = subprocess.run(
        [ruby, "-c", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
        timeout=TIMEOUT_SECONDS,
    )
    if syntax.returncode != 0:
        raise RuntimeError(f"ruby -c failed for {fixture}:\n{syntax.stdout}{syntax.stderr}")

    observed: dict[int, int] = {}
    for source_value in SOURCE_VALUES:
        with tempfile.TemporaryDirectory(prefix="dfb-ruby-168-") as temporary:
            probe = Path(temporary) / fixture.name
            probe.write_text(instrument(body, source_value))
            execution = subprocess.run(
                [ruby, str(probe)],
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
                raise AssertionError(f"{fixture}: expected integer sink output, got {output[0]!r}") from error

    expected_base = CASES[stem][polarity]
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
        f"{stem}-{polarity}: ruby -c + execution => "
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
    parser.add_argument("--ruby", default="ruby", help="Ruby executable")
    args = parser.parse_args()
    for stem in CASES:
        for polarity in ("positive", "negative"):
            run_case(args.root, stem, polarity, args.ruby)


if __name__ == "__main__":
    main()
