"""Validate distributed packages and example outputs, not model reliability."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml
from skills_ref import read_properties, validate


REPO = Path(__file__).resolve().parents[1]
# Reuse the existing, mutation-tested link and template checks.
SPEC = importlib.util.spec_from_file_location(
    "package_checks", REPO / "tests/nexum-chatgpt-development/test_package.py"
)
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)
SKILLS = sorted(path for path in (REPO / "skills").iterdir() if path.is_dir())


class CollectionTests(unittest.TestCase):
    def test_all_packages_use_native_format(self):
        self.assertTrue(SKILLS, "No skill packages found")
        names = []
        for root in SKILLS:
            with self.subTest(skill=root.name):
                self.assertEqual(validate(root), [])
                name = read_properties(root).name
                self.assertEqual(name, root.name)
                names.append(name)
        self.assertEqual(len(names), len(set(names)))

    def test_packaged_resources_are_routed_and_links_resolve(self):
        for root in SKILLS:
            with self.subTest(skill=root.name):
                routes = CHECKS.local_targets(root / "SKILL.md", root)
                resources = {
                    path.resolve()
                    for directory in ("references", "assets", "scripts")
                    for path in (root / directory).rglob("*")
                    if path.is_file()
                }
                self.assertFalse(resources - routes, f"Unrouted resources: {resources - routes}")
                for document in root.rglob("*"):
                    if document.is_file() and document.name.endswith((".md", ".md.tmpl")):
                        CHECKS.local_targets(document, root)

    def test_codex_invocation_metadata(self):
        for root in SKILLS:
            metadata = root / "agents/openai.yaml"
            if not metadata.exists():
                continue
            with self.subTest(skill=root.name):
                data = yaml.safe_load(metadata.read_text())
                interface = data["interface"]
                self.assertTrue(interface["display_name"].strip())
                self.assertGreaterEqual(len(interface["short_description"]), 25)
                self.assertLessEqual(len(interface["short_description"]), 64)
                self.assertIn(f"${root.name}", interface["default_prompt"])
                for key in ("icon_small", "icon_large"):
                    if key in interface:
                        self.assertTrue((root / interface[key]).is_file())

    def test_standalone_document_packages_share_the_management_contract(self):
        contracts = sorted((REPO / "skills").glob("*/references/doc-management-contract.md"))
        self.assertTrue(contracts)
        expected = contracts[0].read_text()
        for contract in contracts[1:]:
            with self.subTest(package=contract.parent.parent.name):
                self.assertEqual(contract.read_text(), expected)

    def test_repository_document_links(self):
        documents = [REPO / "README.md", REPO / "AGENTS.md"]
        documents += list((REPO / "docs").rglob("*.md"))
        documents += list((REPO / "tests").rglob("*.md"))
        for document in documents:
            with self.subTest(document=str(document.relative_to(REPO))):
                CHECKS.local_targets(document, REPO)

    def test_development_templates_produce_linked_artifacts(self):
        fixture = json.loads((REPO / "tests/development-plan-values.json").read_text())
        assets = REPO / "skills/software-development-plan/assets"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "docs").mkdir()
            (target / "docs/design.md").write_text("# Design\n\nUse the agreed TS toolchain.\n")
            for asset, spec in fixture.items():
                template = (assets / asset).read_text()
                self.assertEqual(set(CHECKS.TOKEN.findall(template)), set(spec["values"]))
                rendered = CHECKS.render_template(template, spec["values"])
                output = target / spec["output"]
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(rendered)
                self.assertEqual(output.read_text(), rendered)
            for document in target.rglob("*.md"):
                CHECKS.local_targets(document, target)


if __name__ == "__main__":
    unittest.main()
