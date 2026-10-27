#!/usr/bin/env python3
"""Static and stage-boundary regressions for replacement-21."""
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


p = load("replacement21_protocol_test", BASE / "bifrost-v0140-replacement-21.py")
bridge = load("replacement21_bridge_test", BASE / "bifrost-v0140-frozen-bridge-16.py")
expiry = load("replacement21_noexpiry_test", BASE / "bifrost-v0140-no-expiry-21.py")


class Replacement21Tests(unittest.TestCase):
    def test_protocol_is_append_only_and_stage_exports_are_present(self):
        self.assertEqual(p.MANIFEST_SCHEMA, "v092-bifrost-v0140-replacement-21/v1")
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
        with self.assertRaises(expiry.NoExpiry21Error):
            expiry.lease_remaining(popen_monotonic=100, now_monotonic=20000,
                                   registered_deadline_seconds=13840)

    def test_stage_helper_rejects_serialized_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bridge.FrozenBridge16Error):
                bridge.load_runtime_stage(Path(tmp), graph=object(),
                                          runtime_loader={"serialized": True}, mode="before",
                                          core_identity={})


class RuntimeCoreSchema18Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.core={"manifest_path":p.MANIFEST_PATH}
        refs={}
        def put(path,raw):
            file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
            return {"path":path,"sha256":p.sha256(raw)}
        self.put=put
        roles={"bridge16":"frozen_bridge_source","replacement21":"implementation",
               "protocol21":"implementation","admission21":"bifrost_admission_source",
               "supervisor21":"bifrost_supervisor_source"}
        for name in p.RUNTIME_GRAPH_NAMES:
            if name in p.RUNTIME_FROZEN_REFS:refs[name]=dict(p.RUNTIME_FROZEN_REFS[name]);continue
            if name=="protocol21":refs[name]=refs["replacement21"];continue
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
                       lambda c:c["runtime_module_graph"].update(protocol21=c["frozen_bridge_source"]),
                       lambda c:c["runtime_module_graph"]["incoming_recovery"].update(path="wrong/provider.py"),
                       lambda c:c.update(manifest_path="wrong/manifest.json")):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement21Error):p.validate_runtime_core(self.root,c)

    def test_input_role_duplicate_contract_mismatch_and_unbound_module_rejected(self):
        for mutate in (lambda c:c["source_inputs"][0].update(role="unreviewed"),
                       lambda c:c["source_inputs"].append(c["source_inputs"][0]),
                       lambda c:c["source_inputs"].pop(),
                       lambda c:c["runtime_module_graph"]["policy_source"].update(sha256="f"*64)):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement21Error):p.validate_runtime_core(self.root,c)

    def test_packet_fields_derive_actual_contract_and_explicit_runtime_adapters(self):
        packet=load("replacement21_packet_schema_test",BASE/"bifrost-v0140-packet-21.py")
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
        with self.assertRaises(p.Replacement21Error):p.validate_runtime_core(self.root,c)

    def test_extra_module_not_in_contract_closure_rejected(self):
        c=self.clone();c["runtime_module_graph"]["nested_parser"]=self.put("reports/releases/v0.9.2/acquisition/nested.py",b"# fixture")
        with self.assertRaises(p.Replacement21Error):p.validate_runtime_core(self.root,c)

    def test_stale_module_bytes_fail_without_import(self):
        ref=self.core["runtime_module_graph"]["policy_runtime"]
        (self.root/ref["path"]).write_bytes(b"changed")
        with self.assertRaises(p.Replacement21Error):p.validate_runtime_core(self.root,self.core)

    def test_scripts_use_actual_committed_snapshot_without_raw_source_inputs(self):
        self.assertFalse(any(x["path"].startswith("scripts/") for x in self.core["source_inputs"]))
        extra=self.put("scripts/transitive.py",b"# actual committed synthetic helper\n")
        self.commit();c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        self.assertEqual(p.validate_runtime_core(self.root,c)["transitive"],extra)
        # Matching current bytes cannot replace proof of the exact source blob.
        changed=self.put(extra["path"],b"# different uncommitted bytes\n")
        c["runtime_module_graph"]["transitive"]=changed
        with self.assertRaisesRegex(p.Replacement21Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_script_wrong_sha_or_absent_source_blob_rejects(self):
        extra=self.put("scripts/transitive.py",b"# committed helper\n")
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        with self.assertRaisesRegex(p.Replacement21Error,"absent from committed"):
            p.validate_runtime_core(self.root,c)
        self.commit();c["source_commit"]=self.core["source_commit"]
        c["runtime_module_graph"]["transitive"]={**extra,"sha256":"f"*64}
        with self.assertRaisesRegex(p.Replacement21Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_committed_acquisition_still_requires_exact_raw_source_input(self):
        c=self.clone();ref=c["runtime_module_graph"]["policy_runtime"]
        c["source_inputs"]=[entry for entry in c["source_inputs"] if entry["path"]!=ref["path"]]
        c["contract"]=self.put("missing-acquisition-contract.json",p.canonical_json({"source_inputs":c["source_inputs"]}))
        self.commit();c["source_commit"]=self.core["source_commit"]
        with self.assertRaisesRegex(p.Replacement21Error,"not bound by replacement source inputs"):
            p.validate_runtime_core(self.root,c)

    def test_committed_symlink_script_and_read_time_source_swap_reject(self):
        extra=self.put("scripts/target.py",b"# helper\n")
        alias=self.root/"scripts/alias.py";alias.symlink_to("target.py");self.commit()
        c=self.clone();c["runtime_module_graph"]["alias"]={"path":"scripts/alias.py","sha256":extra["sha256"]}
        with self.assertRaisesRegex(p.Replacement21Error,"not an exact committed regular blob"):
            p.validate_runtime_core(self.root,c)
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        original=p._bound
        def swap(root,ref,label,*args,**kwargs):
            raw=original(root,ref,label,*args,**kwargs)
            if ref==extra:(self.root/extra["path"]).write_bytes(raw+b"# changed during read\n")
            return raw
        with patch.object(p,"_bound",side_effect=swap):
            with self.assertRaisesRegex(p.Replacement21Error,"changed during read"):
                p.validate_runtime_core(self.root,c)



class SourceDesign12SchemaTests(unittest.TestCase):
    """Actual immutable11 shape, with successor values confined to a temp fixture.

    These exercise protocol schema bindings only. The production full Git
    intervening closure and nine-source delta remain stage-runtime authority.
    """
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.repo = BASE.parents[3]
        original = (self.repo / p.SOURCE_DESIGN_15["path"]).read_bytes()
        self.previous = json.loads(original)
        self.assertEqual(p.sha256(original), p.SOURCE_DESIGN_15["sha256"])
        self.assertNotIn("actual_observed_head", self.previous)
        predecessor = self.root / p.SOURCE_DESIGN_15["path"]
        predecessor.parent.mkdir(parents=True)
        predecessor.write_bytes(original)
        self.value = json.loads(original)
        self.value["predecessor_design"] = dict(p.SOURCE_DESIGN_15)
        self.core = {"continuation": dict(self.previous["incoming_codeql"])}

    def tearDown(self):
        self.tmp.cleanup()

    def bind(self, value=None):
        value = self.value if value is None else value
        raw = p.canonical_json(value)
        path = self.root / p.SOURCE_DESIGN_16_PATH
        path.write_bytes(raw)
        self.core["source_design"] = {"path": p.SOURCE_DESIGN_16_PATH,
                                      "sha256": p.sha256(raw)}
        return self.core

    def test_actual11_shape_accepts_correct_successor_schema(self):
        result = p.validate_source_design(self.root, self.bind())
        self.assertEqual(result["reviewed_baseline_head"], self.previous["reviewed_baseline_head"])
        self.assertEqual(result["reviewed_intervening_changes"], self.previous["reviewed_intervening_changes"])
        self.assertEqual(result["allowed_source_delta"], self.previous["allowed_source_delta"])
        self.assertEqual(len(result["allowed_source_delta"]), 9)

    def test_wrong_predecessor04_or07_rejected(self):
        for predecessor in (p.SOURCE_DESIGN_04,
                {"path": p.SOURCE_DESIGN_16_PATH.replace("-16.json", "-07.json"),
                 "sha256": p.sha256((self.repo / p.SOURCE_DESIGN_16_PATH.replace("-16.json", "-07.json")).read_bytes())}):
            value = json.loads(json.dumps(self.value)); value["predecessor_design"] = predecessor
            with self.assertRaisesRegex(p.Replacement21Error, "predecessor/authority/baseline"):
                p.validate_source_design(self.root, self.bind(value))

    def test_foreign_or_missing_baseline_rejected_even_with_observed_head(self):
        for baseline in ("ac0af833bc19c6c9fd343e9e60430a85fb1910e2", "b906ca907bfd11f64ab0f2099e29ccf5d1c3adf1", None):
            value = json.loads(json.dumps(self.value))
            value["reviewed_baseline_head"] = baseline
            value["actual_observed_head"] = self.previous["reviewed_baseline_head"]
            with self.assertRaisesRegex(p.Replacement21Error, "predecessor/authority/baseline"):
                p.validate_source_design(self.root, self.bind(value))

    def test_missing_closure_or_invalid_immediate_base_rejected(self):
        for key in ("reviewed_intervening_changes", "immediate_patch_base"):
            value = json.loads(json.dumps(self.value)); value.pop(key)
            with self.assertRaises(p.Replacement21Error):
                p.validate_source_design(self.root, self.bind(value))

    def test_changed_history_incoming_or_nine_source_policy_rejected(self):
        for key in ("historical_outputs_immutable", "actual_historical_bifrost_contexts",
                    "actual_historical_bifrost_rows", "allowed_source_delta", "unchanged_source_patch",
                    "incoming_codeql"):
            value = json.loads(json.dumps(self.value)); value[key] = None
            with self.assertRaisesRegex(p.Replacement21Error, "immutable source13"):
                p.validate_source_design(self.root, self.bind(value))

    def test_preserved535_closure_paths_cannot_be_dropped_or_duplicated(self):
        self.assertEqual(len(self.previous["reviewed_intervening_changes"]), 591)
        for kind in ("drop", "duplicate", "malformed"):
            value = json.loads(json.dumps(self.value))
            if kind == "drop": value["reviewed_intervening_changes"].pop()
            elif kind == "duplicate": value["reviewed_intervening_changes"].append(value["reviewed_intervening_changes"][0])
            else: value["reviewed_intervening_changes"][0] = None
            with self.subTest(kind=kind), self.assertRaises(p.Replacement21Error):
                p.validate_source_design(self.root, self.bind(value))

    def test_exact_successor_and_predecessor_hashes_required(self):
        core = self.bind(); core["source_design"]["sha256"] = "f" * 64
        with self.assertRaises(p.Replacement21Error): p.validate_source_design(self.root, core)
        predecessor = self.root / p.SOURCE_DESIGN_15["path"]
        predecessor.write_bytes(predecessor.read_bytes() + b" ")
        with self.assertRaises(p.Replacement21Error): p.validate_source_design(self.root, self.bind())

    def test_legacy14_design07_binding_is_not_promoted(self):
        legacy = p.SOURCE_DESIGN_16_PATH.replace("-16.json", "-07.json")
        raw = (self.repo / legacy).read_bytes()
        core = {**self.core, "source_design": {"path": legacy, "sha256": p.sha256(raw)},
                "contract": {"path": "reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-17-contract.json",
                             "sha256": "f" * 64}}
        with self.assertRaisesRegex(p.Replacement21Error, "successor16"):
            p.validate_source_design(self.root, core)


class FullActualCore18Tests(unittest.TestCase):
    """Bounded local integration: actual BF16 config01/contract18, projected only in temp.

    Requires the exact preserved BF16 config01. This is static schema
    validation, not replay, qualification, or approval of future source bindings.
    Every validator runs unmodified, including real committed-script Git reads.
    """
    @classmethod
    def setUpClass(cls):
        import copy
        import os
        import shutil
        cls.tmp = tempfile.TemporaryDirectory(prefix="bf21-full-core-schema-")
        cls.root = Path(cls.tmp.name).resolve()
        repository = BASE.parents[3]
        cfgraw = Path('/private/tmp/bf16-core-config-01.json').read_bytes()
        assert p.sha256(cfgraw) == 'a09a6cacb47c7e0373cf8f945295e0cd6db6fee12893ca12f9331fdb907f35ca'
        cfg = json.loads(cfgraw)
        cls.cfg = cfg
        def put(path, raw):
            target = cls.root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            return {'path':path, 'sha256':p.sha256(raw)}
        cls.put = staticmethod(put)
        def copy_ref(ref):
            raw = (repository/ref['path']).read_bytes()
            if p.sha256(raw) != ref['sha256'] and ref['path'] in {
                    'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py',
                    'reports/releases/v0.9.2/acquisition/test-bifrost-v0140-replacement-14.py'}:
                raw = subprocess.check_output(['git','show',cfg['source_commit']+':'+ref['path']], cwd=repository)
            assert p.sha256(raw) == ref['sha256'], ref['path']
            put(ref['path'], raw)
            return json.loads(raw) if ref['path'].endswith('.json') else None
        incoming = copy_ref(cfg['incoming_contract'])
        replacement = copy_ref(cfg['contract'])
        v = copy.deepcopy(cfg['bindings'])
        # Preserve all real historical bindings; no historical source is relabelled.
        for ref in (p.WINDOW_AUTHORITY, p.WORKING_CAP_AUTHORITY, p.BREADTH_FIRST_AUTHORITY,
                    p.SOURCE_DESIGN_15, v['original_prefix'], v['continuation_prefix'],
                    v['source_evidence']):
            copy_ref(ref)
        seal = copy_ref(v['incoming_history'])
        for key in ('codeql_terminal_receipt', 'recovery_module', 'recovery_manifest'):
            copy_ref(seal[key])
        ledger = cls.root/p.LEDGER_PATH
        ledger.parent.mkdir(parents=True, exist_ok=True)
        os.link(cls.root/v['continuation_prefix']['path'], ledger)
        for ref in v['runtime_module_graph'].values():
            copy_ref(ref)
        # Synthetic prospective source14 and new source-input hashes are confined
        # to this tempfile. They are never written as production evidence.
        copy_ref(v['source_design'])
        design = copy_ref(p.SOURCE_DESIGN_15)
        design['predecessor_design'] = dict(p.SOURCE_DESIGN_15)
        v['source_design'] = put(p.SOURCE_DESIGN_16_PATH, p.canonical_json(design))
        current_refs = {}
        # Exact current source successors, including runtime/loader graph members.
        successor_sources = {}
        for prefix in ("", "test-"):
            for kind in ("replacement", "admission", "supervisor", "packet", "no-expiry", "runtime-loaders"):
                successor_sources[f"{prefix}bifrost-v0140-{kind}-16.py"] = f"{prefix}bifrost-v0140-{kind}-21.py"
        successor_sources.update({
            "bifrost-v0140-frozen-bridge-11.py":"bifrost-v0140-frozen-bridge-16.py",
            "test-bifrost-v0140-frozen-parser-11.py":"test-bifrost-v0140-frozen-parser-16.py",
            "bifrost-v0140-stage-runtime-03.py":"bifrost-v0140-stage-runtime-08.py",
            "test-bifrost-v0140-stage-runtime-03.py":"test-bifrost-v0140-stage-runtime-08.py",
            "test-bifrost-v0140-supervisor-16-production.py":"test-bifrost-v0140-supervisor-21-production.py",
        })
        path_map = {}
        for old, new in successor_sources.items():
            path = 'reports/releases/v0.9.2/acquisition/' + new
            current_refs[path] = put(path, (BASE/new).read_bytes())
            path_map['reports/releases/v0.9.2/acquisition/' + old] = path
        def role(name):
            for old, new in [('bridge11','bridge16'), ('replacement16','replacement21'),
                             ('protocol16','protocol21'), ('admission16','admission21'),
                             ('supervisor16','supervisor21'), ('runtime_loaders16','runtime_loaders21'),
                             ('stage_runtime03','stage_runtime08')]:
                name = name.replace(old,new)
            return name
        v['runtime_module_graph'] = {
            role(name):current_refs[path_map[ref['path']]] if ref['path'] in path_map else ref
            for name,ref in v['runtime_module_graph'].items()}
        # Additive candidate entries; actual BF16 source_inputs are immutable.
        v['source_inputs'] = sorted(v['source_inputs'] + [
            dict(ref,role='release-input') for ref in current_refs.values()], key=lambda ref:ref['path'])
        v['manifest_path'] = p.MANIFEST_PATH
        v['sidecar_namespace'] = 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-21'
        v['configuration_output'] = v['sidecar_namespace']+'/configuration/report-configurations.json'
        replacement['source_inputs'] = copy.deepcopy(v['source_inputs'])
        contract_ref = put('reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-23-contract.json', p.canonical_json(replacement))
        # Only a private Git repository is initialized. Read-only object access
        # to the actual source commit proves every script ref against real blobs.
        subprocess.run(['git','init','-q',str(cls.root)], check=True)
        common = Path(subprocess.check_output(['git','rev-parse','--git-common-dir'], cwd=repository,
                                            text=True).strip())
        common = common if common.is_absolute() else repository/common
        (cls.root/'.git/objects/info/alternates').write_text(str((common/'objects').resolve())+'\n')
        r = load('full_core14_replacement05_constants', BASE/'bifrost-v0140-replacement-05.py')
        v.update(schema=p.IDENTITY_SCHEMA, original_origin_utc=p.ORIGIN, cutoff_utc=None,
                 total_wall_budget_seconds=None, execution_window_authority=p.WINDOW_AUTHORITY,
                 aggregate_source_working_authority=p.WORKING_CAP_AUTHORITY,
                 breadth_first_authority=p.BREADTH_FIRST_AUTHORITY,
                 source_commit=cfg['source_commit'], plan_commit=cfg['plan_commit'], contract=contract_ref,
                 continuation={'schema':'v092-bifrost-v0140-continuation-context/v1',
                     'contract':cfg['incoming_contract'], 'source_commit':incoming['source_commit'],
                     'plan_commit':cfg['incoming_plan_commit'], 'source_inputs':incoming['source_inputs']},
                 runner=replacement['tools']['runner'], binary=replacement['tools']['bifrost'],
                 qualification=r.QUALIFICATION_REF, control_review=r.CONTROL_REVIEW_REF,
                 replacement_groups=[g['id'] for g in replacement['groups'] if g['tool']=='bifrost'],
                 resource_policy=p.RESOURCE_POLICY, lock_path=p.CANONICAL_LOCK_PATH)
        for key, path in {
            'implementation':'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-21.py',
            'implementation_test':'reports/releases/v0.9.2/acquisition/test-bifrost-v0140-replacement-21.py',
            'bifrost_admission_source':p.ADMISSION_SOURCE_PATH,
            'bifrost_supervisor_source':p.SUPERVISOR_SOURCE_PATH,
            'frozen_bridge_source':p.BRIDGE_SOURCE_PATH,
            'frozen_bridge_tests':p.BRIDGE_TEST_PATH,
        }.items():
            v[key] = put(path, (repository/path).read_bytes())
        for key in ('runner','binary'):
            if not Path(v[key]['path']).is_absolute():
                copy_ref({'path':v[key]['path'],'sha256':v[key]['sha256']})
        v['review_policy'] = {'schema':'v092-bifrost-v0140-review-policy/v1',
            'review_types':p.REVIEW_TYPES, 'reviewed_sources':dict(zip(p.SOURCE_NAMES,
                [v[k] for k in ('implementation','implementation_test','bifrost_admission_source',
                               'bifrost_supervisor_source','frozen_bridge_source','frozen_bridge_tests')]))}
        assert set(v) == p.CORE_FIELDS
        cls.core = v
        cls.roundtrip = json.loads(p.canonical_json(v))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def validate(self, value):
        p._validate_core(self.root, value, {'path':p.IDENTITY_PATH,'sha256':p.sha256(p.canonical_json(value))})

    def clone(self):
        return json.loads(json.dumps(self.roundtrip))

    def test_complete_actual_shape_roundtrips_all_static_validators(self):
        self.assertEqual(self.core, self.roundtrip)
        self.assertEqual(set(self.roundtrip), p.CORE_FIELDS)
        self.assertEqual(len(self.roundtrip['runtime_module_graph']), 88)
        self.assertEqual(len(self.roundtrip['replacement_groups']), 20)
        self.validate(self.roundtrip)

    def test_wrong_canonical_manifest_path_and_missing_root_reject(self):
        for path in ('reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-14/manifest.json',
                     '/private/tmp/manifest.json', None):
            value = self.clone()
            value['manifest_path'] = path
            with self.assertRaisesRegex(p.Replacement21Error, 'manifest path'):
                self.validate(value)
        value = self.clone(); del value['manifest_path']
        with self.assertRaisesRegex(p.Replacement21Error, 'field set'):
            self.validate(value)

    def test_nested_manifest_and_all_other_runtime_review_keys_reject(self):
        # Both permissive environment objects and arbitrarily deep list nesting
        # must reach the unchanged recursive prohibition after all prior gates.
        for field in sorted(p._FORBIDDEN_CORE_KEYS):
            value = self.clone()
            value['executor_environment']['nested_probe'] = [{'inner':{field:p.MANIFEST_PATH}}]
            with self.assertRaisesRegex(p.Replacement21Error, 'runtime/review field '+field):
                self.validate(value)

    def test_extra_root_runtime_review_fields_reject(self):
        for field in ('independent_review', 'permit', 'manifest_sha256', 'extra_field'):
            value = self.clone(); value[field] = 'forbidden'
            with self.assertRaisesRegex(p.Replacement21Error, 'field set'):
                self.validate(value)

    def test_unrelated_full_core_guards_remain_active(self):
        mutations = [
            ('resource_policy', {**p.RESOURCE_POLICY, 'working_set_gib':12}),
            ('source_commit', self.roundtrip['plan_commit']),
            ('review_policy', {**self.roundtrip['review_policy'], 'review_types':[]}),
            ('replacement_groups', self.roundtrip['replacement_groups']*2),
        ]
        for field, replacement in mutations:
            value = self.clone(); value[field] = replacement
            with self.assertRaises(p.Replacement21Error):self.validate(value)


if __name__ == "__main__":
    unittest.main()
