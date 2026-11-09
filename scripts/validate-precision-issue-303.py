#!/usr/bin/env python3
"""Validate issue 303 case metadata and executable source dependence."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    print(f"error: Python jsonschema is required: {exc}", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
ALL_LANGUAGES = (
    "c", "cpp", "csharp", "go", "java", "javascript", "typescript",
    "kotlin", "scala", "swift", "rust", "python", "ruby", "php",
)
APPLICABLE_LANGUAGES = tuple(lang for lang in ALL_LANGUAGES if lang != "c")
SLUGS = (
    "same-map-constant-keys",
    "same-map-computed-key",
    "same-map-escaping-callee",
)
TEMPLATE_IDS = {
    "same-map-constant-keys": "dfb-template-issue-303-same-map-constant-keys",
    "same-map-computed-key": "dfb-template-issue-303-same-map-computed-key",
    "same-map-escaping-callee": "dfb-template-issue-303-same-map-escaping-callee",
}
SOURCE_MARKER = "DFB-SOURCE: issue303-source"
SINK_MARKER = "DFB-SINK: issue303-sink"
SOURCE_VALUE = "DFB_SOURCE_303"
MUTATED_VALUE = "DFB_MUTATED_303"
CLEAN_VALUE = "clean"
CLEAN_INT = "0"
RUN_CACHE_ROOT: Path | None = None


class ValidationError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
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
        raise ValidationError(f"could not execute {command[0]}: {exc}") from exc
    if result.returncode != 0:
        tail = (result.stdout + result.stderr)[-3500:]
        raise ValidationError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{tail}"
        )
    return result


def line_number(text: str, marker: str) -> int | None:
    lines = [i for i, line in enumerate(text.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        return None
    return lines[0]


def metadata_check() -> list[tuple[dict, Path, str]]:
    schema_path = ROOT / "schemas" / "case.schema.json"
    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator(schema)
    canonical_tool_references = {
        lang: json.loads(
            (ROOT / "cases" / "taint" / lang / "infeasible-branch-positive" / "case.json").read_text()
        )["tool_model_references"]
        for lang in APPLICABLE_LANGUAGES
    }
    records: dict[tuple[str, str, str], tuple[dict, Path, str]] = {}
    expected_keys = {
        (lang, slug, polarity)
        for lang in APPLICABLE_LANGUAGES
        for slug in SLUGS
        for polarity in ("positive", "negative")
    }

    for lang in APPLICABLE_LANGUAGES:
        for slug in SLUGS:
            for polarity in ("positive", "negative"):
                case_dir = ROOT / "populations" / "precision-gaps-v1" / "cases" / "taint" / lang / f"{slug}-{polarity}"
                case_path = case_dir / "case.json"
                if not case_path.is_file():
                    raise ValidationError(f"missing case file: {case_path.relative_to(ROOT)}")
                case = json.loads(case_path.read_text())
                errors = sorted(validator.iter_errors(case), key=lambda error: list(error.path))
                if errors:
                    formatted = "; ".join(
                        f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
                        for error in errors
                    )
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: {formatted}")

                expected_id = f"dfb-taint-{lang}-{slug}-{polarity}"
                if case["id"] != expected_id:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: unexpected id {case['id']}")
                if case["template_id"] != TEMPLATE_IDS[slug]:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong template_id")
                if case["polarity"] != polarity or case["score_tier"] != "core":
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong polarity or score tier")
                if case["track"] != "taint" or case["language"] != lang:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong track or language")
                if case["model_profile"] != "benchmark-controlled":
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong model profile")
                if case["tool_model_references"] != canonical_tool_references[lang]:
                    raise ValidationError(
                        f"{case_path.relative_to(ROOT)}: tool_model_references must match "
                        f"the language's infeasible-branch-positive case"
                    )
                expected_semantics = {
                    "same-map-constant-keys": (
                        ["heap-field-sensitivity"],
                        ["heap-access-path"],
                        "same-map-constant-key-sensitive-taint",
                    ),
                    "same-map-computed-key": (
                        ["heap-field-sensitivity", "path-sensitivity"],
                        ["heap-access-path", "computed-access"],
                        "computed-map-key-aliasing-taint",
                    ),
                    "same-map-escaping-callee": (
                        ["heap-field-sensitivity", "interprocedural-flow"],
                        ["heap-access-path", "interprocedural-one-hop"],
                        "interprocedural-map-mutation-taint",
                    ),
                }[slug]
                if case["semantic_dimensions"] != expected_semantics[0]:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong semantic dimensions")
                if case["feature_tags"] != expected_semantics[1]:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong feature tags")
                if case["expected_analysis_capability"]["kind"] != expected_semantics[2]:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: wrong expected capability")
                if len(case["fixture_files"]) != 1:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: expected one fixture file")

                fixture_name = case["fixture_files"][0]
                fixture_path = (case_dir / fixture_name).resolve()
                if not fixture_path.is_relative_to(case_dir.resolve()) or not fixture_path.is_file():
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: invalid fixture file {fixture_name}")
                source_text = fixture_path.read_text()
                for anchor_field, wanted_marker in (
                    ("source_anchors", SOURCE_MARKER),
                    ("sink_anchors", SINK_MARKER),
                ):
                    anchors = case[anchor_field]
                    if len(anchors) != 1 or anchors[0]["marker"] != wanted_marker:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: invalid {anchor_field}")
                    anchor = anchors[0]
                    if anchor["file"] != fixture_name:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: anchor names wrong file")
                    actual_line = line_number(source_text, wanted_marker)
                    if actual_line is None:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: marker missing or duplicated: {wanted_marker}")
                    if anchor.get("line_hint") is not None and anchor["line_hint"] != actual_line:
                        raise ValidationError(
                            f"{case_path.relative_to(ROOT)}: {wanted_marker} line_hint "
                            f"{anchor['line_hint']} does not match {actual_line}"
                        )

                if source_text.count(SOURCE_MARKER.split(": ", 1)[1]) < 1:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: source marker absent")
                if polarity == "positive":
                    if case["expected_nonflows"] or len(case["expected_flows"]) != 1:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: positive flow contract is unbalanced")
                    if "negative_mechanism" in case:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: positive has negative_mechanism")
                    expected_checkpoints = {
                        "same-map-constant-keys": [
                            SOURCE_MARKER,
                            "DFB-WITNESS: issue303-store",
                            "DFB-WITNESS: issue303-read",
                            SINK_MARKER,
                        ],
                        "same-map-computed-key": [
                            SOURCE_MARKER,
                            "DFB-WITNESS: issue303-store",
                            "DFB-WITNESS: issue303-read",
                            SINK_MARKER,
                        ],
                        "same-map-escaping-callee": [
                            "DFB-WITNESS: issue303-invoke",
                            SOURCE_MARKER,
                            "DFB-WITNESS: issue303-callee-store",
                            "DFB-WITNESS: issue303-read",
                            SINK_MARKER,
                        ],
                    }[slug]
                    if case["witness_checkpoints"] != expected_checkpoints:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: witness checkpoint order is wrong")
                else:
                    if case["expected_flows"] or len(case["expected_nonflows"]) != 1:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: negative flow contract is unbalanced")
                    if case.get("negative_mechanism") != "unrelated-value":
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: negative mechanism is not explicit")
                    if case["witness_checkpoints"]:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: negative has witness checkpoints")

                expected_flow = {"source": SOURCE_MARKER, "sink": SINK_MARKER}
                actual_flows = case["expected_flows"] if polarity == "positive" else case["expected_nonflows"]
                if actual_flows != [expected_flow]:
                    raise ValidationError(f"{case_path.relative_to(ROOT)}: flow anchors do not match")
                for checkpoint in case["witness_checkpoints"]:
                    if source_text.count(checkpoint) != 1:
                        raise ValidationError(
                            f"{case_path.relative_to(ROOT)}: witness marker missing or duplicated: {checkpoint}"
                        )
                if lang == "swift":
                    if fixture_name != "main.swift":
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift fixture must be main.swift")
                    if not re.search(r"func dfb_source\(\) -> Int", source_text):
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift source signature changed")
                    if not re.search(r"func dfb_sink\(_ value: Int\)", source_text):
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift sink signature changed")
                    if source_text.count("DFB-SOURCE: issue303-source") != 1 or source_text.count("DFB-SINK: issue303-sink") != 1:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift endpoint markers must be unique call-site markers")
                    if not re.search(r"dfb_source\(\).*DFB-SOURCE: issue303-source", source_text):
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift source marker is not on a source call")
                    if not re.search(r"dfb_sink\(.*DFB-SINK: issue303-sink", source_text):
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: Swift sink marker is not on a sink call")
                else:
                    if source_text.count(SOURCE_VALUE) != 1:
                        raise ValidationError(f"{case_path.relative_to(ROOT)}: source value token must occur once")

                records[(lang, slug, polarity)] = (case, fixture_path, source_text)

    actual = set(records)
    if actual != expected_keys:
        raise ValidationError(
            f"case inventory mismatch: missing={sorted(expected_keys - actual)}, "
            f"extra={sorted(actual - expected_keys)}"
        )
    c_issue_cases = [
        path for path in (ROOT / "populations" / "precision-gaps-v1" / "cases" / "taint" / "c").glob("*")
        if path.name in {f"{slug}-{polarity}" for slug in SLUGS for polarity in ("positive", "negative")}
    ]
    if c_issue_cases:
        raise ValidationError("C must remain inapplicable and have no forced map fixtures")
    for lang in APPLICABLE_LANGUAGES:
        for slug in SLUGS:
            positive = records[(lang, slug, "positive")][0]
            negative = records[(lang, slug, "negative")][0]
            for field in ("template_id", "score_tier", "track", "language", "model_profile"):
                if positive[field] != negative[field]:
                    raise ValidationError(f"unbalanced pair metadata for {lang}/{slug}: {field}")
    return list(records.values())


def environment_for(temp: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
    cache_root = RUN_CACHE_ROOT or temp
    env["DOTNET_CLI_HOME"] = str(cache_root / "dotnet-home")
    env["NUGET_PACKAGES"] = str(cache_root / "nuget-packages")
    env["GOCACHE"] = str(cache_root / "go-cache")
    env["GOMODCACHE"] = str(cache_root / "go-mod-cache")
    env["GOTOOLCHAIN"] = "local"
    env["GOSUMDB"] = "off"
    env["COURSIER_CACHE"] = str(cache_root / "coursier-cache")
    env["SCALA_CLI_HOME"] = str(cache_root / "scala-cli-home")
    env["SWIFT_MODULECACHE_PATH"] = str(cache_root / "swift-module-cache")
    env["CLANG_MODULE_CACHE_PATH"] = str(cache_root / "clang-module-cache")
    return env


def needed_tools(lang: str) -> list[str]:
    tools = {
        "cpp": ["g++"],
        "csharp": ["dotnet"],
        "go": ["go"],
        "java": ["javac", "java"],
        "javascript": ["node"],
        "typescript": ["node"],
        "kotlin": ["kotlinc", "java"],
        "scala": ["scala"],
        "swift": ["swiftc"],
        "rust": ["rustc"],
        "python": ["python3"],
        "ruby": ["ruby"],
        "php": ["php"],
    }
    return tools[lang]


def make_runner(lang: str, case: dict, fixture_name: str, source_text: str, temp: Path) -> Callable[[list[str]], str]:
    env = environment_for(temp)
    source = temp / fixture_name
    source.write_text(source_text)
    # The filename/class use the scenario slug followed by polarity.
    case_slug = next(slug for slug in SLUGS if f"-{slug}-" in case["id"])
    polarity = case["polarity"]
    class_name = "".join(part.capitalize() for part in case_slug.split("-")) + polarity.capitalize()

    if lang == "cpp":
        executable = temp / "issue303"
        run(["g++", "-std=c++17", str(source), "-o", str(executable)],
            cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "csharp":
        framework = "net8.0"
        project = temp / "Issue303Runtime.csproj"
        project.write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk\">"
            "<PropertyGroup><OutputType>Exe</OutputType><TargetFramework>" + framework +
            "</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable>"
            "</PropertyGroup></Project>"
        )
        nuget_config = temp / "NuGet.Config"
        nuget_config.write_text(
            "<configuration><packageSources><clear /></packageSources></configuration>"
        )
        assets = temp / "obj" / "project.assets.json"
        if not assets.is_file():
            run(["dotnet", "restore", str(project), "--configfile", str(nuget_config),
                 "--verbosity", "quiet"], cwd=temp, env=env)
        run(["dotnet", "build", str(project), "--no-restore", "--nologo",
             "--verbosity", "quiet"], cwd=temp, env=env)
        dll = temp / "bin" / "Debug" / framework / "Issue303Runtime.dll"
        command = ["dotnet", str(dll)]
    elif lang == "go":
        executable = temp / "issue303"
        run(["go", "build", "-o", str(executable), str(source)], cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "java":
        classes = temp / "classes"
        classes.mkdir(exist_ok=True)
        run(["javac", "-d", str(classes), str(source)], cwd=temp, env=env)
        command = ["java", "-cp", str(classes), class_name]
    elif lang == "javascript":
        command = ["node", str(source)]
    elif lang == "typescript":
        tsc = shutil.which("tsc")
        if tsc:
            output = temp / "ts-out"
            output.mkdir(exist_ok=True)
            run([tsc, "--pretty", "false", "--strict", "--target", "ES2022",
                 "--module", "commonjs", "--outDir", str(output), str(source)],
                cwd=temp, env=env)
            command = ["node", str(output / (Path(fixture_name).stem + ".js"))]
        else:
            node = shutil.which("node")
            help_text = subprocess.run([node, "--help"], text=True, capture_output=True, check=False)
            if "--experimental-strip-types" not in help_text.stdout:
                raise ValidationError("TypeScript needs tsc or Node's --experimental-strip-types")
            command = ["node", "--experimental-strip-types", str(source)]
    elif lang == "kotlin":
        jar = temp / "issue303.jar"
        run(["kotlinc", str(source), "-include-runtime", "-d", str(jar)], cwd=temp, env=env)
        command = ["java", "-jar", str(jar)]
    elif lang == "scala":
        workspace = temp / "scala-workspace"
        workspace.mkdir(exist_ok=True)
        command = [
            "scala", "run", "--server=false", "--workspace", str(workspace),
            "--main-class", class_name, str(source), "--",
        ]
    elif lang == "swift":
        executable = temp / "issue303"
        module_cache = (RUN_CACHE_ROOT or temp) / "swift-module-cache"
        module_cache.mkdir(exist_ok=True)
        run([
            "swiftc", "-module-name", "DataFlowBenchTaintSwift",
            "-module-cache-path", str(module_cache), str(source), "-o", str(executable)
        ], cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "rust":
        executable = temp / "issue303"
        run(["rustc", "--edition=2021", str(source), "-o", str(executable)],
            cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "python":
        command = ["python3", str(source)]
    elif lang == "ruby":
        run(["ruby", "-c", str(source)], cwd=temp, env=env)
        command = ["ruby", str(source)]
    elif lang == "php":
        run(["php", "-l", str(source)], cwd=temp, env=env)
        command = ["php", str(source)]
    else:
        raise ValidationError(f"no runtime configured for {lang}")

    def invoke(args: list[str]) -> str:
        result = run(command + args, cwd=temp, env=env)
        return result.stdout.strip()

    return invoke


def runtime_check(records: list[tuple[dict, Path, str]], selected: set[str]) -> tuple[int, list[str]]:
    global RUN_CACHE_ROOT
    with tempfile.TemporaryDirectory(prefix="dfb-issue303-cache-") as cache_dir:
        RUN_CACHE_ROOT = Path(cache_dir)
        try:
            return _runtime_check(records, selected)
        finally:
            RUN_CACHE_ROOT = None


def _runtime_check(records: list[tuple[dict, Path, str]], selected: set[str]) -> tuple[int, list[str]]:
    unavailable: list[str] = []
    total = 0
    for lang in ALL_LANGUAGES:
        if lang not in selected:
            continue
        if lang == "c":
            print("runtime: c skipped (no standard associative map; documented inapplicable)")
            continue
        missing = [tool for tool in needed_tools(lang) if shutil.which(tool) is None]
        if missing:
            unavailable.append(f"{lang}: missing {', '.join(missing)}")
            print(f"runtime: {lang} unavailable (missing {', '.join(missing)})")
            continue
        if lang == "typescript" and shutil.which("tsc") is None:
            print("runtime: typescript uses Node type stripping; tsc static type-check is unavailable")
        for slug in SLUGS:
            for polarity in ("positive", "negative"):
                case, fixture_path, source_text = next(
                    item for item in records
                    if item[0]["language"] == lang
                    and item[0]["id"] == f"dfb-taint-{lang}-{slug}-{polarity}"
                )
                fixture_name = case["fixture_files"][0]
                swift = lang == "swift"
                base_args = ["payload"] if slug == "same-map-computed-key" else []
                expected_base = "7" if swift and polarity == "positive" else (
                    CLEAN_INT if swift else (SOURCE_VALUE if polarity == "positive" else CLEAN_VALUE)
                )
                expected_mutated = "71" if swift and polarity == "positive" else (
                    CLEAN_INT if swift else (MUTATED_VALUE if polarity == "positive" else CLEAN_VALUE)
                )
                with tempfile.TemporaryDirectory(prefix=f"dfb-issue303-{lang}-") as temporary:
                    temp = Path(temporary)
                    try:
                        original_runner = make_runner(lang, case, fixture_name, source_text, temp)
                        actual = original_runner(base_args)
                        if actual != expected_base:
                            raise ValidationError(
                                f"{case['id']}: expected baseline sink output {expected_base!r}, got {actual!r}"
                            )
                        if slug == "same-map-computed-key":
                            extra_args = ["different-key"] if polarity == "positive" else [""]
                            extra = original_runner(extra_args)
                            if extra != (CLEAN_INT if swift else CLEAN_VALUE):
                                raise ValidationError(
                                    f"{case['id']}: nonaliasing computed-key run was not clean: {extra!r}"
                                )

                        if swift:
                            if source_text.count("return 7") != 1:
                                raise ValidationError(f"{case['id']}: expected one Swift source return literal 7")
                            mutated_text = source_text.replace("return 7", "return 71", 1)
                        else:
                            if source_text.count(SOURCE_VALUE) != 1:
                                raise ValidationError(f"{case['id']}: expected one source value token")
                            mutated_text = source_text.replace(SOURCE_VALUE, MUTATED_VALUE, 1)
                        mutated_runner = make_runner(lang, case, fixture_name, mutated_text, temp)
                        mutated = mutated_runner(base_args)
                        if mutated != expected_mutated:
                            raise ValidationError(
                                f"{case['id']}: source mutation expected sink output "
                                f"{expected_mutated!r}, got {mutated!r}"
                            )
                        total += 1
                    except ValidationError as exc:
                        raise ValidationError(f"{case['id']}: {exc}") from exc
        print(f"runtime: {lang} passed {len(SLUGS) * 2} executable cases")
    return total, unavailable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="validate JSON schema, markers, metadata, and pair balance without running languages",
    )
    parser.add_argument(
        "--language",
        action="append",
        choices=ALL_LANGUAGES,
        help="run runtime validation only for this language; repeat to select several languages",
    )
    args = parser.parse_args()

    try:
        records = metadata_check()
    except (ValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"metadata validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"metadata: passed {len(records)} cases, schema and marker checks, 3 balanced templates")
    if args.metadata_only:
        print("runtime: skipped by --metadata-only")
        return 0

    selected = set(args.language) if args.language else set(ALL_LANGUAGES)
    try:
        total, unavailable = runtime_check(records, selected)
    except ValidationError as exc:
        print(f"runtime validation failed: {exc}", file=sys.stderr)
        return 1
    if unavailable:
        print("runtime validation incomplete; unavailable toolchains:", file=sys.stderr)
        for item in unavailable:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print(f"runtime: passed source-dependence checks for {total} executable cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
