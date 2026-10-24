"""Contract for the May 2023 Writing descriptor dataset (no DB dependency)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = 'https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf'
VERSION = 'ielts_writing_2023_05'
CRITERIA = {
    'task1': ('task_achievement', 'coherence_cohesion', 'lexical_resource', 'grammatical_range_accuracy'),
    'task2': ('task_response', 'coherence_cohesion', 'lexical_resource', 'grammatical_range_accuracy'),
}
FIELDS = {'chunk_id', 'test_part', 'criterion', 'band', 'version', 'source_url', 'text'}


def validate_dataset(data):
    if not isinstance(data, dict) or not isinstance(data.get('chunks'), list):
        raise ValueError('Expected object with chunks list')
    seen_ids, seen_cells = set(), set()
    for c in data['chunks']:
        if not isinstance(c, dict) or set(c) != FIELDS:
            raise ValueError('Each chunk needs exactly text and six metadata fields')
        if c['test_part'] not in CRITERIA or c['criterion'] not in CRITERIA[c['test_part']]:
            raise ValueError('Invalid Task/criterion')
        if type(c['band']) is not int or c['band'] not in range(1, 10):
            raise ValueError('This source grid supports integer bands 1..9 only; band 0 is policy')
        if not isinstance(c['chunk_id'], str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', c['chunk_id']):
            raise ValueError('Invalid chunk_id')
        if c['version'] != VERSION or c['source_url'] != SOURCE_URL:
            raise ValueError('Unexpected descriptor source/version')
        if not isinstance(c['text'], str) or not c['text'].strip() or '\ufffd' in c['text']:
            raise ValueError('Empty or corrupt descriptor text')
        cell = (c['test_part'], c['criterion'], c['band'])
        if c['chunk_id'] in seen_ids or cell in seen_cells:
            raise ValueError('Duplicate ID or Task/criterion/band')
        seen_ids.add(c['chunk_id'])
        seen_cells.add(cell)
    expected = {(t, c, b) for t in CRITERIA for c in CRITERIA[t] for b in range(1, 10)}
    if seen_cells != expected or data.get('meta', {}).get('total_chunks') != 72:
        raise ValueError('Expected complete 72-cell source grid')
    return data['chunks']


def load_dataset(path=ROOT / 'data/processed/writing_descriptors.json'):
    return validate_dataset(json.loads(Path(path).read_text(encoding='utf-8')))
