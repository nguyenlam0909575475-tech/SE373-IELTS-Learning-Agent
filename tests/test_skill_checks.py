import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from scripts.sync_writing_schema import export_schema
from src.skill_checks import run_checks

ROOT = Path(__file__).resolve().parents[1]


class SkillChecksTests(unittest.TestCase):
    def test_delegates_preserving_objects_and_independent_context(self):
        validators = Mock()
        quote_issue, ref_issue, consistency_issue = object(), object(), object()
        validators.quote_validator.return_value = [quote_issue]
        validators.refs_validator.return_value = [ref_issue]
        validators.consistency_validator.return_value = [consistency_issue]
        assessment, chunks, plagiarism, security = object(), [object()], object(), object()
        result = run_checks(assessment, "Original essay", chunks, validators=validators,
                            word_count=20, overall_band=6.25, plagiarism=plagiarism,
                            security=security, off_topic=True)
        self.assertEqual(result, [quote_issue, ref_issue, consistency_issue])
        validators.quote_validator.assert_called_once_with(assessment, "Original essay")
        validators.refs_validator.assert_called_once_with(assessment, chunks)
        validators.consistency_validator.assert_called_once_with(
            assessment, word_count=20, overall_band=6.25, plagiarism=plagiarism,
            security=security, off_topic=True)

    def test_dependency_failure_does_not_become_success(self):
        validators = Mock()
        validators.quote_validator.side_effect = RuntimeError("dependency unavailable")
        with self.assertRaises(RuntimeError):
            run_checks({}, "", [], validators=validators, word_count=0, overall_band=0,
                       plagiarism={}, security={}, off_topic=False)

    def test_invalid_validator_shape_is_not_accepted(self):
        validators = Mock()
        validators.quote_validator.return_value = {"valid": True, "errors": []}
        validators.refs_validator.return_value = []
        validators.consistency_validator.return_value = []
        with self.assertRaises(TypeError):
            run_checks({}, "", [], validators=validators, word_count=0, overall_band=0,
                       plagiarism={}, security={}, off_topic=False)

    def test_skill_entrypoint_is_executable_without_member4_import(self):
        path = ROOT / "skills/writing-assessment/checks.py"
        spec = importlib.util.spec_from_file_location("writing_skill_checks", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIs(module.run_checks, run_checks)

    def test_schema_export_uses_actual_model_and_detects_drift(self):
        schema = {"type": "object", "properties": {"overall_band": {"type": "number"}}}
        model = Mock()
        model.model_json_schema.return_value = schema
        fake = types.ModuleType("test_member3_schema")
        fake.WritingAssessment = model
        with tempfile.TemporaryDirectory() as tmp, patch.dict("sys.modules", {fake.__name__: fake}):
            path = Path(tmp) / "schema.json"
            export_schema(fake.__name__, path)
            self.assertEqual(json.loads(path.read_text()), schema)
            export_schema(fake.__name__, path, check=True)
            path.write_text('{}', encoding="utf-8")
            with self.assertRaises(ValueError):
                export_schema(fake.__name__, path, check=True)

    def test_missing_member3_model_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schema.json"
            with self.assertRaises(ImportError):
                export_schema("nonexistent_member3_model", path)
            self.assertFalse(path.exists())

    def test_yaml_contract_is_synced_and_checked_against_model(self):
        model = Mock()
        model.model_json_schema.return_value = {"type": "object", "required": ["overall_band"]}
        fake = types.ModuleType("test_member3_manifest")
        fake.WritingAssessment = model
        with tempfile.TemporaryDirectory() as tmp, patch.dict("sys.modules", {fake.__name__: fake}):
            output, manifest = Path(tmp) / "schema.json", Path(tmp) / "skill.yaml"
            manifest.write_text(json.dumps({"output": {}, "schema_authority": {}}), encoding="utf-8")
            export_schema(fake.__name__, output, manifest=manifest)
            contract = json.loads(manifest.read_text())
            self.assertEqual(contract["output"]["json_schema"], model.model_json_schema())
            export_schema(fake.__name__, output, manifest=manifest, check=True)
            contract["output"]["json_schema"] = {}
            manifest.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaises(ValueError):
                export_schema(fake.__name__, output, manifest=manifest, check=True)


if __name__ == "__main__":
    unittest.main()
