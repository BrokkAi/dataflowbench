from __future__ import annotations

import hashlib
import importlib.util
import ast
from pathlib import Path
import sys
import unittest
from unittest import mock


SOURCE = Path(__file__).with_name("command_path_amendment_01.py")
SPEC = importlib.util.spec_from_file_location("command_path_amendment_01_tested", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROOT = Path(__file__).resolve().parents[6]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def command(*, path: str, argv: list[str] | None = None,
            environment: dict[str, str] | None = None) -> dict:
    return {
        "argv": argv if argv is not None else ["/tool/frontend", "<CAPTURE>/input.swift"],
        "cwd": "/tmp/<CAPTURE>",
        "environment": environment if environment is not None else {
            "JAVA_HOME": "/java", "PATH": path, "SWIFTASTGEN_BIN": "/swift/bin",
            "_JAVA_OPTIONS": "",
        },
        "measurement_wrapper": [],
        "phase_id": "frontend",
        "role": "frontend",
        "deadline_scope": "phase",
    }


class CommandPathDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_path = "/historical/java/bin:/historical/tools"
        self.new_path = "/sanitized/java/bin:/usr/bin"
        self.old = command(path=self.old_path)
        self.new = command(path=self.new_path)

    def _check(self, old: dict, new: dict) -> str:
        with (mock.patch.object(MODULE, "EXPECTED_OLD_PATH_SHA256", digest(self.old_path)),
              mock.patch.object(MODULE, "EXPECTED_NEW_PATH", self.new_path),
              mock.patch.object(MODULE, "EXPECTED_NEW_PATH_SHA256", digest(self.new_path))):
            return MODULE._matches_path_delta(old, new, "/old/capture", "/new/capture")

    def test_accepts_only_the_bound_path_value_delta(self) -> None:
        self.assertEqual(self._check(self.old, self.new), self.old_path)

    def test_rejects_unreviewed_old_path_digest(self) -> None:
        with self.assertRaises(MODULE.CommandPathError):
            MODULE._matches_path_delta(self.old, self.new, "/old/capture", "/new/capture")

    def test_rejects_near_miss_native_path(self) -> None:
        changed = {**self.new, "environment": dict(self.new["environment"])}
        changed["environment"]["PATH"] += ":/extra"
        with self.assertRaises(MODULE.CommandPathError):
            self._check(self.old, changed)

    def test_rejects_added_or_changed_recorded_environment_values(self) -> None:
        added = {**self.new, "environment": dict(self.new["environment"])}
        added["environment"]["EXTRA"] = "value"
        changed = {**self.new, "environment": dict(self.new["environment"])}
        changed["environment"]["JAVA_HOME"] = "/different/java"
        with self.assertRaises(MODULE.CommandPathError):
            self._check(self.old, added)
        with self.assertRaises(MODULE.CommandPathError):
            self._check(self.old, changed)

    def test_rejects_non_path_command_input_changes(self) -> None:
        changed_argv = {**self.new, "argv": ["/tool/frontend", "different.swift"]}
        changed_wrapper = {**self.new, "measurement_wrapper": ["/usr/bin/time", "-l"]}
        changed_phase = {**self.new, "phase_id": "query"}
        for changed in (changed_argv, changed_wrapper, changed_phase):
            with self.subTest(changed=changed):
                with self.assertRaises(MODULE.CommandPathError):
                    self._check(self.old, changed)

    def test_capture_path_normalization_is_limited_to_argv_and_cwd(self) -> None:
        old = command(path=self.old_path, argv=["/tool", "/old/capture/file.swift"])
        new = command(path=self.new_path, argv=["/tool", "/new/capture/file.swift"])
        self.assertEqual(self._check(old, new), self.old_path)
        new["cwd"] = "/other/capture"
        with self.assertRaises(MODULE.CommandPathError):
            self._check(old, new)

    def test_signature_retains_every_recorded_environment_field(self) -> None:
        value = MODULE.command_input_signature(self.new, "/old/capture", "/new/capture")
        self.assertEqual(set(value["environment"]), set(self.new["environment"]))
        self.assertEqual(value["environment"]["PATH"], self.new_path)
        self.assertEqual(value["phase_id"], "frontend")

    def test_observer08_is_observer07_with_only_the_pinned_loader_extension(self) -> None:
        old_path = ROOT / "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-07.py"
        new_path = ROOT / "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py"
        old_tree = ast.parse(old_path.read_bytes(), filename=str(old_path))
        new_tree = ast.parse(new_path.read_bytes(), filename=str(new_path))

        def declarations(tree: ast.Module) -> dict[tuple[str, str], ast.AST]:
            result = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    result[(type(node).__name__, node.name)] = node
            return result

        old_decls = declarations(old_tree)
        new_decls = declarations(new_tree)
        self.assertEqual(set(old_decls), set(new_decls))
        for key in old_decls:
            if key == ("FunctionDef", "load_original"):
                continue
            self.assertEqual(ast.dump(old_decls[key], include_attributes=False),
                             ast.dump(new_decls[key], include_attributes=False), key)

        old_constants = {node.targets[0].id: ast.dump(node.value, include_attributes=False)
                         for node in old_tree.body if isinstance(node, ast.Assign) and
                         len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
        new_constants = {node.targets[0].id: ast.dump(node.value, include_attributes=False)
                         for node in new_tree.body if isinstance(node, ast.Assign) and
                         len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
        self.assertTrue(set(old_constants) <= set(new_constants))
        for name, value in old_constants.items():
            self.assertEqual(new_constants[name], value, name)
        self.assertEqual(
            {name for name in new_constants if name not in old_constants},
            {"COMMAND_PATH_HELPER_PATH", "COMMAND_PATH_HELPER_SHA256"},
        )

    def test_observer08_load_original_installs_only_the_native08_comparator(self) -> None:
        observer_path = ROOT / "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py"
        before_path = list(sys.path)
        spec = importlib.util.spec_from_file_location("native_observer08_tested", observer_path)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        observer = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(observer)
            retained = observer.load_original(ROOT)
            self.assertTrue(callable(retained._validate_control_command_equivalence))
            self.assertIs(retained._native08_command_input_delta_audit,
                          retained._validate_control_command_equivalence.audit)
            self.assertEqual(retained._assert_canonical_historical_binding.__name__,
                             "_assert_canonical_historical_binding")
            self.assertEqual(observer.COMMAND_PATH_HELPER_SHA256,
                             MODULE.sha_bytes(SOURCE.read_bytes()))
        finally:
            sys.path[:] = before_path


if __name__ == "__main__":
    unittest.main(verbosity=2)
