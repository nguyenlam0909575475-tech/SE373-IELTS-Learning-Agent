import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from scripts.descriptor_data import CRITERIA, ROOT, SOURCE_URL, VERSION, load_dataset
from scripts.rebuild_vectorstore import COLLECTION, rebuild


def _synthetic_dataset_path(tmp_dir):
    chunks = []
    for t in CRITERIA:
        for c in CRITERIA[t]:
            for b in range(1, 10):
                chunks.append({
                    'chunk_id': f'{t}_{c}_{b}',
                    'test_part': t,
                    'criterion': c,
                    'band': b,
                    'version': VERSION,
                    'source_url': SOURCE_URL,
                    'text': f'Descriptor for {t} {c} band {b}.',
                })
    data = {'meta': {'total_chunks': 72}, 'chunks': chunks}
    path = Path(tmp_dir) / 'synthetic_descriptors.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


class RebuildTests(unittest.TestCase):
    def test_persistence_filters_stale_ids_and_other_collection(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            client = chromadb.PersistentClient(path=tmp)
            other = client.create_collection('unrelated', embedding_function=None)
            other.add(ids=['keep'], embeddings=[[1., 0., 0.]])
            source = ROOT / 'data/processed/writing_descriptors.json'
            if not source.is_file():
                source = _synthetic_dataset_path(tmp)
            # Only embedding inference is replaced; persistence/query/filtering use real Chroma.
            # Distinct stable vectors avoid ANN tie/deleted-node behaviour when
            # every source cell and the stale record have the exact same vector.
            # This remains a persistence/filter test, not a semantic quality test.
            def synthetic_embeddings(self, input):
                return [[(byte + 1) / 256 for byte in hashlib.sha256(text.encode()).digest()[:3]]
                        for text in input]

            with patch.object(DefaultEmbeddingFunction, '__call__', synthetic_embeddings):
                rebuild(source, tmp)
                col = client.get_collection(COLLECTION)
                col.add(ids=['stale'], documents=['old'], embeddings=[[1., 0., 0.]], metadatas=[{'test_part': 'task1'}])
                rebuild(source, tmp)
            reopened = chromadb.PersistentClient(path=tmp).get_collection(COLLECTION)
            self.assertEqual(reopened.count(), 72)
            self.assertNotIn('stale', reopened.get()['ids'])
            self.assertEqual(other.get()['ids'], ['keep'])
            result = reopened.query(query_embeddings=[[1., 0., 0.]], n_results=3,
                where={'$and': [{'test_part': 'task1'}, {'criterion': 'lexical_resource'}]})
            self.assertEqual(len(result['ids'][0]), 3)
            self.assertTrue(all(m['test_part'] == 'task1' and m['criterion'] == 'lexical_resource' for m in result['metadatas'][0]))
            stored = reopened.get(include=['documents', 'metadatas'])
            actual = {cid: dict(meta, text=text) for cid, meta, text in zip(stored['ids'], stored['metadatas'], stored['documents'], strict=False)}
            self.assertEqual(actual, {c['chunk_id']: c for c in load_dataset(source)})

    def test_invalid_source_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, db = Path(tmp) / 'bad.json', Path(tmp) / 'db'
            source.write_text(json.dumps({'chunks': []}), encoding='utf-8')
            with self.assertRaises(ValueError):
                rebuild(source, db)
            self.assertFalse(db.exists())
