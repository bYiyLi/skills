"""Validate distributed packages and example outputs, not model reliability."""

import json
import tempfile
import unittest
from pathlib import Path

import yaml
from skills_ref import read_properties, validate


REPO = Path(__file__).resolve().parents[1]
import package_checks as CHECKS
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
                CHECKS.check_resources(root)

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

    def test_consolidated_software_entrypoints(self):
        self.assertTrue((REPO / "skills/develop-software/SKILL.md").is_file())
        retired = {
            "software-requirements-spec", "software-design-spec",
            "software-development-plan", "software-doc-writing-standards",
            "software-usage-docs", "sync-software-docs",
        }
        self.assertFalse(retired & {p.name for p in SKILLS})

    def test_repository_document_links(self):
        documents = [REPO / "README.md", REPO / "AGENTS.md"]
        documents += list((REPO / "docs").rglob("*.md"))
        documents += list((REPO / "tests").rglob("*.md"))
        for document in documents:
            with self.subTest(document=str(document.relative_to(REPO))):
                CHECKS.local_targets(document, REPO)

    def test_development_templates_produce_linked_artifacts(self):
        fixture = json.loads((REPO / "tests/development-plan-values.json").read_text())
        assets = REPO / "skills/develop-software/assets"
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


    def test_implementation_template_works_without_roadmap(self):
        # This validates the asset, not a model's choice of plan cardinality.
        fixture = json.loads((REPO / "tests/development-plan-values.json").read_text())
        spec = fixture["phase-plan-template.md.tmpl"]
        template = (REPO / "skills/develop-software/assets/phase-plan-template.md.tmpl").read_text()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            design = target / "docs/design.md"
            design.parent.mkdir(parents=True)
            design.write_text("# Design\n\nConfirmed implementation input.\n")
            output = target / spec["output"]
            output.parent.mkdir(parents=True)
            rendered = CHECKS.render_template(template, spec["values"])
            output.write_text(rendered)
            self.assertEqual(output.read_text(), rendered)
            self.assertEqual(CHECKS.local_targets(output, target), {design.resolve()})
            self.assertEqual(set((target / "docs/development").rglob("*.md")), {output})
            self.assertFalse((target / "docs/development/README.md").exists())


if __name__ == "__main__":
    unittest.main()
