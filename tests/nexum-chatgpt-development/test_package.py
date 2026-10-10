"""Nexum environment package and Project Instructions template checks."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from skills_ref import read_properties, validate

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests"))
from package_checks import TOKEN, check_resources, local_targets, render_template

SKILL = REPO / "skills/nexum-chatgpt-development"
FIXTURE = Path(__file__).with_name("template-values.json")


class PackageTests(unittest.TestCase):
    def copy_skill(self, directory: str) -> Path:
        return Path(shutil.copytree(SKILL, Path(directory) / SKILL.name))

    def test_official_format(self):
        self.assertEqual(validate(SKILL), [])
        properties = read_properties(SKILL)
        self.assertEqual(properties.name, SKILL.name)
        self.assertTrue(properties.description.strip())

    def test_official_validator_rejects_missing_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_skill(directory)
            (root / "SKILL.md").unlink()
            self.assertTrue(validate(root))

    def test_entrypoint_context_budget(self):
        # Package-specific maintenance budget, not an Agent Skills format rule.
        self.assertLessEqual(len((SKILL / "SKILL.md").read_text().splitlines()), 150)

    def test_resource_routes_and_links(self):
        check_resources(SKILL)

    def test_missing_reference_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_skill(directory)
            (root / "references/local-execution.md").unlink()
            with self.assertRaises(ValueError):
                check_resources(root)

    def test_orphan_resource_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_skill(directory)
            (root / "references/orphan.md").write_text("Not routed.\n")
            with self.assertRaises(ValueError):
                check_resources(root)

    def test_wrong_case_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_skill(directory)
            entry = root / "SKILL.md"
            entry.write_text(entry.read_text().replace("references/local-execution.md", "references/Local-execution.md"))
            with self.assertRaises(ValueError):
                check_resources(root)

    def test_escaping_link_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_skill(directory)
            entry = root / "SKILL.md"
            entry.write_text(entry.read_text() + "\n[escape](../outside.md)\n")
            with self.assertRaises(ValueError):
                check_resources(root)

    def test_templates_are_not_active_nested_instructions(self):
        self.assertFalse(list((SKILL / "assets").rglob("AGENTS.md")))
        self.assertTrue((SKILL / "assets/project-instructions.md").is_file())

    def test_template_fields_have_fixture_and_documentation(self):
        values = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fields = set()
        for asset in (SKILL / "assets").iterdir():
            fields.update(TOKEN.findall(asset.read_text(encoding="utf-8")))
        self.assertEqual(fields, set(values))
        reference_text = "\n".join(p.read_text() for p in (SKILL / "references").glob("*.md"))
        for field in fields:
            with self.subTest(field=field):
                self.assertIn(field, reference_text)

    def test_templates_render_to_output_files(self):
        values = json.loads(FIXTURE.read_text(encoding="utf-8"))
        outputs = {
            "project-instructions.md": "docs/chatgpt-project.md",
        }
        with tempfile.TemporaryDirectory() as directory:
            for asset_name, output_name in outputs.items():
                with self.subTest(asset=asset_name):
                    template = (SKILL / "assets" / asset_name).read_text(encoding="utf-8")
                    rendered = render_template(template, values)
                    output = Path(directory) / output_name
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(rendered, encoding="utf-8")
                    self.assertEqual(output.read_text(encoding="utf-8"), rendered)
                    for field in TOKEN.findall(template):
                        self.assertIn(values[field], rendered)

    def test_missing_template_value_is_rejected(self):
        with self.assertRaises(ValueError):
            render_template("Project {{PROJECT_NAME}}", {})

    def test_unresolved_injected_template_value_is_rejected(self):
        with self.assertRaises(ValueError):
            render_template("{{PROJECT_NAME}}", {"PROJECT_NAME": "{{UNRESOLVED}}"})

    def test_maintainer_document_local_links(self):
        for document in [
            REPO / "docs/skills/nexum-chatgpt-development.md",
            Path(__file__).with_name("scenarios.md"),
        ]:
            local_targets(document, REPO)


if __name__ == "__main__":
    unittest.main()
