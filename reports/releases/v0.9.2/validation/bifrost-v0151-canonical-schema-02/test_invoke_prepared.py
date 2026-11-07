from pathlib import Path, PurePosixPath
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
module = ModuleType("typed_path_repair_test")
module.__file__ = str(HERE / "invoke_prepared.py")
exec(compile((HERE / "invoke_prepared.py").read_bytes(), module.__file__, "exec"), module.__dict__)


class TypedPathRepairTests(unittest.TestCase):
    def test_both_actual_producer_paths_read_the_original_bytes(self):
        legacy = module.load_adapted()
        for path in module.STRING_PATHS:
            document, raw = legacy._read_json_under(module.ROOT, path, "actual producer input")
            self.assertIsInstance(document, dict)
            self.assertEqual(raw, (module.ROOT / path).read_bytes())

    def test_original_typed_api_stays_unchanged(self):
        legacy = module.load_adapted()
        path = PurePosixPath("schemas/result.schema.json")
        document, raw = legacy._read_json_under(module.ROOT, path, "typed source schema")
        self.assertEqual(document["$id"], "https://dataflowbench.dev/schemas/result/v1")
        self.assertEqual(raw, (module.ROOT / path).read_bytes())

    def test_unreviewed_strings_still_fail(self):
        legacy = module.load_adapted()
        for path in ("schemas/result.schema.json", "../escape.json", "/tmp/foreign.json"):
            with self.assertRaises(ValueError):
                legacy._read_json_under(module.ROOT, path, "near miss")

    def test_freshly_loaded_invocation_retains_original_implementation(self):
        legacy = module.load_adapted()
        self.assertEqual(Path(legacy.invoke.__code__.co_filename), module.ROOT / module.OLD_REL)
        self.assertEqual(legacy.RUNNER_SHA256, "99d997b31024ee7ff5edbee381cf2addff5f25d6851cc19980f515142b9508a5")
        self.assertEqual(legacy.TIMEOUT_SECONDS, 1800)


if __name__ == "__main__":
    unittest.main()
