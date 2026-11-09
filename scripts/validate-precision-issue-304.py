#!/usr/bin/env python3
"""Validate issue #304 list-removal fixtures and their runtime dependence."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = (
    "c",
    "cpp",
    "csharp",
    "go",
    "java",
    "javascript",
    "typescript",
    "kotlin",
    "scala",
    "swift",
    "rust",
    "python",
    "ruby",
    "php",
)
TEMPLATE_ID = "dfb-template-list-removal-index-shift"
SOURCE = "DFB-SOURCE: list-removal-index-shift-input"
SINK = "DFB-SINK: list-removal-index-shift-sink"
WITNESS = "DFB-WITNESS: list-removal-index-shift-remove-first"
PROBES = ("17", "83")
INTEGER_LANGUAGES = {"c", "cpp", "csharp", "go", "java", "kotlin", "scala", "swift", "rust"}
SAFE_VALUES = {language: ("9" if language in INTEGER_LANGUAGES else "more-safe") for language in LANGUAGES}


class ValidationError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValidationError(f"could not run {command[0]}: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        raise ValidationError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{detail}"
        )
    return result


def require_tool(language: str, name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(f"{language}: required executable `{name}` is unavailable")
    return path


def expected_filename(language: str, polarity: str) -> str:
    names = {
        "c": f"list_removal_index_shift_{polarity}.c",
        "cpp": f"ListRemovalIndexShift{polarity.title()}.cpp",
        "csharp": f"ListRemovalIndexShift{polarity.title()}.cs",
        "go": f"list_removal_index_shift_{polarity}.go",
        "java": f"ListRemovalIndexShift{polarity.title()}.java",
        "javascript": f"ListRemovalIndexShift{polarity.title()}.js",
        "typescript": f"ListRemovalIndexShift{polarity.title()}.ts",
        "kotlin": f"ListRemovalIndexShift{polarity.title()}.kt",
        "scala": f"ListRemovalIndexShift{polarity.title()}.scala",
        "swift": "main.swift",
        "rust": f"list_removal_index_shift_{polarity}.rs",
        "python": "list_removal_index_shift.py",
        "ruby": "list_removal_index_shift.rb",
        "php": "list_removal_index_shift.php",
    }
    return names[language]


def validate_metadata(languages: tuple[str, ...]) -> int:
    try:
        import jsonschema
    except ImportError as exc:
        raise ValidationError(
            "Python package `jsonschema` is required for case-schema validation"
        ) from exc

    schema_path = ROOT / "schemas" / "case.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    case_count = 0

    for language in languages:
        pair: dict[str, tuple[dict, Path, str]] = {}
        for polarity in ("positive", "negative"):
            case_dir = ROOT / "populations" / "precision-gaps-v1" / "cases" / "taint" / language / f"list-removal-index-shift-{polarity}"
            case_path = case_dir / "case.json"
            if not case_path.is_file():
                raise ValidationError(f"missing case metadata: {case_path.relative_to(ROOT)}")
            case = json.loads(case_path.read_text(encoding="utf-8"))
            errors = sorted(validator.iter_errors(case), key=lambda error: list(error.path))
            if errors:
                first = errors[0]
                location = ".".join(str(part) for part in first.path) or "$"
                raise ValidationError(
                    f"{case_path.relative_to(ROOT)}: schema error at {location}: {first.message}"
                )

            expected_id = f"dfb-taint-{language}-list-removal-index-shift-{polarity}"
            expected = {
                "id": expected_id,
                "template_id": TEMPLATE_ID,
                "polarity": polarity,
                "score_tier": "core",
                "track": "taint",
                "language": language,
                "semantic_dimensions": ["heap-field-sensitivity"],
                "feature_tags": ["heap-access-path"],
                "model_profile": "benchmark-controlled",
                "expected_analysis_capability": {"kind": "heap-list-index-shift-taint"},
            }
            for key, value in expected.items():
                if case.get(key) != value:
                    raise ValidationError(
                        f"{case_path.relative_to(ROOT)}: {key} is {case.get(key)!r}, expected {value!r}"
                    )
            if polarity == "negative":
                if case.get("negative_mechanism") != "field-separation":
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: negative must use field-separation")
            elif "negative_mechanism" in case:
                raise ValidationError(f"{case_path.relative_to(ROOT)}: positive has a negative mechanism")

            filename = expected_filename(language, polarity)
            if case.get("fixture_files") != [filename]:
                raise ValidationError(
                    f"{case_path.relative_to(ROOT)}: fixture_files must be [{filename!r}]"
                )
            fixture_path = case_dir / filename
            if not fixture_path.is_file():
                raise ValidationError(f"missing fixture: {fixture_path.relative_to(ROOT)}")
            fixture = fixture_path.read_text(encoding="utf-8")

            for marker in (SOURCE, SINK, WITNESS):
                count = fixture.count(marker)
                if count != 1:
                    raise ValidationError(
                        f"{fixture_path.relative_to(ROOT)}: expected one {marker!r}, found {count}"
                    )
            safe_literals = ("0", "9") if language in INTEGER_LANGUAGES else ('"safe"', '"more-safe"')
            if any(value not in fixture for value in safe_literals) or "dfb_source" not in fixture:
                raise ValidationError(
                    f"{fixture_path.relative_to(ROOT)}: fixture lacks the safe/source/list values"
                )

            for anchor_key, marker in (("source_anchors", SOURCE), ("sink_anchors", SINK)):
                anchors = case.get(anchor_key)
                if not isinstance(anchors, list) or len(anchors) != 1:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: expected one {anchor_key} entry")
                anchor = anchors[0]
                if anchor.get("marker") != marker or anchor.get("file") != filename:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: invalid {anchor_key}")
                lines = fixture.splitlines()
                marked_lines = [index for index, line in enumerate(lines, 1) if marker in line]
                if marked_lines != [anchor.get("line_hint")]:
                    raise ValidationError(
                        f"{case_path.relative_to(ROOT)}: {anchor_key} line_hint does not identify its marker"
                    )
                if language == "swift":
                    marker_line = lines[marked_lines[0] - 1]
                    call = "dfb_source()" if marker == SOURCE else "dfb_sink("
                    if call not in marker_line:
                        raise ValidationError(
                            f"{case_path.relative_to(ROOT)}: Swift {anchor_key} must mark its endpoint call line"
                        )

            if case.get("witness_checkpoints") != [SOURCE, WITNESS, SINK]:
                raise ValidationError(f"{case_path.relative_to(ROOT)}: unexpected witness checkpoint order")
            expected_flows = [{"source": SOURCE, "sink": SINK}] if polarity == "positive" else []
            expected_nonflows = [{"source": SOURCE, "sink": SINK}] if polarity == "negative" else []
            if case.get("expected_flows") != expected_flows:
                raise ValidationError(f"{case_path.relative_to(ROOT)}: expected_flows do not match polarity")
            if case.get("expected_nonflows") != expected_nonflows:
                raise ValidationError(f"{case_path.relative_to(ROOT)}: expected_nonflows do not match polarity")
            pair[polarity] = (case, fixture_path, fixture)
            case_count += 1

        if pair["positive"][0]["template_id"] != pair["negative"][0]["template_id"]:
            raise ValidationError(f"{language}: positive and negative template IDs differ")
        print(f"PASS {language}: schema, balanced core pair, source/sink/witness markers")

    return case_count


Builder = Callable[[str, Path, Path, dict[str, str]], list[str]]


def build_runner(language: str, fixture: Path, work: Path, env: dict[str, str]) -> list[str]:
    """Build one fixture once and return its executable command prefix."""
    stem = fixture.stem
    if language == "c":
        binary = work / "fixture"
        run([require_tool(language, "cc"), "-std=c11", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(binary)], cwd=work, env=env)
        return [str(binary)]
    if language == "cpp":
        binary = work / "fixture"
        run([require_tool(language, "c++"), "-std=c++17", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(binary)], cwd=work, env=env)
        return [str(binary)]
    if language == "csharp":
        require_tool(language, "dotnet")
        project = work / "project"
        output = work / "output"
        project.mkdir()
        source_copy = project / fixture.name
        shutil.copy2(fixture, source_copy)
        project_file = project / f"{stem}.csproj"
        project_file.write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup>"
            "<OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>"
            "<ImplicitUsings>disable</ImplicitUsings><Nullable>enable</Nullable>"
            "</PropertyGroup></Project>\n",
            encoding="utf-8",
        )
        run(
            ["dotnet", "build", str(project_file), "--nologo", "--verbosity", "quiet", "--output", str(output)],
            cwd=project,
            env=env,
        )
        return ["dotnet", str(output / f"{stem}.dll")]
    if language == "go":
        binary = work / "fixture"
        run([require_tool(language, "go"), "build", "-o", str(binary), str(fixture)], cwd=work, env=env)
        return [str(binary)]
    if language == "java":
        javac = require_tool(language, "javac")
        java = require_tool(language, "java")
        classes = work / "classes"
        classes.mkdir()
        run([javac, "-Xlint:all", "-Werror", "-d", str(classes), str(fixture)], cwd=work, env=env)
        class_name = stem
        return [java, "-cp", str(classes), class_name]
    if language == "javascript":
        return [require_tool(language, "node"), str(fixture)]
    if language == "typescript":
        node = require_tool(language, "node")
        # Node's built-in TypeScript stripping executes this type-annotated fixture.
        # A separate `tsc` check is attempted when available and reported otherwise.
        tsc = shutil.which("tsc")
        if tsc:
            output = work / "compiled"
            output.mkdir()
            run([tsc, "--strict", "--target", "ES2022", "--module", "commonjs", "--outDir", str(output), str(fixture)], cwd=work, env=env)
            return [node, str(output / f"{stem}.js")]
        return [node, "--experimental-strip-types", str(fixture)]
    if language == "kotlin":
        kotlinc = require_tool(language, "kotlinc")
        java = require_tool(language, "java")
        jar = work / "fixture.jar"
        run([kotlinc, str(fixture), "-include-runtime", "-d", str(jar)], cwd=work, env=env)
        return [java, "-jar", str(jar)]
    if language == "scala":
        scala = require_tool(language, "scala")
        workspace = work / "scala-workspace"
        workspace.mkdir()
        return [
            scala,
            "run",
            "--server=false",
            "--workspace",
            str(workspace),
            "--main-class",
            stem,
            str(fixture),
        ]
    if language == "swift":
        binary = work / "fixture"
        module_cache = work / "module-cache"
        module_cache.mkdir(exist_ok=True)
        run(
            [
                require_tool(language, "swiftc"),
                "-module-name",
                "DataFlowBenchTaintSwift",
                "-module-cache-path",
                str(module_cache),
                str(fixture),
                "-o",
                str(binary),
            ],
            cwd=work,
            env=env,
        )
        return [str(binary)]
    if language == "rust":
        binary = work / "fixture"
        run([require_tool(language, "rustc"), "--edition=2021", "-D", "warnings", str(fixture), "-o", str(binary)], cwd=work, env=env)
        return [str(binary)]
    if language == "python":
        return [require_tool(language, "python3"), str(fixture)]
    if language == "ruby":
        return [require_tool(language, "ruby"), str(fixture)]
    if language == "php":
        php = require_tool(language, "php")
        run([php, "-l", str(fixture)], cwd=work, env=env)
        return [php, str(fixture)]
    raise AssertionError(f"no runner defined for {language}")


def validate_runtime(languages: tuple[str, ...]) -> tuple[int, list[str]]:
    successful_cases = 0
    unavailable: list[str] = []
    env = os.environ.copy()
    env.update(
        {
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
            "DOTNET_NOLOGO": "1",
            "GOTOOLCHAIN": "local",
            "GONOSUMDB": "*",
            "GOSUMDB": "off",
        }
    )

    for language in languages:
        for polarity in ("positive", "negative"):
            case_dir = ROOT / "populations" / "precision-gaps-v1" / "cases" / "taint" / language / f"list-removal-index-shift-{polarity}"
            fixture = case_dir / expected_filename(language, polarity)
            try:
                with tempfile.TemporaryDirectory(prefix=f"dfb-304-{language}-") as temporary:
                    work = Path(temporary)
                    command_prefix = None
                    outputs: list[str] = []
                    for probe in PROBES:
                        probe_env = env.copy()
                        probe_env["DFB_INPUT"] = probe
                        if language == "swift":
                            swift_work = work / f"probe-{probe}"
                            swift_work.mkdir()
                            source_text = fixture.read_text(encoding="utf-8")
                            source_declaration = "func dfb_source() -> Int { 7 }"
                            if source_text.count(source_declaration) != 1:
                                raise ValidationError(
                                    "Swift source return literal must have one exact replacement point"
                                )
                            patched_fixture = swift_work / fixture.name
                            patched_fixture.write_text(
                                source_text.replace(
                                    source_declaration,
                                    f"func dfb_source() -> Int {{ {int(probe)} }}",
                                ),
                                encoding="utf-8",
                            )
                            command_prefix = build_runner(language, patched_fixture, swift_work, probe_env)
                        elif command_prefix is None:
                            command_prefix = build_runner(language, fixture, work, probe_env)
                        result = run(command_prefix, cwd=work, env=probe_env)
                        outputs.append(result.stdout.strip())
                    if polarity == "positive":
                        expected = list(PROBES)
                    else:
                        expected = [SAFE_VALUES[language], SAFE_VALUES[language]]
                    if outputs != expected:
                        raise ValidationError(
                            f"runtime output mismatch: got {outputs!r}, expected {expected!r}"
                        )
                print(f"PASS {language}/{polarity}: runtime output {outputs!r}")
                successful_cases += 1
            except FileNotFoundError as exc:
                print(f"UNAVAILABLE {language}/{polarity}: {exc}", file=sys.stderr)
                unavailable.append(f"{language}/{polarity}")
            except ValidationError as exc:
                print(f"FAIL {language}/{polarity}: {exc}", file=sys.stderr)
                raise

    return successful_cases, unavailable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--language",
        dest="languages",
        action="append",
        choices=LANGUAGES,
        help="validate one language; repeat to select several (default: all)",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="check schema, pair balance, anchors, and fixture markers without compiling or running",
    )
    args = parser.parse_args()
    languages = tuple(dict.fromkeys(args.languages or LANGUAGES))

    try:
        case_count = validate_metadata(languages)
        print(f"PASS metadata: {case_count} cases across {len(languages)} language(s)")
        if args.metadata_only:
            print("SKIP runtime: --metadata-only requested")
            return 0
        successful_cases, unavailable = validate_runtime(languages)
        if unavailable:
            print(
                f"INCOMPLETE runtime: {successful_cases} cases ran; unavailable toolchains: {', '.join(unavailable)}",
                file=sys.stderr,
            )
            return 2
        print(f"PASS runtime: {successful_cases} cases; two source probes per case")
        return 0
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
