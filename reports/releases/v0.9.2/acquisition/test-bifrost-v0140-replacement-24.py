#!/usr/bin/env python3
"""Static and stage-boundary regressions for replacement-24."""
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
def repository_root():
    candidate = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents)>4 else Path.cwd()
    if not (candidate/'scripts/execute-release-v092.py').is_file(): candidate=Path.cwd().resolve()
    assert (candidate/'scripts/execute-release-v092.py').is_file(), 'run private canonical staging from repository root'
    return candidate
ROOT=repository_root()
HISTORICAL_BASE=ROOT/'reports/releases/v0.9.2/acquisition'



def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


p = load("replacement24_protocol_test", BASE / "bifrost-v0140-replacement-24.py")
bridge = load("replacement24_bridge_test", BASE / "bifrost-v0140-frozen-bridge-19.py")
expiry = load("replacement24_noexpiry_test", BASE / "bifrost-v0140-no-expiry-24.py")


class Replacement24Tests(unittest.TestCase):
    def test_protocol_is_append_only_and_stage_exports_are_present(self):
        self.assertEqual(p.MANIFEST_SCHEMA, "v092-bifrost-v0140-replacement-24/v1")
        self.assertEqual(p.STAGE_SCHEMA, "v092-bifrost-v0140-replay-stage/v4")
        self.assertEqual(p.PARENT_STAGE_COUNT, 3)
        self.assertEqual(p.CHILD_STAGE_COUNT, 2)
        for name in ("build_parent_stage", "build_successor_stage", "build_child_stage", "write_completion"):
            self.assertTrue(callable(getattr(p, name)))

    def test_no_expiry_keeps_registered_finite_limits(self):
        core = {"cutoff_utc": None, "total_wall_budget_seconds": None,
                "original_origin_utc": expiry.ORIGIN,
                "execution_window_authority": expiry.AUTHORITY,
                "resource_policy": dict(expiry.RESOURCE_POLICY)}
        result = expiry.validate(ROOT, core)
        self.assertEqual(result["status"], "validated")
        self.assertEqual(expiry.lease_remaining(popen_monotonic=100, now_monotonic=101,
                                                 registered_deadline_seconds=13840), 14439)
        with self.assertRaises(expiry.NoExpiry23Error):
            expiry.lease_remaining(popen_monotonic=100, now_monotonic=20000,
                                   registered_deadline_seconds=13840)

    def test_stage_helper_rejects_serialized_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bridge.FrozenBridge19Error):
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
        roles={"bridge19":"frozen_bridge_source","replacement24":"implementation",
               "protocol24":"implementation","admission24":"bifrost_admission_source",
               "supervisor24":"bifrost_supervisor_source"}
        for name in p.RUNTIME_GRAPH_NAMES:
            if name in p.RUNTIME_FROZEN_REFS:refs[name]=dict(p.RUNTIME_FROZEN_REFS[name]);continue
            if name=="protocol24":refs[name]=refs["replacement24"];continue
            refs[name]=put(f"reports/releases/v0.9.2/acquisition/{name}.py",f"# synthetic {name}\n".encode())
        for name,key in roles.items():self.core[key]=refs[name]
        self.core["incoming_history"]=put("history.json",p.canonical_json({"recovery_module":refs["incoming_recovery"]}))
        # Real immutable script bytes and a real miniature committed Git tree.
        for ref in p.RUNTIME_FROZEN_REFS.values():
            put(ref["path"], (ROOT/ref["path"]).read_bytes())
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
                       lambda c:c["runtime_module_graph"].update(protocol24=c["frozen_bridge_source"]),
                       lambda c:c["runtime_module_graph"]["incoming_recovery"].update(path="wrong/provider.py"),
                       lambda c:c.update(manifest_path="wrong/manifest.json")):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement24Error):p.validate_runtime_core(self.root,c)

    def test_input_role_duplicate_contract_mismatch_and_unbound_module_rejected(self):
        for mutate in (lambda c:c["source_inputs"][0].update(role="unreviewed"),
                       lambda c:c["source_inputs"].append(c["source_inputs"][0]),
                       lambda c:c["source_inputs"].pop(),
                       lambda c:c["runtime_module_graph"]["policy_source"].update(sha256="f"*64)):
            c=self.clone();mutate(c)
            with self.assertRaises(p.Replacement24Error):p.validate_runtime_core(self.root,c)

    def test_packet_fields_derive_actual_contract_and_explicit_runtime_adapters(self):
        packet=load("replacement24_packet_schema_test",BASE/"bifrost-v0140-packet-24.py")
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
        with self.assertRaises(p.Replacement24Error):p.validate_runtime_core(self.root,c)

    def test_extra_module_not_in_contract_closure_rejected(self):
        c=self.clone();c["runtime_module_graph"]["nested_parser"]=self.put("reports/releases/v0.9.2/acquisition/nested.py",b"# fixture")
        with self.assertRaises(p.Replacement24Error):p.validate_runtime_core(self.root,c)

    def test_stale_module_bytes_fail_without_import(self):
        ref=self.core["runtime_module_graph"]["policy_runtime"]
        (self.root/ref["path"]).write_bytes(b"changed")
        with self.assertRaises(p.Replacement24Error):p.validate_runtime_core(self.root,self.core)

    def test_scripts_use_actual_committed_snapshot_without_raw_source_inputs(self):
        self.assertFalse(any(x["path"].startswith("scripts/") for x in self.core["source_inputs"]))
        extra=self.put("scripts/transitive.py",b"# actual committed synthetic helper\n")
        self.commit();c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        self.assertEqual(p.validate_runtime_core(self.root,c)["transitive"],extra)
        # Matching current bytes cannot replace proof of the exact source blob.
        changed=self.put(extra["path"],b"# different uncommitted bytes\n")
        c["runtime_module_graph"]["transitive"]=changed
        with self.assertRaisesRegex(p.Replacement24Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_script_wrong_sha_or_absent_source_blob_rejects(self):
        extra=self.put("scripts/transitive.py",b"# committed helper\n")
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        with self.assertRaisesRegex(p.Replacement24Error,"absent from committed"):
            p.validate_runtime_core(self.root,c)
        self.commit();c["source_commit"]=self.core["source_commit"]
        c["runtime_module_graph"]["transitive"]={**extra,"sha256":"f"*64}
        with self.assertRaisesRegex(p.Replacement24Error,"committed source blob"):
            p.validate_runtime_core(self.root,c)

    def test_committed_acquisition_still_requires_exact_raw_source_input(self):
        c=self.clone();ref=c["runtime_module_graph"]["policy_runtime"]
        c["source_inputs"]=[entry for entry in c["source_inputs"] if entry["path"]!=ref["path"]]
        c["contract"]=self.put("missing-acquisition-contract.json",p.canonical_json({"source_inputs":c["source_inputs"]}))
        self.commit();c["source_commit"]=self.core["source_commit"]
        with self.assertRaisesRegex(p.Replacement24Error,"not bound by replacement source inputs"):
            p.validate_runtime_core(self.root,c)

    def test_committed_symlink_script_and_read_time_source_swap_reject(self):
        extra=self.put("scripts/target.py",b"# helper\n")
        alias=self.root/"scripts/alias.py";alias.symlink_to("target.py");self.commit()
        c=self.clone();c["runtime_module_graph"]["alias"]={"path":"scripts/alias.py","sha256":extra["sha256"]}
        with self.assertRaisesRegex(p.Replacement24Error,"not an exact committed regular blob"):
            p.validate_runtime_core(self.root,c)
        c=self.clone();c["runtime_module_graph"]["transitive"]=extra
        original=p._bound
        def swap(root,ref,label,*args,**kwargs):
            raw=original(root,ref,label,*args,**kwargs)
            if ref==extra:(self.root/extra["path"]).write_bytes(raw+b"# changed during read\n")
            return raw
        with patch.object(p,"_bound",side_effect=swap):
            with self.assertRaisesRegex(p.Replacement24Error,"changed during read"):
                p.validate_runtime_core(self.root,c)



class SourceDesign12SchemaTests(unittest.TestCase):
    """Actual immutable11 shape, with successor values confined to a temp fixture.

    These exercise protocol schema bindings only. The production full Git
    intervening closure and nine-source delta remain stage-runtime authority.
    """
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.repo = ROOT
        original = (self.repo / p.SOURCE_DESIGN_18["path"]).read_bytes()
        self.previous = json.loads(original)
        self.assertEqual(p.sha256(original), p.SOURCE_DESIGN_18["sha256"])
        self.assertNotIn("actual_observed_head", self.previous)
        predecessor = self.root / p.SOURCE_DESIGN_18["path"]
        predecessor.parent.mkdir(parents=True)
        predecessor.write_bytes(original)
        self.value = json.loads(original)
        self.value["predecessor_design"] = dict(p.SOURCE_DESIGN_18)
        self.core = {"continuation": dict(self.previous["incoming_codeql"])}

    def tearDown(self):
        self.tmp.cleanup()

    def bind(self, value=None):
        value = self.value if value is None else value
        raw = p.canonical_json(value)
        path = self.root / p.SOURCE_DESIGN_19_PATH
        path.write_bytes(raw)
        self.core["source_design"] = {"path": p.SOURCE_DESIGN_19_PATH,
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
                {"path": p.SOURCE_DESIGN_19_PATH.replace("-19.json", "-07.json"),
                 "sha256": p.sha256((self.repo / p.SOURCE_DESIGN_19_PATH.replace("-19.json", "-07.json")).read_bytes())}):
            value = json.loads(json.dumps(self.value)); value["predecessor_design"] = predecessor
            with self.assertRaisesRegex(p.Replacement24Error, "predecessor/authority/baseline"):
                p.validate_source_design(self.root, self.bind(value))

    def test_foreign_or_missing_baseline_rejected_even_with_observed_head(self):
        for baseline in ("ac0af833bc19c6c9fd343e9e60430a85fb1910e2", "b906ca907bfd11f64ab0f2099e29ccf5d1c3adf1", None):
            value = json.loads(json.dumps(self.value))
            value["reviewed_baseline_head"] = baseline
            value["actual_observed_head"] = self.previous["reviewed_baseline_head"]
            with self.assertRaisesRegex(p.Replacement24Error, "predecessor/authority/baseline"):
                p.validate_source_design(self.root, self.bind(value))

    def test_missing_closure_or_invalid_immediate_base_rejected(self):
        for key in ("reviewed_intervening_changes", "immediate_patch_base"):
            value = json.loads(json.dumps(self.value)); value.pop(key)
            with self.assertRaises(p.Replacement24Error):
                p.validate_source_design(self.root, self.bind(value))

    def test_changed_history_incoming_or_nine_source_policy_rejected(self):
        for key in ("historical_outputs_immutable", "actual_historical_bifrost_contexts",
                    "actual_historical_bifrost_rows", "allowed_source_delta", "unchanged_source_patch",
                    "incoming_codeql"):
            value = json.loads(json.dumps(self.value)); value[key] = None
            with self.assertRaisesRegex(p.Replacement24Error, "immutable source13"):
                p.validate_source_design(self.root, self.bind(value))

    def test_preserved535_closure_paths_cannot_be_dropped_or_duplicated(self):
        self.assertEqual(len(self.previous["reviewed_intervening_changes"]), 674)
        for kind in ("drop", "duplicate", "malformed"):
            value = json.loads(json.dumps(self.value))
            if kind == "drop": value["reviewed_intervening_changes"].pop()
            elif kind == "duplicate": value["reviewed_intervening_changes"].append(value["reviewed_intervening_changes"][0])
            else: value["reviewed_intervening_changes"][0] = None
            with self.subTest(kind=kind), self.assertRaises(p.Replacement24Error):
                p.validate_source_design(self.root, self.bind(value))

    def test_exact_successor_and_predecessor_hashes_required(self):
        core = self.bind(); core["source_design"]["sha256"] = "f" * 64
        with self.assertRaises(p.Replacement24Error): p.validate_source_design(self.root, core)
        predecessor = self.root / p.SOURCE_DESIGN_18["path"]
        predecessor.write_bytes(predecessor.read_bytes() + b" ")
        with self.assertRaises(p.Replacement24Error): p.validate_source_design(self.root, self.bind())

    def test_legacy14_design07_binding_is_not_promoted(self):
        legacy = p.SOURCE_DESIGN_19_PATH.replace("-19.json", "-07.json")
        raw = (self.repo / legacy).read_bytes()
        core = {**self.core, "source_design": {"path": legacy, "sha256": p.sha256(raw)},
                "contract": {"path": "reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-17-contract.json",
                             "sha256": "f" * 64}}
        with self.assertRaisesRegex(p.Replacement24Error, "successor18"):
            p.validate_source_design(self.root, core)


class FullActualCurrent24CoreTests(unittest.TestCase):
    """Actual sealed BF23 shape, projected to current24 only in an isolated temp.

    All current static validators run unmodified, including real committed-script
    Git reads. Future source/design bindings are synthetic fixture data; this is
    neither historical replay nor production qualification evidence.
    """
    @classmethod
    def setUpClass(cls):
        import copy
        import os
        import shutil
        cls.tmp = tempfile.TemporaryDirectory(prefix="bf23-full-core-schema-")
        cls.root = Path(cls.tmp.name).resolve()
        repository = ROOT
        sealedraw=(repository/'reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-23/manifest-identity.json').read_bytes()
        assert p.sha256(sealedraw)=='7341166cf4c1f31d2c336385b2edd974ac68d2d84ea5d839641c5d1e3d22e643'
        sealed=json.loads(sealedraw)
        cfg={'source_commit':sealed['source_commit'],'plan_commit':sealed['plan_commit'],'incoming_contract':sealed['continuation']['contract'],'incoming_plan_commit':sealed['continuation']['plan_commit'],'contract':sealed['contract'],'bindings':sealed}
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
                    p.SOURCE_DESIGN_18, v['original_prefix'], v['continuation_prefix'],
                    v['source_evidence']):
            copy_ref(ref)
        seal = copy_ref(v['incoming_history'])
        for key in ('codeql_terminal_receipt', 'recovery_module', 'recovery_manifest'):
            copy_ref(seal[key])
        ledger = cls.root/p.LEDGER_PATH
        ledger.parent.mkdir(parents=True, exist_ok=True)
        for fixture_ref in walk(SEALED_RESUME_HISTORY):copy_ref(fixture_ref)
        os.link(cls.root/SEALED_RESUME_HISTORY['ledger_prefix']['path'], ledger)
        for ref in v['runtime_module_graph'].values():
            copy_ref(ref)
        # Synthetic prospective source14 and new source-input hashes are confined
        # to this tempfile. They are never written as production evidence.
        copy_ref(v['source_design'])
        design = copy_ref(p.SOURCE_DESIGN_18)
        design['predecessor_design'] = dict(p.SOURCE_DESIGN_18)
        v['source_design'] = put(p.SOURCE_DESIGN_19_PATH, p.canonical_json(design))
        current_refs = {}
        # Exact current source successors, including runtime/loader graph members.
        successor_sources = {}
        for prefix in ("", "test-"):
            for kind in ("replacement", "admission", "supervisor", "packet", "no-expiry", "runtime-loaders"):
                successor_sources[f"{prefix}bifrost-v0140-{kind}-23.py"] = f"{prefix}bifrost-v0140-{kind}-24.py"
        successor_sources.update({
            "bifrost-v0140-frozen-bridge-18.py":"bifrost-v0140-frozen-bridge-19.py",
            "test-bifrost-v0140-frozen-parser-18.py":"test-bifrost-v0140-frozen-parser-19.py",
            "bifrost-v0140-stage-runtime-10.py":"bifrost-v0140-stage-runtime-11.py",
            "test-bifrost-v0140-stage-runtime-10.py":"test-bifrost-v0140-stage-runtime-11.py",
            "test-bifrost-v0140-supervisor-23-production.py":"test-bifrost-v0140-supervisor-24-production.py",
        })
        path_map = {}
        for old, new in successor_sources.items():
            path = 'reports/releases/v0.9.2/acquisition/' + new
            current_refs[path] = put(path, (BASE/new).read_bytes())
            path_map['reports/releases/v0.9.2/acquisition/' + old] = path
        def role(name):
            for old, new in [('bridge18','bridge19'), ('replacement23','replacement24'),
                             ('protocol23','protocol24'), ('admission23','admission24'),
                             ('supervisor23','supervisor24'), ('runtime_loaders23','runtime_loaders24'),
                             ('stage_runtime10','stage_runtime11')]:
                name = name.replace(old,new)
            return name
        v['runtime_module_graph'] = {
            role(name):current_refs[path_map[ref['path']]] if ref['path'] in path_map else ref
            for name,ref in v['runtime_module_graph'].items()}
        # Additive candidate entries; actual BF16 source_inputs are immutable.
        v['source_inputs'] = sorted(v['source_inputs'] + [
            dict(ref,role='release-input') for ref in current_refs.values()], key=lambda ref:ref['path'])
        v['manifest_path'] = p.MANIFEST_PATH
        v['dispatch_groups']=list(p.DISPATCH_GROUPS)
        for fixture_ref in walk(SEALED_RESUME_HISTORY):copy_ref(fixture_ref)
        v['resume_history']=put('reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-24/resume-history.json', p.canonical_json(SEALED_RESUME_HISTORY))
        v['sidecar_namespace'] = 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-24'
        v['configuration_output'] = v['sidecar_namespace']+'/configuration/report-configurations.json'
        replacement['source_inputs'] = copy.deepcopy(v['source_inputs'])
        next(g for g in replacement['groups'] if g['id']=='bifrost-smoke')['maximum_attempts']=3
        contract_ref = put('reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-26-contract.json', p.canonical_json(replacement))
        # Only a private Git repository is initialized. Read-only object access
        # to the actual source commit proves every script ref against real blobs.
        subprocess.run(['git','init','-q',str(cls.root)], check=True)
        common = Path(subprocess.check_output(['git','rev-parse','--git-common-dir'], cwd=repository,
                                            text=True).strip())
        common = common if common.is_absolute() else repository/common
        (cls.root/'.git/objects/info/alternates').write_text(str((common/'objects').resolve())+'\n')
        r = load('full_core14_replacement05_constants', HISTORICAL_BASE/'bifrost-v0140-replacement-05.py')
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
        v['source_contexts']=copy.deepcopy(sealed['source_contexts'])
        for context in v['source_contexts'].values():
            if context['role']=='replacement':context['role']='historical'
        v['source_contexts'][contract_ref['sha256']]={'contract':contract_ref,'source_commit':v['source_commit'],'plan_commit':v['plan_commit'],'role':'replacement'}
        for key, path in {
            'implementation':'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-24.py',
            'implementation_test':'reports/releases/v0.9.2/acquisition/test-bifrost-v0140-replacement-24.py',
            'bifrost_admission_source':p.ADMISSION_SOURCE_PATH,
            'bifrost_supervisor_source':p.SUPERVISOR_SOURCE_PATH,
            'frozen_bridge_source':p.BRIDGE_SOURCE_PATH,
            'frozen_bridge_tests':p.BRIDGE_TEST_PATH,
        }.items():
            v[key] = put(path, (BASE/Path(path).name).read_bytes())
        for key in ('runner','binary'):
            if not Path(v[key]['path']).is_absolute():
                copy_ref({'path':v[key]['path'],'sha256':v[key]['sha256']})
        v['review_policy'] = {'schema':'v092-bifrost-v0140-review-policy/v1',
            'review_types':p.REVIEW_TYPES, 'reviewed_sources':dict(zip(p.SOURCE_NAMES,
                [v[k] for k in ('implementation','implementation_test','bifrost_admission_source',
                               'bifrost_supervisor_source','frozen_bridge_source','frozen_bridge_tests')]))}
        assert set(v) == p.CORE_FIELDS
        next(g for g in replacement['groups'] if g['id']=='bifrost-smoke')['maximum_attempts']=3
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
            with self.assertRaisesRegex(p.Replacement24Error, 'manifest path'):
                self.validate(value)
        value = self.clone(); del value['manifest_path']
        with self.assertRaisesRegex(p.Replacement24Error, 'field set'):
            self.validate(value)

    def test_nested_manifest_and_all_other_runtime_review_keys_reject(self):
        # Both permissive environment objects and arbitrarily deep list nesting
        # must reach the unchanged recursive prohibition after all prior gates.
        for field in sorted(p._FORBIDDEN_CORE_KEYS):
            value = self.clone()
            value['executor_environment']['nested_probe'] = [{'inner':{field:p.MANIFEST_PATH}}]
            with self.assertRaisesRegex(p.Replacement24Error, 'runtime/review field '+field):
                self.validate(value)

    def test_extra_root_runtime_review_fields_reject(self):
        for field in ('independent_review', 'permit', 'manifest_sha256', 'extra_field'):
            value = self.clone(); value[field] = 'forbidden'
            with self.assertRaisesRegex(p.Replacement24Error, 'field set'):
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
            with self.assertRaises(p.Replacement24Error):self.validate(value)




