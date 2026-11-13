#!/usr/bin/env python3
"""Build append-only prospective bindings from retained verification receipts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
FAMILIES = ("bifrost", "codeql", "joern", "semgrep", "opentaint", "infer", "flowdroid", "pysa")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def create(output):
    source_path = ROOT / "reports/timing/v0.9.2/20261113-01/plan.json"
    source = load(source_path)
    assert source["release_commit"] == RELEASE
    cold = [g for g in source["groups"] if g["kind"] == "cold"]
    assert len(cold) == 84
    roots, runtimes, receipt_bindings = {}, {}, []

    def retain_receipt(path):
        receipt_bindings.append({"path": relative(path), "sha256": sha(path)})

    relocation = PREP / "jvm-runtimes/relocated-manifests-receipt-v2.json"
    retain_receipt(relocation)
    maps = {}
    for item in load(relocation)["manifests"]:
        if item["manifest_id"] in {"go-pinned-entry", "kotlin-pinned-entries"}:
            continue
        identifier = item["manifest_id"]
        binding = {"id": identifier, "path": item["manifest_path"],
            "sha256": item["manifest_sha256"]}
        if item.get("compressed"):
            binding["uncompressed_sha256"] = item["uncompressed_sha256"]
        runtimes[identifier] = binding
        roots[identifier] = item["new_root"]
        if item.get("source_root") != item["new_root"]:
            if Path(item["source_root"]).is_absolute():
                maps[item["source_root"]] = item["new_root"]
            else:
                # Scala is staged by pinned setup_files, not a CLI prefix.
                assert identifier == "scala-library-2.13.16"
    for name in ("prospective-compiler-distribution-inventories-v1.json",
                 "prospective-host-toolchain-inventories-v1.json"):
        path = PREP / "jvm-runtimes" / name
        if not path.exists():
            continue
        retain_receipt(path)
        for item in load(path)["inventories"]:
            binding = {k: item[k] for k in ("id", "path", "sha256")}
            if item.get("compressed"):
                binding["uncompressed_sha256"] = item["uncompressed_sha256"]
            runtimes[item["id"]] = binding
            roots[item["id"]] = item["root"]
    core = PREP / "core-runtime/retention-receipt-v1.json"
    retain_receipt(core)
    for item in load(core)["runtimes"]:
        runtimes[item["id"]] = {k: item[k] for k in ("id", "path", "sha256")}
        roots[item["id"]] = item["root"]
    python_receipt = PREP / "python-runtimes/runtime-restoration-receipt.json"
    python_data = load(python_receipt)
    assert python_data["status"] == "normalized_payloads_match"
    retain_receipt(python_receipt)
    for family in ("pysa", "semgrep"):
        assert python_data["normalized_payload_comparison"][family]["normalized_payload_match"]
        roots[family] = python_data["new_roots"][family]
        maps[python_data["old_roots"][family]] = roots[family]
    compressed = PREP / "python-runtimes/compressed-python-runtime-receipt-index.json"
    retain_receipt(compressed)
    for item in load(compressed)["files"]:
        for family in ("pysa", "semgrep"):
            if Path(item["source"]).name == family + "-relocated-runtime-manifest.json":
                runtimes[family] = {"id": family, "path": item["compressed_copy"],
                    "sha256": item["compressed_sha256"],
                    "uncompressed_sha256": item["source_sha256"]}
    retain_receipt(PREP / "jvm-runtimes/core-runtime-tree-check-results-v1.json")
    retain_receipt(PREP / "qualification/helper-transition-v1.json")
    warm_path = PREP / "warm-population/derivation-v1.json"
    warm = load(warm_path)
    retain_receipt(warm_path)
    tools_paths = {
        "runner": Path(roots["runner"]) / "dataflowbench",
        "bifrost": Path(roots["bifrost"]) / "bifrost",
        "codeql": Path(roots["codeql"]) / "codeql",
        "joern": Path(roots["joern"]) / "joern",
        "semgrep": Path(roots["semgrep"]) / "bin/semgrep",
        "pysa": Path(roots["pysa"]) / "bin/pyre",
        "infer": Path(roots["infer"]) / "lib/infer/infer/bin/infer",
        "opentaint": Path(roots["opentaint"]) / "opentaint-project-analyzer.jar",
        "flowdroid": Path(roots["flowdroid"]) / "soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar",
    }
    tools = {name: {"path": str(path), "sha256": sha(path)} for name, path in tools_paths.items()}
    maps[source["tools"]["runner"]["path"]] = tools["runner"]["path"]
    maps["/usr/bin/java"] = roots["java"] + "/bin/java"
    maps["/usr/bin/javac"] = roots["java"] + "/bin/javac"
    for group in cold:
        if group["family"] == "bifrost":
            index = group["argv"].index("--bifrost") + 1
            if group["argv"][index] != tools["bifrost"]["path"]:
                maps[group["argv"][index]] = tools["bifrost"]["path"]
    common_path = roots["java"] + "/bin:/opt/homebrew/bin:/usr/local/bin:/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    overrides = {}
    dependencies = {}
    compiler_id, rust_id = "clt27.2-compiler-prospective", "rust1.97.1-distribution-prospective"
    for group in cold:
        gid, family = group["id"], group["family"]
        ids = ["runner", family]
        environment = {"JAVA_HOME": roots["java"], "PATH": common_path}
        blocker = None
        setup = []
        if family in {"joern", "flowdroid", "opentaint"} or "java" in gid or "kotlin" in gid or "scala" in gid:
            ids.append("java")
        if family == "codeql":
            ids.append("codeql-packs")
            if gid in {"codeql-c-kernel", "codeql-cpp-kernel"}:
                if compiler_id not in runtimes:
                    blocker = "Prospective exact host compiler closure is not yet bound."
                else:
                    ids += [compiler_id, "swift-sdk-26.5"]
                    environment.update({"CC": roots[compiler_id] + "/bin/clang",
                        "CXX": roots[compiler_id] + "/bin/clang++",
                        "PATH": roots[compiler_id] + "/bin:" + common_path,
                        "SDKROOT": roots["swift-sdk-26.5"]})
            if gid == "codeql-go-kernel":
                ids.append("go-full-distribution-prospective")
                environment["GOTOOLCHAIN"] = "local"
            if gid == "codeql-rust-kernel":
                if rust_id not in runtimes:
                    blocker = "Exact prospective Rust/Cargo runtime closure is not yet bound."
                else:
                    ids.append(rust_id)
                    environment.update({"PATH": roots[rust_id] + "/bin:" + common_path,
                        "RUSTUP_TOOLCHAIN": "1.97.1", "CARGO_NET_OFFLINE": "true"})
        if gid == "joern-rust-kernel":
            ids.append(rust_id)
            environment.update({"PATH": roots[rust_id] + "/bin:" + common_path,
                "RUSTUP_TOOLCHAIN": "1.97.1", "CARGO_NET_OFFLINE": "true"})
        if "kotlin" in gid and family in {"codeql", "flowdroid", "opentaint"}:
            ids.append("kotlin-full-distribution-prospective")
        if family == "infer" and gid in {"infer-c-kernel", "infer-cpp-kernel"}:
            ids.append("swift-sdk-26.5")
            environment["SDKROOT"] = roots["swift-sdk-26.5"]
        if family == "semgrep":
            environment["PATH"] = roots[family] + "/bin:" + common_path
        if gid == "bifrost-scala-kernel":
            ids += ["java", "scala-library-2.13.16"]
            for origin in sorted(Path(roots["scala-library-2.13.16"]).rglob("*")):
                if origin.is_file():
                    setup.append({"source": str(origin),
                        "path": "home/.m2/repository/" + origin.relative_to(roots["scala-library-2.13.16"]).as_posix(),
                        "sha256": sha(origin), "mode": 420})
            assert len(setup) == 3
        if "swift-common108" in gid:
            blocker = "Pinned Swift6.3.3 package recovered but payload is not expanded/full-manifest-verified; Swift driver plan/runtime relocation remains unqualified."
            if family == "codeql":
                blocker += " Three custom CodeQL extractor files and the entry2 custom query pack are not recovered."
        ids = list(dict.fromkeys(ids))
        dependencies[gid] = ids
        overrides[gid] = {"status": "blocked" if blocker else "ready", "runtime_ids": ids,
            "environment": environment}
        if blocker:
            overrides[gid]["blocker"] = blocker
        if setup:
            overrides[gid]["setup_files"] = setup
    auxiliary = []
    representatives = {"bifrost": ("python", "bifrost-python-kernel"),
        "codeql": ("ruby", "codeql-ruby-kernel"), "joern": ("php", "joern-php-kernel"),
        "semgrep": ("kotlin", "semgrep-kotlin-kernel"), "opentaint": ("kotlin", "opentaint-kotlin-kernel"),
        "infer": ("c", "infer-c-kernel"), "flowdroid": ("java", "flowdroid-java-kernel"),
        "pysa": ("python", "pysa-python-kernel")}
    for family in FAMILIES:
        language, representative = representatives[family]
        variants = [(language, representative)] + ([("java", "joern-java-kernel")] if family == "joern" else [])
        for language, representative in variants:
            original = next(g for g in cold if g["id"] == representative)
            gid = "overhead-" + family + "-" + language
            auxiliary.append({"id": gid, "family": family, "tool": family, "kind": "overhead", "language": language,
                "deadline_seconds": 600, "argv": [tools["runner"]["path"], "--population", "v0.9.0",
                    "estimate-invocation-overhead", "--tool", family, "--language", language, *original["argv"][4:]],
                "environment": {**original["environment"], **overrides[representative]["environment"]}, "output_roots": ["reports/raw/invocation-overhead/" + family + "-" + language]})
            overrides[gid] = {k: v for k, v in overrides[representative].items() if k != "setup_files"}
    for family in ("joern", "semgrep"):
        gid = "warm-" + family + "-java"
        representative = family + "-java-kernel"
        sizes = warm[family]["batch_sizes"]
        auxiliary.append({"id": gid, "family": family, "tool": family, "kind": "warm", "language": "java",
            "deadline_seconds": 600, "argv": [tools["runner"]["path"], "--population", "v0.9.0",
                "measure-warm-latency", "--tool", family, "--language", "java", "--batch-sizes",
                ",".join(map(str, sizes)), "--" + family, tools[family]["path"]],
            "warm_case_ids": warm[family]["case_ids"], "warm_batch_sizes": sizes,
            "environment": {**next(g for g in cold if g["id"] == representative)["environment"],
                **overrides[representative]["environment"]},
            "output_roots": ["reports/raw/warm-latency/" + family + "-java-kernel"]})
        overrides[gid] = dict(overrides[representative])
    balanced = ["bifrost-java-kernel", "codeql-java-kernel", "joern-java-kernel", "semgrep-java-kernel",
        "opentaint-java-kernel", "infer-java-kernel", "flowdroid-java-kernel", "pysa-python-kernel"]
    assert all(overrides[gid]["status"] == "ready" for gid in balanced)
    preregistration = ROOT / "docs/latency-v092-20261114.md"
    result = {"schema": "v092-qualified-runtime-bindings/v1", "release_commit": RELEASE,
        "campaign_id": "20261114-01", "launch_after_utc": "2026-11-14T00:00:00+00:00",
        "source_plan": {"path": relative(source_path), "sha256": sha(source_path)},
        "preregistration": {"path": relative(preregistration), "sha256": sha(preregistration)},
        "preparation_receipts": receipt_bindings, "source_projection": source["source_projection"],
        "tools": tools, "runtimes": list(runtimes.values()), "path_rebindings": maps,
        "group_overrides": overrides, "auxiliary_groups": auxiliary,
        "group_order": balanced + [g["id"] for g in cold if g["id"] not in balanced] + [g["id"] for g in auxiliary],
        "max_campaign_wall_seconds": 172800,
        "qualification_note": "Fresh quiet before each group; active contention only telemetry. Frozen analyzer payloads/pins and fixture population retained. Host compiler distribution snapshots and relocated Python launchers/metadata are prospective environment identities, not assertions of historical byte equality. PID/start polling containment remains unproven. Every completed command remains candidate evidence pending independent qualification/publication review."}
    for item in result["runtimes"]:
        assert sha(ROOT / item["path"]) == item["sha256"]
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"bindings": str(output), "sha256": sha(output),
        "ready_cold": sum(overrides[g["id"]]["status"] == "ready" for g in cold),
        "blocked_cold": [g["id"] for g in cold if overrides[g["id"]]["status"] == "blocked"],
        "auxiliary": len(auxiliary), "runtimes": len(runtimes)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    create(parser.parse_args().output)
