from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path.cwd()
REPORT = REPO / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01"
OUT = REPORT / "entry2-parser-preflight-01"
PATCH = REPO / "adapters/codeql/swift-entry-extractor-v1/repair.patch"
BASELINE = REPO / "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/codeql-packs.json.gz"
FILES = REPO / "reports/releases/v0.9.2/qualification/codeql-swift-packs/candidate-packs-files-entry2.json"
TREE = REPO / "reports/releases/v0.9.2/qualification/codeql-swift-packs/candidate-packs-tree-entry2.json"
EXPECTED = {
    "swift/ql/lib/codeql/swift/controlflow/internal/ControlFlowGraphImpl.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/controlflow/internal/ControlFlowGraphImpl.qll",
    "swift/ql/lib/codeql/swift/controlflow/internal/Scope.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/controlflow/internal/Scope.qll",
    "swift/ql/lib/codeql/swift/elements.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/elements.qll",
    "swift/ql/lib/codeql/swift/generated/ParentChild.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/generated/ParentChild.qll",
    "swift/ql/lib/codeql/swift/generated/Raw.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/generated/Raw.qll",
    "swift/ql/lib/codeql/swift/generated/Synth.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/generated/Synth.qll",
    "swift/ql/lib/codeql/swift/generated/SynthConstructors.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/generated/SynthConstructors.qll",
    "swift/ql/lib/swift.dbscheme": "codeql/swift-all/6.8.5-dfb.entry2/swift.dbscheme",
    "swift/ql/lib/codeql/swift/elements/TopLevelEntryPoint.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/elements/TopLevelEntryPoint.qll",
    "swift/ql/lib/codeql/swift/elements/internal/TopLevelEntryPointConstructor.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/elements/internal/TopLevelEntryPointConstructor.qll",
    "swift/ql/lib/codeql/swift/elements/internal/TopLevelEntryPointImpl.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/elements/internal/TopLevelEntryPointImpl.qll",
    "swift/ql/lib/codeql/swift/generated/TopLevelEntryPoint.qll": "codeql/swift-all/6.8.5-dfb.entry2/codeql/swift/generated/TopLevelEntryPoint.qll",
}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

if OUT.exists():
    raise SystemExit(f"preserving existing parser preflight; refusing to reuse {OUT}")
patch_bytes=PATCH.read_bytes()
assert sha(patch_bytes)=="e7da7352a8b3a8e7679760e49e8f8abff05d7fa3e16007c7ed2987f49074f26a"
files_bytes=FILES.read_bytes();tree_bytes=TREE.read_bytes();base_gz=BASELINE.read_bytes()
assert sha(files_bytes)=="fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc"
assert sha(tree_bytes)=="5b1dca82019e9d47a6aa6a38f1045d69422e4d627b04331205d418344388f431"
assert sha(base_gz)=="41c6d2edb417e5a01f824e7bfd03c24ad48968840625e23484b48a8c7f0adf89"
patch_text=patch_bytes.decode("utf-8")
header_re=re.compile(r"(?m)^diff --git a/(?P<a>[^\s]+) b/(?P<b>[^\s]+)$")
matches=list(header_re.finditer(patch_text))
source_paths=[m.group("a") for m in matches]
assert all(m.group("a")==m.group("b") for m in matches)
assert len(source_paths)==19 and len(set(source_paths))==19
assert set(EXPECTED).issubset(set(source_paths))
sections=[]
for index,m in enumerate(matches):
    src=m.group("a")
    if src not in EXPECTED: continue
    end=matches[index+1].start() if index+1<len(matches) else len(patch_text)
    block=patch_text[m.start():end]
    target=EXPECTED[src]
    block=block.replace(f"diff --git a/{src} b/{src}",f"diff --git a/{target} b/{target}",1)
    block=block.replace(f"--- a/{src}",f"--- a/{target}",1)
    block=block.replace(f"+++ b/{src}",f"+++ b/{target}",1)
    sections.append((src,target,block))
assert {src for src,_,_ in sections}==set(EXPECTED) and len(sections)==12
filtered="".join(block for _,_,block in sections)
OUT.mkdir()
(OUT/"filtered-generic-pack-sections.patch").write_text(filtered)

# Parse both the original and remapped patches through Git's standard patch parser.
cmd=["git","apply","--numstat","-"]
started=now()
original_result=subprocess.run(cmd,input=patch_text,text=True,capture_output=True,cwd=REPO)
(OUT/"original-numstat.stdout.txt").write_text(original_result.stdout)
(OUT/"original-numstat.stderr.txt").write_text(original_result.stderr)
(OUT/"original-numstat.command.json").write_text(json.dumps({"argv":cmd,"cwd":str(REPO.resolve()),"started_utc":started,"input_sha256":sha(patch_bytes)},indent=2)+"\n")
original_paths=[]
for line in original_result.stdout.splitlines():
    fields=line.split("\t",2)
    if len(fields)==3: original_paths.append(fields[2])
assert original_result.returncode==0, original_result.stderr
assert set(original_paths)==set(source_paths) and len(original_paths)==19