# Actual sealed107-history fixture; future a/b/c identifiers below are synthetic only.
import copy,hashlib,pathlib,shutil
D=BASE
SEALED_RESUME_HISTORY={'automatic_retry': False, 'batch_stop': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/batch-stop-18.json', 'sha256': 'b8673e2fc856291ebf64e74ec50ca5fddb55d3ce3d8505998e8a05ff434500a3'}, 'consumed_events': [{'admission': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/18-bifrost-smoke/admission.json', 'sha256': '2528161e372baeb437e070a5b29f390fe9bb1599d73c4a86cb2db2bb1c40346e'}, 'attempt_id': 'bifrost-smoke-attempt-02-series-02', 'classification': 'started-unclosed-unknown-interrupted', 'group_id': 'bifrost-smoke', 'phase_gate': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/18-bifrost-smoke/phase-gate.json', 'sha256': 'c488f5a33a9c198cc0f1388b7301ded254fcfd5596c730a261352b1510afa632'}, 'started': {'path': 'reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-02-series-02/started.json', 'sha256': 'd7cdfdc49b032e95f3404bb3cebd8ffc48819191cc518e813f9284c389a2025b'}, 'supervisor_permit': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/18-bifrost-smoke/supervisor-permit.json', 'sha256': '03647c2c9d543dde23237fc51d67fc72a0d648dc12777b918e1a6120cc85f838'}}], 'dispatch_groups': ['bifrost-smoke', 'bifrost-typescript-kernel'], 'ledger_prefix': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-18-ledger.jsonl', 'rows': 107, 'sha256': '38c71c33e13b28eff69fa6be8374ad8dd00c0cfb42e39625ffc01618272ea578'}, 'original89_prefix': {'path': 'reports/releases/v0.9.2/qualification/independent-pending-groups-01/sealed-ledger-prefix-89.jsonl', 'rows': 89, 'sha256': '11afe8706c33a2dfe8e0bc66a43f3cdca701bdfe8060dafd752f6c414282cfd6'}, 'retained_core': {'path': 'reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-23/manifest-identity.json', 'sha256': '7341166cf4c1f31d2c336385b2edd974ac68d2d84ea5d839641c5d1e3d22e643'}, 'retained_manifest': {'path': 'reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-23/manifest.json', 'sha256': 'd5e2b67910f5c7e7f5912dd87b7c9b363b5ba780330b4d9e85ba1761ecf69c1b'}, 'retained_outcomes': [{'attempt_id': 'bifrost-c-kernel-attempt-03-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/00-bifrost-c-kernel/completion.json', 'sha256': '8aea96ef1739625fa1ef630041ce5d375e3d3f7f31b6800cafb0e53ebc6c6335'}, 'group_id': 'bifrost-c-kernel', 'raw_line_sha256': '660bff9bab9b76871742f72901bdeaccb03000566f8f20a93dbc9af4cdd4d46c', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-01.json', 'sha256': '0bd245120c6824d3f50dbc24c14619bdc4a90fa24d66c000892076c12f334de8'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-c-kernel-attempt-03-series-02/completed.json', 'sha256': 'b9be7dda82be63d8dcb24faa0468413de15be9373cdaf47962513215e7d06bf5'}}, {'attempt_id': 'bifrost-cpp-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/01-bifrost-cpp-kernel/completion.json', 'sha256': '5c60f20b93b1947f4d354254adc53e6ad63160fe84895903c869fddf98bac696'}, 'group_id': 'bifrost-cpp-kernel', 'raw_line_sha256': '30e64daa2cff30784cdfc2448d4eaafa02c3db91dc18e346eac40426ffc893f5', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-02.json', 'sha256': '983b81f3aaa6ed2ae1ad9ec1d640a2058cde78b293e32c9092fda65589b2c28c'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-cpp-kernel-attempt-02-series-02/completed.json', 'sha256': 'a19e935a4984c35d708df1f350c03c7a89b24efc6cef3e707484d1f3ba3cdcc3'}}, {'attempt_id': 'bifrost-csharp-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/02-bifrost-csharp-kernel/completion.json', 'sha256': 'd5d20513e26ef84bb8b6f05408308c5ffa8d5015eb422f8937f7652d83ee9d8c'}, 'group_id': 'bifrost-csharp-kernel', 'raw_line_sha256': '365aeaaa892ca119f3243ae74c27c647278d2a4e9297f079b55c2db45d211e2d', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-03.json', 'sha256': '121179e88ff406d1e7b858717a1f3206aaaf613c053c9fad2005719f877bbbe2'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-csharp-kernel-attempt-02-series-02/completed.json', 'sha256': '5a247cc8d4cdd345203e819b70ce13a45beeb15ba31ea81de7c7d833c2a74e83'}}, {'attempt_id': 'bifrost-go-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/03-bifrost-go-kernel/completion.json', 'sha256': '2e1d56063e42e1d8f17eb65adb17cb29de419f3293e50237babf7437c342f68a'}, 'group_id': 'bifrost-go-kernel', 'raw_line_sha256': 'e4ff8dacf5e6cd03bea59f8a0b099b5334a887268170376e14b45b6455e856fd', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-04.json', 'sha256': '4f03c49399ae3ab52dc25d8603b597924c88e4fc42060156184f3c29c3f7facd'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-go-kernel-attempt-02-series-02/completed.json', 'sha256': '5034331a2c3d073c4049558f67226f8cec20f559c708c4c6ef364efe3008a94e'}}, {'attempt_id': 'bifrost-java-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/04-bifrost-java-kernel/completion.json', 'sha256': '861b76052cc0dd73a0e3ffde7a3756025b1cfaaac3c3cdbd247bb8cc884b165e'}, 'group_id': 'bifrost-java-kernel', 'raw_line_sha256': '20e061e599cccdfa51a61c25cca97d2877d970c3e451d2320c5233ebaa8c0493', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-05.json', 'sha256': '202e57a891271580d0a3eb82c951ddb05c887687063274b7c5d28f2c68d3186a'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-java-kernel-attempt-02-series-02/completed.json', 'sha256': 'adc9171e188c080a825d091cb206003acd1a6ef7d3be5c0bc03f11b41941423b'}}, {'attempt_id': 'bifrost-java-modeling-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/05-bifrost-java-modeling/completion.json', 'sha256': '45415984e89eac960ca898fcb64176ef2648cc3c040eba1608369d8d78a79b74'}, 'group_id': 'bifrost-java-modeling', 'raw_line_sha256': 'c63c6b901410f8b5163da4b7036d4354618210dff769aae994552bfd7253635f', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-06.json', 'sha256': '477a6a4bef42b730181e0487719588d1d48c14279da206ec5d36e5bb2362627c'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-java-modeling-attempt-02-series-02/completed.json', 'sha256': 'a7cd83ea69fb6d939f3a1fba10ee003986f3c6e73d843c038fb8d19999b70e52'}}, {'attempt_id': 'bifrost-java-native-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/06-bifrost-java-native/completion.json', 'sha256': '17906a48a6a32cce8696b43350ebea984640abf76d43215c189c08612d149e4d'}, 'group_id': 'bifrost-java-native', 'raw_line_sha256': 'b2a9148058b8e431bc6174186d387935a94706bdbc33f8442dc6640a9289ffee', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-07.json', 'sha256': '6325e5def27f92d8805ee92da5ed4c677b7c1ae5de24df8336954188018947e5'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-java-native-attempt-02-series-02/completed.json', 'sha256': 'aeaca9f9a7bf62bf98eeb29a85ac8580e7f1e9a8f9d2c209cf6096a04f5a0108'}}, {'attempt_id': 'bifrost-javascript-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/07-bifrost-javascript-kernel/completion.json', 'sha256': 'e58fe109fc62c1f34f5815f3026f7a40d262a4ec6a8554c768d0d1cf8f5b694f'}, 'group_id': 'bifrost-javascript-kernel', 'raw_line_sha256': '0469456f6ff12c353b919acdea8bb1f53284982af45952842349ea1173d4b832', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-08.json', 'sha256': '3c0e389120c8b866723e50c3fedd414e7c64f27a92098ae79fb621fda212e69a'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-javascript-kernel-attempt-02-series-02/completed.json', 'sha256': '115ca4f8adf3b8013d8ff8dffa33caf2020185f339992ec1790f6c8e19cf54ff'}}, {'attempt_id': 'bifrost-javascript-modeling-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/08-bifrost-javascript-modeling/completion.json', 'sha256': 'cb4e785702d53e453d035d4abf7f203b3fd2827b79cbe57d4b634d12cd662972'}, 'group_id': 'bifrost-javascript-modeling', 'raw_line_sha256': 'abf59c717bfc62a650c80d5b5a5198742b9d1152538bae7ec122914b068b153c', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-09.json', 'sha256': '87021c2f87f227ea4792ecc12121d509c6b1c0a39151918ec379a2757f6bc78d'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-javascript-modeling-attempt-02-series-02/completed.json', 'sha256': 'd67e91bab645037a5f1b78169911997e1673f0c0a522a462e568f990312b751e'}}, {'attempt_id': 'bifrost-javascript-native-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/09-bifrost-javascript-native/completion.json', 'sha256': 'c932d7cf07add658f3ecc9ddf2314bd6281ac5be328ffb23aeab3eadf01468ed'}, 'group_id': 'bifrost-javascript-native', 'raw_line_sha256': '2f7bf5ba7809e6b927dde70bf3b0ea4e9e2b604649624eb0f76c6dd55107bece', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-10.json', 'sha256': '4ec4fe10c418dff5bd261c35f2a6db784e48d5abdd30b5c5f024d4fdf46369a4'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-javascript-native-attempt-02-series-02/completed.json', 'sha256': '2a38de6613ffe27287b2fba55d0f6a539318290212cd3eda4677addb1a16b01a'}}, {'attempt_id': 'bifrost-kotlin-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/10-bifrost-kotlin-kernel/completion.json', 'sha256': '816238aa1b1dcb2c7b36b9459f8ddd63640e9b9ea4d92b78ff801709977a25a2'}, 'group_id': 'bifrost-kotlin-kernel', 'raw_line_sha256': 'cc5dbb5c4e0c3186d8da96c3cc26c9cdbb24034cf1e99f16a2e4fefab1719108', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-11.json', 'sha256': '51d8bcd8f94ae55b4a205aac132f1db0bbb26929824a897b8994c0080344b490'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-kotlin-kernel-attempt-02-series-02/completed.json', 'sha256': '39b9e5bc709a1dd5e55af5331bf7fbeb691f095edd7115ff64bf2869f652cc4c'}}, {'attempt_id': 'bifrost-php-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/11-bifrost-php-kernel/completion.json', 'sha256': '946ecd175f3572a5e03a8e3f6729e26e507cd0b34db61872152bddfea6811f68'}, 'group_id': 'bifrost-php-kernel', 'raw_line_sha256': '400321c0236ce7f0472f45955b549b4d1652000db74e429dc58d09561410a59c', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-12.json', 'sha256': 'e1eb6dcb7e3a946033187653bad2aac85b9b96b0cd5c72061a5b87849704b5b4'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-php-kernel-attempt-02-series-02/completed.json', 'sha256': '3ec7a4f7ca3796da20c903b64a0547d83056b4d833210d0b43872d228756ca46'}}, {'attempt_id': 'bifrost-python-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/12-bifrost-python-kernel/completion.json', 'sha256': '9928b7f89dbf773d2dd2d7994fffd3a32862901542be2ccaa4dc04247673660d'}, 'group_id': 'bifrost-python-kernel', 'raw_line_sha256': 'd82f6089436d736cf8d294b9df6890a5553a45c563373a9aaaed2dc116c6be4b', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-13.json', 'sha256': 'c36f21d9111703eb5d480c7004fdd642db3a5f3df984d20c5fd9844dada22f60'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-python-kernel-attempt-02-series-02/completed.json', 'sha256': '465fa2869cfa0597535af20b53e7458ac02e88189f9573306920f6f8342772b2'}}, {'attempt_id': 'bifrost-python-modeling-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/13-bifrost-python-modeling/completion.json', 'sha256': 'a4c265aefbaaf48f0613e8ad5f8eeac823d88d980be7aa7b6dea7906fada8267'}, 'group_id': 'bifrost-python-modeling', 'raw_line_sha256': 'afc1579162108162d8d2b4ad6397fde3c72da4cee2e696462b9a01e207870113', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-14.json', 'sha256': '552a064fb1ef6a74b938d480e4707954933c86889de26983dbfdf3240f5c28fe'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-python-modeling-attempt-02-series-02/completed.json', 'sha256': 'acda744718d30e6f13046e38563b23c4e788186256af7141a9dd30af74e98728'}}, {'attempt_id': 'bifrost-python-native-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/14-bifrost-python-native/completion.json', 'sha256': '1fee395e139c991d317785d46ea644a85a91f4e65eeec47bb1894a536da90be9'}, 'group_id': 'bifrost-python-native', 'raw_line_sha256': '9f11fbbf2b36759306fa07abe50fa37d97c0750fb24f9d5e3d80fded96c380be', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-15.json', 'sha256': '9c3dd42c1f31c77e339e0ba7758029d6c8462068147f0c9b16da870a02649aaf'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-python-native-attempt-02-series-02/completed.json', 'sha256': '9b24b452d64e806bce6d07bfd1ba863336d567e215b10c492991d8af33c16edc'}}, {'attempt_id': 'bifrost-ruby-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/15-bifrost-ruby-kernel/completion.json', 'sha256': '143543ef3d30fe5fea02d1fb67949839f999af60b9d59e2d0715dda20b3bf5ba'}, 'group_id': 'bifrost-ruby-kernel', 'raw_line_sha256': 'e5b4ab44083486d6b253a80fe37691f5848115afef20e87d40e22b310dc7c37f', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-16.json', 'sha256': 'd4c88d40be13bf89ffaa363ba2c297ec1b77c2ca95004997500b016faff6fa83'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-ruby-kernel-attempt-02-series-02/completed.json', 'sha256': '94b87595bde7c01f8f8e2a1f37e8a7e39f2a1d7544d99e2b4d938857abe7c8a4'}}, {'attempt_id': 'bifrost-rust-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/16-bifrost-rust-kernel/completion.json', 'sha256': '585ab77d32d6b9d1f72ef9bf154379eb03aaf2c5252eefb4d3162a5d30aa9ee0'}, 'group_id': 'bifrost-rust-kernel', 'raw_line_sha256': '52f65c67f27494acbb6121c8c991cfe297a66c7c812962b54817645300e61d52', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-17.json', 'sha256': 'ae6a91bfcf3c2ed47be51a81cf95aca1b40f4dd616ac269e36a47bac6f7e17f3'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-rust-kernel-attempt-02-series-02/completed.json', 'sha256': 'aa4228b15d2b984ec33b282d0b841e5ebc927bbf4b3bd47ba5050a024196f148'}}, {'attempt_id': 'bifrost-scala-kernel-attempt-02-series-02', 'completion': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/17-bifrost-scala-kernel/completion.json', 'sha256': '57e3ff223f49aae10d16f0be3eace76cfb15ca3fee16f8ab10e098361824ad21'}, 'group_id': 'bifrost-scala-kernel', 'raw_line_sha256': 'b52412186e0dd104f7e01a0a75a7f4f2be257a7d08625a763e0a971ba88285da', 'stage_after': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-18.json', 'sha256': 'f8739be253d23bb0d7080085973ae173373076f8e51e15852e58a7a2584a2d13'}, 'terminal': {'path': 'reports/releases/v0.9.2/attempts/bifrost-scala-kernel-attempt-02-series-02/completed.json', 'sha256': 'f23dc5504aa83d25e7145822347418c497a38197e4b172b2ff0f5ca3bbed7f3a'}}], 'retained_reconciliation': {'path': 'reports/releases/v0.9.2/validation/bifrost-v0140-replacement-23/retained18-terminal-reconciliation-01.json', 'sha256': '31f9503a0cf5664c7d4dd0e40af544dfe06ba4400de00f77676c1da055af6368'}, 'retained_stage18': {'path': 'reports/releases/v0.9.2/execution-v4/bifrost-v0140-replacement-23/stages/stage-18.json', 'sha256': 'f8739be253d23bb0d7080085973ae173373076f8e51e15852e58a7a2584a2d13'}, 'schema': 'v092-bifrost-v0140-resume-history/v1', 'stop_diagnosis': {'path': 'reports/releases/v0.9.2/validation/bifrost-v0140-replacement-23/smoke-timeout-stop-diagnosis-01.json', 'sha256': 'feb2b7a69a86af3ca2d445501de22aa6abd3ec284845b67a5ce2c38484a58480'}, 'stop_review': {'path': 'reports/releases/v0.9.2/validation/bifrost-v0140-replacement-23/smoke-timeout-independent-review-01.json', 'sha256': 'b1f8a249ee5f9d58055c99f81cfa3b6324e68d26a88258e064c7663b65010bb9'}}
e=load('canonical_frozen_executor',ROOT/'scripts/execute-release-v092.py')
c=load('canonical_frozen_checker',ROOT/'scripts/check-release-v092.py')
r=load('canonical_replacement05',HISTORICAL_BASE/'bifrost-v0140-replacement-05.py')
def rawjson(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def walk(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:yield v
  else:
   for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
class RealFunctions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='bf24-registry-fixture-');cls.root=pathlib.Path(cls.temp.name).resolve()
  cls.h=copy.deepcopy(SEALED_RESUME_HISTORY)
  old=json.loads((ROOT/cls.h['retained_core']['path']).read_bytes());cls.old=old
  refs=list(walk(cls.h))+[old['contract']]
  # Exact byte copies, never hard links or symlinks to production evidence.
  for ref in refs:
   dst=cls.root/ref['path'];dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists():shutil.copyfile(ROOT/ref['path'],dst)
  dst=cls.root/p.LEDGER_PATH;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p.LEDGER_PATH,dst)
  cls.hpath='reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-24/resume-history.json'
  cls.core=copy.deepcopy(old);cls.core['source_commit']='a'*40;cls.core['plan_commit']='b'*40
  cls.core['contract']={'path':'reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-26-contract.json','sha256':'c'*64}
  cls.core['dispatch_groups']=list(p.DISPATCH_GROUPS)
  for v in cls.core['source_contexts'].values():
   if v['role']=='replacement':v['role']='historical'
  cls.core['source_contexts']['c'*64]={'contract':cls.core['contract'],'source_commit':'a'*40,'plan_commit':'b'*40,'role':'replacement'}
  cls.install_history(cls.h)
  cls.raw=(cls.root/p.LEDGER_PATH).read_bytes();cls.rows=[json.loads(x) for x in cls.raw.splitlines()]
  cls.contexts={k:{**v} for k,v in cls.core['source_contexts'].items()}
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 @classmethod
 def install_history(cls,h):
  data=rawjson(h);dst=cls.root/cls.hpath;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
  cls.core['resume_history']={'path':cls.hpath,'sha256':digest(data)}
 def tearDown(self):
  self.install_history(self.h);(self.root/p.LEDGER_PATH).write_bytes(self.raw)
 def test_01_real_history_provenance(self):
  x=p.validate_resume_history(self.root,self.core);self.assertEqual((len(x['rows']),len(x['consumed_attempt_ids'])),(107,1));self.assertEqual(x['retained_contract']['source_commit'],self.old['source_commit'])
 def test_02_missing_extra_unknown_event_denied(self):
  for edit in ('missing','duplicate','unknown','foreign'):
   h=copy.deepcopy(self.h)
   if edit=='missing':h['consumed_events']=[]
   elif edit=='duplicate':h['consumed_events']*=2
   elif edit=='unknown':h['consumed_events'][0]['unsupported']='x'
   else:h['consumed_events'][0]['attempt_id']='bifrost-smoke-attempt-03-series-02'
   self.install_history(h)
   with self.subTest(edit=edit),self.assertRaises(ValueError):p.validate_resume_history(self.root,self.core)
 def test_03_hash_and_symlink_denied(self):
  target=self.root/self.h['consumed_events'][0]['started']['path'];original=target.read_bytes()
  try:
   target.write_bytes(original+b' ')
   with self.assertRaises(ValueError):p.validate_resume_history(self.root,self.core)
   target.unlink();target.symlink_to(ROOT/self.h['consumed_events'][0]['started']['path'])
   with self.assertRaises(ValueError):p.validate_resume_history(self.root,self.core)
  finally:
   target.unlink();target.write_bytes(original)
 def test_04_orphan_terminal_cannot_be_inferred(self):
  target=self.root/self.h['consumed_events'][0]['started']['path'];target=target.with_name('completed.json');target.write_bytes(b'{}\n')
  try:
   with self.assertRaises(ValueError):p.validate_resume_history(self.root,self.core)
  finally:target.unlink()
 def test_05_real_frozen_freshness_selects03_then02_and_restores(self):
  original,paths=e._assert_fresh,e._attempt_paths
  for group,n in zip(p.DISPATCH_GROUPS,(3,2)):
   g={'id':group,'maximum_attempts':n}
   (self.root/p.LEDGER_PATH).write_bytes(self.raw+(p.canonical_json(self.tail('bifrost-smoke')) if group==p.DISPATCH_GROUPS[1] else b''))
   if group=='bifrost-smoke':
    with self.assertRaises(e.ReleaseError):original(self.root,g,[],2)
   with p.scoped_consumed_freshness(e,self.root,self.core,group):
    selected=e._assert_fresh(self.root,g,[],2);self.assertEqual(selected[-1],f'{group}-attempt-{n:02d}-series-02');self.assertIs(e._attempt_paths,paths)
   self.assertIs(e._assert_fresh,original);self.assertIs(e._attempt_paths,paths)
 def test_06_real_freshness_preserves_all_collision_checks(self):
  group='bifrost-smoke';g={'id':group,'maximum_attempts':3};paths=e._attempt_paths(self.root,group,2,3)
  for target in paths[:3]:
   target.mkdir(parents=True)
   try:
    with p.scoped_consumed_freshness(e,self.root,self.core,group),self.assertRaises(e.ReleaseError):e._assert_fresh(self.root,g,[],2)
   finally:target.rmdir()
  report={'path':str(e.NORMAL_ROOT/'fixture.json')}
  staged=self.root/'reports/releases/v0.9.2/normal/attempts'/p._attempt_id(group)/'fixture.json';staged.parent.mkdir(parents=True);staged.write_bytes(b'{}')
  try:
   with p.scoped_consumed_freshness(e,self.root,self.core,group),self.assertRaises(e.ReleaseError):e._assert_fresh(self.root,g,[report],2)
  finally:staged.unlink()
 def test_07_scope_rejects_caps_othergroup_and_restores_on_exception(self):
  original=e._assert_fresh
  with self.assertRaises(ValueError):
   with p.scoped_consumed_freshness(e,self.root,self.core,'bifrost-smoke'):e._assert_fresh(self.root,{'id':'bifrost-smoke','maximum_attempts':2},[],2)
  self.assertIs(e._assert_fresh,original)
  with self.assertRaises(ValueError):
   with p.scoped_consumed_freshness(e,self.root,self.core,'bifrost-java-kernel'):pass
 def test_08_real_directory_checker_exact_union(self):
  ids=p.resume_attempt_directory_ids(self.root,self.core,self.rows)
  for identity in ids:(self.root/pathlib.Path(*c.ATTEMPTS_ROOT.parts)/identity).mkdir(parents=True,exist_ok=True)
  with self.assertRaises(c.EvidenceError):c._assert_attempt_directories(self.root,{x['attempt_id'] for x in self.rows})
  c._assert_attempt_directories(self.root,ids)
  extra=self.root/pathlib.Path(*c.ATTEMPTS_ROOT.parts)/'foreign-attempt';extra.mkdir()
  try:
   with self.assertRaises(c.EvidenceError):c._assert_attempt_directories(self.root,ids)
  finally:extra.rmdir()
 def tail(self,group,status='completed'):
  value=copy.deepcopy(self.rows[-1]);value.update({'group_id':group,'attempt_id':p._attempt_id(group),'tool':'bifrost','execution_series':2,'contract_sha256':'c'*64,'source_commit':'a'*40,'plan_commit':'b'*40,'status':status,'exit_code':0 if status=='completed' else 1,'capacity_loss':None,'timed_out':False});return value
 def test_09_actual_context_checker107_boundary_and_no_fallback(self):
  context={'replacement':r,'contexts':self.contexts}
  p.check_resume_rows_context(r,self.root,self.core,self.rows,self.contexts)
  with self.assertRaises(ValueError):r._check_rows_context(self.rows,self.contexts,'c'*64,'a'*40,'b'*40,89)
  self.assertEqual(len(p.select_resume_rows(self.root,self.core,context,self.rows)),81)
  rows=self.rows+[self.tail(p.DISPATCH_GROUPS[0],'failed')]
  selected=p.select_resume_rows(self.root,self.core,context,rows);self.assertEqual(len(selected),81);self.assertNotIn('bifrost-smoke',selected)
  rows=self.rows+[self.tail(x) for x in p.DISPATCH_GROUPS]
  self.assertEqual(len(p.select_resume_rows(self.root,self.core,context,rows,final=True)),83)
 def test_10_context_tail_order_attempt_foreign_denied(self):
  for mutation in ('order','attempt','context','unknown'):
   tail=self.tail(p.DISPATCH_GROUPS[0])
   if mutation=='order':tail=self.tail(p.DISPATCH_GROUPS[1])
   elif mutation=='attempt':tail['attempt_id']=p.ORPHAN_ID
   elif mutation=='context':tail['source_commit']='d'*40
   else:tail['status']='mystery'
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):p.check_resume_rows_context(r,self.root,self.core,self.rows+[tail],self.contexts)
 
 def test_11_real_parent_successor_child_source_and_ledger_boundaries(self):
  # Real constructors/opaque types and exact inventory readers. Only runtime
  # acquisition is a fixture graph seam; no copied historical validator is run.
  import types
  b=load('private_bridge19_constructor',D/'bifrost-v0140-frozen-bridge-19.py')
  root=self.root
  refs={};modules={}
  for i,name in enumerate(b.REQUIRED_GRAPH_NAMES):
   path=f'fixturegraph/{i}-{name}.py';target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f'fixture={i}\n'.encode())
   refs[name]={'path':path,'sha256':digest(target.read_bytes())};modules[name]=types.ModuleType('fixture_'+name);modules[name].__file__=str(target)
  def runtime_loader(*,mode,core,graph,ledger_bytes=None):
   raw=(root/p.LEDGER_PATH).read_bytes() if ledger_bytes is None else ledger_bytes;rows=[json.loads(x) for x in raw.splitlines()]
   m={name:graph.module(name) for name in b.REQUIRED_GRAPH_NAMES};diag={'ledger_sha256':digest(raw),'ledger_rows':len(rows),'context_digest':digest(raw)}
   return b.ActualRuntimeContext(root=root,mode=mode,graph=graph,modules=m,diagnostic=diag,objects={'modules':m,'bridge_context':diag,'mixed_context':{'rows':rows}})
  modules['bridge19'].load_runtime_context=runtime_loader
  graph=b.load_graph(root,refs,fixture_modules=modules,fixture_only=True)
  def put(path,raw):
   target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);return {'path':path,'sha256':digest(raw)}
  src=put('fixturegraph/source.bin',b'typed source')
  typed={**src,'role':'release-input'}
  contract=put('fixturegraph/contract.json',rawjson({'source_commit':'a'*40,'source_inputs':[typed]}))
  core={'runtime_module_graph':refs,'source_commit':'a'*40,'plan_commit':'b'*40,'contract':contract,'source_inputs':[typed],'analyzer_deadline_seconds':706,'resume_history':self.core['resume_history']}
  lockfile=root/'fixturegraph/canonical.lock';lockfile.write_bytes(b'held');lock=b.capture_lock(root,str(lockfile),101,'fixturebirth')
  manifest=put('fixturegraph/manifest.json',b'{}\n');side=put('fixturegraph/parent-admission.json',b'{}\n')
  ledger={'path':p.LEDGER_PATH,'sha256':digest(self.raw),'rows':107}
  parent=b.create_parent_stage(root,core,manifest,0,lock,ledger,sidecars={'admission':side},graph=graph)
  self.assertEqual((parent.identity.index,parent.identity.ledger_rows),(0,107))
  dispatch={'fixturegraph/child/'+name+'.json':put('fixturegraph/child/'+name+'.json',b'{}\n') for name in ('admission','phase','supervisor-permit')}
  lease=b.Lease(100.0,706.0,b.STARTUP_SECONDS);birth={'creator_pid':101,'creator_birth':'creator','pid':102,'birth':'child'}
  # Exact real child consumer demands positive integer rows (the BF22 stop).
  with self.assertRaises(b.FrozenBridge19Error):b.create_child_stage(root,core,manifest,parent,lock,lease,birth,{k:v for k,v in ledger.items() if k!='rows'},sidecars=dispatch,graph=graph)
  child=b.create_child_stage(root,core,manifest,parent,lock,lease,birth,ledger,sidecars=dispatch,graph=graph)
  self.assertEqual(child.identity.ledger_rows,107)
  previous=parent
  for index in (1,2):
   raw=self.raw+b''.join(b.canonical_json(self.tail(g)) for g in p.DISPATCH_GROUPS[:index])
   after=put(f'fixturegraph/after{index}.jsonl',raw)|{'rows':107+index}
   stage=b.create_parent_stage(root,core,manifest,index,lock,after,sidecars={'phase':side},predecessor=previous,graph=graph)
   self.assertEqual(stage.identity.ledger_rows,107+index);previous=stage
  with self.assertRaises(b.FrozenBridge19Error):b.create_parent_stage(root,core,manifest,3,lock,after,sidecars={'phase':side},predecessor=previous,graph=graph)
  # Strict generic refs still reject source-record metadata.
  with self.assertRaises(b.FrozenBridge19Error):b._ref(typed,'generic ref')
  wrong={**typed,'role':'generated'}
  with self.assertRaises(b.FrozenBridge19Error):b._core_source_refs(root,{**core,'source_inputs':[wrong]})

 def test_12_actual_run_group_reaches_real_freshness03_before_any_allocation(self):
  import contextlib,time
  from unittest.mock import patch
  class BeforeAttemptAllocation(Exception):pass
  for group_id,number in zip(p.DISPATCH_GROUPS,(3,2)):
   (self.root/p.LEDGER_PATH).write_bytes(self.raw+(p.canonical_json(self.tail('bifrost-smoke')) if group_id==p.DISPATCH_GROUPS[1] else b''))
   group={'id':group_id,'maximum_attempts':number,'deadline_seconds':706,'tool':'bifrost','reports':[]}
   plan={'execution_authorized':True,'groups':[group],'source_commit':'a'*40,'runner_source_sha256':'d'*64,'population':{'path':'fixture.json','sha256':'e'*64},'resource_reservation':{'exclusive_analyzer_slot':True,'expires_at_unix_seconds':time.time()+1000},'resource_budget':{'minimum_launch_free_gib':127},'execution_series':2}
   validated={'plan':plan,'repo_root':self.root,'groups':[group],'source_inputs':[],'tools':{},'total_wall_budget_seconds':1000}
   expected=e._attempt_paths(self.root,group_id,2,number)[0];mkdir=pathlib.Path.mkdir;seen=[]
   def allocation(path,*args,**kwargs):
    if path==expected:seen.append(path);raise BeforeAttemptAllocation()
    return mkdir(path,*args,**kwargs)
   # Upstream source/acquisition/resource I/O only. Real run_group, real
   # _assert_fresh, real _attempt_paths and narrow scoped adapter all execute.
   with patch.object(e,'_require_group_qualification',return_value={}),patch.object(e,'_exclusive_lock',return_value=contextlib.nullcontext()),patch.object(e,'_assert_contract_snapshot',return_value='b'*40),patch.object(e,'_matrix_elapsed_wall',return_value=0),patch.object(e,'_assert_source_snapshot',return_value=None),patch.object(e,'_source_file',return_value=None),patch.object(e,'_check_resources',return_value=None),patch.object(pathlib.Path,'mkdir',new=allocation):
    with p.scoped_consumed_freshness(e,self.root,self.core,group_id),self.assertRaises(BeforeAttemptAllocation):e.run_group(validated,group_id)
   self.assertEqual(seen,[expected]);self.assertFalse(expected.exists())

 def test_13_strict_registry_all_boundaries_reject_foreign_tail(self):
  foreign=self.tail('bifrost-smoke');foreign['group_id']='bifrost-foreign-group';foreign['attempt_id']='bifrost-foreign-group-attempt-02-series-02'
  raw=self.raw+p.canonical_json(foreign);(self.root/p.LEDGER_PATH).write_bytes(raw)
  for call in (lambda:p.validate_resume_history(self.root,self.core),lambda:p.resume_attempt_directory_ids(self.root,self.core,self.rows+[foreign])):
   with self.assertRaises(ValueError):call()
  original=e._assert_fresh
  with self.assertRaises(ValueError):
   with p.scoped_consumed_freshness(e,self.root,self.core,'bifrost-smoke'):pass
  self.assertIs(e._assert_fresh,original)
 def test_14_supplied_directory_rows_and_failure_order_rejected(self):
  # Live exact107 does not authorize a foreign separately supplied inventory.
  foreign=self.tail('bifrost-smoke');foreign['source_commit']='d'*40
  with self.assertRaises(ValueError):p.resume_attempt_directory_ids(self.root,self.core,self.rows+[foreign])
  rows=self.rows+[self.tail('bifrost-smoke','failed'),self.tail('bifrost-typescript-kernel')]
  for call in (lambda:p.check_resume_rows_context(r,self.root,self.core,rows,self.contexts),lambda:p.resume_attempt_directory_ids(self.root,self.core,rows)):
   with self.assertRaises(ValueError):call()
  (self.root/p.LEDGER_PATH).write_bytes(self.raw+b''.join(p.canonical_json(x) for x in rows[107:]))
  with self.assertRaises(ValueError):p.validate_resume_history(self.root,self.core)
 def test_15_typescript_freshness_requires_completed_smoke(self):
  for tail in ([],[self.tail('bifrost-smoke','failed')]):
   (self.root/p.LEDGER_PATH).write_bytes(self.raw+b''.join(p.canonical_json(x) for x in tail))
   with self.assertRaises(ValueError):
    with p.scoped_consumed_freshness(e,self.root,self.core,'bifrost-typescript-kernel'):pass
 def test_16_actual_origin_context_binds_explicit_and_normalized_source(self):
  stage=load('source_bound_stage11_revision02',D/'bifrost-v0140-stage-runtime-11.py');row=self.rows[0]
  origin={'validated':{'bytes_sha256':row['contract_sha256'],'plan':{'source_commit':row['source_commit']}},'source_commit':row['source_commit'],'plan_commit':row['plan_commit'],'role':'historical'}
  context={'contexts':{row['contract_sha256']:origin}}
  self.assertIs(stage._origin_context(context,row),origin)
  origin['source_commit']='f'*40
  with self.assertRaises(ValueError):stage._origin_context(context,row)




def load_current_fixture():
    """Return current24 fixture class; caller owns setUpClass/tearDownClass lifecycle.

    This is an I/O fixture boundary only, not a production stage/qualification.
    """
    import types
    opaque=load('canonical_current24_opaque_fixture',BASE/'test-bifrost-v0140-frozen-parser-19.py')
    return types.SimpleNamespace(RealFunctions=RealFunctions,ChildReadyReceiptTests=opaque.ChildReadyReceiptTests,p=p,e=e,r=r,rawjson=rawjson,digest=digest)

if __name__=='__main__':unittest.main()
