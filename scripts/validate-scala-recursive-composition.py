#!/usr/bin/env python3
"""Compile and execute the Scala recursive-composition fixture pairs.

The fixtures keep ``dfb_sink`` as a no-op and use source literal ``7``. This
bounded analyzer-independent check copies each fixture to a temporary probe,
instruments the sink, and varies the source between ``7`` and ``11``. The
positive output must move by ``+4``; negative output must remain constant.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


EXPECTED = {
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
SOURCE_LITERAL = re.compile(r"(?m)^(?P<indent>[ \t]*)7[ \t]*$")
OBJECT_DECLARATION = re.compile(r"\bobject\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
TIMEOUT_SECONDS = 30


def run_command(command: list[str], fixture: Path, context: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{context} timed out for {fixture}") from error


def marker_line(body: str, marker: str) -> int:
    lines = [line_number for line_number, line in enumerate(body.splitlines(), 1) if marker in line]
    if len(lines) != 1:
        raise AssertionError(f"marker {marker!r} must occur exactly once (found {len(lines)})")
    return lines[0]


def source_variant(original: str, source_value: int, fixture: Path) -> str:
    matches = list(SOURCE_LITERAL.finditer(original))
    if len(matches) != 1:
        raise AssertionError(f"{fixture}: expected exactly one source literal 7 (found {len(matches)})")
    match = matches[0]
    return original[: match.start()] + f"{match.group('indent')}{source_value}" + original[match.end() :]


def compile_fixture(fixture: Path, scalac: str) -> None:
    with tempfile.TemporaryDirectory(prefix="dfb-scala-168-compile-") as temporary:
        classes = Path(temporary) / "classes"
        classes.mkdir()
        result = run_command([scalac, "-d", str(classes), str(fixture)], fixture, "scalac compile")
        if result.returncode != 0:
            raise RuntimeError(f"scalac compile failed for {fixture}:\n{result.stdout}{result.stderr}")


def probe_fixture(fixture: Path, source: str, object_name: str, scala: str, scalac: str) -> int:
    instrumented = source.replace(
        "def dfb_sink(value: Int): Unit = {}",
        "def dfb_sink(value: Int): Unit = { println(value) }",
        1,
    )
    if instrumented == source:
        raise AssertionError(f"{fixture}: cannot instrument sink")

    with tempfile.TemporaryDirectory(prefix="dfb-scala-168-probe-") as temporary:
        temporary_root = Path(temporary)
        probe_fixture = temporary_root / fixture.name
        probe_fixture.write_text(instrumented)
        probe = temporary_root / "Probe.scala"
        probe.write_text(
            "package dataflowbench\n\n"
            "object Probe {\n"
            "  def main(args: Array[String]): Unit = {\n"
            f"    {object_name}.run()\n"
            "  }\n"
            "}\n"
        )
        classes = temporary_root / "classes"
        classes.mkdir()
        compile_result = run_command(
            [scalac, "-d", str(classes), str(probe_fixture), str(probe)],
            fixture,
            "scalac probe compile",
        )
        if compile_result.returncode != 0:
            raise RuntimeError(
                f"scalac probe compile failed for {fixture}:\n"
                f"{compile_result.stdout}{compile_result.stderr}"
            )
        execution = run_command(
            [scala, "run", "--classpath", str(classes), "--main-class", "dataflowbench.Probe", "--server=false"],
            fixture,
            "Scala probe execution",
        )
        if execution.returncode != 0:
            raise RuntimeError(
                f"Scala probe execution failed for {fixture}:\n"
                f"{execution.stdout}{execution.stderr}"
            )
        output = execution.stdout.strip().splitlines()
        if len(output) != 1:
            raise AssertionError(f"{fixture}: expected one integer sink output, got {output!r}")
        try:
            return int(output[0])
        except ValueError as error:
            raise AssertionError(f"{fixture}: expected integer sink output, got {output[0]!r}") from error


def check_fixture(root: Path, stem: str, polarity: str, scalac: str, scala: str) -> str:
    case_dir = root / "cases" / "taint" / "scala" / f"{stem}-{polarity}"
    metadata_path = case_dir / "case.json"
    metadata = json.loads(metadata_path.read_text())
    fixture = case_dir / metadata["fixture_files"][0]
    original = fixture.read_text()

    expected = EXPECTED[stem]
    if metadata["schema_version"] != 2:
        raise AssertionError(f"{metadata_path}: expected schema version 2")
    if metadata["language"] != "scala" or metadata["track"] != "taint" or metadata["score_tier"] != "core":
        raise AssertionError(f"{metadata_path}: incorrect language, track, or score tier")
    expected_template = f"dfb-template-chal-{stem}"
    if metadata["template_id"] != expected_template:
        raise AssertionError(f"{metadata_path}: expected template {expected_template!r}")
    if metadata["polarity"] != polarity:
        raise AssertionError(f"{metadata_path}: expected polarity {polarity!r}")
    if metadata["semantic_dimensions"] != expected["dimensions"]:
        raise AssertionError(f"{metadata_path}: semantic dimensions drifted")
    if metadata["feature_tags"] != expected["tags"]:
        raise AssertionError(f"{metadata_path}: feature tags drifted")
    if metadata["fixture_provenance"]["revision"] != "m4-recursive-composition-scala":
        raise AssertionError(f"{metadata_path}: unexpected provenance revision")
    if polarity == "negative" and metadata.get("negative_mechanism") != "overwrite-kill":
        raise AssertionError(f"{metadata_path}: negative mechanism must be overwrite-kill")
    if polarity == "positive" and "negative_mechanism" in metadata:
        raise AssertionError(f"{metadata_path}: positive case must not declare negative_mechanism")

    for anchor in metadata["source_anchors"] + metadata["sink_anchors"]:
        marker_line(original, anchor["marker"])
    for checkpoint in metadata["witness_checkpoints"]:
        marker_line(original, checkpoint)
    if polarity == "negative" and "DFB-KILL:" not in original:
        raise AssertionError(f"{fixture}: negative fixture is missing DFB-KILL")
    if polarity == "positive" and "DFB-KILL:" in original:
        raise AssertionError(f"{fixture}: positive fixture contains DFB-KILL")

    object_match = OBJECT_DECLARATION.search(original)
    if object_match is None:
        raise AssertionError(f"{fixture}: cannot find Scala object declaration")
    object_name = object_match.group(1)
    compile_fixture(fixture, scalac)

    observed = {}
    for source_value in SOURCE_VALUES:
        observed[source_value] = probe_fixture(
            fixture,
            source_variant(original, source_value, fixture),
            object_name,
            scala,
            scalac,
        )

    expected_base = EXPECTED[stem][polarity]
    if observed[SOURCE_VALUES[0]] != expected_base:
        raise AssertionError(
            f"{fixture}: source {SOURCE_VALUES[0]} expected {expected_base}, got {observed[SOURCE_VALUES[0]]}"
        )
    observed_delta = observed[SOURCE_VALUES[1]] - observed[SOURCE_VALUES[0]]
    expected_delta = SOURCE_VALUES[1] - SOURCE_VALUES[0] if polarity == "positive" else 0
    if observed_delta != expected_delta:
        raise AssertionError(
            f"{fixture}: source delta {SOURCE_VALUES[1] - SOURCE_VALUES[0]} produced sink delta "
            f"{observed_delta}; expected {expected_delta} for {polarity}"
        )
    return (
        f"{stem}-{polarity}: scalac + execution => "
        f"{SOURCE_VALUES[0]}:{observed[SOURCE_VALUES[0]]}, "
        f"{SOURCE_VALUES[1]}:{observed[SOURCE_VALUES[1]]} (delta {observed_delta})"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--scalac", default="scalac")
    parser.add_argument("--scala", default="scala")
    args = parser.parse_args()

    for stem in EXPECTED:
        for polarity in ("positive", "negative"):
            print(check_fixture(args.root, stem, polarity, args.scalac, args.scala))


if __name__ == "__main__":
    main()