filtered_bytes=filtered.encode("utf-8")
filtered_result=subprocess.run(cmd,input=filtered,text=True,capture_output=True,cwd=REPO)
(OUT/"filtered-numstat.stdout.txt").write_text(filtered_result.stdout)
(OUT/"filtered-numstat.stderr.txt").write_text(filtered_result.stderr)
(OUT/"filtered-numstat.command.json").write_text(json.dumps({"argv":cmd,"cwd":str(REPO.resolve()),"started_utc":now(),"input_sha256":sha(filtered_bytes)},indent=2)+"\n")
filtered_paths=[]
for line in filtered_result.stdout.splitlines():
    fields=line.split("\t",2)
    if len(fields)==3: filtered_paths.append(fields[2])
assert filtered_result.returncode==0, filtered_result.stderr
assert set(filtered_paths)==set(EXPECTED.values()) and len(filtered_paths)==12

files_doc=json.loads(files_bytes); tree_doc=json.loads(tree_bytes)
files_by_path={x["path"]:x for x in json.loads(gzip.decompress(base_gz))["files"]}
expected_after={k[len("codeql/swift-all/6.8.5-dfb.entry2/"):]:v for k,v in files_doc.items() if k.startswith("codeql/swift-all/6.8.5-dfb.entry2/")}
expected_tree={k[len("codeql/swift-all/6.8.5-dfb.entry2/"):]:v for k,v in tree_doc.items() if k.startswith("codeql/swift-all/6.8.5-dfb.entry2/")}
source_prefix="codeql/swift-all/6.8.5/"
source_pack=REPO/"execution-state/timing-runtime-20261114-01/codeql/packs/codeql/swift-all/6.8.5"
checks=[]
for src,target,_ in sections:
    if src=="swift/ql/lib/swift.dbscheme": source_rel=source_prefix+"swift.dbscheme"; target_rel="swift.dbscheme"
    else:
        source_rel=source_prefix+"codeql/swift/"+src[len("swift/ql/lib/codeql/swift/"):]
        target_rel="codeql/swift/"+src[len("swift/ql/lib/codeql/swift/"):]
    before=files_by_path.get(source_rel)
    after_hash=expected_after.get(target_rel)
    assert after_hash is not None, f"no frozen after hash for {target}"
    if before is None:
        assert not (source_pack/source_rel[len(source_prefix):]).exists()
        before_sha=None; actual_before=None
    else:
        source_file=source_pack/source_rel[len(source_prefix):]
        actual_before=sha(source_file.read_bytes())
        before_sha=before["sha256"]
        assert actual_before==before_sha, f"source runtime hash differs from frozen baseline for {source_rel}"
    checks.append({"source_patch_path":src,"destination_pack_path":target,"baseline_source_path":source_rel,"before_sha256":before_sha,"observed_before_sha256":actual_before,"before_absent":before is None,"after_sha256":after_hash,"after_mode":expected_tree[target_rel]["mode"]})

result={
 "schema":"codeql-entry2-generic-patch-parser-preflight/v1",
 "status":"verified-12-remapped-sections-and-frozen-hash-bindings",
 "started_utc":started,
 "finished_utc":now(),
 "source_commit":"a7057b836bf29767461026718b14d20790b9085f",
 "patch_path":str(PATCH.resolve()),
 "patch_sha256":sha(patch_bytes),
 "original_git_apply_numstat_exit_code":original_result.returncode,
 "original_git_apply_numstat_output_path":str((OUT/"original-numstat.stdout.txt").resolve()),
 "original_paths_count":len(original_paths),
 "filtered_git_apply_numstat_exit_code":filtered_result.returncode,
 "filtered_git_apply_numstat_output_path":str((OUT/"filtered-numstat.stdout.txt").resolve()),
 "filtered_paths_count":len(filtered_paths),
 "filtered_patch_path":str((OUT/"filtered-generic-pack-sections.patch").resolve()),
 "filtered_patch_sha256":sha(filtered_bytes),
 "expected_source_path_set":sorted(EXPECTED),
 "expected_destination_path_set":sorted(EXPECTED.values()),
 "before_after_hash_bindings":checks,
 "baseline_runtime_manifest":{"path":str(BASELINE.resolve()),"compressed_sha256":sha(base_gz),"uncompressed_sha256":sha(gzip.decompress(base_gz))},
 "candidate_files_manifest":{"path":str(FILES.resolve()),"sha256":sha(files_bytes)},
 "candidate_tree_manifest":{"path":str(TREE.resolve()),"sha256":sha(tree_bytes)},
 "no_copy_patch_or_runtime_invocation":True,
}
(OUT/"receipt.json").write_text(json.dumps(result,indent=2)+"\n")
(OUT/"terminal.json").write_text(json.dumps({"status":result["status"],"finished_utc":result["finished_utc"],"receipt_sha256":sha((OUT/"receipt.json").read_bytes())},indent=2)+"\n")
print(json.dumps({"status":result["status"],"original_paths":len(original_paths),"filtered_paths":len(filtered_paths),"filtered_patch_sha256":result["filtered_patch_sha256"],"receipt":str((OUT/"receipt.json").resolve()),"receipt_sha256":sha((OUT/"receipt.json").read_bytes())},indent=2))
