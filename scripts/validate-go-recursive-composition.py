#!/usr/bin/env python3
"""Compile and execute the Go recursive-composition fixture pairs.

The fixtures intentionally keep ``dfb_sink`` as a no-op and use a fixed source
literal. This bounded, analyzer-independent check copies each fixture to a
temporary package, instruments the sink, and varies the source between 7 and
11. Repository files and frozen reports are never modified.
"""

from __future__ import annotations

import argparse
import json
import os
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


def go_env(cache: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["GOCACHE"] = str(cache)
    environment["GO111MODULE"] = "off"
    return environment


def check_fixture(fixture: Path, metadata: dict, polarity: str) -> str:
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

    with tempfile.TemporaryDirectory(prefix="dfb-go-168-cache-") as cache:
        syntax = subprocess.run(
            ["gofmt", "-d", str(fixture)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        if syntax.returncode != 0 or syntax.stdout:
            raise RuntimeError(f"gofmt check failed for {fixture}:\n{syntax.stdout}{syntax.stderr}")
        build = subprocess.run(
            ["go", "build", str(fixture)],
            capture_output=True,
            text=True,
            check=False,
            env=go_env(Path(cache)),
            timeout=TIMEOUT_SECONDS,
        )
        if build.returncode != 0:
            raise RuntimeError(f"go build failed for {fixture}:\n{build.stdout}{build.stderr}")

    observed: dict[int, int] = {}
    for source_value in SOURCE_VALUES:
        probe_source = original.replace("package dataflowbench", "package main", 1)
        probe_source = probe_source.replace("return 7", f"return {source_value}", 1)
        probe_source = probe_source.replace(
            "func dfb_sink(value int) {}",
            "func dfb_sink(value int) { fmt.Println(value) }",
            1,
        )
        if "package main" not in probe_source or "fmt.Println(value)" not in probe_source:
            raise AssertionError(f"{fixture}: could not instrument package or sink")
        probe_source = probe_source.replace("package main\n", 'package main\n\nimport "fmt"\n', 1)
        probe_source += "\nfunc main() { run() }\n"

        with tempfile.TemporaryDirectory(prefix="dfb-go-168-probe-") as temporary:
            temporary_path = Path(temporary)
            probe = temporary_path / "probe.go"
            executable = temporary_path / "probe"
            probe.write_text(probe_source)
            with tempfile.TemporaryDirectory(prefix="dfb-go-168-cache-") as cache:
                build = subprocess.run(
                    ["go", "build", "-o", str(executable), str(probe)],
                    capture_output=True,
                    text=True,
                    check=False,
                    env=go_env(Path(cache)),
                    timeout=TIMEOUT_SECONDS,
                )
            if build.returncode != 0:
                raise RuntimeError(f"probe build failed for {fixture}:\n{build.stdout}{build.stderr}")
            execution = subprocess.run(
                [str(executable)],
                capture_output=True,
                text=True,
                check=False,
                timeout=TIMEOUT_SECONDS,
            )
            if execution.returncode != 0:
                raise RuntimeError(f"probe execution failed for {fixture}:\n{execution.stdout}{execution.stderr}")
            output = execution.stdout.strip().splitlines()
            if len(output) != 1:
                raise AssertionError(f"{fixture}: expected one integer sink output, got {output!r}")
            try:
                observed[source_value] = int(output[0])
            except ValueError as error:
                raise AssertionError(f"{fixture}: expected integer sink output, got {output[0]!r}") from error

    expected_base = EXPECTED[fixture.parent.name.removesuffix(f"-{polarity}")][polarity]
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
    return f"{fixture.parent.name}: {SOURCE_VALUES[0]}:{observed[7]}, {SOURCE_VALUES[1]}:{observed[11]} (delta {observed_delta})"


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
            case_dir = args.root / "cases" / "taint" / "go" / f"{stem}-{polarity}"
            metadata = json.loads((case_dir / "case.json").read_text())
            fixture = case_dir / metadata["fixture_files"][0]
            print(check_fixture(fixture, metadata, polarity))


if __name__ == "__main__":
    main()
