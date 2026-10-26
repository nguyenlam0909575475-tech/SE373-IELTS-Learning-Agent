import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_writing_benchmark import check_benchmark, load_benchmark, validate_record

ROOT = Path(__file__).resolve().parents[1]


class WritingBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(
            case_id="example",
            task_type="task2",
            exam_question="Discuss both views.",
            essay="Original student writing.",
            material=None,
            scores=dict(
                task_response=6,
                coherence_cohesion=6,
                lexical_resource=5,
                grammatical_range_accuracy=5,
                overall_band=5.5,
            ),
            feedback="Published feedback.",
            source="https://example.org/essay",
        )

    def test_compact_record_rejects_redundant_fields(self):
        validate_record(self.row)
        for key in ("split", "word_count", "review_status", "provenance"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_record({**self.row, key: "unused"})

    def test_wrong_criterion_boolean_and_nan_are_rejected(self):
        for key, value in [("overall_band", True), ("task_response", float("nan"))]:
            row = copy.deepcopy(self.row)
            row["scores"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_record(row)
        row = copy.deepcopy(self.row)
        row["scores"]["task_achievement"] = row["scores"].pop("task_response")
        with self.assertRaises(ValueError):
            validate_record(row)

    def test_task1_material_is_portable_and_confined_to_evals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "evals/materials/chart.png"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"chart image")
            row = copy.deepcopy(self.row)
            row.update(
                task_type="task1", exam_question="The chart below shows the data.", material="evals/materials/chart.png"
            )
            row["scores"]["task_achievement"] = row["scores"].pop("task_response")
            validate_record(row, root=root)
            for bad in (
                "http://127.0.0.1:8765/chart.png",
                "data/benchmark_local/chart.png",
                "evals/materials/../../../outside.png",
                "evals/materials/missing.png",
            ):
                with self.subTest(path=bad), self.assertRaises(ValueError):
                    validate_record({**row, "material": bad}, root=root)
            with self.assertRaises(ValueError):
                validate_record({**row, "exam_question": "Write a letter to your manager."}, root=root)

    def test_final_dataset_covers_both_tasks_and_complete_materials(self):
        report = check_benchmark()
        self.assertEqual(report["total"], 84)
        self.assertEqual(report["splits"], {"dev": 69, "test": 15})
        self.assertEqual(report["tasks"], {"task1": 31, "task2": 53})

    def test_reference_content_and_split_match_the_original_84_essays(self):
        fields = ("case_id", "task_type", "exam_question", "essay", "scores", "feedback", "source")
        protected = [
            dict(split=split, **{key: r[key] for key in fields})
            for split in ("dev", "test")
            for r in sorted(load_benchmark(split), key=lambda r: r["case_id"])
        ]
        checksum = hashlib.sha256(json.dumps(protected, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        self.assertEqual(checksum, "2383d5374255f70495d60fdfab594d7efc3ec6f5b9150b579da538eac6614b4b")

    def test_cross_split_duplicate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in ("dev", "test"):
                path = root / f"evals/benchmark_{split}/benchmark.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps([{**self.row, "case_id": split}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "across dev/test"):
                check_benchmark(root=root)


if __name__ == "__main__":
    unittest.main()
