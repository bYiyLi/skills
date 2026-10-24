import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plugin_build", ROOT / "plugins" / "build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class PluginDistributionTests(unittest.TestCase):
    def test_disjoint_skills_and_complete_resources(self):
        core = builder.collect("development-standards")
        nexum = builder.collect("nexum-development")
        self.assertEqual(len([p for p in core if p.endswith("/SKILL.md")]), 3)
        self.assertEqual(len([p for p in nexum if p.endswith("/SKILL.md")]), 1)
        self.assertFalse(set(core) & set(nexum) - {"plugin.json"})
        self.assertNotIn(".app.json", core)
        self.assertNotIn(".app.json", nexum)
        for name, data in core.items():
            if name.endswith("/SKILL.md"):
                self.assertEqual(data, (ROOT / name).read_bytes())
    def test_private_binding_is_opt_in(self):
        files = builder.collect("nexum-development", "asdk_app_testfixture")
        self.assertEqual(json.loads(files[".app.json"])["apps"]["nexum"]["id"], "asdk_app_testfixture")
        for target, value in [("development-standards", "asdk_app_testfixture"), ("nexum-development", "plugin_wrong")]:
            with self.assertRaises(ValueError):
                builder.collect(target, value)
    def test_missing_resource_is_rejected(self):
        files = builder.collect("development-standards")
        del files["skills/develop-software/references/verification.md"]
        with self.assertRaises(ValueError):
            builder.validate(files, "development-standards")
    def test_archive_is_deterministic_and_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            path = builder.build("development-standards", folder)
            first = path.read_bytes()
            self.assertEqual(first, builder.build("development-standards", folder).read_bytes())
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), set(builder.collect("development-standards")))
    def test_source_output_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.build("development-standards", ROOT / "skills" / "bad-output")

if __name__ == "__main__":
    unittest.main()
