#!/usr/bin/env python3
"""Derive prospective warm inputs from immutable, authored v0.9.2 fixtures."""
import collections
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[5]
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
PLAN = ROOT / "reports/timing/v0.9.2/20261113-01/plan.json"
OUT = Path(__file__).with_name("derivation-v1.json")


def main():
    plan = json.loads(PLAN.read_text())
    assert plan["release_commit"] == RELEASE
    joern = next(g for g in plan["groups"] if g["id"] == "joern-java-kernel")
    semgrep = next(g for g in plan["groups"] if g["id"] == "semgrep-java-kernel")
    archive = subprocess.check_output(["git", "archive", RELEASE,
        "cases/taint/java", "adapters/semgrep/rules/java.yaml"])
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        members = {m.name: stream.extractfile(m).read() for m in stream if m.isfile()}
    template = members["adapters/semgrep/rules/java.yaml"].decode()
    ids = set(semgrep["case_ids"])
    grouped = collections.defaultdict(list)
    resolved = []
    for path, raw in sorted(members.items()):
        if not path.endswith("/case.json"):
            continue
        case = json.loads(raw)
        if case["id"] not in ids or "intraprocedural" not in case.get("feature_tags", []):
            continue
        # These authored local templates are outside the challenge partition.
        assert not case["template_id"].startswith("dfb-template-chal-")
        pair, anchors = [], []
        for field in ("source_anchors", "sink_anchors"):
            names = set()
            for anchor in case[field]:
                source_path = path.rsplit("/", 1)[0] + "/" + anchor["file"]
                body = members[source_path]
                lines = [line for line in body.decode().splitlines() if anchor["marker"] in line]
                assert len(lines) == 1
                # This is an audit of the 14 explicit authored declarations,
                # not a replacement endpoint resolver in an analyzer.
                declaration = lines[0].split("//")[0].split("(")[0]
                name = declaration.split()[-1]
                assert re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name)
                assert "static" in declaration.split()
                names.add(name)
                anchors.append({"source_path": source_path,
                    "source_sha256": hashlib.sha256(body).hexdigest(),
                    "marker": anchor["marker"], "declaration": lines[0], "name": name})
            assert len(names) == 1
            pair.append(next(iter(names)))
        rule = template.replace("__DFB_SOURCE__", pair[0]).replace("__DFB_SINK__", pair[1])
        digest = hashlib.sha256(rule.encode()).hexdigest()
        grouped[digest].append(case["id"])
        resolved.append({"case_id": case["id"], "metadata_path": path,
            "metadata_sha256": hashlib.sha256(raw).hexdigest(),
            "resolved_rule_sha256": digest, "anchors": anchors})
    ordered = sorted(grouped.items(), key=lambda item: (len(item[1]), item[0]))
    assert len(ordered[-1][1]) > len(ordered[-2][1])
    majority, cases = ordered[-1]
    assert len(cases) == 12 and sum(map(len, grouped.values())) == 14
    result = {"schema": "v092-prospective-warm-populations/v1",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "release_commit": RELEASE, "source_plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "method": "Frozen metadata capability partition and explicit authored marker declarations; identical resolved rule bytes. No timing or new analyzer outcomes used.",
        "source_implementation": "src/latency.rs::warm_population; src/adapters/semgrep.rs::semgrep_capability_exclusion",
        "analyzer_invocations": 0, "joern": {"case_ids": sorted(joern["case_ids"]),
            "batch_sizes": [1, 2, 4, 8, 16], "population_available": len(joern["case_ids"])},
        "semgrep": {"case_ids": sorted(cases), "batch_sizes": [1, 2, 4, 8, 12],
            "population_available": len(cases), "invocable_cases": 14,
            "resolved_rule_sha256": majority, "resolved_declarations": resolved}}
    with OUT.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(OUT), "joern_cases": len(joern["case_ids"]), "semgrep_cases": len(cases)}))


if __name__ == "__main__":
    main()
