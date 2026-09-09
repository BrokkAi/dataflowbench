#!/usr/bin/env python3
"""Compile and execute the C# recursive-composition fixture pairs.

The committed fixtures deliberately expose a no-op ``dfb_sink`` and have no
entry point. For this bounded source-dependence check, each fixture is copied
to a temporary .NET console project, its sink is instrumented to print the
integer argument, and the source literal is varied between 7 and 11. The
repository fixtures and all benchmark artifacts are never modified.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
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


def run_process(
    command: list[str], *, timeout: int, context: str
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{context} timed out") from error
    return result


def load_case(root: Path, stem: str, polarity: str) -> dict[str, object]:
    case_dir = root / "cases" / "taint" / "csharp" / f"{stem}-{polarity}"
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
    if original.count("return 7;") != 1:
        raise AssertionError(f"{fixture}: expected one source literal")
    class_match = re.search(r"static class ([A-Za-z0-9_]+)\s*\{", original)
    if class_match is None:
        raise AssertionError(f"{fixture}: cannot find fixture class")
    return {
        "stem": stem,
        "polarity": polarity,
        "metadata": metadata,
        "fixture": fixture,
        "fixture_name": fixture_name,
        "original": original,
        "class_name": class_match.group(1),
    }


def instrument_case(case: dict[str, object], source_value: int) -> str:
    fixture = case["fixture"]
    source = case["original"].replace("return 7;", f"return {source_value};", 1)
    instrumented = source.replace(
        "static void dfb_sink(int value) { }",
        "static void dfb_sink(int value) { System.Console.WriteLine(value); }",
        1,
    )
    if instrumented == source:
        raise AssertionError(f"{fixture}: cannot instrument sink")
    exposed = instrumented.replace("static void Run()", "public static void Run()", 1)
    if exposed == instrumented:
        raise AssertionError(f"{fixture}: cannot expose Run for temporary probe")
    return exposed


def write_project(project: Path, cases: list[dict[str, object]]) -> None:
    compile_items = "".join(
        f'    <Compile Include="{case["fixture_name"]}" />\n' for case in cases
    )
    (project / "Probe.csproj").write_text(
        "<Project Sdk=\"Microsoft.NET.Sdk\">\n"
        "  <PropertyGroup>\n"
        "    <OutputType>Exe</OutputType>\n"
        "    <TargetFramework>net8.0</TargetFramework>\n"
        "    <ImplicitUsings>disable</ImplicitUsings>\n"
        "    <Nullable>enable</Nullable>\n"
        "    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n"
        "    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>\n"
        "  </PropertyGroup>\n"
        "  <ItemGroup>\n"
        f"{compile_items}"
        "    <Compile Include=\"Probe.cs\" />\n"
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    calls = "".join(
        f"        DataFlowBench.{case['class_name']}.Run();\n" for case in cases
    )
    (project / "Probe.cs").write_text(
        "static class Probe\n"
        "{\n"
        "    static void Main()\n"
        "    {\n"
        f"{calls}"
        "    }\n"
        "}\n"
    )


def probe_cases(
    cases: list[dict[str, object]], dotnet: str
) -> dict[tuple[str, str], dict[int, int]]:
    observed: dict[tuple[str, str], dict[int, int]] = {
        (str(case["stem"]), str(case["polarity"])): {} for case in cases
    }
    with tempfile.TemporaryDirectory(prefix="dfb-csharp-168-") as temporary:
        project = Path(temporary)
        write_project(project, cases)
        output_dir = project / "out"
        for index, source_value in enumerate(SOURCE_VALUES):
            for case in cases:
                (project / str(case["fixture_name"])).write_text(
                    instrument_case(case, source_value)
                )
            command = [
                dotnet,
                "build",
                str(project / "Probe.csproj"),
                "--nologo",
                "--verbosity",
                "quiet",
                "-o",
                str(output_dir),
            ]
            if index > 0:
                command.append("--no-restore")
            build = run_process(
                command,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
                context="dotnet build for C# recursive-composition probes",
            )
            if build.returncode != 0:
                raise RuntimeError(
                    "dotnet build failed for C# recursive-composition probes:\n"
                    f"{build.stdout}{build.stderr}"
                )
            execution = run_process(
                [dotnet, str(output_dir / "Probe.dll")],
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
                context="execution of C# recursive-composition probes",
            )
            if execution.returncode != 0:
                raise RuntimeError(
                    "execution failed for C# recursive-composition probes:\n"
                    f"{execution.stdout}{execution.stderr}"
                )
            lines = execution.stdout.strip().splitlines()
            if len(lines) != len(cases):
                raise AssertionError(
                    f"expected {len(cases)} integer sink outputs, got {len(lines)}: {lines!r}"
                )
            for case, line in zip(cases, lines):
                try:
                    value = int(line)
                except ValueError as error:
                    raise AssertionError(
                        f"{case['fixture']}: expected integer sink output, got {line!r}"
                    ) from error
                observed[(str(case["stem"]), str(case["polarity"]))][source_value] = value
    return observed


def check_observed(
    cases: list[dict[str, object]], observed: dict[tuple[str, str], dict[int, int]]
) -> None:
    source_delta = SOURCE_VALUES[1] - SOURCE_VALUES[0]
    for case in cases:
        key = (str(case["stem"]), str(case["polarity"]))
        values = observed[key]
        expected_base = EXPECTED[str(case["stem"])][str(case["polarity"])]
        fixture = case["fixture"]
        if values[SOURCE_VALUES[0]] != expected_base:
            raise AssertionError(
                f"{fixture}: source {SOURCE_VALUES[0]} expected sink value {expected_base}, "
                f"got {values[SOURCE_VALUES[0]]}"
            )
        observed_delta = values[SOURCE_VALUES[1]] - values[SOURCE_VALUES[0]]
        expected_delta = source_delta if case["polarity"] == "positive" else 0
        if observed_delta != expected_delta:
            raise AssertionError(
                f"{fixture}: source delta {source_delta} produced sink delta {observed_delta}; "
                f"expected {expected_delta} for {case['polarity']}"
            )
        print(
            f"{case['stem']}-{case['polarity']}: dotnet build + execution => "
            f"{SOURCE_VALUES[0]}:{values[SOURCE_VALUES[0]]}, "
            f"{SOURCE_VALUES[1]}:{values[SOURCE_VALUES[1]]} (delta {observed_delta})"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="DataFlowBench checkout (defaults to this script's repository)",
    )
    parser.add_argument(
        "--dotnet",
        default=shutil.which("dotnet"),
        help="dotnet executable (defaults to the PATH lookup)",
    )
    args = parser.parse_args()
    if not args.dotnet:
        raise RuntimeError("dotnet SDK/runtime not found; C# fixture probes cannot run")
    cases = [
        load_case(args.root, stem, polarity)
        for stem in EXPECTED
        for polarity in ("positive", "negative")
    ]
    check_observed(cases, probe_cases(cases, args.dotnet))


if __name__ == "__main__":
    main()
