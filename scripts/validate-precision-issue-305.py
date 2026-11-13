#!/usr/bin/env python3
"""Validate Issue 305 fixtures and prove their selected source dependence."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TEMPLATE_ID = "dfb-template-constant-string-selector"
SOURCE_MARKER = "DFB-SOURCE: constant-selector-input"
SINK_MARKER = "DFB-SINK: constant-selector-sink"
WITNESS_MARKER = "DFB-WITNESS: constant-selector-source-arm"
SOURCE_DECLARATIONS = {
    "c": "static const char *dfb_source(void)",
    "cpp": "static std::string dfb_source()",
    "csharp": "private static string dfb_source()",
    "go": "func dfb_source() string",
    "java": "private static String dfb_source()",
    "javascript": "function dfb_source()",
    "typescript": "function dfb_source(): string",
    "kotlin": "private fun dfb_source(): String =",
    "scala": "def dfb_source(): String =",
    "rust": "fn dfb_source() -> &'static str",
    "python": "def dfb_source():",
    "ruby": "def dfb_source",
    "php": "function dfb_source(): string",
}
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
TOOLCHAINS = {
    "c": (("cc", "gcc", "clang"),),
    "cpp": (("c++", "g++", "clang++"),),
    "csharp": (("dotnet",),),
    "go": (("go",),),
    "java": (("javac",), ("java",)),
    "javascript": (("node",),),
    "typescript": (("tsc",), ("node",)),
    "kotlin": (("kotlinc",), ("java",)),
    "scala": (("scala",), ("java",)),
    "swift": (("swiftc",),),
    "rust": ((str(Path.home() / ".cargo" / "bin" / "cargo"),), ("rustc",)),
    "python": (),
    "ruby": (("ruby",),),
    "php": (("php",),),
}
TIMEOUT_SECONDS = 90


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def selected_case(root: Path, language: str, polarity: str) -> tuple[dict, Path, str]:
    case_dir = root / "populations" / "precision-gaps-v1" / "cases" / "taint" / language
    case_dir /= f"constant-string-selector-{polarity}"
    case_path = case_dir / "case.json"
    metadata = json.loads(case_path.read_text())
    require(len(metadata["fixture_files"]) == 1, f"{case_path}: expected one fixture")
    fixture_name = metadata["fixture_files"][0]
    fixture_path = case_dir / fixture_name
    require(fixture_path.is_file(), f"{case_path}: missing fixture {fixture_name}")
    return metadata, fixture_path, fixture_name


def validate_metadata(root: Path, languages: list[str]) -> list[tuple[str, dict, Path, str]]:
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("metadata validation requires the Python jsonschema package") from error

    schema_path = root / "schemas" / "case.schema.json"
    schema = json.loads(schema_path.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    validated: list[tuple[str, dict, Path, str]] = []
    seen_ids: set[str] = set()

    for language in languages:
        pair = {}
        for polarity in ("positive", "negative"):
            metadata, fixture_path, fixture_name = selected_case(root, language, polarity)
            errors = sorted(validator.iter_errors(metadata), key=lambda error: list(error.path))
            require(
                not errors,
                f"{fixture_path.parent / 'case.json'}: schema errors: "
                + "; ".join(error.message for error in errors),
            )
            require(metadata["template_id"] == TEMPLATE_ID, f"{fixture_path}: wrong template ID")
            require(metadata["id"] not in seen_ids, f"duplicate case ID {metadata['id']}")
            seen_ids.add(metadata["id"])
            require(metadata["polarity"] == polarity, f"{fixture_path}: wrong polarity")
            require(metadata["score_tier"] == "core", f"{fixture_path}: must be core")
            require(metadata["track"] == "taint", f"{fixture_path}: wrong track")
            require(metadata["language"] == language, f"{fixture_path}: wrong language")
            require(
                metadata["model_profile"] == "benchmark-controlled",
                f"{fixture_path}: wrong model profile",
            )
            require(
                metadata["semantic_dimensions"] == ["local-flow", "path-sensitivity"],
                f"{fixture_path}: unexpected semantic dimensions",
            )
            require(metadata["feature_tags"] == ["intraprocedural"], f"{fixture_path}: wrong tags")
            require(
                metadata["fixture_provenance"]
                == {
                    "kind": "authored",
                    "origin": "DataFlowBench",
                    "revision": "issue-305",
                    "license": "MIT",
                },
                f"{fixture_path}: wrong fixture provenance",
            )
            require(metadata["expected_analysis_capability"]["kind"] == "constant-selector-intraprocedural-taint", f"{fixture_path}: wrong capability")

            source = fixture_path.read_text()
            for marker in (SOURCE_MARKER, SINK_MARKER, WITNESS_MARKER):
                require(source.count(marker) == 1, f"{fixture_path}: expected exactly one {marker}")
            require("dfb_source" in source, f"{fixture_path}: source arm is absent")
            if language == "swift":
                require("return 7" in source, f"{fixture_path}: Swift source value is absent")
                require("value = 0" in source, f"{fixture_path}: Swift safe arm is absent")
            else:
                require('"source-one"' in source, f"{fixture_path}: source value is absent")
                require('"safe"' in source, f"{fixture_path}: safe arm is absent")

            for anchor_group, marker in (
                ("source_anchors", SOURCE_MARKER),
                ("sink_anchors", SINK_MARKER),
            ):
                anchors = metadata[anchor_group]
                require(len(anchors) == 1, f"{fixture_path}: expected one {anchor_group}")
                anchor = anchors[0]
                require(anchor["marker"] == marker, f"{fixture_path}: wrong {anchor_group} marker")
                require(anchor["file"] == fixture_name, f"{fixture_path}: wrong {anchor_group} file")
                matching_lines = [
                    number
                    for number, line in enumerate(source.splitlines(), 1)
                    if marker in line
                ]
                require(
                    anchor.get("line_hint") == matching_lines[0],
                    f"{fixture_path}: stale line hint for {marker}",
                )

            require(
                len(metadata["expected_flows"]) == (1 if polarity == "positive" else 0),
                f"{fixture_path}: unbalanced expected flows",
            )
            require(
                len(metadata["expected_nonflows"]) == (1 if polarity == "negative" else 0),
                f"{fixture_path}: unbalanced expected nonflows",
            )
            relation = {"source": SOURCE_MARKER, "sink": SINK_MARKER}
            if polarity == "positive":
                require(metadata["expected_flows"] == [relation], f"{fixture_path}: wrong flow")
                require(
                    metadata["witness_checkpoints"] == [SOURCE_MARKER, WITNESS_MARKER, SINK_MARKER],
                    f"{fixture_path}: wrong positive witness",
                )
                require("negative_mechanism" not in metadata, f"{fixture_path}: positive has a negative mechanism")
            else:
                require(metadata["expected_nonflows"] == [relation], f"{fixture_path}: wrong nonflow")
                require(metadata["negative_mechanism"] == "infeasible-path", f"{fixture_path}: wrong negative mechanism")
                require(not metadata["witness_checkpoints"], f"{fixture_path}: negative has witness checkpoints")

            witness_lines = [
                line for line in source.splitlines()
                if WITNESS_MARKER in line
            ]
            require(
                len(witness_lines) == 1 and "dfb_source" in witness_lines[0],
                f"{fixture_path}: witness must mark the source arm",
            )
            if language == "swift":
                require(fixture_name == "main.swift", f"{fixture_path}: Swift endpoint contract requires main.swift")
                require("func dfb_source() -> Swift.Int" in source, f"{fixture_path}: wrong Swift source signature")
                require("func dfb_sink(_ value: Int) -> Void" in source, f"{fixture_path}: wrong Swift sink signature")
                require("dfb_source()" in witness_lines[0], f"{fixture_path}: source anchor must mark the endpoint call")
                require("dfb_sink(value)" in source, f"{fixture_path}: missing Swift sink endpoint call")
            else:
                source_marker_line = next(
                    line for line in source.splitlines() if SOURCE_MARKER in line
                )
                require(
                    SOURCE_DECLARATIONS[language] in source_marker_line,
                    f"{fixture_path}: source marker must be on the source declaration",
                )
                require(
                    source.count('"source-one"') == 1,
                    f"{fixture_path}: expected one replaceable source return literal",
                )
            pair[polarity] = metadata
            validated.append((language, metadata, fixture_path, fixture_name))

        positive = pair["positive"]
        negative = pair["negative"]
        for field in (
            "template_id",
            "score_tier",
            "track",
            "language",
            "semantic_dimensions",
            "feature_tags",
            "model_profile",
            "expected_analysis_capability",
        ):
            require(positive[field] == negative[field], f"{language}: pair differs in {field}")
        print(f"{language}: schema, markers, and balanced pair valid")

    return validated


def executable(name_options: tuple[str, ...]) -> str | None:
    return next((path for name in name_options if (path := shutil.which(name))), None)


def missing_toolchains(languages: list[str]) -> list[str]:
    missing = []
    for language in languages:
        for alternatives in TOOLCHAINS[language]:
            if executable(alternatives) is None:
                missing.append(f"{language}: requires one of {', '.join(alternatives)}")
    return missing


def invoke(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"timed out: {' '.join(command)}") from error
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result.stdout.strip()


def compile_and_run(language: str, fixture_name: str, source: str, directory: Path) -> str:
    fixture = directory / fixture_name
    fixture.write_text(source)
    binary = directory / "fixture"
    env = os.environ.copy()

    if language == "c":
        compiler = executable(TOOLCHAINS["c"][0])
        assert compiler
        invoke([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(binary)], directory)
        return invoke([str(binary)], directory)
    if language == "cpp":
        compiler = executable(TOOLCHAINS["cpp"][0])
        assert compiler
        invoke([compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(binary)], directory)
        return invoke([str(binary)], directory)
    if language == "csharp":
        dotnet = executable(TOOLCHAINS["csharp"][0])
        assert dotnet
        project = directory / "RuntimeProbe.csproj"
        project.write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk\">\n"
            "  <PropertyGroup>\n"
            "    <OutputType>Exe</OutputType>\n"
            "    <TargetFramework>net8.0</TargetFramework>\n"
            "    <AssemblyName>RuntimeProbe</AssemblyName>\n"
            "    <ImplicitUsings>disable</ImplicitUsings>\n"
            "    <Nullable>disable</Nullable>\n"
            "  </PropertyGroup>\n"
            "</Project>\n"
        )
        env["DOTNET_NOLOGO"] = "1"
        env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
        env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
        output = directory / "out"
        invoke([dotnet, "build", str(project), "--output", str(output), "--nologo", "--verbosity", "quiet"], directory, env)
        return invoke([dotnet, str(output / "RuntimeProbe.dll")], directory, env)
    if language == "go":
        go = executable(TOOLCHAINS["go"][0])
        assert go
        env["GO111MODULE"] = "off"
        return invoke([go, "run", str(fixture)], directory, env)
    if language == "java":
        javac = executable(TOOLCHAINS["java"][0])
        java = executable(TOOLCHAINS["java"][1])
        assert javac and java
        invoke([javac, "-Xlint:all", "-Werror", str(fixture)], directory)
        return invoke([java, f"ConstantStringSelector{fixture.stem.rsplit('_', 1)[1].title()}"], directory)
    if language == "javascript":
        node = executable(TOOLCHAINS["javascript"][0])
        assert node
        return invoke([node, str(fixture)], directory)
    if language == "typescript":
        compiler = executable(TOOLCHAINS["typescript"][0])
        node = executable(TOOLCHAINS["typescript"][1])
        assert compiler and node
        output = directory / "typescript-output"
        output.mkdir()
        invoke(
            [
                compiler,
                "--strict",
                "--target",
                "ES2019",
                "--module",
                "commonjs",
                "--outDir",
                str(output),
                str(fixture),
            ],
            directory,
        )
        return invoke([node, str(output / f"{fixture.stem}.js")], directory)
    if language == "kotlin":
        compiler = executable(TOOLCHAINS["kotlin"][0])
        java = executable(TOOLCHAINS["kotlin"][1])
        assert compiler and java
        jar = directory / "fixture.jar"
        invoke([compiler, str(fixture), "-include-runtime", "-d", str(jar)], directory)
        return invoke([java, "-jar", str(jar)], directory)
    if language == "scala":
        runner = executable(TOOLCHAINS["scala"][0])
        assert runner
        class_name = "ConstantStringSelector" + fixture.stem.rsplit("_", 1)[1].title()
        env["SCALA_CLI_HOME"] = str(directory / "scala-cli-home")
        env["COURSIER_CACHE"] = str(directory / "coursier-cache")
        return invoke(
            [runner, "run", "--server=false", "--main-class", class_name, str(fixture)],
            directory,
            env,
        )
    if language == "swift":
        compiler = executable(TOOLCHAINS["swift"][0])
        assert compiler
        module_cache = directory / "swift-module-cache"
        module_cache.mkdir()
        invoke(
            [
                compiler,
                "-module-name",
                "DataFlowBenchTaintSwift",
                "-module-cache-path",
                str(module_cache),
                "-clang-scanner-module-cache-path",
                str(module_cache / "clang-scanner"),
                "-warnings-as-errors",
                str(fixture),
                "-o",
                str(binary),
            ],
            directory,
        )
        return invoke([str(binary)], directory)
    if language == "rust":
        cargo = executable(TOOLCHAINS["rust"][0])
        assert cargo
        project = directory / "rust-project"
        source_dir = project / "src"
        source_dir.mkdir(parents=True)
        (source_dir / "main.rs").write_text(source)
        manifest = project / "Cargo.toml"
        manifest.write_text(
            "[package]\n"
            'name = "dfb-issue-305-probe"\n'
            'version = "0.1.0"\n'
            'edition = "2021"\n'
        )
        env["CARGO_TARGET_DIR"] = str(directory / "cargo-target")
        env["CARGO_BUILD_JOBS"] = "2"
        invoke(
            [cargo, "build", "--offline", "--quiet", "--manifest-path", str(manifest)],
            directory,
            env,
        )
        return invoke(
            [str(directory / "cargo-target" / "debug" / "dfb-issue-305-probe")],
            directory,
            env,
        )
    if language == "python":
        return invoke([sys.executable, str(fixture)], directory)
    if language == "ruby":
        interpreter = executable(TOOLCHAINS["ruby"][0])
        assert interpreter
        return invoke([interpreter, str(fixture)], directory)
    if language == "php":
        interpreter = executable(TOOLCHAINS["php"][0])
        assert interpreter
        return invoke([interpreter, "-d", "display_errors=1", str(fixture)], directory)
    raise AssertionError(f"unhandled language {language}")


def validate_runtime(validated: list[tuple[str, dict, Path, str]]) -> None:
    for language, metadata, fixture_path, fixture_name in validated:
        original = fixture_path.read_text()
        if language == "swift":
            require("return 7" in original, f"{fixture_path}: Swift source value cannot be varied")
            changed = original.replace("return 7", "return 11", 1)
            source_before, source_after, safe_value = "7", "11", "0"
        else:
            require(
                original.count('"source-one"') == 1,
                f"{fixture_path}: expected one replaceable source return literal",
            )
            changed = original.replace('"source-one"', '"source-two"', 1)
            source_before, source_after, safe_value = "source-one", "source-two", "safe"
        require(changed != original, f"{fixture_path}: source substitution did not change the fixture")
        polarity = metadata["polarity"]
        expected_before = source_before if polarity == "positive" else safe_value
        expected_after = source_after if polarity == "positive" else safe_value

        outputs = []
        for variant in (original, changed):
            with tempfile.TemporaryDirectory(prefix=f"dfb-305-{language}-") as temporary:
                output = compile_and_run(language, fixture_name, variant, Path(temporary))
                outputs.append(output)
        require(
            outputs == [expected_before, expected_after],
            f"{fixture_path}: source mutation produced {outputs!r}; "
            f"expected {[expected_before, expected_after]!r}",
        )
        print(
            f"{language}/{polarity}: compiled and ran; "
            f"{source_before} => {outputs[0]}, {source_after} => {outputs[1]}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="validate JSON schema, markers, pair balance, and provenance without runtimes",
    )
    parser.add_argument(
        "--language",
        action="append",
        choices=LANGUAGES,
        help="select a language; repeat the option to select more than one",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="DataFlowBench checkout (defaults to this script's repository)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    languages = list(dict.fromkeys(args.language or LANGUAGES))

    try:
        validated = validate_metadata(root, languages)
    except (AssertionError, OSError, ValueError, RuntimeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.metadata_only:
        print(f"PASS: metadata checks for {len(languages)} language(s)")
        return 0

    missing = missing_toolchains(languages)
    if missing:
        print("UNAVAILABLE: full-runtime validation lacks required toolchains:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
    unavailable_languages = {item.split(":", 1)[0] for item in missing}
    runtime_cases = [item for item in validated if item[0] not in unavailable_languages]
    try:
        validate_runtime(runtime_cases)
    except (AssertionError, OSError, RuntimeError) as error:
        print(f"FAIL: runtime validation: {error}", file=sys.stderr)
        return 1
    if missing:
        print(
            f"INCOMPLETE: runtime checks ran where possible, but {len(missing)} "
            "required toolchain group(s) were unavailable",
            file=sys.stderr,
        )
        return 2
    print(f"PASS: metadata and runtime checks for {len(languages)} language(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
