#!/usr/bin/env python3
"""Compile and execute the Java recursive-composition fixture pairs.

The benchmark fixtures intentionally have a no-op ``dfb_sink``.  For this
bounded source-dependence check, the script copies each fixture into a
temporary package, instruments that sink copy to print its integer argument,
and invokes the fixture's package-local ``run`` method from a temporary
harness.  The repository fixtures themselves are never modified.
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
SUBPROCESS_TIMEOUT_SECONDS = 30


def run_case(root: Path, stem: str, polarity: str) -> None:
    case_dir = root / "cases" / "taint" / "java" / f"{stem}-{polarity}"
    metadata = json.loads((case_dir / "case.json").read_text())
    fixture = case_dir / metadata["fixture_files"][0]
    original = fixture.read_text()
    class_match = re.search(r"final class ([A-Za-z0-9_]+)\s*\{", original)
    if class_match is None:
        raise ValueError(f"cannot find fixture class in {fixture}")
    class_name = class_match.group(1)
    if original.count("return 7;") != 1:
        raise ValueError(f"expected one source literal in {fixture}")

    observed = {}
    for source_value in SOURCE_VALUES:
        source = original.replace("return 7;", f"return {source_value};", 1)
        instrumented = source.replace(
            "static void dfb_sink(int value) { }",
            "static void dfb_sink(int value) { System.out.println(value); }",
            1,
        )
        if instrumented == source:
            raise ValueError(f"cannot instrument sink in {fixture}")

        with tempfile.TemporaryDirectory(prefix="dfb-java-168-") as temporary:
            temporary_root = Path(temporary)
            package_dir = temporary_root / "dataflowbench" / "taint"
            package_dir.mkdir(parents=True)
            fixture_copy = package_dir / fixture.name
            fixture_copy.write_text(instrumented)
            harness = package_dir / "Probe.java"
            harness.write_text(
                "package dataflowbench.taint;\n"
                "final class Probe {\n"
                "    public static void main(String[] args) {\n"
                f"        {class_name}.run();\n"
                "    }\n"
                "}\n"
            )
            classes = temporary_root / "classes"
            classes.mkdir()
            try:
                compile_result = subprocess.run(
                    [
                        "javac",
                        "-Xlint:all",
                        "-d",
                        str(classes),
                        str(fixture_copy),
                        str(harness),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=SUBPROCESS_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as error:
                raise RuntimeError(f"javac timed out for {fixture}") from error
            if compile_result.returncode != 0:
                raise RuntimeError(
                    f"javac failed for {fixture}:\n{compile_result.stdout}{compile_result.stderr}"
                )
            try:
                execution = subprocess.run(
                    ["java", "-cp", str(classes), "dataflowbench.taint.Probe"],
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
        f"{stem}-{polarity}: javac + execution => "
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
