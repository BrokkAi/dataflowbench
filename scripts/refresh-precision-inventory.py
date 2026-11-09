#!/usr/bin/env python3
"""Check or refresh only the explicitly preregistered precision additions."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = (
    "c", "cpp", "csharp", "go", "java", "javascript", "typescript", "kotlin",
    "scala", "swift", "rust", "python", "ruby", "php",
)
TEMPLATES = (
    ("dfb-template-folded-local-constant-if", "folded-local-constant-if", LANGUAGES),
    ("dfb-template-folded-local-constant-conditional-expression",
     "folded-local-constant-conditional-expression", tuple(x for x in LANGUAGES if x != "go")),
    ("dfb-template-issue-303-same-map-constant-keys", "same-map-constant-keys",
     tuple(x for x in LANGUAGES if x != "c")),
    ("dfb-template-issue-303-same-map-computed-key", "same-map-computed-key",
     tuple(x for x in LANGUAGES if x != "c")),
    ("dfb-template-issue-303-same-map-escaping-callee", "same-map-escaping-callee",
     tuple(x for x in LANGUAGES if x != "c")),
    ("dfb-template-list-removal-index-shift", "list-removal-index-shift", LANGUAGES),
    ("dfb-template-constant-string-selector", "constant-string-selector", LANGUAGES),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root=ROOT):
    templates, cases = [], []
    for template, slug, languages in TEMPLATES:
        templates.append({"template_id": template, "languages": list(languages)})
        for language in languages:
            for polarity in ("positive", "negative"):
                path = root / f"populations/precision-gaps-v1/cases/taint/{language}/{slug}-{polarity}/case.json"
                case = json.loads(path.read_text())
                expected = {
                    "template_id": template, "language": language, "polarity": polarity,
                    "id": f"dfb-taint-{language}-{slug}-{polarity}", "score_tier": "core",
                    "track": "taint", "model_profile": "benchmark-controlled",
                }
                for key, value in expected.items():
                    if case.get(key) != value:
                        raise ValueError(f"{path}: expected {key}={value!r}")
                fixtures = []
                for name in case["fixture_files"]:
                    relative = Path(name)
                    if relative.is_absolute() or ".." in relative.parts:
                        raise ValueError(f"{path}: unsafe fixture path {name}")
                    fixture = path.parent / relative
                    fixtures.append({"path": fixture.relative_to(root).as_posix(), "sha256": sha(fixture)})
                cases.append({**{key: case[key] for key in ("id", "template_id", "language", "polarity")},
                              "path": path.relative_to(root).as_posix(), "sha256": sha(path),
                              "fixture_digests": fixtures})
    return {"schema_version": 1, "status": "prospective", "templates": templates,
            "cases": sorted(cases, key=lambda entry: entry["path"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh the prospective inventory only")
    args = parser.parse_args()
    path = ROOT / "populations/precision-gaps-v1.json"
    registered = inventory()
    expected = json.dumps(registered, indent=2) + "\n"
    if args.write:
        path.write_text(expected)
    elif path.read_text() != expected:
        raise ValueError("precision inventory differs from its explicit registration; review changes before --write")
    count = len(registered["cases"])
    print(f"precision additions: {len(registered['templates'])} templates, {count // 2} balanced pairs, {count} assertions")


if __name__ == "__main__":
    main()
