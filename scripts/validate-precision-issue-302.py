#!/usr/bin/env python3
"""Validate and execute the folded-local-constant fixtures for issue #302."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as error:  # pragma: no cover - environment-specific diagnostic
    raise SystemExit(
        "jsonschema is required for case validation (install the repository's "
        "Python validation dependencies)"
    ) from error


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "case.schema.json"
SOURCE = "DFB-SOURCE: folded-local-constant-source"
SINK = "DFB-SINK: folded-local-constant-sink"
WITNESS = "DFB-WITNESS: folded-local-constant-source-selected"
TEMPLATES = {
    "if": "dfb-template-folded-local-constant-if",
    "conditional-expression": "dfb-template-folded-local-constant-conditional-expression",
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
APPLICABLE = {
    "if": set(LANGUAGES),
    "conditional-expression": set(LANGUAGES) - {"go"},
}
EXTENSIONS = {
    "c": ".c",
    "cpp": ".cpp",
    "csharp": ".cs",
    "go": ".go",
    "java": ".java",
    "javascript": ".js",
    "typescript": ".ts",
    "kotlin": ".kt",
    "scala": ".scala",
    "swift": ".swift",
    "rust": ".rs",
    "python": ".py",
    "ruby": ".rb",
    "php": ".php",
}
MARKER_RE = re.compile(r"DFB-(?:SOURCE|SINK|WITNESS): [A-Za-z0-9-]+")
REQUIRED_TOOLS = {
    "c": ("cc",),
    "cpp": ("c++",),
    "csharp": ("dotnet",),
    "go": ("go",),
    "java": ("javac", "java"),
    "javascript": ("node",),
    "typescript": ("tsc", "node"),
    "kotlin": ("kotlinc", "java"),
    "scala": ("scala",),
    "swift": ("swiftc",),
    "rust": ("rustc",),
    "python": ("python3",),
    "ruby": ("ruby",),
    "php": ("php",),
}
NUMERIC_LANGUAGES = {"c", "cpp", "csharp", "go", "java", "kotlin", "scala", "swift", "rust"}


class ValidationError(Exception):
    pass


def case_slug(form: str) -> str:
    return f"folded-local-constant-{form}"


def selected_languages(args: argparse.Namespace) -> set[str]:
    if not args.language:
        return set(LANGUAGES)
    unknown = sorted(set(args.language) - set(LANGUAGES))
    if unknown:
        raise ValidationError(f"unknown language key(s): {', '.join(unknown)}")
    return set(args.language)


def load_and_validate_cases(languages: set[str]) -> list[tuple[Path, dict]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    template_to_form = {template: form for form, template in TEMPLATES.items()}
    grouped: dict[tuple[str, str, str], list[tuple[Path, dict]]] = defaultdict(list)
    all_cases: list[tuple[Path, dict]] = []
    seen_case_ids: set[str] = set()

    for case_path in sorted((ROOT / "cases" / "taint").glob("*/folded-local-constant-*/case.json")):
        metadata = json.loads(case_path.read_text(encoding="utf-8"))
        if metadata.get("template_id") not in template_to_form:
            continue
        lang = metadata.get("language")
        if lang not in languages:
            continue
        try:
            validator.validate(metadata)
        except Exception as error:
            raise ValidationError(f"{case_path.relative_to(ROOT)}: schema validation failed: {error}") from error

        form = template_to_form[metadata["template_id"]]
        polarity = metadata["polarity"]
        expected_id = f"dfb-taint-{lang}-{case_slug(form)}-{polarity}"
        if metadata["id"] != expected_id:
            raise ValidationError(f"{case_path.relative_to(ROOT)}: expected case ID {expected_id}")
        if metadata["id"] in seen_case_ids:
            raise ValidationError(f"duplicate case ID {metadata['id']}")
        seen_case_ids.add(metadata["id"])
        if case_path.parent.name != f"{case_slug(form)}-{polarity}":
            raise ValidationError(f"{case_path.relative_to(ROOT)}: directory does not match template and polarity")
        if metadata["score_tier"] != "core" or metadata["track"] != "taint":
            raise ValidationError(f"{metadata['id']}: expected a core taint case")
        if metadata["model_profile"] != "benchmark-controlled":
            raise ValidationError(f"{metadata['id']}: expected benchmark-controlled profile")
        if metadata.get("negative_mechanism") != ("infeasible-path" if polarity == "negative" else None):
            raise ValidationError(f"{metadata['id']}: incorrect negative mechanism")
        if len(metadata["fixture_files"]) != 1:
            raise ValidationError(f"{metadata['id']}: expected exactly one fixture source file")
        fixture_path = case_path.parent / metadata["fixture_files"][0]
        if not fixture_path.is_file() or fixture_path.suffix != EXTENSIONS[lang]:
            raise ValidationError(f"{metadata['id']}: missing or unexpected fixture file {fixture_path.name}")
        source_anchors = metadata["source_anchors"]
        sink_anchors = metadata["sink_anchors"]
        if len(source_anchors) != 1 or {key: source_anchors[0].get(key) for key in ("marker", "file")} != {
            "marker": SOURCE,
            "file": fixture_path.name,
        }:
            raise ValidationError(f"{metadata['id']}: source anchor mismatch")
        if len(sink_anchors) != 1 or {key: sink_anchors[0].get(key) for key in ("marker", "file")} != {
            "marker": SINK,
            "file": fixture_path.name,
        }:
            raise ValidationError(f"{metadata['id']}: sink anchor mismatch")

        expected_flow = {"source": SOURCE, "sink": SINK}
        if polarity == "positive":
            if metadata["expected_flows"] != [expected_flow] or metadata["expected_nonflows"]:
                raise ValidationError(f"{metadata['id']}: positive must declare exactly its source-to-sink flow")
            if metadata["witness_checkpoints"] != [SOURCE, WITNESS, SINK]:
                raise ValidationError(f"{metadata['id']}: positive witness path mismatch")
        else:
            if metadata["expected_nonflows"] != [expected_flow] or metadata["expected_flows"]:
                raise ValidationError(f"{metadata['id']}: negative must declare exactly its source-to-sink nonflow")
            if metadata["witness_checkpoints"]:
                raise ValidationError(f"{metadata['id']}: negative must not declare positive-path witnesses")

        source_text = fixture_path.read_text(encoding="utf-8")
        if lang == "swift":
            for marker, anchors, call in (
                (SOURCE, source_anchors, "dfb_source()"),
                (SINK, sink_anchors, "dfb_sink(value)"),
            ):
                marker_line = next(
                    (line_number for line_number, line in enumerate(source_text.splitlines(), 1) if marker in line),
                    None,
                )
                if anchors[0].get("line_hint") != marker_line:
                    raise ValidationError(f"{metadata['id']}: Swift {marker} requires an exact call-line hint")
                if marker_line is None or call not in source_text.splitlines()[marker_line - 1]:
                    raise ValidationError(f"{metadata['id']}: Swift {marker} must annotate {call}")
            if not re.search(r"\bfunc\s+dfb_source\s*\(\s*\)\s*->\s*Int\b", source_text):
                raise ValidationError(f"{metadata['id']}: Swift source must preserve dfb_source() -> Int")
            if not re.search(r"\bfunc\s+dfb_sink\s*\(\s*_\s*value\s*:\s*Int\s*\)", source_text):
                raise ValidationError(f"{metadata['id']}: Swift sink must preserve dfb_sink(_ value: Int)")
        marker_counts = Counter(MARKER_RE.findall(source_text))
        expected_markers = {SOURCE, SINK} | ({WITNESS} if polarity == "positive" else set())
        if set(marker_counts) != expected_markers or any(count != 1 for count in marker_counts.values()):
            raise ValidationError(
                f"{metadata['id']}: marker set/count mismatch; "
                f"expected={sorted(expected_markers)}, actual={dict(marker_counts)}"
            )

        grouped[(metadata["template_id"], lang, metadata["model_profile"])].append((case_path, metadata))
        all_cases.append((case_path, metadata))

    if not all_cases:
        raise ValidationError("no issue #302 cases found for the selected language(s)")

    for form, template in TEMPLATES.items():
        for lang in sorted(languages & APPLICABLE[form]):
            key = (template, lang, "benchmark-controlled")
            pair = grouped.get(key, [])
            polarities = sorted(case["polarity"] for _, case in pair)
            if polarities != ["negative", "positive"]:
                raise ValidationError(f"{template} / {lang}: expected one positive and one negative, found {polarities}")
        for lang in sorted(languages - APPLICABLE[form]):
            if grouped.get((template, lang, "benchmark-controlled")):
                raise ValidationError(f"{template} / {lang}: case exists for a documented inapplicable cell")

    print(f"metadata: PASS ({len(all_cases)} cases; schema, IDs, pair balance, anchors, markers)")
    return all_cases


def run_checked(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode:
        raise ValidationError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def class_name(form: str, polarity: str) -> str:
    return "FoldedLocalConstant" + "".join(part.title() for part in form.split("-")) + polarity.title()


def source_variant(lang: str, source_text: str) -> tuple[str, str]:
    """Change only the source payload to an independent second value."""
    mutations = {
        "c": ("return 1;", "return 2;", "2"),
        "cpp": ("return 1;", "return 2;", "2"),
        "csharp": ("return 1;", "return 2;", "2"),
        "go": ("return 1\n", "return 2\n", "2"),
        "java": ("return 1;", "return 2;", "2"),
        "javascript": ('return "tainted";', 'return "alternate-tainted";', "alternate-tainted"),
        "typescript": ('return "tainted";', 'return "alternate-tainted";', "alternate-tainted"),
        "kotlin": ("return 1\n", "return 2\n", "2"),
        "scala": ("    1\n  }\n\n  def dfb_sink", "    2\n  }\n\n  def dfb_sink", "2"),
        "swift": ("    return 7\n", "    return 19\n", "19"),
        "rust": ("    1\n}\n\nfn dfb_sink", "    2\n}\n\nfn dfb_sink", "2"),
        "python": ('return "tainted"\n', 'return "alternate-tainted"\n', "alternate-tainted"),
        "ruby": ('  "tainted"\nend\n\ndef dfb_sink', '  "alternate-tainted"\nend\n\ndef dfb_sink', "alternate-tainted"),
        "php": ('return "tainted";', 'return "alternate-tainted";', "alternate-tainted"),
    }
    old, new, payload = mutations[lang]
    if source_text.count(old) != 1:
        raise ValidationError(f"cannot uniquely vary the {lang} source payload; expected one {old!r}")
    return source_text.replace(old, new, 1), payload


def execute_fixture(lang: str, form: str, polarity: str, source: Path, temp: Path) -> str:
    env = os.environ.copy()
    env.update(
        {
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_NOLOGO": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        }
    )
    executable = temp / "fixture"
    if lang == "c":
        run_checked(["cc", "-std=c11", "-Wall", "-Wextra", "-pedantic", str(source), "-o", str(executable)], cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "cpp":
        run_checked(["c++", "-std=c++17", "-Wall", "-Wextra", "-pedantic", str(source), "-o", str(executable)], cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "csharp":
        project = temp / "PrecisionValidation.csproj"
        project.write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk\">\n"
            "  <PropertyGroup>\n"
            "    <OutputType>Exe</OutputType>\n"
            "    <TargetFramework>net8.0</TargetFramework>\n"
            "    <ImplicitUsings>disable</ImplicitUsings>\n"
            "    <Nullable>disable</Nullable>\n"
            "  </PropertyGroup>\n"
            "</Project>\n",
            encoding="utf-8",
        )
        run_checked(["dotnet", "build", str(project), "--nologo", "--verbosity", "quiet", "--ignore-failed-sources"], cwd=temp, env=env)
        command = ["dotnet", "run", "--no-build", "--no-restore", "--project", str(project), "--no-launch-profile"]
    elif lang == "go":
        env["GO111MODULE"] = "off"
        command = ["go", "run", str(source)]
    elif lang == "java":
        run_checked(["javac", "-d", str(temp), str(source)], cwd=temp, env=env)
        command = ["java", "-cp", str(temp), class_name(form, polarity)]
    elif lang == "javascript":
        command = ["node", str(source)]
    elif lang == "typescript":
        out_dir = temp / "ts-out"
        out_dir.mkdir(exist_ok=True)
        run_checked(["tsc", "--strict", "--target", "ES2020", "--module", "commonjs", "--outDir", str(out_dir), str(source)], cwd=temp, env=env)
        command = ["node", str(out_dir / (source.stem + ".js"))]
    elif lang == "kotlin":
        jar = temp / "fixture.jar"
        run_checked(["kotlinc", str(source), "-include-runtime", "-d", str(jar)], cwd=temp, env=env)
        command = ["java", "-jar", str(jar)]
    elif lang == "scala":
        command = ["scala", "run", "--server=false", str(source)]
    elif lang == "swift":
        module_cache = temp / "SwiftModuleCache"
        module_cache.mkdir(exist_ok=True)
        run_checked(
            [
                "swiftc",
                "-module-name",
                "DataFlowBenchTaintSwift",
                "-module-cache-path",
                str(module_cache),
                str(source),
                "-o",
                str(executable),
            ],
            cwd=temp,
            env=env,
        )
        command = [str(executable)]
    elif lang == "rust":
        run_checked(["rustc", "--edition=2021", str(source), "-o", str(executable)], cwd=temp, env=env)
        command = [str(executable)]
    elif lang == "python":
        command = ["python3", str(source)]
    elif lang == "ruby":
        command = ["ruby", str(source)]
    elif lang == "php":
        command = ["php", str(source)]
    else:  # pragma: no cover - the fixture matrix is fixed above
        raise ValidationError(f"no runtime configured for {lang}")

    result = run_checked(command, cwd=temp, env=env)
    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    try:
        source_label = source.relative_to(ROOT)
    except ValueError:
        source_label = source
    if len(output_lines) != 1:
        raise ValidationError(
            f"{source_label}: runtime expected exactly one non-empty output line, "
            f"got {output_lines!r}; stderr={result.stderr!r}"
        )
    return output_lines[0]


def validate_runtime(cases: list[tuple[Path, dict]], languages: set[str]) -> None:
    missing: dict[str, list[str]] = {}
    for lang in sorted(languages):
        absent = [tool for tool in REQUIRED_TOOLS[lang] if shutil.which(tool) is None]
        if absent:
            missing[lang] = absent
    if missing:
        for lang, tools in missing.items():
            print(f"runtime: UNAVAILABLE {lang}: missing {', '.join(tools)}", file=sys.stderr)

    executed = 0
    with tempfile.TemporaryDirectory(prefix="dfb-precision-302-") as temp_root:
        for case_path, metadata in cases:
            lang = metadata["language"]
            if lang in missing:
                continue
            source = case_path.parent / metadata["fixture_files"][0]
            form = "if" if metadata["template_id"] == TEMPLATES["if"] else "conditional-expression"
            case_temp = Path(temp_root) / metadata["id"]
            case_temp.mkdir()
            try:
                source_text = source.read_text(encoding="utf-8")
                source_copy = case_temp / source.name
                source_copy.write_text(source_text, encoding="utf-8")
                actual = execute_fixture(lang, form, metadata["polarity"], source_copy, case_temp)
                variant_text, _ = source_variant(lang, source_text)
                source_copy.write_text(variant_text, encoding="utf-8")
                variant_actual = execute_fixture(lang, form, metadata["polarity"], source_copy, case_temp)
            except (OSError, subprocess.TimeoutExpired, ValidationError) as error:
                raise ValidationError(f"{metadata['id']}: runtime validation failed: {error}") from error
            if metadata["polarity"] == "positive":
                expected = ("7", "19") if lang == "swift" else (
                    ("1", "2") if lang in NUMERIC_LANGUAGES else ("tainted", "alternate-tainted")
                )
                if (actual, variant_actual) != expected:
                    raise ValidationError(
                        f"{metadata['id']}: positive sink must follow both source payloads; "
                        f"expected {expected}, got {(actual, variant_actual)}"
                    )
            else:
                expected_safe = "0" if lang in NUMERIC_LANGUAGES else "safe"
                if (actual, variant_actual) != (expected_safe, expected_safe):
                    raise ValidationError(
                        f"{metadata['id']}: negative sink must remain source-independent; "
                        f"expected {expected_safe!r} for both source payloads, got {(actual, variant_actual)}"
                    )
            executed += 1
            print(f"runtime: PASS {metadata['id']} -> {actual}; altered source -> {variant_actual}")

    print(f"runtime: {executed}/{len(cases)} cases executed")
    if missing:
        raise ValidationError("full-runtime validation incomplete because requested toolchains are unavailable")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="validate JSON Schema, IDs, pair balance, anchors, and markers without running fixtures",
    )
    parser.add_argument(
        "--language",
        action="append",
        choices=LANGUAGES,
        help="limit validation to a language key; repeat for multiple languages (default: all)",
    )
    args = parser.parse_args()
    try:
        languages = selected_languages(args)
        cases = load_and_validate_cases(languages)
        if not args.metadata_only:
            validate_runtime(cases, languages)
    except (ValidationError, OSError, json.JSONDecodeError) as error:
        print(f"issue #302 validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
