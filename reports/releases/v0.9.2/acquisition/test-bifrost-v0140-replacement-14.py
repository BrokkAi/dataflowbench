#!/usr/bin/env python3
"""Static and stage-boundary regressions for replacement-14."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import unittest


BASE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


p = load("replacement14_protocol_test", BASE / "bifrost-v0140-replacement-14.py")
bridge = load("replacement14_bridge_test", BASE / "bifrost-v0140-frozen-bridge-09.py")
expiry = load("replacement14_noexpiry_test", BASE / "bifrost-v0140-no-expiry-14.py")


class Replacement14Tests(unittest.TestCase):
    def test_protocol_is_append_only_and_stage_exports_are_present(self):
        self.assertEqual(p.MANIFEST_SCHEMA, "v092-bifrost-v0140-replacement-14/v1")
        self.assertEqual(p.STAGE_SCHEMA, "v092-bifrost-v0140-replay-stage/v4")
        self.assertEqual(p.PARENT_STAGE_COUNT, 21)
        self.assertEqual(p.CHILD_STAGE_COUNT, 20)
        for name in ("build_parent_stage", "build_successor_stage", "build_child_stage", "write_completion"):
            self.assertTrue(callable(getattr(p, name)))

    def test_no_expiry_keeps_registered_finite_limits(self):
        core = {"cutoff_utc": None, "total_wall_budget_seconds": None,
                "original_origin_utc": expiry.ORIGIN,
                "execution_window_authority": expiry.AUTHORITY,
                "resource_policy": dict(expiry.RESOURCE_POLICY)}
        result = expiry.validate(Path(__file__).resolve().parents[4], core)
        self.assertEqual(result["status"], "validated")
        self.assertEqual(expiry.lease_remaining(popen_monotonic=100, now_monotonic=101,
                                                 registered_deadline_seconds=13840), 14439)
        with self.assertRaises(expiry.NoExpiry14Error):
            expiry.lease_remaining(popen_monotonic=100, now_monotonic=20000,
                                   registered_deadline_seconds=13840)

    def test_stage_helper_rejects_serialized_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bridge.FrozenBridge09Error):
                bridge.load_runtime_stage(Path(tmp), graph=object(),
                                          runtime_loader={"serialized": True}, mode="before",
                                          core_identity={})


class RuntimeCoreSchema14Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.core={"manifest_path":p.MANIFEST_PATH}
        refs={}
        def put(path,raw):
            file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
            return {"path":path,"sha256":p.sha256(raw)}
        self.put=put
        roles={"bridge09":"frozen_bridge_source","replacement14":"implementation",
               "protocol14":"implementation","admission14":"bifrost_admission_source",
               "supervisor14":"bifrost_supervisor_source"}
        for name in p.RUNTIME_GRAPH_NAMES:
            if name in p.RUNTIME_FROZEN_REFS:refs[name]=dict(p.RUNTIME_FROZEN_REFS[name]);continue
            if name=="protocol14":refs[name]=refs["replacement14"];continue
            refs[name]=put(f"reports/releases/v0.9.2/acquisition/{name}.py",f"# synthetic {name}\n".encode())
        for name,key in roles.items():self.core[key]=refs[name]
        self.core["incoming_history"]=put("history.json",p.canonical_json({"recovery_module":refs["incoming_recovery"]}))
        # Real immutable script bytes and a real miniature committed Git tree.
        for ref in p.RUNTIME_FROZEN_REFS.values():
            put(ref["path"], (BASE.parents[3]/ref["path"]).read_bytes())
        self.core["runtime_module_graph"]=dict(sorted(refs.items()))
        self.core["source_inputs"]=[{"path":path,"sha256":sha,"role":"release-input"}
            for path,sha in sorted({r["path"]:r["sha256"] for r in refs.values()
                                   if not r["path"].startswith("scripts/")}.items())]
        self.core["contract"]=put("contract.json",p.canonical_json({"source_inputs":self.core["source_inputs"]}))
        self.git("init", "-q")
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "-c", "user.name=SyntheticFixture",
                 "-c", "user.email=fixture@example.invalid", "commit", "-qm", "synthetic fixture only")
        self.core["source_commit"] = self.git("rev-parse", "HEAD").decode().strip()

    def tearDown(self):self.tmp.cleanup()

    def clone(self):return json.loads(json.dumps(self.core))

    def test_sorted_serialized_graph_and_real_contract_source_closure(self):
        result=p.validate_runtime_core(self.root,self.clone())
        self.assertEqual(tuple(result),p.RUNTIME_GRAPH_NAMES)
        self.assertEqual(set(self.core)&{"runtime_module_graph","manifest_path","source_inputs"},
                         {"runtime_module_graph","manifest_path","source_inputs"})
        self.assertTrue({"runtime_module_graph","manifest_path","source_inputs"} <= p.CORE_FIELDS)

    def test_missing_extra_wrong_role_and_recovery_refs_rejected(self):
        for mutate in (lambda c:c["runtime_module_graph"].pop("checker"),
                       lambda c:c["runtime_module_graph"].update({"bad-name":c["implementation"]}),
                       lambda c:c["runtime_module_graph"].update(protocol14=c["frozen_bridge_source"]),
                       lambda c:c["runtime_module_graph"]["incoming_recovery"].update(path="wrong/provider.py"),
                       lambda c:c.update(manifest_path="wrong/manifest.json")):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement14Error):p.validate_runtime_core(self.root,c)

    def test_input_role_duplicate_contract_mismatch_and_unbound_module_rejected(self):
        for mutate in (lambda c:c["source_inputs"][0].update(role="unreviewed"),
                       lambda c:c["source_inputs"].append(c["source_inputs"][0]),
                       lambda c:c["source_inputs"].pop(),
                       lambda c:c["runtime_module_graph"]["policy_source"].update(sha256="f"*64)):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement14Error):p.validate_runtime_core(self.root,c)

    def test_packet_fields_derive_actual_contract_and_explicit_runtime_adapters(self):
        packet=load("replacement14_packet_schema_test",BASE/"bifrost-v0140-packet-14.py")
        refs=self.core["runtime_module_graph"]
        with patch.object(packet,"_protocol",return_value=p):
            actual=packet.runtime_core_fields(self.root,self.core,
                policy_source=refs["policy_source"],policy_runtime=refs["policy_runtime"],
                incoming_recovery=refs["incoming_recovery"],runtime_module_graph=refs)
        self.assertEqual(actual["source_inputs"],self.core["source_inputs"])
        self.assertEqual(actual["manifest_path"],p.MANIFEST_PATH)
        self.assertEqual(actual["runtime_module_graph"],refs)
        self.assertEqual(set(actual["runtime_module_graph"]),set(p.RUNTIME_GRAPH_NAMES))
        self.assertFalse((self.root/p.IDENTITY_PATH).exists())
        self.assertFalse((self.root/p.MANIFEST_PATH).exists())

    def test_complete_transitive_graph_and_distinct_instances_preserved(self):
        c=self.clone()
        extra=self.put("scripts/nested-parser.py", b"# synthetic transitive parser\n")
        c["runtime_module_graph"].update(stage_runtime01=extra,nested_parser=extra,
                                          nested_checker=c["runtime_module_graph"]["checker"])
        self.commit()
        c["source_commit"] = self.core["source_commit"]
        c["contract"]=self.put("expanded-contract.json",p.canonical_json({"source_inputs":c["source_inputs"]}))
        actual=p.validate_runtime_core(self.root,c)
        self.assertEqual(actual["stage_runtime01"],extra)
        self.assertEqual(actual["nested_parser"],extra)
        self.assertEqual(len(actual),len(p.RUNTIME_GRAPH_NAMES)+3)
        c["runtime_module_graph"]["nested_parser"]={**extra,"sha256":"f"*64}
        with self.assertRaises(p.Replacement14Error):p.validate_runtime_core(self.root,c)

    def test_extra_module_not_in_contract_closure_rejected(self):
        c=self.clone();c["runtime_module_graph"]["nested_parser"]=self.put("reports/releases/v0.9.2/acquisition/nested.py",b"# fixture")
        with self.assertRaises(p.Replacement14Error):p.validate_runtime_core(self.root,c)

    def test_stale_module_bytes_fail_without_import(self):
        ref=self.core["runtime_module_graph"]["policy_runtime"]
        (self.root/ref["path"]).write_bytes(b"changed")
        with self.assertRaises(p.Replacement14Error):p.validate_runtime_core(self.root,self.core)

    def test_scripts_use_actual_committed_snapshot_without_raw_source_inputs(self):
        self.assertFalse(any(x["path"].startswith("scripts/") for x in self.core["source_inputs"]))
        extra=self.put("scripts/transitive.py",b"# actual committed synthetic helper\n")
        self.commit();c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        self.assertEqual(p.validate_runtime_core(self.root,c)["transitive"],extra)
        # Matching current bytes cannot replace proof of the exact source blob.
        changed=self.put(extra["path"],b"# different uncommitted bytes\n")
        c["runtime_module_graph"]["transitive"]=changed
        with self.assertRaisesRegex(p.Replacement14Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_script_wrong_sha_or_absent_source_blob_rejects(self):
        extra=self.put("scripts/transitive.py",b"# committed helper\n")
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        with self.assertRaisesRegex(p.Replacement14Error,"absent from committed"):
            p.validate_runtime_core(self.root,c)
        self.commit();c["source_commit"]=self.core["source_commit"]
        c["runtime_module_graph"]["transitive"]={**extra,"sha256":"f"*64}
        with self.assertRaisesRegex(p.Replacement14Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_committed_acquisition_still_requires_exact_raw_source_input(self):
        c=self.clone();ref=c["runtime_module_graph"]["policy_runtime"]
        c["source_inputs"]=[entry for entry in c["source_inputs"] if entry["path"]!=ref["path"]]
        c["contract"]=self.put("missing-acquisition-contract.json",p.canonical_json({"source_inputs":c["source_inputs"]}))
        self.commit();c["source_commit"]=self.core["source_commit"]
        with self.assertRaisesRegex(p.Replacement14Error,"not bound by replacement source inputs"):
            p.validate_runtime_core(self.root,c)

    def test_committed_symlink_script_and_read_time_source_swap_reject(self):
        extra=self.put("scripts/target.py",b"# helper\n")
        alias=self.root/"scripts/alias.py";alias.symlink_to("target.py");self.commit()
        c=self.clone();c["runtime_module_graph"]["alias"]={"path":"scripts/alias.py","sha256":extra["sha256"]}
        with self.assertRaisesRegex(p.Replacement14Error,"not an exact committed regular blob"):
            p.validate_runtime_core(self.root,c)
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        original=p._bound
        def swap(root,ref,label,*args,**kwargs):
            raw=original(root,ref,label,*args,**kwargs)
            if ref==extra:(self.root/extra["path"]).write_bytes(raw+b"# changed during read\n")
            return raw
        with patch.object(p,"_bound",side_effect=swap):
            with self.assertRaisesRegex(p.Replacement14Error,"changed during read"):
                p.validate_runtime_core(self.root,c)


if __name__ == "__main__":
    unittest.main()
