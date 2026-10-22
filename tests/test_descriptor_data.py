import json
import copy
import unittest
import tempfile
import pymupdf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from scripts.descriptor_data import load_dataset, validate_dataset


class DescriptorTests(unittest.TestCase):
    def test_extraction_rejects_modified_pdf_with_same_layout(self):
        from scripts.extract_descriptors import extract
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / 'altered.pdf'
            with pymupdf.open(ROOT / 'ielts-writing-band-descriptors.pdf') as doc:
                metadata = dict(doc.metadata)
                metadata['subject'] = 'Modified source for regression testing'
                doc.set_metadata(metadata)
                doc.save(altered)
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                extract(altered)

    def test_validation_rejects_corruption(self):
        original = json.loads((ROOT / 'data/processed/writing_descriptors.json').read_text(encoding='utf-8'))
        for field, value in [('test_part', 'task1_task2'), ('criterion', 'task_response'), ('text', ''), ('band', True), ('band', 6.5), ('version', 'invented'), ('source_url', 'https://example.com')]:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(original)
                data['chunks'][0][field] = value
                with self.assertRaises(ValueError):
                    validate_dataset(data)

    def test_duplicate_and_missing_cells_rejected(self):
        original = json.loads((ROOT / 'data/processed/writing_descriptors.json').read_text(encoding='utf-8'))
        for chunks in [original['chunks'][:-1], original['chunks'] + [original['chunks'][0]]]:
            with self.assertRaises(ValueError):
                validate_dataset({'meta': original['meta'], 'chunks': chunks})

    def test_source_geometry_reproduces_every_cell(self):
        from scripts.extract_descriptors import extract
        data, audit = extract(ROOT / 'ielts-writing-band-descriptors.pdf')
        self.assertEqual(data['chunks'], load_dataset())
        self.assertEqual(len(audit['cells']), 72)
        self.assertEqual({p['test_part'] for p in audit['band_zero_policies']}, {'task1', 'task2'})
        self.assertTrue(all('\ufffd' not in p['text'] for p in audit['band_zero_policies']))

    def test_band_two_column_boundary(self):
        chunks = load_dataset()
        ta = next(c['text'] for c in chunks if c['test_part'] == 'task1' and c['criterion'] == 'task_achievement' and c['band'] == 2)
        cc = next(c['text'] for c in chunks if c['test_part'] == 'task1' and c['criterion'] == 'coherence_cohesion' and c['band'] == 2)
        self.assertNotIn('off-topic', ta)
        self.assertIn('off-topic', cc)
    def test_task_specific_complete_grid(self):
        chunks = json.loads((ROOT / 'data/processed/writing_descriptors.json').read_text(encoding='utf-8'))['chunks']
        self.assertEqual(len(chunks), 72)
        self.assertEqual({c['test_part'] for c in chunks}, {'task1', 'task2'})
        self.assertEqual(len({c['chunk_id'] for c in chunks}), 72)

    def test_task_specific_paragraphing(self):
        chunks = json.loads((ROOT / 'data/processed/writing_descriptors.json').read_text(encoding='utf-8'))['chunks']
        matches = {c['test_part']: c['text'] for c in chunks if c['criterion'] == 'coherence_cohesion' and c['band'] == 7}
        self.assertNotEqual(matches.get('task1'), matches.get('task2'))
        self.assertIn('Paragraphing', matches['task2'])


if __name__ == '__main__':
    unittest.main()
