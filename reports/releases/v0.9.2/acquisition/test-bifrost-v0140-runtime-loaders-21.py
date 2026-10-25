#!/usr/bin/env python3
"""Synthetic exact frozen loader call sites; no analyzer or production replay."""
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
spec = importlib.util.spec_from_file_location("bf21_runtime_loaders_tests", BASE / "bifrost-v0140-runtime-loaders-21.py")
h = importlib.util.module_from_spec(spec); sys.modules[spec.name] = h; spec.loader.exec_module(h)


class Graph:
    def __init__(self, members): self.members = members
    def assert_member(self, name, module):
        if not any(m.name == name and m.module_object is module for m in self.members):
            raise h.RuntimeLoaders21Error("foreign graph member")


class RuntimeLoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name).resolve()
        self.members = []
        self.e = types.ModuleType("synthetic_frozen_executor")
        self.e.__file__ = str(self.root / "scripts/execute-release-v092.py")
        self.e.Path = Path; self.e.importlib = importlib; self.e.ReleaseError = ValueError
        frozen = (ROOT / "scripts/execute-release-v092.py").read_text()
        tree = ast.parse(frozen)
        tracker = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_process_tracker")
        # Compile the actual frozen function, not a test reimplementation.
        exec(compile(ast.Module(body=[tracker], type_ignores=[]), "actual-frozen-tracker", "exec"), self.e.__dict__)
        run_group = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_group")
        c4 = next(n for n in ast.walk(run_group) if isinstance(n, ast.If) and
                  isinstance(n.test, ast.Name) and n.test.id == "c4" and n.body and
                  isinstance(n.body[0], ast.Assign) and isinstance(n.body[0].value, ast.Call) and
                  ast.unparse(n.body[0].value.func) == "importlib.util.spec_from_file_location")
        # Exact inline disk spec/module/exec block used by run_group.
        disk = ast.FunctionDef(name="disk", args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],
                            kw_defaults=[],defaults=[]), body=c4.body[:4]+[ast.Return(ast.Name("disk_guard_module",ast.Load()))],
                            decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[disk], type_ignores=[])),
                     "actual-frozen-disk-loader", "exec"), self.e.__dict__)
        self.add("executor", "scripts/execute-release-v092.py", self.e, frozen.encode())
        self.tracker = types.ModuleType("already_loaded_tracker")
        self.disk = types.ModuleType("already_loaded_disk")
        self.add("tracker", h.LOADERS["v092_process_tracker"], self.tracker, b"raise RuntimeError('must not reexecute')\n")
        self.add("disk_guard", h.LOADERS["v092_disk_guard_runtime"], self.disk, b"raise RuntimeError('must not reexecute')\n")
        self.add("runtime_loaders21", "reports/releases/v0.9.2/acquisition/bifrost-v0140-runtime-loaders-21.py", h,
                 Path(h.__file__).read_bytes(), set_file=False)
        self.graph = Graph(self.members)
        self.original = self.e.importlib

    def add(self, name, path, module, data, set_file=True):
        p = self.root / path; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        if set_file: module.__file__ = str(p)
        self.members.append(types.SimpleNamespace(name=name,canonical_path=path,
            source_sha256=hashlib.sha256(data).hexdigest(),module_object=module))

    def tearDown(self): self.tmp.cleanup()

    def scope(self, **kwargs): return h.scoped_runtime_loaders(self.root,executor=self.e,graph=self.graph,**kwargs)

    def test_actual_frozen_tracker_and_disk_reuse_graph_identity(self):
        original_util = importlib.util
        with self.scope():
            self.assertIs(self.e._process_tracker(),self.tracker)
            self.assertIs(self.e._process_tracker(),self.tracker)
            self.assertIs(self.e.disk(),self.disk)
            self.assertIs(importlib.util,original_util)
        self.assertIs(self.e.importlib,self.original)

    def test_actual_executor_loader_bodies_use_all_late_routes_before_downstream(self):
        """Exercise the frozen callers, stopping only at their evidence readers.

        The loader map is already covered by direct spec tests.  This regression
        additionally compiles the unchanged executor bodies that request the
        packet/resource/checker modules and lets their real importlib call sites
        resolve the graph members.  Their first downstream packet validation is
        a harmless sentinel, so no historical replay or analyzer work occurs.
        """
        frozen = (ROOT / "scripts/execute-release-v092.py").read_text()
        tree = ast.parse(frozen)
        for name in ("_scoped_recovery_module", "_validate_scoped_recovery",
                     "_validate_resource_recovery"):
            function = next(node for node in tree.body
                            if isinstance(node, ast.FunctionDef) and node.name == name)
            exec(compile(ast.fix_missing_locations(
                ast.Module(body=[function], type_ignores=[])),
                "actual-frozen-loader-bodies", "exec"), self.e.__dict__)

        def add_actual(name, relative):
            module = types.ModuleType(name)
            data = (ROOT / relative).read_bytes()
            self.add(name, relative, module, data)
            return module

        packet = add_actual("nested_020_v092_scoped_recovery_packet",
                            "scripts/v092_scoped_recovery.py")
        resource = add_actual("nested_021_v092_resource_recovery",
                              "scripts/v092_resource_recovery.py")
        scoped_checker = add_actual("nested_022_check_release_v092_scoped_replay",
                                    "scripts/check-release-v092.py")
        resource_checker = add_actual("nested_023_check_release_v092_resource_replay",
                                      "scripts/check-release-v092.py")
        # The fixture already owns the tracker/disk objects used by the
        # direct-body tests; register the production graph role names as
        # aliases to those exact objects rather than creating a second object.
        for role, existing_name in (
                ("nested_024_v092_process_tracker", "tracker"),
                ("nested_025_v092_disk_guard_runtime", "disk_guard")):
            original = next(member for member in self.members if member.name == existing_name)
            self.members.append(types.SimpleNamespace(
                name=role,
                canonical_path=original.canonical_path,
                source_sha256=original.source_sha256,
                module_object=original.module_object,
            ))

        class PacketRejected(RuntimeError):
            pass

        class ResourceRejected(RuntimeError):
            pass

        packet.ScopedRecoveryError = PacketRejected
        packet.validate_packet = lambda *args: (_ for _ in ()).throw(
            PacketRejected("packet sentinel"))
        resource.ResourceRecoveryError = ResourceRejected
        resource.validate_packet = lambda *args: (_ for _ in ()).throw(
            ResourceRejected("resource sentinel"))
        selected = dict(h.PRODUCTION_MODULE_NAMES)
        original_importlib = self.e.importlib
        with self.assertRaisesRegex(ValueError, "scoped recovery packet rejected"):
            with self.scope(module_names=selected):
                self.assertIs(self.e._scoped_recovery_module(), packet)
                self.e._validate_scoped_recovery({"repo_root": self.root,
                                                  "plan": {}})
        self.assertIs(self.e.importlib, original_importlib)

        with self.assertRaisesRegex(ValueError, "resource recovery packet rejected"):
            with self.scope(module_names=selected):
                self.e._validate_resource_recovery({
                    "repo_root": self.root,
                    "plan": {"resource_recovery": {}},
                })
        self.assertIs(self.e.importlib, original_importlib)
        # The two checker roles are distinct graph instances even though their
        # frozen source path is intentionally shared.
        self.assertIsNot(scoped_checker, resource_checker)

    def test_exception_restores_exact_executor_binding(self):
        with self.assertRaisesRegex(RuntimeError,"consumer"):
            with self.scope(): raise RuntimeError("consumer")
        self.assertIs(self.e.importlib,self.original)

    def test_source_mutation_rejected_at_each_loader_use(self):
        with self.scope():
            (self.root / h.LOADERS["v092_process_tracker"]).write_text("changed")
            with self.assertRaisesRegex(h.RuntimeLoaders21Error,"SHA"):
                self.e._process_tracker()

    def test_wrong_initial_source_rejected_before_scope(self):
        (self.root / h.LOADERS["v092_disk_guard_runtime"]).write_text("changed")
        with self.assertRaises(h.RuntimeLoaders21Error):
            with self.scope(): self.fail("entered")
        self.assertIs(self.e.importlib,self.original)

    def test_unknown_loader_and_wrong_path_rejected(self):
        with self.scope():
            for name,path in (("other",self.root/"scripts/other.py"),
                              ("v092_disk_guard_runtime",self.root/"other/v092_disk_guard.py")):
                with self.assertRaises(h.RuntimeLoaders21Error):
                    self.e.importlib.util.spec_from_file_location(name,path)

    def test_foreign_spec_and_module_rejected(self):
        with self.scope():
            with self.assertRaises(h.RuntimeLoaders21Error): self.e.importlib.util.module_from_spec(object())
            with self.assertRaises(h.RuntimeLoaders21Error): self.e.importlib.util.exec_module(types.ModuleType("foreign"))

    def test_foreign_executor_or_scope_module_rejected(self):
        for role in ("executor","runtime_loaders21"):
            m=next(m for m in self.members if m.name==role); old=m.module_object; m.module_object=object()
            with self.assertRaises(h.RuntimeLoaders21Error):
                with self.scope(): self.fail("entered")
            m.module_object=old

    def test_symlink_source_rejected(self):
        p=self.root/h.LOADERS["v092_process_tracker"]; data=p.read_bytes(); p.unlink()
        target=self.root/"target.py";target.write_bytes(data);p.symlink_to(target)
        with self.assertRaises(h.RuntimeLoaders21Error):
            with self.scope(): self.fail("entered")

    def test_nested_scope_rejected_outer_restored(self):
        with self.scope():
            with self.assertRaisesRegex(h.RuntimeLoaders21Error,"already active"):
                with self.scope(): self.fail("entered")
            self.assertIs(self.e.disk(),self.disk)
        self.assertIs(self.e.importlib,self.original)

    def test_explicit_alias_selection_is_exact(self):
        alias=types.ModuleType("second_tracker");alias.__file__=self.tracker.__file__
        original=next(m for m in self.members if m.name=="tracker")
        self.members.append(types.SimpleNamespace(**{**vars(original),"name":"tracker_alias","module_object":alias}))
        with self.scope(module_names={"v092_process_tracker":"tracker_alias"}):
            self.assertIs(self.e._process_tracker(),alias)
        with self.assertRaises(h.RuntimeLoaders21Error):
            with self.scope(module_names={"v092_process_tracker":"disk_guard"}): self.fail("entered")

    def test_ambiguous_alias_without_explicit_selection_fails_closed(self):
        original = next(m for m in self.members if m.name == "tracker")
        self.members.append(types.SimpleNamespace(**{**vars(original), "name": "other_tracker"}))
        with self.assertRaisesRegex(h.RuntimeLoaders21Error, "ambiguous"):
            with self.scope(): self.fail("entered")
        self.assertIs(self.e.importlib, self.original)

    def test_all_six_explicit_production_roles_return_exact_distinct_instances(self):
        self.assertEqual(set(h.PRODUCTION_MODULE_NAMES), set(h.LOADERS))
        modules = {}
        for name, role in h.PRODUCTION_MODULE_NAMES.items():
            path = h.LOADERS[name]
            existing = next((m for m in self.members if m.canonical_path == path), None)
            data = (self.root / path).read_bytes() if existing else b"raise RuntimeError('no execution')\n"
            module = types.ModuleType(role)
            self.add(role, path, module, data)
            modules[name] = module
        with self.scope(module_names=h.PRODUCTION_MODULE_NAMES):
            for name, module in modules.items():
                spec = self.e.importlib.util.spec_from_file_location(name, self.root / h.LOADERS[name])
                self.assertIs(self.e.importlib.util.module_from_spec(spec), module)
                self.e.importlib.util.exec_module(module)
            self.assertIsNot(modules["check_release_v092_scoped_replay"],
                             modules["check_release_v092_resource_replay"])

    def test_foreign_same_path_role_selection_is_rejected(self):
        with self.assertRaisesRegex(h.RuntimeLoaders21Error, "requested helper"):
            with self.scope(module_names={"v092_process_tracker": "missing_role"}):
                self.fail("entered")
        self.assertIs(self.e.importlib, self.original)

    def test_binding_tamper_restores_and_rejects(self):
        with self.assertRaisesRegex(h.RuntimeLoaders21Error,"binding changed"):
            with self.scope(): self.e.importlib=object()
        self.assertIs(self.e.importlib,self.original)


if __name__ == "__main__": unittest.main()
