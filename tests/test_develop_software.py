"""Consolidated package structure and isolated template consumption."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from skills_ref import validate
import package_checks as checks

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/develop-software"


class DevelopSoftwareTests(unittest.TestCase):
    def test_isolated_package_needs_no_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(shutil.copytree(SKILL, Path(directory) / SKILL.name)).resolve()
            self.assertEqual(validate(root), [])
            checks.check_resources(root)
            self.assertTrue(all(p.is_relative_to(root) for p in checks.reachable_resources(root)))

    def test_small_entrypoint_and_inactive_instruction_asset(self):
        # A maintenance budget, not proof of effective progressive loading.
        self.assertLessEqual(len((SKILL / "SKILL.md").read_text().splitlines()), 150)
        self.assertFalse(list((SKILL / "assets").rglob("AGENTS.md")))
        self.assertTrue((SKILL / "assets/AGENTS.md.tmpl").is_file())

    def test_all_assets_can_be_instantiated(self):
        # Unique synthetic values test substitution, not factual document quality.
        for asset in (SKILL / "assets").iterdir():
            with self.subTest(asset=asset.name):
                template = asset.read_text()
                fields = set(checks.TOKEN.findall(template))
                self.assertTrue(fields)
                values = {field: f"fixture-value-{field}" for field in fields}
                result = checks.render_template(template, values)
                self.assertNotIn("{{", result)
                for value in values.values():
                    self.assertIn(value, result)

    def test_repository_and_journal_templates_with_inspected_fixture_values(self):
        values = json.loads((REPO / "tests/develop-software/template-values.json").read_text())
        reference_text = "\n".join(p.read_text() for p in (SKILL / "references").glob("*.md"))
        with tempfile.TemporaryDirectory() as directory:
            for name, output_name in [("AGENTS.md.tmpl", "AGENTS.md"),
                                      ("daily-log.md", f"docs/vlog/{values['DATE']}.md")]:
                with self.subTest(asset=name):
                    text = (SKILL / "assets" / name).read_text()
                    for field in checks.TOKEN.findall(text):
                        self.assertIn(field, reference_text)
                    result = checks.render_template(text, values)
                    output = Path(directory) / output_name
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(result)
                    self.assertEqual(output.read_text(), result)
                    checks.local_targets(output, Path(directory))


class ResourceGraphTests(unittest.TestCase):
    def fixture(self, directory):
        root = (Path(directory) / "example").resolve()
        (root / "references").mkdir(parents=True)
        (root / "assets").mkdir()
        (root / "SKILL.md").write_text("# Example\n[route](references/topic.md)\n")
        (root / "references/topic.md").write_text("Use [template](../assets/output.md.tmpl) when drafting.\n")
        (root / "assets/output.md.tmpl").write_text("# {{TITLE}}\n")
        return root

    def test_reference_to_asset_route_is_sufficient(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            checks.check_resources(root)
            self.assertEqual(checks.reachable_resources(root), {
                root / "SKILL.md", root / "references/topic.md", root / "assets/output.md.tmpl"
            })

    def test_missing_second_hop_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            (root / "assets/output.md.tmpl").unlink()
            with self.assertRaises(ValueError):
                checks.check_resources(root)

    def test_wrong_case_second_hop_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            p = root / "references/topic.md"
            p.write_text(p.read_text().replace("output.md.tmpl", "Output.md.tmpl"))
            with self.assertRaises(ValueError):
                checks.check_resources(root)

    def test_second_hop_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            (Path(directory) / "outside.md").write_text("outside")
            (root / "references/topic.md").write_text("[outside](../../outside.md)\n")
            with self.assertRaises(ValueError):
                checks.check_resources(root)

    def test_unreachable_cycle_does_not_count_as_routing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            (root / "references/a.md").write_text("[b](b.md)\n")
            (root / "references/b.md").write_text("[a](a.md)\n")
            with self.assertRaises(ValueError):
                checks.check_resources(root)

    def test_reachable_cycle_terminates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            p = root / "references/topic.md"
            p.write_text(p.read_text() + "[entry](../SKILL.md)\n")
            checks.check_resources(root)

    def test_directory_link_does_not_load_its_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            (root / "references/topic.md").write_text("[assets](../assets/)\n")
            with self.assertRaises(ValueError):
                checks.check_resources(root)


if __name__ == "__main__":
    unittest.main()
